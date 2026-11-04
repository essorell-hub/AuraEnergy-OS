import sqlite3

sample_retx = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
conn = sqlite3.connect(sample_retx)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [x[0] for x in c.fetchall()]
print(f"Total tables inside .retx: {len(tables)}")
for t in tables[:35]:
    c.execute(f"SELECT COUNT(*) FROM [{t}]")
    print(f" - {t}: {c.fetchone()[0]} rows")
conn.close()
