import sqlite3

sample_retx = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
conn = sqlite3.connect(sample_retx)
c = conn.cursor()

c.execute("SELECT uri, length(content) FROM [retscreen.opc.content]")
rows = c.fetchall()
print(f"Total parts inside RETScreen OPC package: {len(rows)}")
for r in rows:
    print(f" - URI: {r[0]} ({r[1]} bytes)")

conn.close()
