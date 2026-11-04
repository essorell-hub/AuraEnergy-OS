import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Hledání invertorů a baterií
cursor.execute("""
SELECT pc.ProductCategoryID, pc.Caption, pc.SubTypeCaption, COUNT(p.ProductID)
FROM ProductCategory pc
JOIN Product p ON p.ProductCategoryID = pc.ProductCategoryID
WHERE pc.Caption LIKE '%Inverter%' OR pc.Caption LIKE '%Battery%' OR pc.Caption LIKE '%Storage%' OR pc.Caption LIKE '%Solar%'
GROUP BY pc.ProductCategoryID, pc.Caption, pc.SubTypeCaption
""")
print("Solar / Inverter / Storage categories in RETScreen:")
for r in cursor.fetchall():
    print(r)

conn.close()
