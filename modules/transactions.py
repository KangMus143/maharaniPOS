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
        for item in st.session_state.keranjang:
            cursor.execute("""
                INSERT INTO transaction_items
                (transaction_id, product_id, quantity, price_per_unit, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (id_transaksi, item['id'], item['quantity'], item['price'], item['subtotal']))
            
            # Perbarui stok produk setelah transaksi
            berhasil, pesan = perbarui_stok_produk(item['id'], -item['quantity'])  # Mengurangi stok berdasarkan jumlah produk

            # Jika ada masalah dalam memperbarui stok, tampilkan pesan error
            if not berhasil:
                st.error(pesan)
                conn.rollback()
                return False
        
        conn.commit()  # Simpan semua perubahan
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
    cursor = conn.cursor()
    cursor.execute(query, (transaction_id,))
    transaction = cursor.fetchone()
    conn.close()
    
    if not transaction:
        st.error(f"Transaksi dengan ID {transaction_id} tidak ditemukan.")
    else:
        st.subheader(f"Struk Transaksi {transaction_id}")
        st.write(f"Nomor Faktur: {transaction['invoice_number']}")
        st.write(f"Total: Rp {transaction['total_amount']:,.0f}")
        st.write(f"Metode Pembayaran: {transaction['payment_method']}")
        st.write(f"Tanggal: {transaction['created_at']}")
        st.write(f"Kasir: {transaction['cashier']}")
        
        # Tampilkan detail produk dalam transaksi
        query_details = '''
        SELECT ti.product_id, p.name, ti.quantity, ti.price_per_unit, ti.subtotal
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        WHERE ti.transaction_id = ?
        '''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_details, (transaction_id,))
        items = cursor.fetchall()
        conn.close()

        if items:
            st.write("**Detail Produk**")
            for item in items:
                st.write(f"**{item['name']}** x {item['quantity']} - Rp {item['subtotal']:,.0f}")
        else:
            st.info("Tidak ada produk dalam transaksi.")

def transaction_history():
    """Menampilkan riwayat transaksi"""
    st.title("Riwayat Transaksi")

    # Ambil data transaksi dari database
    query = '''
    SELECT t.invoice_number, t.total_amount, t.payment_method, t.created_at, u.username AS cashier
    FROM transactions t
    JOIN users u ON t.cashier_id = u.id
    ORDER BY t.created_at DESC
    '''
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        st.info("Belum ada transaksi yang dilakukan.")
    else:
        # Convert to DataFrame for display
        df = pd.DataFrame([dict(t) for t in transactions])
        st.write(df)
        
        # Pilih transaksi untuk melihat detail
        transaction_ids = [t['invoice_number'] for t in transactions]
        transaction_id = st.selectbox("Pilih Transaksi", transaction_ids)
        
        if transaction_id:
            # Tampilkan detail transaksi berdasarkan ID
            query_details = '''
            SELECT ti.product_id, p.name, ti.quantity, ti.price_per_unit, ti.subtotal
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            WHERE ti.transaction_id = ?
            '''
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query_details, (transaction_id,))
            transaction_items = cursor.fetchall()
            conn.close()
            
            if transaction_items:
                st.subheader(f"Detail Transaksi {transaction_id}")
                # Convert to DataFrame for display
                items_df = pd.DataFrame([dict(item) for item in transaction_items])
                st.write(items_df)
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
    
    if produk['stock'] < jumlah:
        st.error(f"Stok tidak mencukupi. Tersedia: {produk['stock']}")
        return False
    
    # Periksa apakah produk sudah ada di keranjang
    for item in st.session_state.keranjang:
        if item['id'] == id_produk:
            item['quantity'] += jumlah
            item['subtotal'] = item['quantity'] * item['price']
            return True
    
    # Tambahkan item baru ke keranjang
    st.session_state.keranjang.append({
        'id': id_produk,
        'name': produk['name'],
        'price': produk['price'],
        'quantity': jumlah,
        'subtotal': produk['price'] * jumlah
    })
    return True

def perbarui_item_keranjang(indeks, jumlah):
    """Memperbarui jumlah item di keranjang"""
    if 'keranjang' not in st.session_state or indeks >= len(st.session_state.keranjang):
        return False
    
    item = st.session_state.keranjang[indeks]
    produk = ambil_produk_berdasarkan_id(item['id'])
    
    if produk['stock'] < jumlah:
        st.error(f"Stok tidak mencukupi. Tersedia: {produk['stock']}")
        return False
    
    item['quantity'] = jumlah
    item['subtotal'] = jumlah * item['price']
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
