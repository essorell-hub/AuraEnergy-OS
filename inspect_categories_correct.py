import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
SELECT pc.ProductCategoryID, pc.Caption, pc.SubTypeCaption, COUNT(p.ProductID) as cnt
FROM ProductCategory pc
LEFT JOIN Product p ON p.ProductCategoryID = pc.ProductCategoryID
GROUP BY pc.ProductCategoryID, pc.Caption, pc.SubTypeCaption
HAVING cnt > 0
ORDER BY cnt DESC
LIMIT 25
""")
print("Top Categories in RETScreen:")
for r in cursor.fetchall():
    print(f" - [{r[0]}] {r[1]} ({r[2]}): {r[3]} produktů")

conn.close()
