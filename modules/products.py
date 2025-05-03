import streamlit as st
import pandas as pd
import sqlite3
from .database import get_db_connection, execute_query, get_dataframe_from_query

def tambah_produk(nama, kategori, harga, stok):
    """Menambahkan produk baru ke database"""
    query = '''
    INSERT INTO products (name, category, price, stock)
    VALUES (?, ?, ?, ?)
    '''
    
    try:
        execute_query(query, (nama, kategori, harga, stok))
        return True, f"Produk '{nama}' berhasil ditambahkan"
    except sqlite3.IntegrityError:
        return False, f"Produk '{nama}' sudah ada"
    except Exception as e:
        return False, f"Error: {str(e)}"

def perbarui_produk(id_produk, nama, kategori, harga, stok):
    """Memperbarui produk yang ada"""
    query = '''
    UPDATE products
    SET name = ?, category = ?, price = ?, stock = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        execute_query(query, (nama, kategori, harga, stok, id_produk))
        return True, f"Produk '{nama}' berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def hapus_produk(id_produk):
    """Menghapus produk dari database"""
    # Periksa apakah produk digunakan dalam transaksi
    check_query = '''
    SELECT COUNT(*) as count FROM transaction_items WHERE product_id = ?
    '''
    result = execute_query(check_query, (id_produk,), fetchall=False)
    
    if result and result[0] > 0:
        return False, "Tidak dapat menghapus produk karena digunakan dalam transaksi"
    
    # Menghapus produk
    query = "DELETE FROM products WHERE id = ?"
    try:
        execute_query(query, (id_produk,))
        return True, "Produk berhasil dihapus"
    except Exception as e:
        return False, f"Error: {str(e)}"

def ambil_produk(id_produk):
    """Mengambil produk berdasarkan ID"""
    query = "SELECT * FROM products WHERE id = ?"
    result = execute_query(query, (id_produk,), fetchall=False)
    return result

# Fungsi tambahan yang dipanggil dari transactions.py
def ambil_produk_berdasarkan_id(id_produk):
    """Mengambil produk berdasarkan ID (alias untuk ambil_produk)"""
    return ambil_produk(id_produk)

def perbarui_stok_produk(id_produk, perubahan_stok):
    """Memperbarui stok produk (tambah atau kurangi)"""
    query = '''
    UPDATE products
    SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        execute_query(query, (perubahan_stok, id_produk))
        return True, "Stok berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def ambil_produk_list(search_term="", kategori=""):
    """Mengambil daftar produk dengan filter opsional"""
    query = "SELECT * FROM products"
    params = []
    
    conditions = []
    if search_term:
        conditions.append("name LIKE ?")
        params.append(f"%{search_term}%")
    
    if kategori and kategori != "Semua":
        conditions.append("category = ?")
        params.append(kategori)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY category, name"
    
    return get_dataframe_from_query(query, params)

def ambil_kategori_produk():
    """Mengambil semua kategori produk"""
    query = "SELECT DISTINCT category FROM products ORDER BY category"
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    categories = df['category'].tolist()
    return categories

def perbarui_stok(id_produk, perubahan_stok):
    """Memperbarui stok produk (tambah atau kurangi)"""
    return perbarui_stok_produk(id_produk, perubahan_stok)

def ambil_produk_stok_rendah(batas=10):
    """Mengambil produk dengan stok di bawah batas"""
    query = "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC"
    return get_dataframe_from_query(query, (batas,))
