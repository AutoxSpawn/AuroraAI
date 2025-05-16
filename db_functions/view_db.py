import sqlite3

conn = sqlite3.connect("aurora_memory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("Select * FROM chat_memory")
rows = cursor.fetchall()

print("\n AuroraAI Memory Chat History:\n")

for row in rows:
    print(f"ID: {row[0]}")
    print(f"User: {row[1]}")
    print(f"AuroraAI: {row[2]}\n")
    print("-" * 50)

conn.close()