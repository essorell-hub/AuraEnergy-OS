import sqlite3

sample_retx = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
conn = sqlite3.connect(sample_retx)
c = conn.cursor()

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Financial.xml'")
raw = c.fetchone()[0]
text = raw.decode('utf-8-sig', errors='ignore')
with open('d:/REST/sample_financial.xml', 'w', encoding='utf-8') as f:
    f.write(text)

c.execute("SELECT content FROM [retscreen.opc.content] WHERE uri='/retscreen/content0/elements/Energy.xml'")
raw_e = c.fetchone()[0]
text_e = raw_e.decode('utf-8-sig', errors='ignore')
with open('d:/REST/sample_energy.xml', 'w', encoding='utf-8') as f:
    f.write(text_e[:50000]) # prvních 50 kB

conn.close()
print("Saved sample_financial.xml and sample_energy.xml successfully!")
