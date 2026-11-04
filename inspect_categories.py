import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Vypsat hlavní kategorie produktů v RETScreen
cursor.execute("""
SELECT pc.ID, pc.Code, COUNT(p.ID) as cnt
FROM ProductCategory pc
LEFT JOIN Product p ON p.ProductCategoryID = pc.ID
GROUP BY pc.ID, pc.Code
HAVING cnt > 0
ORDER BY cnt DESC
LIMIT 20
""")
print("Top Product Categories in RETScreen:")
for r in cursor.fetchall():
    print(f" - ID: {r[0]}, Code: {r[1]}, Total Products: {r[2]}")

conn.close()
