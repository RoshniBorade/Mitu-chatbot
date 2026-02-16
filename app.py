from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from enrollment import EnrollmentFlow
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()
import os
import random
import re
import sqlite3
import requests
from werkzeug.security import generate_password_hash, check_password_hash

from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import bcrypt
import datetime
import jwt

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'MITU_SECRET_KEY_2024')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
# Allow HTTP for OAuth (Development only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Security Headers
# Talisman(app, content_security_policy=None) # Disable CSP for now to allow external fonts/styles if needed, or configure it

# CSRF Protection
csrf = CSRFProtect(app)
app.config['WTF_CSRF_TIME_LIMIT'] = None # Token valid for session lifetime

# Mail Configuration (Example using Gmail)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')

mail = Mail(app)

CORS(app)

# ---------- Google OAuth Configuration ----------
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# ---------- Helper Functions ----------
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password.encode('utf-8'))

def send_email(subject, recipient, body_html):
    # Print to console for development convenience
    print(f"\n--- DEBUG: Sending Email ---")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    # Extract link if present in html for easier access in terminal
    import re
    links = re.findall(r'href="([^"]+)"', body_html)
    if links:
        print(f"Links found: {links[0]}")
    print(f"---------------------------\n")

    msg = Message(subject, recipients=[recipient])
    msg.html = body_html
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e} (Expected if SMTP not configured)")

def create_verification_token(email):
    return jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.secret_key, algorithm="HS256")

def create_reset_token(email):
    return jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)}, app.secret_key, algorithm="HS256")

def verify_token(token):
    try:
        data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        return data['email']
    except jwt.ExpiredSignatureError:
        return "expired"
    except jwt.InvalidTokenError:
        return None

# ---------- Database Setup ----------
DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # User Table Update
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'Student',
                google_id TEXT,
                is_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                reset_token TEXT,
                reset_token_expiry DATETIME,
                failed_attempts INTEGER DEFAULT 0,
                lock_until DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Check for missing columns in existing users table (Migration)
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Student'")
        if 'google_id' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        if 'is_verified' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0")
        if 'verification_token' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
        if 'reset_token' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        if 'reset_token_expiry' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME")
        if 'failed_attempts' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0")
        if 'lock_until' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN lock_until DATETIME")
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")

        # Login Activity Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                course_name TEXT,
                status TEXT DEFAULT 'Pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
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
        email = request.form["email"].lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form.get("role", "Student")

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for("signup"))

        # Password complexity validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("signup"))
        if not re.search(r'[A-Z]', password):
            flash("Password must contain at least one capital letter.", "error")
            return redirect(url_for("signup"))
        if not re.search(r'[0-9]', password):
            flash("Password must contain at least one number.", "error")
            return redirect(url_for("signup"))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            flash("Password must contain at least one special character.", "error")
            return redirect(url_for("signup"))

        hashed_pw = hash_password(password)
        token = create_verification_token(email)

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (name, email, password, role, verification_token, is_verified) 
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (name, email, hashed_pw, role, token))
                conn.commit()
            
            # Send welcome email (Optional, or removed as per request) - Verification skipped
            # base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
            # verify_url = f"{base_url}/verify_email/{token}"
            # html = render_template('emails/verify_email.html', name=name, verify_url=verify_url)
            # send_email("Welcome to MITU Skillologies", email, html)

            flash("Account created! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists!", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/verify_email/<token>")
def verify_email(token):
    email = verify_token(token)
    if not email or email == "expired":
        flash("Invalid or expired verification link.", "error")
        return redirect(url_for("signup"))
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified = 1, verification_token = NULL WHERE email = ?", (email,))
        conn.commit()
    
    flash("Email verified! You can now login.", "success")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]
        remember = request.form.get("remember") == "on"

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, password, role, is_verified, failed_attempts, lock_until FROM users WHERE LOWER(email) = ?", (email.lower(),))
            user = cursor.fetchone()

            if not user:
                flash("User not found.", "error")
                return redirect(url_for("login"))

            user_id, name, email_val, hashed_pw, role, is_verified, failed_attempts, lock_until = user

            # Account locking removed as per request
            # if lock_until: ...

            if user and check_password(hashed_pw, password):
                # Email verification check removed as per request
                # if not is_verified: ...

                # Reset failed attempts logic removed/simplified
                cursor.execute("UPDATE users SET failed_attempts = 0, lock_until = NULL WHERE id = ?", (user_id,))
                
                # Log success
                cursor.execute("INSERT INTO login_activity (user_id, ip_address, status) VALUES (?, ?, ?)", 
                               (user_id, request.remote_addr, "Success"))
                conn.commit()

                session["user_id"] = user_id
                session["user_name"] = name
                session["user_role"] = role
                if remember:
                    session.permanent = True
                
                # Role-based redirect
                if role == "Admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "Counselor":
                    return redirect(url_for("index")) 
                else:
                    return redirect(url_for("index"))
            else:
                # Handle failed attempt - No locking logic
                flash("Invalid email or password!", "error")

                # Just log the failure, don't lock
                cursor.execute("INSERT INTO login_activity (user_id, ip_address, status) VALUES (?, ?, ?)", 
                               (user_id, request.remote_addr, "Failed"))
                conn.commit()
                return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].lower()
        token = create_reset_token(email)
        expiry = (datetime.datetime.now() + datetime.timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE LOWER(email) = ?", 
                           (token, expiry, email.lower()))
            conn.commit()

        base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
        reset_url = f"{base_url}/reset_password/{token}"
        html = render_template('emails/reset_password.html', reset_url=reset_url)
        send_email("Reset your MITU password", email, html)

        flash("Password reset link sent to your email.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_token(token)
    if not email or email == "expired":
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("reset_password.html", token=token)

        hashed_pw = hash_password(password)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ?, reset_token = NULL, reset_token_expiry = NULL, is_verified = 1 WHERE LOWER(email) = ?", 
                           (hashed_pw, email.lower()))
            conn.commit()

        flash("Password updated successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("user_role") != "Admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("index"))
    
    # Filters
    course_filter = request.args.get('course', '')
    status_filter = request.args.get('status', '')
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Fetch login activity logs
        cursor.execute("""
            SELECT l.timestamp, u.name, u.email, l.ip_address, l.status 
            FROM login_activity l 
            JOIN users u ON l.user_id = u.id 
            ORDER BY l.timestamp DESC LIMIT 100
        """)
        logs = cursor.fetchall()

        # Fetch all registered users
        cursor.execute("SELECT id, name, email, role, is_verified, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()

        # Build query for leads with filters
        query = "SELECT id, full_name, email, phone, course_name, status, created_at FROM leads"
        params = []
        where_clauses = []
        
        if course_filter:
            where_clauses.append("course_name = ?")
            params.append(course_filter)
        if status_filter:
            where_clauses.append("status = ?")
            params.append(status_filter)
            
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        leads = cursor.fetchall()

        # Analytics (Global Totals)
        total_users = len(users)
        
        # Get absolute totals for cards regardless of filters
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads_absolute = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Converted'")
        converted_leads_absolute = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Pending'")
        pending_leads_absolute = cursor.fetchone()[0]

        # Leads by Course
        cursor.execute("SELECT course_name, COUNT(*) FROM leads GROUP BY course_name")
        leads_by_course = cursor.fetchall()
        
        # Leads by Status
        cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
        leads_by_status = cursor.fetchall()

        # Calculate conversion rate
        conversion_rate = (converted_leads_absolute / total_leads_absolute * 100) if total_leads_absolute > 0 else 0
        conversion_rate = round(conversion_rate, 1)

    return render_template("admin_dashboard.html", 
                           logs=logs, 
                           users=users, 
                           leads=leads,
                           total_users=total_users,
                           total_leads=total_leads_absolute,
                           leads_by_course=leads_by_course,
                           leads_by_status=leads_by_status,
                           pending_leads=pending_leads_absolute,
                           converted_leads=converted_leads_absolute,
                           conversion_rate=conversion_rate,
                           course_filter=course_filter,
                           status_filter=status_filter,
                           all_courses=EnrollmentFlow.COURSES,
                           all_statuses=['Pending', 'Contacted', 'Converted'])

@app.route("/admin/verify_user/<int:user_id>")
def admin_verify_user(user_id):
    if "user_id" not in session or session.get("user_role") != "Admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("index"))
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
        conn.commit()
    
    flash("User verified successfully!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/update_lead_status/<int:lead_id>/<status>")
def update_lead_status(lead_id, status):
    if "user_id" not in session or session.get("user_role") != "Admin":
        flash("Unauthorized access!", "error")
        return redirect(url_for("index"))
    
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
        conn.commit()
    
    flash(f"Lead status updated to {status}", "success")
    return redirect(url_for("admin_dashboard"))

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

    bot_reply = ""
    buttons = []
    progress = ""
    
    # Check for active enrollment flow
    if session.get('flow') == 'enrollment':
        response = EnrollmentFlow.handle_input(user_message)
        bot_reply = response.get('reply')
        buttons = response.get('buttons', [])
        progress = response.get('progress', "")
        
        # Check if lead needs to be saved
        if response.get('save_lead'):
            lead_data = response.get('lead_data')
            try:
                with sqlite3.connect(DATABASE) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO leads (user_id, full_name, email, phone, course_name)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, lead_data['name'], lead_data['email'], lead_data['phone'], lead_data['course']))
                    conn.commit()
            except Exception as e:
                print(f"Error saving lead: {e}")
            
            # Clear session
            session.pop('flow', None)
            session.pop('step', None)
            session.pop('enroll_data', None)
            
    else:
        # Check if user wants to enroll
        # Check intent or keywords "enroll", "register", "join course"
        user_text_lower = user_message.lower()
        if any(w in user_text_lower for w in ['enroll', 'register', 'join course', 'book demo']):
            response = EnrollmentFlow.start_flow()
            bot_reply = response.get('reply')
            progress = response.get('progress')
        elif user_message.strip().lower() == 'courses' or any(w in user_text_lower for w in ['explore courses', 'show courses']):
            # Special handling for courses
            bot_reply = "You can explore our courses in the courses section. Just click the button below or the 'Courses' link in the sidebar!"
            progress = "Opening Courses..."
        else:
            bot_reply = get_response(user_message)
        
        # Add quick replies for general chat (if not in a guided flow)
        if not session.get('flow'):
            buttons = [
            {"label": "Enroll Now", "payload": "enroll"},
            {"label": "Explore Courses", "payload": "courses"},
            {"label": "Contact Us", "payload": "contact"}
            ]

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

    return jsonify({
        "reply": bot_reply, 
        "session_id": session_id, 
        "buttons": buttons, 
        "progress": progress
    })

@app.route("/google-login")
def google_login():
    base_url = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
    redirect_uri = f"{base_url}/google-callback"
    print(f"DEBUG: Google Redirect URI: {redirect_uri}")
    return google.authorize_redirect(redirect_uri)

@app.route("/google-callback")
def google_authorize():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=None)
        
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        google_id = user_info.get('sub')
        
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? OR google_id = ?", (email, google_id))
            user = cursor.fetchone()
            
            if not user:
                # Create a new user for Google login
                random_password = os.urandom(16).hex()
                hashed_password = hash_password(random_password)
                cursor.execute("""
                    INSERT INTO users (name, email, password, google_id, is_verified, role) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, email, hashed_password, google_id, 1, 'Student'))
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
            elif not user[5]: # If google_id not stored but email matches
                cursor.execute("UPDATE users SET google_id = ?, is_verified = 1 WHERE email = ?", (google_id, email))
                conn.commit()
            
            # user schema: id[0], name[1], email[2], password[3], role[4], google_id[5], is_verified[6]...
            # Fetch updated user to be sure
            cursor.execute("SELECT id, name, role FROM users WHERE email = ?", (email,))
            user_data = cursor.fetchone()

            session["user_id"] = user_data[0]
            session["user_name"] = user_data[1]
            session["user_role"] = user_data[2]
            
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Google Login Error: {e}")
        flash("Failed to login with Google.", "error")
        return redirect(url_for("login"))

@app.route("/delete_session/<int:session_id>", methods=["POST"])
def delete_session(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Please log in"}), 401
    
    user_id = session["user_id"]
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # Ensure the session belongs to the user
            cursor.execute("SELECT id FROM sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
            if not cursor.fetchone():
                return jsonify({"error": "Session not found or unauthorized"}), 404
            
            # Delete messages first due to foreign key constraints (though sqlite might handle it if configured with CASCADE)
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
