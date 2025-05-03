"""
Modul produk untuk aplikasi MaharaniPOS
"""

import streamlit as st
import pandas as pd
import sqlite3
from database import dapatkan_koneksi_db, eksekusi_query, dapatkan_dataframe_dari_query

def tambah_produk(nama, kategori, harga, stok):
    """Tambah produk baru ke database"""
    query = '''
    INSERT INTO produk (nama, kategori, harga, stok)
    VALUES (?, ?, ?, ?)
    '''
    
    try:
        eksekusi_query(query, (nama, kategori, harga, stok))
        return True, f"Produk '{nama}' berhasil ditambahkan"
    except sqlite3.IntegrityError:
        return False, f"Produk '{nama}' sudah ada"
    except Exception as e:
        return False, f"Error: {str(e)}"

def perbarui_produk(id_produk, nama, kategori, harga, stok):
    """Perbarui produk yang ada"""
    query = '''
    UPDATE produk
    SET nama = ?, kategori = ?, harga = ?, stok = ?, diperbarui_pada = CURRENT_TIMESTAMP
    WHERE id_produk = ?
    '''
    
    try:
        eksekusi_query(query, (nama, kategori, harga, stok, id_produk))
        return True, f"Produk '{nama}' berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def hapus_produk(id_produk):
    """Hapus produk dari database"""
    # Periksa apakah produk digunakan dalam transaksi
    check_query = '''
    SELECT COUNT(*) as count FROM detail_transaksi WHERE id_produk = ?
    '''
    result = eksekusi_query(check_query, (id_produk,), fetchall=False)
    
    if result and result[0] > 0:
        return False, "Tidak dapat menghapus produk karena sudah direferensikan dalam transaksi"
    
    # Hapus produk
    query = "DELETE FROM produk WHERE id_produk = ?"
    try:
        eksekusi_query(query, (id_produk,))
        return True, "Produk berhasil dihapus"
    except Exception as e:
        return False, f"Error: {str(e)}"

def dapatkan_produk(id_produk):
    """Dapatkan satu produk berdasarkan ID"""
    query = "SELECT * FROM produk WHERE id_produk = ?"
    result = eksekusi_query(query, (id_produk,), fetchall=False)
    return result

def dapatkan_produk_berdasarkan_id(id_produk):
    """Dapatkan satu produk berdasarkan ID (alias untuk dapatkan_produk untuk kompatibilitas)"""
    return dapatkan_produk(id_produk)

def perbarui_stok_produk(id_produk, perubahan_jumlah):
    """Perbarui stok produk (tambah atau kurang)"""
    query = '''
    UPDATE produk
    SET stok = stok + ?, diperbarui_pada = CURRENT_TIMESTAMP
    WHERE id_produk = ?
    '''
    
    try:
        eksekusi_query(query, (perubahan_jumlah, id_produk))
        return True, "Stok berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def dapatkan_produk_semua(kata_kunci="", kategori=""):
    """Dapatkan semua produk dengan filter opsional"""
    query = "SELECT * FROM produk"
    params = []
    
    conditions = []
    if kata_kunci:
        conditions.append("nama LIKE ?")
        params.append(f"%{kata_kunci}%")
    
    if kategori and kategori != "Semua":
        conditions.append("kategori = ?")
        params.append(kategori)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY kategori, nama"
    
    return dapatkan_dataframe_dari_query(query, params)

def dapatkan_kategori_produk():
    """Dapatkan semua kategori produk"""
    query = "SELECT DISTINCT kategori FROM produk ORDER BY kategori"
    conn = dapatkan_koneksi_db()
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    kategori = df['kategori'].tolist()
    return kategori

def perbarui_stok(id_produk, perubahan_jumlah):
    """Perbarui stok produk (tambah atau kurang)"""
    return perbarui_stok_produk(id_produk, perubahan_jumlah)

def dapatkan_produk_stok_rendah(ambang_batas=10):
    """Dapatkan produk dengan stok di bawah ambang batas"""
    query = "SELECT * FROM produk WHERE stok <= ? ORDER BY stok ASC"
    return dapatkan_dataframe_dari_query(query, (ambang_batas,))

def manajemen_produk():
    """Antarmuka manajemen produk"""
    st.subheader("Manajemen Produk")
    
    tab1, tab2 = st.tabs(["Daftar Produk", "Tambah Produk"])
    
    # Tab 1: Daftar Produk
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            kata_kunci = st.text_input("Cari Produk", key="cari_produk")
        
        with col2:
            kategori = ["Semua"] + dapatkan_kategori_produk()
            filter_kategori = st.selectbox("Kategori", kategori, key="filter_kategori")
        
        # Dapatkan produk dengan filter
        produk_df = dapatkan_produk_semua(kata_kunci, filter_kategori)
        
        if produk_df.empty:
            st.info("Tidak ada produk ditemukan")
        else:
            for index, produk in produk_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{produk['nama']}**")
                    st.write(f"Kategori: {produk['kategori']}")
                
                with col2:
                    st.write(f"Harga: Rp {produk['harga']:,.0f}")
                    st.write(f"Stok: {produk['stok']}")
                
                with col3:
                    if st.button("Edit", key=f"edit_{produk['id_produk']}"):
                        st.session_state.edit_produk = produk['id_produk']
                        st.experimental_rerun()
                    
                    if st.button("Hapus", key=f"hapus_{produk['id_produk']}"):
                        sukses, pesan = hapus_produk(produk['id_produk'])
                        if sukses:
                            st.success(pesan)
                            st.experimental_rerun()
                        else:
                            st.error(pesan)
                
                # Tampilkan formulir edit jika produk ini sedang diedit
                if st.session_state.get("edit_produk") == produk['id_produk']:
                    with st.form(key=f"form_edit_produk_{produk['id_produk']}"):
                        st.subheader(f"Edit Produk: {produk['nama']}")
                        
                        nama = st.text_input("Nama Produk", value=produk['nama'])
                        
                        # Jika kategori ada, gunakan dropdown, jika tidak gunakan teks bebas
                        kategori_list = dapatkan_kategori_produk()
                        if kategori_list and produk['kategori'] in kategori_list:
                            kategori = st.selectbox("Kategori", kategori_list, 
                                                   index=kategori_list.index(produk['kategori']))
                        else:
                            kategori = st.text_input("Kategori", value=produk['kategori'])
                            
                        harga = st.number_input("Harga (Rp)", 
                                              min_value=0.0, 
                                              value=float(produk['harga']),
                                              step=1000.0)
                        
                        stok = st.number_input("Stok", 
                                              min_value=0, 
                                              value=int(produk['stok']))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            submit = st.form_submit_button("Perbarui")
                        with col2:
                            if st.form_submit_button("Batal"):
                                st.session_state.edit_produk = None
                                st.experimental_rerun()
                        
                        if submit:
                            sukses, pesan = perbarui_produk(
                                produk['id_produk'], nama, kategori, harga, stok
                            )
                            if sukses:
                                st.success(pesan)
                                st.session_state.edit_produk = None
                                st.experimental_rerun()
                            else:
                                st.error(pesan)
                
                st.divider()
    
    # Tab 2: Tambah Produk
    with tab2:
        with st.form(key='form_tambah_produk'):
            st.subheader("Tambah Produk Baru")
            
            nama = st.text_input("Nama Produk")
            
            # Jika kategori ada, gunakan dropdown dengan opsi "Kategori Baru", jika tidak gunakan teks bebas
            kategori_list = dapatkan_kategori_produk()
            if kategori_list:
                opsi_kategori = st.select
