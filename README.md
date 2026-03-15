# 🤖 MITU Skillologies Chatbot

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-flask-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/database-mysql-orange.svg)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, full-stack AI chatbot solution designed for educational institutions. This platform streamlines student inquiries, course enrollments, and administrative oversight through an integrated AI engine and a robust web dashboard.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🧠 Smart Intent AI** | Neural network-based classification for accurate query handling. |
| **🔐 Secure Auth** | Multi-role authentication (Admin/Student) with JWT and Bcrypt security. |
| **📊 Admin Dashboard** | Live analytics, lead conversion tracking, and security auditing. |
| **💬 Session Persistence** | MySQL-backed chat history tracking for seamless conversations. |
| **📧 Automated Mail** | Integrated SMTP support for email verification and password recovery. |
| **🛠️ Dynamic Profile** | Personalized user profiles with avatar uploads and role-based views. |

---

## 🛠️ Technology Stack

- **Backend:** Python 3 + Flask
- **Core AI:** TensorFlow / Simple Intent Matching (JSON)
- **Database:** MySQL 8.0 (Production-grade)
- **Security:** CSRF Protection, JWT, Password Salting
- **UI/UX:** Modern CSS3, HTML5, JavaScript (ES6)

---

## 🚀 Quick Start

### 1. Repository Setup
```bash
git clone https://github.com/RoshniBorade/Mitu-chatbot.git
cd Mitu-chatbot
```

### 2. Dependency Injection
```bash
pip install -r requirement.txt
pip install pymysql cryptography
```

### 3. Database Initialization
Create a database named `mitu_chatbot_db` in your MySQL server:
```sql
CREATE DATABASE mitu_chatbot_db;
```

### 4. Environment Variables
Create a `.env` file in the root directory:
```env
# Database
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=mitu_chatbot_db

# Security
SECRET_KEY=generate_a_random_string

# Mail Settings
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_specific_password
```

### 5. Launch
```bash
python app.py
```
The application will automatically perform schema migrations on the first run.

---

## 📂 Project Structure

```text
├── app.py              # Central application logic & routing
├── db.py               # Database compatibility layer
├── enrollment.py       # Conversational enrollment engine
├── intents.json        # AI Training dataset
├── static/             # Visual assets (CSS, JS, Images)
├── templates/          # Jinja2 HTML views
└── requirement.txt     # Python dependencies
```

---

## 🛡️ Security & Scalability

This project has been migrated from SQLite to **MySQL** to support concurrent connections and data integrity in a production environment. It implements industry-standard security headers and password protection mechanisms.

---


