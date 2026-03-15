import db
import inspect

def test():
    try:
        print("Connecting to MySQL...")
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("Tables in database:", tables)
        print("Success.")
    except Exception as e:
        print("Error details:", e)

if __name__ == "__main__":
    test()
