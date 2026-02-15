import sqlite3

DATABASE = 'database.db'

def clear_users():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Deleting in order to respect potential foreign keys
        print("Cleaning up database...")
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM sessions")
        cursor.execute("DELETE FROM login_activity")
        cursor.execute("DELETE FROM users")
        
        conn.commit()
        print("✅ Successfully deleted all users and related activity.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_users()
