import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT course_name, COUNT(*) FROM leads GROUP BY course_name")
print("Leads by Course:", cursor.fetchall())
cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
print("Leads by Status:", cursor.fetchall())
conn.close()
