from modules.database import get_connection
from datetime import datetime

def new_transaction():
    conn = get_connection()
    cursor = conn.cursor()

    # Tampilkan produk
    cursor.execute("SELECT id, nama, harga, stok FROM produk")
    produk_list = cursor.fetchall()

    if not produk_list:
        print("❌ Tidak ada produk tersedia.")
        return

    print("\nProduk tersedia:")
    for p in produk_list:
        print(f"[{p[0]}] {p[1]} | Harga: {p[2]} | Stok: {p[3]}")

    transaksi_items = []
    total = 0

    while True:
        produk_id = input("\nMasukkan ID produk (atau tekan Enter untuk selesai): ")
        if produk_id == "":
            break

        try:
            produk_id = int(produk_id)
            jumlah = int(input("Jumlah beli: "))

            # Ambil data produk
            cursor.execute("SELECT nama, harga, stok FROM produk WHERE id = ?", (produk_id,))
            produk = cursor.fetchone()
            if not produk:
                print("❌ Produk tidak ditemukan.")
                continue

            if jumlah > produk[2]:
                print(f"❌ Stok tidak cukup (tersedia: {produk[2]})")
                continue

            subtotal = produk[1] * jumlah
            total += subtotal

            transaksi_items.append({
                "produk_id": produk_id,
                "jumlah": jumlah,
                "subtotal": subtotal
            })

            print(f"✅ Ditambahkan: {produk[0]} x {jumlah} = {subtotal}")

        except ValueError:
            print("❌ Input tidak valid.")
            continue

    if not transaksi_items:
        print("❌ Transaksi dibatalkan (tidak ada item).")
        return

    # Simpan transaksi utama
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO transaksi (tanggal, total) VALUES (?, ?)", (tanggal, total))
    transaksi_id = cursor.lastrowid

    # Simpan detail transaksi dan update stok
    for item in transaksi_items:
        cursor.execute("""
            INSERT INTO detail_transaksi (transaksi_id, produk_id, jumlah, subtotal)
            VALUES (?, ?, ?, ?)
        """, (transaksi_id, item["produk_id"], item["jumlah"], item["subtotal"]))

        cursor.execute("""
            UPDATE produk SET stok = stok - ?
            WHERE id = ?
        """, (item["jumlah"], item["produk_id"]))

    conn.commit()
    conn.close()

    print(f"\n✅ Transaksi berhasil disimpan. Total: {total}")
