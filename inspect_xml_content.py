import sqlite3

sample_retx = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
conn = sqlite3.connect(sample_retx)
c = conn.cursor()

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Financial.xml'")
xml_fin = c.fetchone()[0].decode('utf-8')
print("=== Financial.xml from RETScreen Hospital.retx ===")
print(xml_fin[:1500])

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Emission.xml'")
xml_ems = c.fetchone()[0].decode('utf-8')
print("\n=== Emission.xml from RETScreen Hospital.retx ===")
print(xml_ems[:1500])

conn.close()
