import sqlite3
import os

DATABASE = 'database.db'
EMAIL_TO_DELETE = 'roshniborade25021@gmail.com'

def delete_user_by_email(email):
    if not os.path.exists(DATABASE):
        print(f"Error: {DATABASE} not found.")
        return

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Find user ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            print(f"User with email {email} not found.")
            return

        user_id = user[0]
        print(f"Found user ID: {user_id} for email: {email}")

        # Delete from messages
        cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        print("Deleted related messages.")

        # Delete from sessions
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        print("Deleted related sessions.")

        # Delete from login_activity
        cursor.execute("DELETE FROM login_activity WHERE user_id = ?", (user_id,))
        print("Deleted related login activity.")

        # Delete from users
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        print(f"Deleted user {email} from users table.")

        conn.commit()
        print("\nSuccessfully deleted user and all related data.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    delete_user_by_email(EMAIL_TO_DELETE)
