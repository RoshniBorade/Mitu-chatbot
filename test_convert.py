import db

def test():
    with db.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM users LIMIT 1")
        row = cursor.fetchone()
        if row:
            print(f"created_at value: {repr(row[0])}, type: {type(row[0])}")
        else:
            print("No users found to test.")
        
test()
