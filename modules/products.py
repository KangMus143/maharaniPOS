import streamlit as st
import pandas as pd
from .database import get_db_connection

def product_management():
    """Manage products - add, update, delete, view"""
    st.title("Manajemen Produk")
    
    # Create tabs for different product management operations
    tab1, tab2, tab3 = st.tabs(["Daftar Produk", "Tambah Produk", "Update Stok"])
    
    with tab1:
        display_product_list()
    
    with tab2:
        add_product_form()
    
    with tab3:
        update_stock_form()

def display_product_list():
    """Display the list of products with search and filter options"""
    st.subheader("Daftar Produk")
    
    # Search and filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Cari Produk", "")
    with col2:
        filter_category = st.selectbox("Kategori", ["Semua"] + get_product_categories())
    
    # Get products with filtering
    products = get_products(search_term, filter_category)
    
    if not products:
        st.info("Tidak ada produk yang ditemukan.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(products)
    
    # Display products
    for i, product in df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{product['name']}** - {product['category']}")
            st.write(f"Harga: Rp {product['price']:,.0f} | Stok: {product['stock']}")
        
        with col2:
            if st.button("Edit", key=f"edit_{product['id']}"):
                st.session_state.edit_product_id = product['id']
                st.session_state.edit_product_data = product
                st.experimental_rerun()
        
        with col3:
            if st.button("Hapus", key=f"delete_{product['id']}"):
                delete_product(product['id'])
                st.success(f"Produk {product['name']} berhasil dihapus")
                st.experimental_rerun()
        
        st.divider()
    
    # Edit product form (show if a product is selected for editing)
    if "edit_product_id" in st.session_state and "edit_product_data" in st.session_state:
        with st.form("edit_product_form"):
            st.subheader(f"Edit Produk: {st.session_state.edit_product_data['name']}")
            
            name = st.text_input("Nama Produk", st.session_state.edit_product_data['name'])
            price = st.number_input("Harga (Rp)", min_value=0.0, value=float(st.session_state.edit_product_data['price']))
            stock = st.number_input("Stok", min_value=0, value=int(st.session_state.edit_product_data['stock']))
            category = st.text_input("Kategori", st.session_state.edit_product_data['category'])
            description = st.text_area("Deskripsi", st.session_state.edit_product_data.get('description', ''))
            barcode = st.text_input("Barcode (Opsional)", st.session_state.edit_product_data.get('barcode', ''))
            
            submit = st.form_submit_button("Update Produk")
            
            if submit:
                product_data = {
                    'name': name,
                    'price': price,
                    'stock': stock,
                    'category': category,
                    'description': description,
                    'barcode': barcode
                }
                
                update_product(st.session_state.edit_product_id, product_data)
                st.success(f"Produk {name} berhasil diupdate")
                
                # Clear the edit state
                del st.session_state.edit_product_id
                del st.session_state.edit_product_data
                st.experimental_rerun()

def add_product_form():
    """Form to add a new product"""
    st.subheader("Tambah Produk Baru")
    
    with st.form("add_product_form"):
        name = st.text_input("Nama Produk")
        price = st.number_input("Harga (Rp)", min_value=0.0, step=1000.0)
        stock = st.number_input("Stok Awal", min_value=0)
        category = st.text_input("Kategori")
        description = st.text_area("Deskripsi (Opsional)")
        barcode = st.text_input("Barcode (Opsional)")
        
        submit = st.form_submit_button("Tambah Produk")
        
        if submit:
            if not name or price <= 0 or not category:
                st.error("Nama produk, harga, dan kategori harus diisi!")
            else:
                product_data = {
                    'name': name,
                    'price': price,
                    'stock': stock,
                    'category': category,
                    'description': description,
                    'barcode': barcode
                }
                
                add_product(product_data)
                st.success(f"Produk {name} berhasil ditambahkan")
                st.experimental_rerun()

def update_stock_form():
    """Form to update product stock"""
    st.subheader("Update Stok Produk")
    
    products = get_products()
    if not products:
        st.info("Tidak ada produk yang terdaftar.")
        return
    
    # Convert to list of dictionaries with id and name for the selectbox
    product_options = [{"id": p["id"], "name": p["name"]} for p in products]
    
    # Create a selectbox with product names
    selected_product = st.selectbox(
        "Pilih Produk",
        options=range(len(product_options)),
        format_func=lambda i: product_options[i]["name"]
    )
    
    # Get the selected product ID
    product_id = product_options[selected_product]["id"]
    
    # Get the current product details
    product = ambil_produk_berdasarkan_id(product_id)
    
    if product:
        st.write(f"Stok Saat Ini: {product['stock']}")
        
        # Options for stock adjustment
        action = st.radio("Tindakan", ["Tambah Stok", "Kurangi Stok"])
        
        # Amount to adjust
        amount = st.number_input("Jumlah", min_value=1, value=1)
        
        # Reason for adjustment
        reason = st.text_input("Alasan Penyesuaian (Opsional)")
        
        if st.button("Update Stok"):
            # Determine the adjustment (positive for addition, negative for reduction)
            adjustment = amount if action == "Tambah Stok" else -amount
            
            # Check if reduction would result in negative stock
            if action == "Kurangi Stok" and product["stock"] < amount:
                st.error("Stok tidak mencukupi untuk pengurangan!")
            else:
                success, message = perbarui_stok_produk(product_id, adjustment, reason)
                if success:
                    st.success(message)
                    st.experimental_rerun()
                else:
                    st.error(message)

def get_products(search_term="", category="Semua"):
    """Get list of products with optional filtering"""
    conn = get_db_connection()
    
    # Determine if we're using Supabase or SQLite
    if hasattr(conn, 'table'):  # Supabase client
        query = conn.table('products').select('*')
        
        if search_term:
            query = query.ilike('name', f'%{search_term}%')
        
        if category and category != "Semua":
            query = query.eq('category', category)
        
        response = query.order('name').execute()
        products = response.data
    else:  # SQLite connection
        cursor = conn.cursor()
        
        sql = "SELECT * FROM products"
        params = []
        
        if search_term or (category and category != "Semua"):
            sql += " WHERE"
            
            if search_term:
                sql += " name LIKE ?"
                params.append(f"%{search_term}%")
                
                if category and category != "Semua":
                    sql += " AND"
            
            if category and category != "Semua":
                sql += " category = ?"
                params.append(category)
        
        sql += " ORDER BY name"
        
        cursor.execute(sql, params)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
    
    return products

def get_product_categories():
    """Get unique list of product categories"""
    conn = get_db_connection()
    
    # Determine if we're using Supabase or SQLite
    if hasattr(conn, 'table'):  # Supabase client
        response = conn.table('products').select('category').execute()
        categories = set(item['category'] for item in response.data)
    else:  # SQLite connection
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = set(row['category'] for row in cursor.fetchall())
        conn.close()
    
    return sorted(list(categories))

def ambil_produk_berdasarkan_id(product_id):
    """Get product by its ID"""
    conn = get_db_connection()
    
    # Determine if we're using Supabase or SQLite
    if hasattr(conn, 'table'):  # Supabase client
        response = conn.table('products').select('*').eq('id', product_id).execute()
        if response.data:
            return response.data[0]
        return None
    else:  # SQLite connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        
        if product:
            return dict(product)
        return None

def add_product(product_data):
    """Add a new product to the database"""
    conn = get_db_connection()
    
    try:
        # Determine if we're using Supabase or SQLite
        if hasattr(conn, 'table'):  # Supabase client
            response = conn.table('products').insert(product_data).execute()
            return True, "Produk berhasil ditambahkan"
        else:  # SQLite connection
            cursor = conn.cursor()
            
            columns = ', '.join(product_data.keys())
            placeholders = ', '.join(['?'] * len(product_data))
            
            sql = f"INSERT INTO products ({columns}) VALUES ({placeholders})"
            
            cursor.execute(sql, list(product_data.values()))
            conn.commit()
            conn.close()
            
            return True, "Produk berhasil ditambahkan"
    except Exception as e:
        if not hasattr(conn, 'table'):  # SQLite connection
            conn.close()
        return False, f"Error: {str(e)}"

def update_product(product_id, product_data):
    """Update an existing product"""
    conn = get_db_connection()
    
    try:
        # Determine if we're using Supabase or SQLite
        if hasattr(conn, 'table'):  # Supabase client
            response = conn.table('products').update(product_data).eq('id', product_id).execute()
            return True, "Produk berhasil diupdate"
        else:  # SQLite connection
            cursor = conn.cursor()
            
            set_clause = ', '.join([f"{key} = ?" for key in product_data.keys()])
            values = list(product_data.values())
            values.append(product_id)
            
            sql = f"UPDATE products SET {set_clause} WHERE id = ?"
            
            cursor.execute(sql, values)
            conn.commit()
            conn.close()
            
            return True, "Produk berhasil diupdate"
    except Exception as e:
        if not hasattr(conn, 'table'):  # SQLite connection
            conn.close()
        return False, f"Error: {str(e)}"

def delete_product(product_id):
    """Delete a product by its ID"""
    conn = get_db_connection()
    
    try:
        # Determine if we're using Supabase or SQLite
        if hasattr(conn, 'table'):  # Supabase client
            response = conn.table('products').delete().eq('id', product_id).execute()
            return True, "Produk berhasil dihapus"
        else:  # SQLite connection
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            
            return True, "Produk berhasil dihapus"
    except Exception as e:
        if not hasattr(conn, 'table'):  # SQLite connection
            conn.close()
        return False, f"Error: {str(e)}"

def perbarui_stok_produk(product_id, adjustment, reason=""):
    """Update product stock by adding or subtracting"""
    conn = get_db_connection()
    
    try:
        # Get current product info
        product = ambil_produk_berdasarkan_id(product_id)
        
        if not product:
            return False, "Produk tidak ditemukan"
        
        # Calculate new stock
        new_stock = product['stock'] + adjustment
        
        # Prevent negative stock
        if new_stock < 0:
            return False, "Stok tidak boleh negatif"
        
        # Determine if we're using Supabase or SQLite
        if hasattr(conn, 'table'):  # Supabase client
            response = conn.table('products').update({
                'stock': new_stock,
                'updated_at': 'now()'
            }).eq('id', product_id).execute()
            
            action = "ditambahkan" if adjustment > 0 else "dikurangi"
            return True, f"Stok produk berhasil {action} menjadi {new_stock}"
        else:  # SQLite connection
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (new_stock, product_id)
            )
            conn.commit()
            conn.close()
            
            action = "ditambahkan" if adjustment > 0 else "dikurangi"
            return True, f"Stok produk berhasil {action} menjadi {new_stock}"
    except Exception as e:
        if not hasattr(conn, 'table'):  # SQLite connection
            conn.close()
        return False, f"Error: {str(e)}"

def get_low_stock_products(threshold=10):
    """Get products with stock below the threshold"""
    conn = get_db_connection()
    
    # Determine if we're using Supabase or SQLite
    if hasattr(conn, 'table'):  # Supabase client
        response = conn.table('products').select('*').lt('stock', threshold).execute()
        low_stock = response.data
        return pd.DataFrame(low_stock) if low_stock else pd.DataFrame()
    else:  # SQLite connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE stock < ?", (threshold,))
        low_stock = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return pd.DataFrame(low_stock) if low_stock else pd.DataFrame()
