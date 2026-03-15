# MITU Skillologies Chatbot Project

A comprehensive Flask-based chatbot application with user authentication, an admin dashboard for lead management, and a robust MySQL database backend.

## 🚀 Features

- **Intelligent Chatbot**: Neural network-based intent classification for handling student queries.
- **User Authentication**: Secure signup and login system with password hashing and session management.
- **Admin Dashboard**: Real-time analytics, lead tracking, user verification, and login activity logs.
- **Profile Management**: Profile customization and password update functionality.
- **Enrollment Flow**: Guided conversational flow for course registrations.
- **MySQL Integration**: Persistent storage for users, messages, sessions, and leads.

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: MySQL (via PyMySQL)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript
- **Security**: JWT, Bcrypt, Dotenv, CSRF Protection
- **Email**: Flask-Mail for verification and password resets

## 📋 Prerequisites

- Python 3.x
- MySQL Server (Community Edition or XAMPP)
- `pip` (Python package manager)

## ⚙️ Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/RoshniBorade/Mitu-chatbot.git
   cd Mitu-chatbot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirement.txt
   pip install pymysql cryptography
   ```

3. **Database Configuration**
   - Open your MySQL terminal or phpMyAdmin.
   - Create a new database:
     ```sql
     CREATE DATABASE mitu_chatbot_db;
     ```

4. **Environment Variables**
   - Create a `.env` file in the root directory and add your credentials:
     ```env
     MYSQL_HOST=localhost
     MYSQL_USER=your_username
     MYSQL_PASSWORD=your_password
     MYSQL_DB=mitu_chatbot_db
     SECRET_KEY=your_secret_key
     MAIL_SERVER=smtp.gmail.com
     MAIL_PORT=587
     MAIL_USE_TLS=True
     MAIL_USERNAME=your_email@gmail.com
     MAIL_PASSWORD=your_app_password
     ```

5. **Initialize Database & Run**
   The application handles table creation automatically on the first run.
   ```bash
   python app.py
   ```
   Access the application at `http://127.0.0.1:5000`

## 📂 Project Structure

- `app.py`: Main Flask application server.
- `db.py`: Database compatibility layer for MySQL.
- `enrollment.py`: Logic for the conversational enrollment flow.
- `intents.json`: Training data for chatbot intents and responses.
- `static/`: CSS and JavaScript assets.
- `templates/`: HTML templates for different views.

## 🤝 Contributing

Feel free to fork this repository and submit pull requests for any enhancements or fixes.
