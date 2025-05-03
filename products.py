from modules.database import get_connection

def add_product():
    nama = input("Nama produk: ")
    harga = float(input("Harga produk: "))
    stok = int(input("Stok awal: "))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produk (nama, harga, stok) VALUES (?, ?, ?)", (nama, harga, stok))
    conn.commit()
    conn.close()

    print("✅ Produk berhasil ditambahkan!")

def list_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama, harga, stok FROM produk")
    rows = cursor.fetchall()
    conn.close()

    print("\nDaftar Produk:")
    print("-" * 30)
    for row in rows:
        print(f"[{row[0]}] {row[1]} | Harga: {row[2]} | Stok: {row[3]}")
    print("-" * 30)
