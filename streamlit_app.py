import streamlit as st
from modules import database, auth, products, transactions, reports

st.set_page_config(page_title="POS Maharani", layout="wide")

# Inisialisasi DB
database.init_db()
auth.init_users()

# Session State
if "user" not in st.session_state:
    st.session_state.user = None

# Login
if not st.session_state.user:
    st.title("🔐 Login POS Maharani")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            user = auth.login_streamlit(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Login berhasil sebagai {user['username']} ({user['role']})")
            else:
                st.error("Username atau password salah.")

else:
    # Menu
    st.sidebar.title("📋 Menu")
    menu = st.sidebar.radio("Pilih halaman:", ["Produk", "Transaksi", "Laporan", "Export Excel", "Logout"])

    st.sidebar.write(f"👤 {st.session_state.user['username']} ({st.session_state.user['role']})")

    if menu == "Produk":
        products.streamlit_view(st.session_state.user)

    elif menu == "Transaksi":
        transactions.streamlit_transaksi()

    elif menu == "Laporan":
        reports.streamlit_laporan()

    elif menu == "Export Excel":
        reports.export_to_excel()
        st.success("Laporan berhasil diekspor ke 'laporan_penjualan.xlsx'")

    elif menu == "Logout":
        st.session_state.user = None
        st.experimental_rerun()

