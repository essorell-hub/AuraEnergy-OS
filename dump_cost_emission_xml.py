import sqlite3
import xml.etree.ElementTree as ET

sample_retx = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
conn = sqlite3.connect(sample_retx)
c = conn.cursor()

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Cost.xml'")
raw_cost = c.fetchone()[0].decode('utf-8-sig', errors='ignore')
with open('d:/REST/sample_cost.xml', 'w', encoding='utf-8') as f:
    f.write(raw_cost[:35000])

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Emission.xml'")
raw_ems = c.fetchone()[0].decode('utf-8-sig', errors='ignore')
with open('d:/REST/sample_emission.xml', 'w', encoding='utf-8') as f:
    f.write(raw_ems)

conn.close()
print("Saved sample_cost.xml and sample_emission.xml successfully!")
