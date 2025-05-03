import sqlite3
import os
import streamlit as st
import pandas as pd

# Pastikan direktori data ada
if not os.path.exists('data'):
    os.makedirs('data')

def get_db_connection():
    """Membuat koneksi database ke SQLite"""
    conn = sqlite3.connect('data/maharani.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Inisialisasi database dengan tabel yang diperlukan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Membuat tabel produk
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Membuat tabel transaksi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        cashier_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cashier_id) REFERENCES users (id)
    )
    ''')
    
    # Membuat tabel item transaksi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_per_unit REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetchall=False):
    """Menjalankan query ke database"""
    conn = get_db_connection()
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

def get_dataframe_from_query(query, params=()):
    """Menjalankan query dan mengembalikan hasilnya sebagai DataFrame pandas"""
    conn = get_db_connection()
    return pd.read_sql_query(query, conn, params=params)
