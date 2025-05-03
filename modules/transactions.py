import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from database import dapatkan_koneksi_db
from products import dapatkan_produk_berdasarkan_id, perbarui_stok_produk

def hasilkan_id_transaksi():
    """Menghasilkan ID transaksi unik dengan awalan timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d")
    id_unik = str(uuid.uuid4()).split('-')[0]
    return f"TRX-{timestamp}-{id_unik}"

def tambah_ke_keranjang(id_produk, jumlah):
    """Menambahkan produk ke keranjang belanja"""
    if 'keranjang' not in st.session_state:
        st.session_state.keranjang = []
    
    produk = dapatkan_produk_berdasarkan_id(id_produk)
    
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
    produk = dapatkan_produk_berdasarkan_id(item['id_produk'])
    
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
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    try:
        # Masukkan header transaksi
        cursor.execute("""
            INSERT INTO transaksi 
            (id_transaksi, tanggal_transaksi, nama_pelanggan, total_belanja, metode_pembayaran, jumlah_pembayaran, jumlah_kembalian, id_kasir) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_transaksi, tanggal_transaksi, nama_pelanggan, total_belanja, metode_pembayaran, jumlah_pembayaran, jumlah_kembalian, st.session_state.pengguna["id"]))
        
        # Masukkan detail transaksi
        for item in st.session_state.keranjang:
            cursor.execute("""
                INSERT INTO detail_transaksi
                (id_transaksi, id_produk, jumlah, harga, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (id_transaksi, item['id_produk'], item['jumlah'], item['harga'], item['subtotal']))
            
            # Perbarui stok
            perbarui_stok_produk(item['id_produk'], -item['jumlah'])
        
        conn.commit()
        bersihkan_keranjang()
        
        # Persiapkan untuk menampilkan struk
        st.session_state.tampilkan_struk = id_transaksi
        
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

def dapatkan_transaksi_berdasarkan_id(id_transaksi):
    """Mendapatkan detail transaksi berdasarkan ID"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    try:
        # Dapatkan header transaksi
        cursor.execute("""
            SELECT id_transaksi, tanggal_transaksi, nama_pelanggan, 
                   total_belanja, metode_pembayaran, jumlah_pembayaran, jumlah_kembalian
            FROM transaksi
            WHERE id_transaksi = ?
        """, (id_transaksi,))
        
        transaksi = cursor.fetchone()
        if not transaksi:
            return None
        
        # Dapatkan detail transaksi
        cursor.execute("""
            SELECT dt.id_produk, p.nama, dt.jumlah, dt.harga, dt.subtotal
            FROM detail_transaksi dt
            JOIN produk p ON dt.id_produk = p.id_produk
            WHERE dt.id_transaksi = ?
        """, (id_transaksi,))
        
        detail = cursor.fetchall()
        
        return {
            'header': dict(transaksi),
            'detail': [dict(item) for item in detail]
        }
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    finally:
        conn.close()

def dapatkan_transaksi_terbaru(batas=10):
    """Mendapatkan daftar transaksi terbaru"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id_transaksi, tanggal_transaksi, nama_pelanggan, total_belanja, metode_pembayaran
            FROM transaksi
            ORDER BY tanggal_transaksi DESC
            LIMIT ?
        """, (batas,))
        
        transaksi = cursor.fetchall()
        return [dict(row) for row in transaksi]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def cari_transaksi(kata_kunci=None, tanggal_mulai=None, tanggal_akhir=None, batas=100):
    """Mencari transaksi berdasarkan kriteria"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    query = """
        SELECT id_transaksi, tanggal_transaksi, nama_pelanggan, total_belanja, metode_pembayaran
        FROM transaksi
        WHERE 1=1
    """
    params = []
    
    if kata_kunci:
        query += " AND (id_transaksi LIKE ? OR nama_pelanggan LIKE ?)"
        params.extend([f"%{kata_kunci}%", f"%{kata_kunci}%"])
    
    if tanggal_mulai:
        query += " AND tanggal_transaksi >= ?"
        params.append(tanggal_mulai)
    
    if tanggal_akhir:
        query += " AND tanggal_transaksi <= ?"
        params.append(tanggal_akhir + " 23:59:59")
    
    query += " ORDER BY tanggal_transaksi DESC LIMIT ?"
    params.append(batas)
    
    try:
        cursor.execute(query, params)
        transaksi = cursor.fetchall()
        return [dict(row) for row in transaksi]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def pos_interface():
    """Menampilkan antarmuka POS"""
    st.header("Transaksi Penjualan")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Tambah Produk")
        
        # Cari dan tambahkan produk
        conn = dapatkan_koneksi_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id_produk, nama, harga, stok FROM produk WHERE stok > 0")
        produk = cursor.fetchall()
        conn.close()
        
        if not produk:
            st.warning("Tidak ada produk tersedia.")
            return
        
        opsi_produk = {f"{p['nama']} (Stok: {p['stok']})": p['id_produk'] for p in produk}
        produk_terpilih = st.selectbox("Pilih Produk", options=list(opsi_produk.keys()))
        id_produk_terpilih = opsi_produk[produk_terpilih]
        
        # Dapatkan detail produk terpilih
        produk = dapatkan_produk_berdasarkan_id(id_produk_terpilih)
        if produk:
            st.write(f"Harga: Rp {produk['harga']:,.0f}")
            jumlah = st.number_input("Jumlah", min_value=1, max_value=produk['stok'], value=1)
            
            if st.button("Tambah ke Keranjang"):
                if tambah_ke_keranjang(id_produk_terpilih, jumlah):
                    st.success("Produk ditambahkan ke keranjang.")
    
    with col2:
        st.subheader("Ringkasan")
        
        # Tampilkan keranjang
        if 'keranjang' not in st.session_state or not st.session_state.keranjang:
            st.info("Keranjang belanja kosong.")
        else:
            total = dapatkan_total_keranjang()
            st.write(f"Total: Rp {total:,.0f}")
            
            # Form pembayaran
            nama_pelanggan = st.text_input("Nama Pelanggan", "")
            metode_pembayaran = st.selectbox("Metode Pembayaran", ["Tunai", "Debit", "Kredit", "QRIS"])
            jumlah_pembayaran = st.number_input("Jumlah Pembayaran", min_value=float(total), value=float(total))
            
            if st.button("Proses Transaksi"):
                hasil = proses_transaksi(nama_pelanggan, metode_pembayaran, jumlah_pembayaran)
                if hasil:
                    st.success(f"Transaksi berhasil! ID: {hasil['id_transaksi']}")
                    st.write(f"Total: Rp {hasil['total']:,.0f}")
                    st.write(f"Pembayaran: Rp {hasil['pembayaran']:,.0f}")
                    st.write(f"Kembalian: Rp {hasil['kembalian']:,.0f}")
    
    # Tampilkan isi keranjang
    if 'keranjang' in st.session_state and st.session_state.keranjang:
        st.subheader("Keranjang Belanja")
        
        for i, item in enumerate(st.session_state.keranjang):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"{item['nama']}")
            with col2:
                st.write(f"Rp {item['harga']:,.0f}")
            with col3:
                st.write(f"x {item['jumlah']}")
            with col4:
                st.write(f"Rp {item['subtotal']:,.0f}")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button(f"Hapus", key=f"hapus_{i}"):
                    hapus_dari_keranjang(i)
                    st.experimental_rerun()
        
        if st.button("Bersihkan Keranjang"):
            bersihkan_keranjang()
            st.experimental_rerun()

def transaction_history():
    """Menampilkan riwayat transaksi"""
    st.header("Riwayat Transaksi")
    
    # Filter
    col1, col2, col3 = st.columns(3)
    with col1:
        kata_kunci = st.text_input("Cari", placeholder="ID Transaksi atau Nama Pelanggan")
    with col2:
        tanggal_mulai = st.date_input("Dari Tanggal", datetime.now().date())
    with col3:
        tanggal_akhir = st.date_input("Sampai Tanggal", datetime.now().date())
    
    # Format tanggal untuk pencarian
    tanggal_mulai_str = tanggal_mulai.strftime("%Y-%m-%d")
    tanggal_akhir_str = tanggal_akhir.strftime("%Y-%m-%d")
    
    # Cari transaksi
    transaksi = cari_transaksi(kata_kunci, tanggal_mulai_str, tanggal_akhir_str)
    
    if not transaksi:
        st.info("Tidak ada transaksi ditemukan.")
        return
    
    # Tampilkan transaksi
    for trx in transaksi:
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.write(f"**{trx['id_transaksi']}**")
            st.write(f"Tanggal: {trx['tanggal_transaksi']}")
        
        with col2:
            if trx['nama_pelanggan']:
                st.write(f"Pelanggan: {trx['nama_pelanggan']}")
            st.write(f"Metode: {trx['metode_pembayaran']}")
        
        with col3:
            st.write(f"Rp {trx['total_belanja']:,.0f}")
            if st.button("Detail", key=f"detail_{trx['id_transaksi']}"):
                st.session_state.tampilkan_struk = trx['id_transaksi']
                st.experimental_rerun()
        
        st.divider()

def show_receipt(id_transaksi):
    """Menampilkan struk transaksi"""
    transaksi = dapatkan_transaksi_berdasarkan_id(id_transaksi)
    
    if not transaksi:
        st.error("Transaksi tidak ditemukan.")
        if st.button("Kembali"):
            st.session_state.tampilkan_struk = None
            st.experimental_rerun()
        return
    
    header = transaksi['header']
    detail = transaksi['detail']
    
    # Tampilkan header
    st.header("Struk Transaksi")
    st.subheader(f"POS Maharani - {header['id_transaksi']}")
    st.write(f"Tanggal: {header['tanggal_transaksi']}")
    if header['nama_pelanggan']:
        st.write(f"Pelanggan: {header['nama_pelanggan']}")
    
    # Tampilkan detail produk
    st.subheader("Detail Pembelian")
    for item in detail:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"{item['nama']}")
        with col2:
            st.write(f"Rp {item['harga']:,.0f}")
        with col3:
            st.write(f"x {item['jumlah']}")
        with col4:
            st.write(f"Rp {item['subtotal']:,.0f}")
    
    # Tampilkan footer
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Total**")
        st.write("Pembayaran")
        st.write("Kembalian")
    with col2:
        st.write(f"**Rp {header['total_belanja']:,.0f}**")
        st.write(f"Rp {header['jumlah_pembayaran']:,.0f} ({header['metode_pembayaran']})")
        st.write(f"Rp {header['jumlah_kembalian']:,.0f}")
    
    # Tombol print/kembali
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cetak"):
            st.success("Struk dicetak!")
    with col2:
        if st.button("Kembali"):
            st.session_state.tampilkan_struk = None
            st.experimental_rerun()
