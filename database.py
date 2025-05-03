import sqlite3

DB_NAME = "database/db.sqlite"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel produk
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produk (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        harga REAL NOT NULL,
        stok INTEGER NOT NULL
    )
    """)

    # Tabel transaksi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT NOT NULL,
        total REAL NOT NULL
    )
    """)

    # Tabel detail transaksi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detail_transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaksi_id INTEGER NOT NULL,
        produk_id INTEGER NOT NULL,
        jumlah INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY(transaksi_id) REFERENCES transaksi(id),
        FOREIGN KEY(produk_id) REFERENCES produk(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database berhasil diinisialisasi.")
