import streamlit as st
import pandas as pd
import os

# Importações diretas dos arquivos
from auth import inisialisasi_autentikasi, formulir_login, manajemen_pengguna, keluar
from database import inisialisasi_database
from products import manajemen_produk, dapatkan_produk_stok_rendah
from transactions import pos_interface, transaction_history, show_receipt
from reports import reports_dashboard

# Konfigurasi halaman
st.set_page_config(
    page_title="POS Maharani",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi database dan autentikasi
inisialisasi_database()
inisialisasi_autentikasi()

# Periksa autentikasi
if "terotentikasi" not in st.session_state:
    st.session_state.terotentikasi = False

# Tata letak aplikasi
if not st.session_state.terotentikasi:
    formulir_login()
else:
    # Sidebar - navigasi
    st.sidebar.title("POS Maharani")
    st.sidebar.image("https://img.freepik.com/free-vector/gradient-pos-logo-template_23-2149284672.jpg", width=200)
    
    # Navigasi
    halaman = st.sidebar.radio(
        "Navigasi",
        ["Kasir", "Produk", "Transaksi", "Laporan", "Manajemen Pengguna"]
    )
    
    # Konten berdasarkan halaman yang dipilih
    if halaman == "Kasir":
        # Tampilkan struk jika ada ID transaksi di session state, jika tidak tampilkan antarmuka POS
        if st.session_state.get("tampilkan_struk"):
            show_receipt(st.session_state.tampilkan_struk)
        else:
            pos_interface()
    
    elif halaman == "Produk":
        manajemen_produk()
    
    elif halaman == "Transaksi":
        # Tampilkan struk jika ada ID transaksi di session state, jika tidak tampilkan riwayat transaksi
        if st.session_state.get("tampilkan_struk"):
            show_receipt(st.session_state.tampilkan_struk)
        else:
            transaction_history()
    
    elif halaman == "Laporan":
        reports_dashboard()
    
    elif halaman == "Manajemen Pengguna":
        if st.session_state.pengguna.get("peran") == "admin":
            manajemen_pengguna()
        else:
            st.warning("Anda tidak memiliki izin untuk mengakses Manajemen Pengguna")
    
    # Tombol keluar
    keluar()

    # Opsional - Tampilkan peringatan stok rendah ke pengguna admin
    if st.session_state.pengguna.get("peran") == "admin":
        # Dapatkan produk stok rendah
        stok_rendah_df = dapatkan_produk_stok_rendah(ambang_batas=10)
        
        if not stok_rendah_df.empty:
            with st.sidebar.expander("⚠️ Peringatan Stok Rendah"):
                st.warning(f"{len(stok_rendah_df)} produk memiliki stok rendah!")
                
                for index, produk in stok_rendah_df.iterrows():
                    st.write(f"**{produk['nama']}**: {produk['stok']} tersisa")
