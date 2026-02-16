import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("UPDATE leads SET status = 'Converted' WHERE id = 2")
conn.commit()
print("Updated lead 2 to Converted")
conn.close()
