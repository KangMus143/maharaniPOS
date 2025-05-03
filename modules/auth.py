import streamlit as st
import hashlib
from .database import get_db_connection

def buat_hash(password):
    """Buat hash SHA256 dari password"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def login(username, password):
    """Verifikasi kredensial login"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = buat_hash(password)
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {"id": user[0], "username": user[1], "role": user[2]}
    return None

def login_form():
    """Menampilkan form login"""
    st.title("POS Maharani - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Harap masukkan username dan password")
                return False
                
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.session_state.authenticated = True
                st.success(f"Selamat datang, {username}!")
                st.experimental_rerun()  # Halaman di-refresh
                return True
            else:
                st.error("Username atau password salah")
                return False
    
    return False
