import streamlit as st
import hashlib
import sqlite3
from .database import get_db_connection

def buat_hash(password):
    """Buat hash SHA256 dari password"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def buat_tabel_pengguna():
    """Membuat tabel pengguna jika belum ada"""
    conn = get_db_connection()
    cursor = conn.cursor()
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

def buat_pengguna_default():
    """Membuat pengguna default admin jika tidak ada pengguna"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_username = "admin"
        default_password = "admin123"
        hashed_password = buat_hash(default_password)
        
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (default_username, hashed_password, "admin")
        )
        conn.commit()
    
    conn.close()

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

def tambah_pengguna(username, password, role):
    """Menambahkan pengguna baru ke database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        hashed_password = buat_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        sukses = True
        pesan = f"Pengguna {username} berhasil ditambahkan"
    except sqlite3.IntegrityError:
        sukses = False
        pesan = f"Username {username} sudah ada"
    except Exception as e:
        sukses = False
        pesan = f"Error: {str(e)}"
    
    conn.close()
    return sukses, pesan

def ambil_pengguna():
    """Mengambil semua pengguna dari database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, role, created_at FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return users

def hapus_pengguna(user_id):
    """Menghapus pengguna dari database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

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

def init_auth():
    """Inisialisasi otentikasi"""
    buat_tabel_pengguna()
    buat_pengguna_default()

def form_login():
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
                st.experimental_rerun()
                return True
            else:
                st.error("Username atau password salah")
                return False
    
    return False

def manajemen_pengguna():
    """Antarmuka manajemen pengguna"""
    if not st.session_state.get("authenticated", False) or st.session_state.user["role"] != "admin":
        st.warning("Akses tidak sah")
        return
    
    st.subheader("Manajemen Pengguna")
    
    # Tambahkan pengguna baru
    with st.expander("Tambah Pengguna Baru"):
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "cashier"])
            
            submitted = st.form_submit_button("Tambah Pengguna")
            if submitted:
                if not new_username or not new_password:
                    st.error("Harap lengkapi semua kolom")
                else:
                    sukses, pesan = tambah_pengguna(new_username, new_password, new_role)
                    if sukses:
                        st.success(pesan)
                    else:
                        st.error(pesan)
    
    # Daftar pengguna
    st.subheader("Daftar Pengguna")
    users = ambil_pengguna()
    
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

def logout():
    """Logout pengguna saat ini"""
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.experimental_rerun()
