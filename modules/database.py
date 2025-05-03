import sqlite3
import os
import streamlit as st
import pandas as pd

# Pastikan direktori data ada
if not os.path.exists('data'):
    os.makedirs('data')

def dapatkan_koneksi_db():
    """Membuat koneksi database ke SQLite"""
    conn = sqlite3.connect('data/maharani.db')
    conn.row_factory = sqlite3.Row
    return conn

def inisialisasi_database():
    """Inisialisasi database dengan tabel yang diperlukan"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    # Buat tabel produk
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produk (
        id_produk INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT NOT NULL,
        kategori TEXT NOT NULL,
        harga REAL NOT NULL,
        stok INTEGER NOT NULL,
        dibuat_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        diperbarui_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Buat tabel transaksi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaksi (
        id_transaksi TEXT PRIMARY KEY,
        tanggal_transaksi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        nama_pelanggan TEXT,
        total_belanja REAL NOT NULL,
        metode_pembayaran TEXT NOT NULL,
        jumlah_pembayaran REAL NOT NULL,
        jumlah_kembalian REAL NOT NULL,
        id_kasir INTEGER NOT NULL,
        FOREIGN KEY (id_kasir) REFERENCES pengguna (id_pengguna)
    )
    ''')
    
    # Buat tabel detail_transaksi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detail_transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_transaksi TEXT NOT NULL,
        id_produk INTEGER NOT NULL,
        jumlah INTEGER NOT NULL,
        harga REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (id_transaksi) REFERENCES transaksi (id_transaksi),
        FOREIGN KEY (id_produk) REFERENCES produk (id_produk)
    )
    ''')
    
    conn.commit()
    conn.close()

def eksekusi_query(query, params=(), fetchall=False):
    """Eksekusi kueri database"""
    conn = dapatkan_koneksi_db()
    cursor = conn.cursor()
    
    cursor.execute(query, params)
    
    if query.strip().upper().startswith("SELECT"):
        if fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.fetchone()
    else:
        conn.commit()
        result = None
    
    conn.close()
    return result

def dapatkan_dataframe_dari_query(query, params=()):
    """Eksekusi kueri dan mengembalikan hasil sebagai pandas DataFrame"""
    conn = dapatkan_koneksi_db()
    return pd.read_sql_query(query, conn, params=params)

def cadangkan_database():
    """Cadangkan database ke file CSV"""
    conn = dapatkan_koneksi_db()
    
    # Cadangkan produk
    produk_df = pd.read_sql_query("SELECT * FROM produk", conn)
    produk_df.to_csv("data/cadangan_produk.csv", index=False)
    
    # Cadangkan transaksi
    transaksi_df = pd.read_sql_query("SELECT * FROM transaksi", conn)
    transaksi_df.to_csv("data/cadangan_transaksi.csv", index=False)
    
    # Cadangkan detail transaksi
    detail_transaksi_df = pd.read_sql_query("SELECT * FROM detail_transaksi", conn)
    detail_transaksi_df.to_csv("data/cadangan_detail_transaksi.csv", index=False)
    
    # Cadangkan pengguna
    pengguna_df = pd.read_sql_query("SELECT id_pengguna, nama_pengguna, peran, dibuat_pada FROM pengguna", conn)
    pengguna_df.to_csv("data/cadangan_pengguna.csv", index=False)
    
    conn.close()
    return True
