import sqlite3
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
            if submit:
                if user:
                    st.session_state.user = user
                    st.session_state.authenticated = True
                    st.success(f"Selamat datang, {username}!")
                    st.rerun()  # Ganti dengan st.rerun()
                else:
                    st.error("Username atau password salah")  
            return False

def init_auth():
    """Inisialisasi otentikasi - Membuat tabel pengguna jika belum ada"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Membuat tabel pengguna jika belum ada
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

    # Membuat pengguna admin default jika tidak ada pengguna
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    if count == 0:
        # Membuat pengguna default (admin)
        default_username = "admin"
        default_password = "admin123"
        hashed_password = buat_hash(default_password)
        
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (default_username, hashed_password, "admin")
        )
        conn.commit()
    conn.close()

def user_management():
    """Manajemen pengguna (menambahkan, menghapus, memperbarui pengguna)"""
    if not st.session_state.get("authenticated", False) or st.session_state.user["role"] != "admin":
        st.warning("Akses tidak sah")
        return
    
    st.subheader("Manajemen Pengguna")
    
    # Daftar Pengguna
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, role, created_at FROM users")
    users = cursor.fetchall()
    
    for user in users:
        user_id, username, role, created_at = user
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{username}** ({role})")
        
        with col2:
            if st.button("Reset Password", key=f"reset_{user_id}"):
                new_pass = "password123"
                ganti_password(user_id, new_pass)
                st.info(f"Password reset menjadi: {new_pass}")
        
        with col3:
            if username != "admin" and st.button("Hapus", key=f"delete_{user_id}"):
                hapus_pengguna(user_id)
                st.success(f"Pengguna {username} dihapus")
                st.experimental_rerun()
        
        st.divider()

def ganti_password(user_id, new_password):
    """Mengganti password pengguna"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = buat_hash(new_password)
    cursor.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (hashed_password, user_id)
    )
    conn.commit()
    conn.close()

def hapus_pengguna(user_id):
    """Menghapus pengguna dari database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def logout():
    """Mengeluarkan pengguna dan menghapus status otentikasi"""
    if "authenticated" in st.session_state:
        del st.session_state["authenticated"]
        del st.session_state["user"]
    st.success("Anda telah logout.")
    st.experimental_rerun()

def init_auth():
    """Inisialisasi otentikasi - Membuat tabel pengguna jika belum ada"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Membuat tabel pengguna jika belum ada
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Membuat pengguna admin default jika tidak ada pengguna
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Membuat pengguna default (admin)
        default_username = "admin"
        default_password = "admin123"
        hashed_password = buat_hash(default_password)
        
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (default_username, hashed_password, "admin")
        )
        conn.commit()

    # Jangan tutup koneksi di sini, biarkan tetap terbuka
    # conn.close()  # Hapus baris ini
    
    # Jika Anda ingin menutup koneksi, pastikan melakukannya setelah semua operasi selesai
    return conn  # Anda bisa menutup koneksi saat sudah selesai menggunakan `conn.close()`
