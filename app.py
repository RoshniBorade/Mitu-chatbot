from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import json
import os
import random
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a random secret key for production
CORS(app)

# ---------- Database Setup ----------
DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id INTEGER,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        conn.commit()

init_db()

# ---------- Load intents ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

with open(INTENTS_PATH, "r", encoding="utf-8") as file:
    intents = json.load(file)

# ---------- Text preprocessing ----------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text

# ---------- Intent matching ----------
def match_intent(user_text):
    best_intent = None
    highest_score = 0

    for intent in intents["intents"]:
        score = 0
        for keyword in intent.get("keywords", []):
            # Check for keyword in processed user text
            if keyword.lower() in user_text:
                # Score based on how many words match to favor specific keywords
                # e.g. "data science" (2 words) > "ai" (1 word)
                score += len(keyword.split())

        if score > highest_score:
            highest_score = score
            best_intent = intent

    return best_intent

# ---------- Chat response ----------
def get_response(user_input):
    user_text = preprocess_text(user_input)
    intent = match_intent(user_text)

    if intent:
        return random.choice(intent["responses"])

    return "Sorry, I couldn't understand that. For more details, please contact us at +91 9960 16 3010 or visit our Pune/Nashik office."

# ---------- API endpoint ----------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    current_session_id = request.args.get("session_id")
    sessions_list = []
    messages = []

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Fetch all sessions for the user
            cursor.execute("SELECT id, title FROM sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            sessions_list = cursor.fetchall()

            # If a session ID is provided, fetch its messages
            if current_session_id:
                cursor.execute("SELECT sender, message FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (current_session_id,))
                messages = cursor.fetchall()
            elif sessions_list:
             # Optional: Redirect to the most recent session if none selected, or stay on new chat
             # For now, let's start a new chat by default if no session specified
             pass

    except Exception as e:
        print(f"Error fetching data: {e}")

    return render_template("index.html", user_name=session.get("user_name"), messages=messages, sessions=sessions_list, current_session_id=current_session_id)

@app.route("/new_chat")
def new_chat():
    return redirect(url_for("index"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
                conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"reply": "Please log in to chat."}), 401
    
    data = request.get_json()
    user_message = data.get("message", "")
    session_id = data.get("session_id")
    user_id = session["user_id"]

    bot_reply = get_response(user_message)

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            
            # Create new session if none exists
            if not session_id:
                # Use first few words as title
                title = " ".join(user_message.split()[:5]) + "..."
                cursor.execute("INSERT INTO sessions (user_id, title) VALUES (?, ?)", (user_id, title))
                session_id = cursor.lastrowid
            
            cursor.execute("INSERT INTO messages (user_id, session_id, sender, message) VALUES (?, ?, ?, ?)", 
                           (user_id, session_id, "user", user_message))
            cursor.execute("INSERT INTO messages (user_id, session_id, sender, message) VALUES (?, ?, ?, ?)", 
                           (user_id, session_id, "bot", bot_reply))
            conn.commit()
    except Exception as e:
        print(f"Error saving message: {e}")
        return jsonify({"error": str(e)}), 500

    return jsonify({"reply": bot_reply, "session_id": session_id})

if __name__ == "__main__":
    app.run(debug=True)
