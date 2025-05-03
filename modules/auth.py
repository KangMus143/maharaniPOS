import streamlit as st
import hashlib
import sqlite3
from .database import dapatkan_koneksi_db

def buat_hash(kata_sandi):
    """Membuat hash SHA256 dari kata sandi"""
    return hashlib.sha256(str.encode(kata_sandi)).hexdigest()

def buat_tabel_pengguna():
    """Membuat tabel pengguna jika belum ada"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pengguna (
        id_pengguna INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_pengguna TEXT UNIQUE NOT NULL,
        kata_sandi TEXT NOT NULL,
        peran TEXT NOT NULL,
        dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def buat_pengguna_default():
    """Membuat pengguna admin default jika tidak ada pengguna"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pengguna")
    jumlah = cursor.fetchone()[0]
    
    if jumlah == 0:
        nama_pengguna_default = "admin"
        kata_sandi_default = "admin123"
        hash_kata_sandi = buat_hash(kata_sandi_default)
        
        cursor.execute(
            "INSERT INTO pengguna (nama_pengguna, kata_sandi, peran) VALUES (?, ?, ?)",
            (nama_pengguna_default, hash_kata_sandi, "admin")
        )
        conn.commit()
    
    conn.close()

def masuk(nama_pengguna, kata_sandi):
    """Memverifikasi kredensial login"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    hash_kata_sandi = buat_hash(kata_sandi)
    cursor.execute(
        "SELECT id_pengguna, nama_pengguna, peran FROM pengguna WHERE nama_pengguna = ? AND kata_sandi = ?",
        (nama_pengguna, hash_kata_sandi)
    )
    pengguna = cursor.fetchone()
    conn.close()
    
    if pengguna:
        return {"id": pengguna[0], "nama_pengguna": pengguna[1], "peran": pengguna[2]}
    return None

def tambah_pengguna(nama_pengguna, kata_sandi, peran):
    """Menambahkan pengguna baru ke database"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    try:
        hash_kata_sandi = buat_hash(kata_sandi)
        cursor.execute(
            "INSERT INTO pengguna (nama_pengguna, kata_sandi, peran) VALUES (?, ?, ?)",
            (nama_pengguna, hash_kata_sandi, peran)
        )
        conn.commit()
        sukses = True
        pesan = f"Pengguna {nama_pengguna} berhasil ditambahkan"
    except sqlite3.IntegrityError:
        sukses = False
        pesan = f"Nama pengguna {nama_pengguna} sudah ada"
    except Exception as e:
        sukses = False
        pesan = f"Error: {str(e)}"
    
    conn.close()
    return sukses, pesan

def dapatkan_pengguna():
    """Mendapatkan semua pengguna dari database"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id_pengguna, nama_pengguna, peran, dibuat_pada FROM pengguna")
    pengguna = cursor.fetchall()
    conn.close()
    
    return pengguna

def hapus_pengguna(id_pengguna):
    """Menghapus pengguna dari database"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM pengguna WHERE id_pengguna = ?", (id_pengguna,))
    conn.commit()
    conn.close()

def ubah_kata_sandi(id_pengguna, kata_sandi_baru):
    """Mengubah kata sandi pengguna"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    hash_kata_sandi = buat_hash(kata_sandi_baru)
    cursor.execute(
        "UPDATE pengguna SET kata_sandi = ? WHERE id_pengguna = ?",
        (hash_kata_sandi, id_pengguna)
    )
    conn.commit()
    conn.close()

def inisialisasi_autentikasi():
    """Inisialisasi autentikasi"""
    buat_tabel_pengguna()
    buat_pengguna_default()

def formulir_login():
    """Menampilkan formulir login"""
    st.title("POS Maharani - Login")
    
    with st.form("formulir_login"):
        nama_pengguna = st.text_input("Nama Pengguna")
        kata_sandi = st.text_input("Kata Sandi", type="password")
        tombol = st.form_submit_button("Masuk")
        
        if tombol:
            if not nama_pengguna or not kata_sandi:
                st.error("Silakan masukkan nama pengguna dan kata sandi")
                return False
                
            pengguna = masuk(nama_pengguna, kata_sandi)
            if pengguna:
                st.session_state.pengguna = pengguna
                st.session_state.terotentikasi = True
                st.success(f"Selamat datang, {nama_pengguna}!")
                st.experimental_rerun()
                return True
            else:
                st.error("Nama pengguna atau kata sandi tidak valid")
                return False
    
    return False

def manajemen_pengguna():
    """Antarmuka manajemen pengguna"""
    if not st.session_state.get("terotentikasi", False) or st.session_state.pengguna["peran"] != "admin":
        st.warning("Akses tidak diizinkan")
        return
    
    st.subheader("Manajemen Pengguna")
    
    # Tambah pengguna baru
    with st.expander("Tambah Pengguna Baru"):
        with st.form("formulir_tambah_pengguna"):
            nama_pengguna_baru = st.text_input("Nama Pengguna")
            kata_sandi_baru = st.text_input("Kata Sandi", type="password")
            peran_baru = st.selectbox("Peran", ["admin", "kasir"])
            
            terkirim = st.form_submit_button("Tambah Pengguna")
            if terkirim:
                if not nama_pengguna_baru or not kata_sandi_baru:
                    st.error("Harap isi semua kolom")
                else:
                    sukses, pesan = tambah_pengguna(nama_pengguna_baru, kata_sandi_baru, peran_baru)
                    if sukses:
                        st.success(pesan)
                    else:
                        st.error(pesan)
    
    # Daftar pengguna
    st.subheader("Daftar Pengguna")
    pengguna_list = dapatkan_pengguna()
    
    for pengguna in pengguna_list:
        id_pengguna, nama_pengguna, peran, dibuat_pada = pengguna
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{nama_pengguna}** ({peran})")
        
        with col2:
            if st.button("Reset Kata Sandi", key=f"reset_{id_pengguna}"):
                kata_sandi_baru = "password123"
                ubah_kata_sandi(id_pengguna, kata_sandi_baru)
                st.info(f"Kata sandi direset menjadi: {kata_sandi_baru}")
        
        with col3:
            if nama_pengguna != "admin" and st.button("Hapus", key=f"hapus_{id_pengguna}"):
                hapus_pengguna(id_pengguna)
                st.success(f"Pengguna {nama_pengguna} dihapus")
                st.experimental_rerun()
        
        st.divider()

def keluar():
    """Keluar pengguna saat ini"""
    if st.sidebar.button("Keluar"):
        st.session_state.terotentikasi = False
        st.session_state.pengguna = None
        st.experimental_rerun()
