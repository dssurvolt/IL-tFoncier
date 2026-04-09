import sqlite3
import os

db_path = 'backend/db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM listings")
        cursor.execute("DELETE FROM transaction_folios")
        cursor.execute("DELETE FROM properties")
        conn.commit()
        print("Data cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("DB not found.")
