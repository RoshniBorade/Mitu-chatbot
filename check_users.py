import db
conn = db.connect()
cursor = conn.cursor()
cursor.execute("SELECT email, name, role FROM users")
users = cursor.fetchall()
for user in users:
    print(user)
conn.close()
