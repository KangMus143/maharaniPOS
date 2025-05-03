import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from modules.database import dapatkan_koneksi_db
from modules.products import dapatkan_produk_berdasarkan_id, perbarui_stok_produk

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
