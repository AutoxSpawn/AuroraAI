import sqlite3

conn = sqlite3.connect("aurora_memory.db", check_same_thread=False)
cursor = conn

cursor.execute("DELETE FROM chat_memory")
conn.commit()

cursor.execute("DELETE FROM chat_memory")
conn.commit()

cursor.execute("DELETE FROM sqlite_sequence WHERE name='chat_memory'")
conn.commit()

conn.close()

print("Database has been completely reset. AuroraAI will now start fresh!")


