import json
import os
import random
import re

# ---------- Load intents.json ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTENTS_PATH = os.path.join(BASE_DIR, "intents.json")

with open(INTENTS_PATH, "r", encoding="utf-8") as file:
    intents = json.load(file)

# ---------- Text preprocessing ----------
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    return text.split()

# ---------- Intent matching ----------
def match_intent(user_words):
    best_intent = None
    highest_score = 0

    for intent in intents["intents"]:
        keywords = intent.get("keywords", [])
        score = sum(1 for word in user_words if word in keywords)

        if score > highest_score:
            highest_score = score
            best_intent = intent

    return best_intent

# ---------- Get chatbot response ----------
def get_response(user_input):
    user_words = preprocess_text(user_input)
    intent = match_intent(user_words)

    if intent:
        return random.choice(intent["responses"])

    return "Sorry, I couldn't understand that. Please try asking in a different way."

# ---------- Chat loop ----------
print("MITU Skillologies Chatbot is running (type 'quit' to exit)")

while True:
    user_input = input("You: ")

    if user_input.lower() == "quit":
        print("Bot: Goodbye! Have a great day 😊")
        break

    response = get_response(user_input)
    print("Bot:", response)
