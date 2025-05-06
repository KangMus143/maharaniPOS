import streamlit as st
import pandas as pd
from .database import get_db_connection, execute_query, get_dataframe_from_query

def perbarui_stok_produk(id_produk, perubahan_stok):
    """Memperbarui stok produk (tambah atau kurangi)"""
    query = '''
    UPDATE products
    SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (perubahan_stok, id_produk))
        conn.commit()
        conn.close()
        return True, "Stok produk berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def perbarui_stok_produk(id_produk, perubahan_stok):
    """Memperbarui stok produk (tambah atau kurangi)"""
    query = '''
    UPDATE products
    SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (perubahan_stok, id_produk))
        conn.commit()
        conn.close()
        return True, "Stok produk berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_product_categories():
    """Mengambil semua kategori produk yang ada di database"""
    query = "SELECT DISTINCT category FROM products ORDER BY category"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(query)
    categories = cursor.fetchall()
    conn.close()

    # Mengembalikan daftar kategori
    return [category[0] for category in categories]

def dapatkan_laporan_penjualan(tanggal_mulai, tanggal_akhir):
    """Dapatkan laporan penjualan antara dua tanggal"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                t.id_transaksi,
                t.tanggal_transaksi,
                t.nama_pelanggan,
                t.total_belanja,
                t.metode_pembayaran
            FROM transaksi t
            WHERE t.tanggal_transaksi BETWEEN ? AND ?
            ORDER BY t.tanggal_transaksi DESC
        """, (tanggal_mulai, tanggal_akhir + " 23:59:59"))
        
        transaksi = cursor.fetchall()
        return [dict(row) for row in transaksi]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def get_low_stock_products(threshold=10):
    """Mengambil produk dengan stok di bawah threshold"""
    query = "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC"
    return get_dataframe_from_query(query, (threshold,))

def perbarui_stok_produk(id_produk, perubahan_stok):
    """Memperbarui stok produk (tambah atau kurangi)"""
    query = '''
    UPDATE products
    SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (perubahan_stok, id_produk))
        conn.commit()
        conn.close()
        return True, "Stok produk berhasil diperbarui"
    except Exception as e:
        return False, f"Error: {str(e)}"

def ambil_produk_berdasarkan_id(id_produk):
    """Mengambil produk berdasarkan ID"""
    query = "SELECT * FROM products WHERE id = ?"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(query, (id_produk,))
    product = cursor.fetchone()
    
    conn.close()
    
    if product:
        return {
            "id": product[0],
            "name": product[1],
            "category": product[2],
            "price": product[3],
            "stock": product[4]
        }
    return None
    
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
    check_query = '''
    SELECT COUNT(*) as count FROM transaction_items WHERE product_id = ?
    '''
    result = execute_query(check_query, (id_produk,), fetchall=False)
    
    if result and result[0] > 0:
        return False, "Tidak dapat menghapus produk karena digunakan dalam transaksi"
    
    query = "DELETE FROM products WHERE id = ?"
    try:
        execute_query(query, (id_produk,))
        return True, "Produk berhasil dihapus"
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

def product_management():
    """Antarmuka manajemen produk"""
    st.subheader("Manajemen Produk")
    
    # Tab 1: Daftar Produk
    with st.expander("Daftar Produk"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("Cari Produk", key="product_search")
        
        with col2:
            categories = ["Semua"] + get_product_categories()
            category_filter = st.selectbox("Kategori", categories, key="category_filter")
        
        # Ambil produk dengan filter
        products_df = ambil_produk_list(search_term, category_filter)
        
        if products_df.empty:
            st.info("Tidak ada produk ditemukan")
        else:
            for index, product in products_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{product['name']}**")
                    st.write(f"Kategori: {product['category']}")
                
                with col2:
                    st.write(f"Harga: Rp {product['price']:,.0f}")
                    st.write(f"Stok: {product['stock']}")
                
                with col3:
                    if st.button("Edit", key=f"edit_{product['id']}"):
                        st.session_state.editing_product = product['id']
                        st.experimental_rerun()
                    
                    if st.button("Hapus", key=f"delete_{product['id']}"):
                        success, message = hapus_produk(product['id'])
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                
                # Menampilkan form edit produk jika produk sedang diedit
                if st.session_state.get("editing_product") == product['id']:
                    with st.form(key=f"edit_product_form_{product['id']}"):
                        st.subheader(f"Edit Produk: {product['name']}")
                        
                        name = st.text_input("Nama Produk", value=product['name'])
                        categories = get_product_categories()
                        category = st.selectbox("Kategori", categories, index=categories.index(product['category']))
                        price = st.number_input("Harga (Rp)", min_value=0.0, value=float(product['price']), step=1000.0)
                        stock = st.number_input("Stok", min_value=0, value=int(product['stock']))
                        
                        submit = st.form_submit_button("Perbarui")
                        if submit:
                            success, message = perbarui_produk(product['id'], name, category, price, stock)
                            if success:
                                st.success(message)
                                st.session_state.editing_product = None
                                st.experimental_rerun()
                            else:
                                st.error(message)
                
                st.divider()
    
    # Tab 2: Tambah Produk Baru
    with st.expander("Tambah Produk Baru"):
        with st.form(key="add_product_form"):
            st.subheader("Tambah Produk")
            
            name = st.text_input("Nama Produk")
            categories = get_product_categories()
            category_option = st.selectbox("Kategori", categories + ["Kategori Baru"], index=len(categories) if categories else 0)
            
            if category_option == "Kategori Baru":
                category = st.text_input("Nama Kategori Baru")
            else:
                category = category_option
            
            price = st.number_input("Harga (Rp)", min_value=0.0, value=0.0, step=1000.0)
            stock = st.number_input("Stok Awal", min_value=0, value=0)
            
            submit = st.form_submit_button("Tambah Produk")
            if submit:
                if not name or not category:
                    st.error("Harap lengkapi semua kolom")
                else:
                    success, message = tambah_produk(name, category, price, stock)
                    if success:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
