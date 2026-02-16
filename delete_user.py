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

        # Delete all data
        cursor.execute("DELETE FROM messages")
        print("Deleted all messages.")

        cursor.execute("DELETE FROM sessions")
        print("Deleted all sessions.")

        cursor.execute("DELETE FROM login_activity")
        print("Deleted form login_activity.")

        cursor.execute("DELETE FROM users")
        print("Deleted all users.")

        conn.commit()
        print("\nSuccessfully deleted all users and related data.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    delete_user_by_email(EMAIL_TO_DELETE)
