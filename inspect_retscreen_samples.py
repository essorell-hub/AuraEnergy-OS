import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kategorie 81 a 82 jsou fotovoltaické panely (monoSi, polySi)
cursor.execute("""
SELECT p.ProductID, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
FROM Product p
JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
WHERE p.ProductCategoryID IN (81, 82)
ORDER BY p.CapacityValue DESC
LIMIT 10
""")
print("Vzorky fotovoltaických panelů z RETScreen databáze:")
for r in cursor.fetchall():
    print(f" - {r[1]}: {r[2]} ({r[3]} {r[4]})")

# Větrné turbíny (kategorie 88)
cursor.execute("""
SELECT p.ProductID, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
FROM Product p
JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
WHERE p.ProductCategoryID = 88
ORDER BY p.CapacityValue DESC
LIMIT 5
""")
print("\nVzorky větrných turbín z RETScreen databáze:")
for r in cursor.fetchall():
    print(f" - {r[1]}: {r[2]} ({r[3]} {r[4]})")

# Tepelná čerpadla (kategorie 50, 13, 49, 12)
cursor.execute("""
SELECT p.ProductID, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
FROM Product p
JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
WHERE p.ProductCategoryID IN (50, 13, 49, 12)
LIMIT 5
""")
print("\nVzorky tepelných čerpadel z RETScreen databáze:")
for r in cursor.fetchall():
    print(f" - {r[1]}: {r[2]} ({r[3]} {r[4]})")

conn.close()
