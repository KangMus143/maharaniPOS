import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from modules.database import get_db_connection
from modules.products import get_product_by_id, update_product_stock

def generate_transaction_id():
    """Generate unique transaction ID with timestamp prefix"""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4()).split('-')[0]
    return f"TRX-{timestamp}-{unique_id}"

def add_to_cart(product_id, quantity):
    """Add product to shopping cart"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    product = get_product_by_id(product_id)
    
    if not product:
        st.error("Produk tidak ditemukan.")
        return False
    
    if product['stock'] < quantity:
        st.error(f"Stok tidak mencukupi. Tersedia: {product['stock']}")
        return False
    
    # Check if product already in cart
    for item in st.session_state.cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = item['quantity'] * item['price']
            return True
    
    # Add new item to cart
    st.session_state.cart.append({
        'product_id': product_id,
        'name': product['name'],
        'price': product['price'],
        'quantity': quantity,
        'subtotal': product['price'] * quantity
    })
    return True

def update_cart_item(index, quantity):
    """Update quantity of item in cart"""
    if 'cart' not in st.session_state or index >= len(st.session_state.cart):
        return False
    
    item = st.session_state.cart[index]
    product = get_product_by_id(item['product_id'])
    
    if product['stock'] < quantity:
        st.error(f"Stok tidak mencukupi. Tersedia: {product['stock']}")
        return False
    
    item['quantity'] = quantity
    item['subtotal'] = quantity * item['price']
    return True

def remove_from_cart(index):
    """Remove item from cart"""
    if 'cart' in st.session_state and index < len(st.session_state.cart):
        st.session_state.cart.pop(index)
        return True
    return False

def clear_cart():
    """Clear all items from cart"""
    if 'cart' in st.session_state:
        st.session_state.cart = []

def get_cart_total():
    """Calculate total amount of all items in cart"""
    if 'cart' not in st.session_state or not st.session_state.cart:
        return 0
    return sum(item['subtotal'] for item in st.session_state.cart)

def process_transaction(customer_name, payment_method, payment_amount):
    """Process transaction and save to database"""
    if 'cart' not in st.session_state or not st.session_state.cart:
        st.error("Keranjang belanja kosong.")
        return False
    
    transaction_id = generate_transaction_id()
    total_amount = get_cart_total()
    
    if payment_amount < total_amount:
        st.error("Pembayaran kurang dari total belanja.")
        return False
    
    change_amount = payment_amount - total_amount
    transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insert transaction header
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert transaction header
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, transaction_date, customer_name, total_amount, payment_method, payment_amount, change_amount) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (transaction_id, transaction_date, customer_name, total_amount, payment_method, payment_amount, change_amount))
        
        # Insert transaction details
        for item in st.session_state.cart:
            cursor.execute("""
                INSERT INTO transaction_details
                (transaction_id, product_id, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (transaction_id, item['product_id'], item['quantity'], item['price'], item['subtotal']))
            
            # Update stock
            update_product_stock(item['product_id'], -item['quantity'])
        
        conn.commit()
        clear_cart()
        return {
            'transaction_id': transaction_id,
            'total': total_amount,
            'payment': payment_amount,
            'change': change_amount,
            'date': transaction_date
        }
    
    except Exception as e:
        conn.rollback()
        st.error(f"Error dalam transaksi: {str(e)}")
        return False
    finally:
        conn.close()

def get_transaction_by_id(transaction_id):
    """Get transaction details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get transaction header
        cursor.execute("""
            SELECT transaction_id, transaction_date, customer_name, 
                   total_amount, payment_method, payment_amount, change_amount
            FROM transactions
            WHERE transaction_id = ?
        """, (transaction_id,))
        
        transaction = cursor.fetchone()
        if not transaction:
            return None
        
        # Get transaction details
        cursor.execute("""
            SELECT td.product_id, p.name, td.quantity, td.price, td.subtotal
            FROM transaction_details td
            JOIN products p ON td.product_id = p.product_id
            WHERE td.transaction_id = ?
        """, (transaction_id,))
        
        details = cursor.fetchall()
        
        return {
            'header': dict(transaction),
            'details': [dict(item) for item in details]
        }
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    finally:
        conn.close()

def get_recent_transactions(limit=10):
    """Get list of recent transactions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT transaction_id, transaction_date, customer_name, total_amount, payment_method
            FROM transactions
            ORDER BY transaction_date DESC
            LIMIT ?
        """, (limit,))
        
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def search_transactions(keyword=None, start_date=None, end_date=None, limit=100):
    """Search transactions based on criteria"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT transaction_id, transaction_date, customer_name, total_amount, payment_method
        FROM transactions
        WHERE 1=1
    """
    params = []
    
    if keyword:
        query += " AND (transaction_id LIKE ? OR customer_name LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if start_date:
        query += " AND transaction_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND transaction_date <= ?"
        params.append(end_date + " 23:59:59")
    
    query += " ORDER BY transaction_date DESC LIMIT ?"
    params.append(limit)
    
    try:
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        return [dict(row) for row in transactions]
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []
    finally:
        conn.close()

def display_transaction_ui():
    """Display transaction UI in Streamlit"""
    st.header("Transaksi Penjualan")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Tambah Produk")
        
        # Search and add products
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, name, price, stock FROM products WHERE stock > 0")
        products = cursor.fetchall()
        conn.close()
        
        if not products:
            st.warning("Tidak ada produk tersedia.")
            return
        
        product_options = {f"{p['name']} (Stok: {p['stock']})": p['product_id'] for p in products}
        selected_product = st.selectbox("Pilih Produk", options=list(product_options.keys()))
        selected_product_id = product_options[selected_product]
        
        # Get selected product details
        product = get_product_by_id(selected_product_id)
        if product:
            st.write(f"Harga: Rp {product['price']:,.0f}")
            quantity = st.number_input("Jumlah", min_value=1, max_value=product['stock'], value=1)
            
            if st.button("Tambah ke Keranjang"):
                if add_to_cart(selected_product_id, quantity):
                    st.success("Produk ditambahkan ke keranjang.")
    
    with col2:
        st.subheader("Ringkasan")
        
        # Display cart
        if 'cart' not in st.session_state or not st.session_state.cart:
            st.info("Keranjang belanja kosong.")
        else:
            total = get_cart_total()
            st.write(f"Total: Rp {total:,.0f}")
            
            # Payment form
            customer_name = st.text_input("Nama Pelanggan", "")
            payment_method = st.selectbox("Metode Pembayaran", ["Tunai", "Debit", "Kredit", "QRIS"])
            payment_amount = st.number_input("Jumlah Pembayaran", min_value=float(total), value=float(total))
            
            if st.button("Proses Transaksi"):
                result = process_transaction(customer_name, payment_method, payment_amount)
                if result:
                    st.success(f"Transaksi berhasil! ID: {result['transaction_id']}")
                    st.write(f"Total: Rp {result['total']:,.0f}")
                    st.write(f"Pembayaran: Rp {result['payment']:,.0f}")
                    st.write(f"Kembalian: Rp {result['change']:,.0f}")
    
    # Display cart contents
    if 'cart' in st.session_state and st.session_state.cart:
        st.subheader("Keranjang Belanja")
        
        for i, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"{item['name']}")
            with col2:
                st.write(f"Rp {item['price']:,.0f}")
            with col3:
                st.write(f"x {item['quantity']}")
            with col4:
                st.write(f"Rp {item['subtotal']:,.0f}")
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button(f"Hapus", key=f"remove_{i}"):
                    remove_from_cart(i)
                    st.experimental_rerun()
        
        if st.button("Bersihkan Keranjang"):
            clear_cart()
            st.experimental_rerun()
