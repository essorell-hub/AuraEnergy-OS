import sqlite3

db_path = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for tbl in ['ProductCategory', 'ProductManufacturer', 'Product']:
    cursor.execute(f"PRAGMA table_info([{tbl}]);")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"Table {tbl}: {cols}")

conn.close()
