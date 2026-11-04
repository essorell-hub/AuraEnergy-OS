import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in RETScreen product.sqlite:")
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM [{t[0]}]")
    cnt = cursor.fetchone()[0]
    print(f" - {t[0]}: {cnt} rows")

conn.close()
