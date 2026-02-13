import sqlite3

DATABASE = 'database.db'

def migrate():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 1. Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 2. Check if session_id column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'session_id' not in columns:
            print("Adding session_id column to messages...")
            cursor.execute("ALTER TABLE messages ADD COLUMN session_id INTEGER DEFAULT NULL REFERENCES sessions(id)")
        
        # 3. Create default session for existing messages
        cursor.execute("SELECT DISTINCT user_id FROM messages WHERE session_id IS NULL")
        users_with_messages = cursor.fetchall()
        
        for (user_id,) in users_with_messages:
            cursor.execute("INSERT INTO sessions (user_id, title) VALUES (?, ?)", (user_id, "Previous Chat"))
            session_id = cursor.lastrowid
            cursor.execute("UPDATE messages SET session_id = ? WHERE user_id = ? AND session_id IS NULL", (session_id, user_id))
            print(f"Migrated messages for user {user_id} to session {session_id}")
            
        conn.commit()
        print("Migration complete!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
