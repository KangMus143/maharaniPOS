import streamlit as st
import pandas as pd
import os

# Mengimpor fungsi-fungsi yang diperlukan dari modul
from modules.auth import init_auth, login_form, logout, user_management
from modules.database import init_database
from modules.products import get_low_stock_products, product_management
from modules.transactions import pos_interface, transaction_history
from modules.reports import reports_dashboard

# Konfigurasi Halaman
st.set_page_config(
    page_title="POS Maharani",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi database dan otentikasi
init_database()
init_auth()  # Fungsi ini menginisialisasi otentikasi, termasuk membuat tabel pengguna jika perlu

# Cek apakah pengguna sudah login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Layout aplikasi
if not st.session_state.authenticated:
    login_form()  # Menampilkan form login jika pengguna belum login
else:
    # Sidebar - navigasi
    st.sidebar.title("POS Maharani")
    st.sidebar.image("https://img.freepik.com/free-vector/gradient-pos-logo-template_23-2149284672.jpg", width=200)
    
    # Navigasi
    halaman = st.sidebar.radio(
        "Navigasi",
        ["Point of Sale", "Produk", "Transaksi", "Laporan", "Manajemen Pengguna"]
    )
    
     # Konten berdasarkan halaman yang dipilih
    if halaman == "Point of Sale":
        pos_interface()
    
    elif halaman == "Produk":
        product_management()
    
    elif halaman == "Transaksi":
        transaction_history()
    
    elif halaman == "Laporan":
        reports_dashboard()
    
    elif halaman == "Manajemen Pengguna":
        if st.session_state.user.get("role") == "admin":
            user_management()
        else:
            st.warning("Anda tidak memiliki izin untuk mengakses Manajemen Pengguna")
    
    # Tombol logout
    if st.sidebar.button("Logout"):
        logout()

    # Opsional - Tampilkan peringatan stok rendah untuk pengguna admin
    if st.session_state.user.get("role") == "admin":
        low_stock_df = get_low_stock_products(threshold=10)
        
        if not low_stock_df.empty:
            with st.sidebar.expander("⚠️ Peringatan Stok Menipis"):
                st.warning(f"{len(low_stock_df)} produk dengan stok rendah!")
                
                for index, product in low_stock_df.iterrows():
                    st.write(f"**{product['name']}**: {product['stock']} tersisa")
