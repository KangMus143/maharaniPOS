import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from modules.database import get_db_connection
from modules.products import ambil_produk_berdasarkan_id, perbarui_stok_produk

def proses_transaksi(nama_pelanggan, metode_pembayaran, jumlah_pembayaran):
    """Memproses transaksi dan menyimpan ke database"""
    if 'keranjang' not in st.session_state or not st.session_state.keranjang:
        st.error("Keranjang belanja kosong.")
        return False
    
    id_transaksi = hasilkan_id_transaksi()
    total_belanja = dapatkan_total_keranjang()
    
    if jumlah_pembayaran < total_belanja:
        st.error("Pembayaran kurang dari total belanja.")
        return False
    
    jumlah_kembalian = jumlah_pembayaran - total_belanja
    tanggal_transaksi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Masukkan header transaksi
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Masukkan header transaksi
        cursor.execute("""
            INSERT INTO transactions 
            (invoice_number, total_amount, payment_method, cashier_id, created_at) 
            VALUES (?, ?, ?, ?, ?)
        """, (id_transaksi, total_belanja, metode_pembayaran, 1, tanggal_transaksi))  # Asumsikan cashier_id adalah 1
        
        # Masukkan detail transaksi dan update stok
        stock_update_failed = False
        for item in st.session_state.keranjang:
            cursor.execute("""
                INSERT INTO transaction_items
                (transaction_id, product_id, quantity, price_per_unit, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (id_transaksi, item['id'], item['quantity'], item['price'], item['subtotal']))
            berhasil, pesan = perbarui_stok_produk(item['id'], -item['quantity'])  # Mengurangi stok berdasarkan jumlah produk

            print(f"Hasil perbarui_stok_produk: Berhasil={berhasil}, Pesan={pesan}")
            if not berhasil:
                st.error(pesan)
                stock_update_failed = True
                break  # Hentikan proses jika ada masalah stok

        if stock_update_failed:
            conn.rollback() # Rollback jika ada kesalahan stok
            return False
        else:
            conn.commit()  # Simpan semua perubahan jika tidak ada kesalahan stok
        bersihkan_keranjang()  # Kosongkan keranjang setelah transaksi selesai
        return {
            'id_transaksi': id_transaksi,
            'total': total_belanja,
            'pembayaran': jumlah_pembayaran,
            'kembalian': jumlah_kembalian,
            'tanggal': tanggal_transaksi
        }
    
    except Exception as e:
        conn.rollback()
        st.error(f"Error dalam transaksi: {str(e)}")
        return False
    finally:
        conn.close()

def show_receipt(transaction_id):
    """Menampilkan struk transaksi"""
    # Ambil data transaksi berdasarkan ID
    query = '''
    SELECT t.invoice_number, t.total_amount, t.payment_method, t.created_at, u.username AS cashier
    FROM transactions t
    JOIN users u ON t.cashier_id = u.id
    WHERE t.invoice_number = ?
    '''
    
    conn = get_db_connection()
    transaction = pd.read_sql_query(query, conn, params=(transaction_id,))
    conn.close()
    
    if transaction.empty:
        st.error(f"Transaksi dengan ID {transaction_id} tidak ditemukan.")
    else:
        st.subheader(f"Struk Transaksi {transaction_id}")
        st.write(f"Nomor Faktur: {transaction.iloc[0]['invoice_number']}")
        st.write(f"Total: Rp {transaction.iloc[0]['total_amount']:,.0f}")
        st.write(f"Metode Pembayaran: {transaction.iloc[0]['payment_method']}")
        st.write(f"Tanggal: {transaction.iloc[0]['created_at']}")
        st.write(f"Kasir: {transaction.iloc[0]['cashier']}")
        
        # Tampilkan detail produk dalam transaksi
        query_details = '''
        SELECT ti.product_id, p.name, ti.quantity, ti.price_per_unit, ti.subtotal
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        WHERE ti.transaction_id = ?
        '''
        conn = get_db_connection()
        items = pd.read_sql_query(query_details, conn, params=(transaction_id,))
        conn.close()

        if not items.empty:
            st.write("**Detail Produk**")
            for index, item in items.iterrows():
                st.write(f"**{item['name']}** x {item['quantity']} - Rp {item['subtotal']:,.0f}")
        else:
            st.info("Tidak ada produk dalam transaksi.")

def transaction_history():
    """Menampilkan riwayat transaksi"""
    st.title("Riwayat Transaksi")

    # Ambil data transaksi dari database
    query = '''
    SELECT t.id, t.invoice_number, t.total_amount, t.payment_method, t.created_at, u.username AS cashier
    FROM transactions t
    JOIN users u ON t.cashier_id = u.id
    ORDER BY t.created_at DESC
    '''
    
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        st.info("Belum ada transaksi yang dilakukan.")
    else:
        st.write(df)
        
        # Pilih transaksi untuk melihat detail
        transaction_id = st.selectbox("Pilih Transaksi", df['invoice_number'])
        
        if transaction_id:
            # Tampilkan detail transaksi berdasarkan ID
            query_details = '''
            SELECT ti.product_id, p.name, ti.quantity, ti.price_per_unit, ti.subtotal
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transaction_id = ?
            '''
            conn = get_db_connection()
            transaction_items = pd.read_sql_query(query_details, conn, params=(transaction_id,))
            conn.close()
            
            if not transaction_items.empty:
                st.subheader(f"Detail Transaksi {transaction_id}")
                st.write(transaction_items)
            else:
                st.info(f"Tidak ada detail transaksi untuk {transaction_id}")

def pos_interface():
    """Antarmuka untuk Point of Sale"""
    st.title("Point of Sale")

    # Pastikan 'keranjang' ada di session state
    if 'keranjang' not in st.session_state:
        st.session_state.keranjang = []

    # Form untuk memilih produk
    produk_id = st.number_input("ID Produk", min_value=1, step=1)
    jumlah = st.number_input("Jumlah", min_value=1, step=1)

    # Tombol untuk menambah produk ke keranjang
    if st.button("Tambahkan ke Keranjang"):
        produk = ambil_produk_berdasarkan_id(produk_id)

        if produk:
            if produk["stock"] >= jumlah:
                subtotal = produk["price"] * jumlah
                st.session_state.keranjang.append({
                    "id": produk["id"],
                    "name": produk["name"],
                    "quantity": jumlah,
                    "price": produk["price"],
                    "subtotal": subtotal
                })
                st.success(f"{produk['name']} berhasil ditambahkan ke keranjang.")
            else:
                st.warning("Stok tidak cukup.")
        else:
            st.error("Produk tidak ditemukan.")
    
    # Menampilkan keranjang belanja
    if "keranjang" in st.session_state and st.session_state.keranjang:
        st.subheader("Keranjang Belanja")
        for item in st.session_state.keranjang:
            st.write(f"**{item['name']}** x {item['quantity']} - Rp {item['subtotal']:,.0f}")
        
        total = sum(item['subtotal'] for item in st.session_state.keranjang)
        st.write(f"**Total: Rp {total:,.0f}**")

        # Tombol untuk memproses transaksi
        if st.button("Proses Transaksi"):
            if total > 0:
                st.session_state.keranjang = []
                st.success("Transaksi berhasil diproses.")
            else:
                st.warning("Keranjang belanja kosong.")

def hasilkan_id_transaksi():
    """Menghasilkan ID transaksi unik dengan awalan timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d")
    id_unik = str(uuid.uuid4()).split('-')[0]
    return f"TRX-{timestamp}-{id_unik}"

def tambah_ke_keranjang(id_produk, jumlah):
    """Menambahkan produk ke keranjang belanja"""
    if 'keranjang' not in st.session_state:
        st.session_state.keranjang = []
    
    produk = ambil_produk_berdasarkan_id(id_produk)
    
    if not produk:
        st.error("Produk tidak ditemukan.")
        return False
    
    if produk['stok'] < jumlah:
        st.error(f"Stok tidak mencukupi. Tersedia: {produk['stok']}")
        return False
    
    # Periksa apakah produk sudah ada di keranjang
    for item in st.session_state.keranjang:
        if item['id_produk'] == id_produk:
            item['jumlah'] += jumlah
            item['subtotal'] = item['jumlah'] * item['harga']
            return True
    
    # Tambahkan item baru ke keranjang
    st.session_state.keranjang.append({
        'id_produk': id_produk,
        'nama': produk['nama'],
        'harga': produk['harga'],
        'jumlah': jumlah,
        'subtotal': produk['harga'] * jumlah
    })
    return True

def perbarui_item_keranjang(indeks, jumlah):
    """Memperbarui jumlah item di keranjang"""
    if 'keranjang' not in st.session_state or indeks >= len(st.session_state.keranjang):
        return False
    
    item = st.session_state.keranjang[indeks]
    produk = ambil_produk_berdasarkan_id(item['id_produk'])
    
    if produk['stok'] < jumlah:
        st.error(f"Stok tidak mencukupi. Tersedia: {produk['stok']}")
        return False
    
    item['jumlah'] = jumlah
    item['subtotal'] = jumlah * item['harga']
    return True

def hapus_dari_keranjang(indeks):
    """Menghapus item dari keranjang"""
    if 'keranjang' in st.session_state and indeks < len(st.session_state.keranjang):
        st.session_state.keranjang.pop(indeks)
        return True
    return False

def bersihkan_keranjang():
    """Menghapus semua item dari keranjang"""
    if 'keranjang' in st.session_state:
        st.session_state.keranjang = []

def dapatkan_total_keranjang():
    """Menghitung total jumlah semua item di keranjang"""
    if 'keranjang' not in st.session_state or not st.session_state.keranjang:
        return 0
    return sum(item['subtotal'] for item in st.session_state.keranjang)
