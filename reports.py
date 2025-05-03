from modules.database import get_connection
import pandas as pd

def generate_report():
    conn = get_connection()
    cursor = conn.cursor()

    # Ambil semua transaksi
    cursor.execute("SELECT id, tanggal, total FROM transaksi ORDER BY tanggal DESC")
    transaksi_list = cursor.fetchall()

    if not transaksi_list:
        print("❌ Belum ada transaksi.")
        return

    print("\n=== Laporan Penjualan ===")
    for t in transaksi_list:
        print(f"\n🧾 ID: {t[0]} | Tanggal: {t[1]} | Total: {t[2]}")

        # Ambil detail transaksi
        cursor.execute("""
            SELECT p.nama, d.jumlah, d.subtotal
            FROM detail_transaksi d
            JOIN produk p ON p.id = d.produk_id
            WHERE d.transaksi_id = ?
        """, (t[0],))
        detail_list = cursor.fetchall()

        for d in detail_list:
            print(f"   - {d[0]} x {d[1]} = {d[2]}")

    conn.close()

def export_to_excel():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.id as transaksi_id, t.tanggal, p.nama, d.jumlah, d.subtotal, t.total
        FROM transaksi t
        JOIN detail_transaksi d ON t.id = d.transaksi_id
        JOIN produk p ON p.id = d.produk_id
        ORDER BY t.tanggal DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("❌ Tidak ada data untuk diekspor.")
        return

    df = pd.DataFrame(rows, columns=["ID Transaksi", "Tanggal", "Produk", "Jumlah", "Subtotal", "Total Transaksi"])
    df.to_excel("laporan_penjualan.xlsx", index=False)
    print("✅ Laporan berhasil diekspor ke 'laporan_penjualan.xlsx'")
