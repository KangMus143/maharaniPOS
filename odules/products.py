import streamlit as st
import pandas as pd
import sqlite3
from .database import get_db_connection, execute_query, get_dataframe_from_query

def add_product(name, category, price, stock):
    """Add a new product to the database"""
    query = '''
    INSERT INTO products (name, category, price, stock)
    VALUES (?, ?, ?, ?)
    '''
    
    try:
        execute_query(query, (name, category, price, stock))
        return True, f"Product '{name}' added successfully"
    except sqlite3.IntegrityError:
        return False, f"Product '{name}' already exists"
    except Exception as e:
        return False, f"Error: {str(e)}"

def update_product(product_id, name, category, price, stock):
    """Update an existing product"""
    query = '''
    UPDATE products
    SET name = ?, category = ?, price = ?, stock = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        execute_query(query, (name, category, price, stock, product_id))
        return True, f"Product '{name}' updated successfully"
    except Exception as e:
        return False, f"Error: {str(e)}"

def delete_product(product_id):
    """Delete a product from the database"""
    # Check if the product is used in any transaction
    check_query = '''
    SELECT COUNT(*) as count FROM transaction_items WHERE product_id = ?
    '''
    result = execute_query(check_query, (product_id,), fetchall=False)
    
    if result and result[0] > 0:
        return False, "Cannot delete product because it is referenced in transactions"
    
    # Delete the product
    query = "DELETE FROM products WHERE id = ?"
    try:
        execute_query(query, (product_id,))
        return True, "Product deleted successfully"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_product(product_id):
    """Get a single product by ID"""
    query = "SELECT * FROM products WHERE id = ?"
    result = execute_query(query, (product_id,), fetchall=False)
    return result

def get_products(search_term="", category=""):
    """Get all products with optional filtering"""
    query = "SELECT * FROM products"
    params = []
    
    conditions = []
    if search_term:
        conditions.append("name LIKE ?")
        params.append(f"%{search_term}%")
    
    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY category, name"
    
    return get_dataframe_from_query(query, params)

def get_product_categories():
    """Get all product categories"""
    query = "SELECT DISTINCT category FROM products ORDER BY category"
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    categories = df['category'].tolist()
    return categories

def update_stock(product_id, quantity_change):
    """Update product stock (add or subtract)"""
    query = '''
    UPDATE products
    SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    
    try:
        execute_query(query, (quantity_change, product_id))
        return True, "Stock updated successfully"
    except Exception as e:
        return False, f"Error: {str(e)}"

def product_management():
    """Product management interface"""
    st.subheader("Product Management")
    
    tab1, tab2 = st.tabs(["Product List", "Add Product"])
    
    # Tab 1: Product List
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("Search Products", key="product_search")
        
        with col2:
            categories = ["All"] + get_product_categories()
            category_filter = st.selectbox("Category", categories, key="category_filter")
        
        # Get products with filters
        products_df = get_products(search_term, category_filter)
        
        if products_df.empty:
            st.info("No products found")
        else:
            for index, product in products_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{product['name']}**")
                    st.write(f"Category: {product['category']}")
                
                with col2:
                    st.write(f"Price: Rp {product['price']:,.0f}")
                    st.write(f"Stock: {product['stock']}")
                
                with col3:
                    if st.button("Edit", key=f"edit_{product['id']}"):
                        st.session_state.editing_product = product['id']
                        st.experimental_rerun()
                    
                    if st.button("Delete", key=f"delete_{product['id']}"):
                        success, message = delete_product(product['id'])
                        if success:
                            st.success(message)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                
                # Show edit form if this product is being edited
                if st.session_state.get("editing_product") == product['id']:
                    with st.form(key=f"edit_product_form_{product['id']}"):
                        st.subheader(f"Edit Product: {product['name']}")
                        
                        name = st.text_input("Product Name", value=product['name'])
                        
                        # If categories exist, use them for a dropdown, otherwise free text
                        categories = get_product_categories()
                        if categories and product['category'] in categories:
                            category = st.selectbox("Category", categories, 
                                                   index=categories.index(product['category']))
                        else:
                            category = st.text_input("Category", value=product['category'])
                            
                        price = st.number_input("Price (Rp)", 
                                              min_value=0.0, 
                                              value=float(product['price']),
                                              step=1000.0)
                        
                        stock = st.number_input("Stock", 
                                              min_value=0, 
                                              value=int(product['stock']))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            submit = st.form_submit_button("Update")
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_product = None
                                st.experimental_rerun()
                        
                        if submit:
                            success, message = update_product(
                                product['id'], name, category, price, stock
                            )
                            if success:
                                st.success(message)
                                st.session_state.editing_product = None
                                st.experimental_rerun()
                            else:
                                st.error(message)
                
                st.divider()
    
    # Tab 2: Add Product
    with tab2:
        with st.form(key='add_product_form'):
            st.subheader("Add New Product")
            
            name = st.text_input("Product Name")
            
            # If categories exist, use them for a dropdown with "New Category" option, otherwise free text
            categories = get_product_categories()
            if categories:
                category_option = st.selectbox(
                    "Category", 
                    categories + ["New Category"],
                    index=len(categories) if categories else 0
                )
                
                if category_option == "New Category":
                    category = st.text_input("New Category Name")
                else:
                    category = category_option
            else:
                category = st.text_input("Category")
                
            price = st.number_input("Price (Rp)", min_value=0.0, value=0.0, step=1000.0)
            stock = st.number_input("Initial Stock", min_value=0, value=0)
            
            submit = st.form_submit_button("Add Product")
            
            if submit:
                if not name or not category:
                    st.error("Please fill in all required fields")
                else:
                    success, message = add_product(name, category, price, stock)
                    if success:
                        st.success(message)
                        # Clear form fields
                        st.experimental_rerun()
                    else:
                        st.error(message)

def get_low_stock_products(threshold=10):
    """Get products with stock below the threshold"""
    query = "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC"
    return get_dataframe_from_query(query, (threshold,))
