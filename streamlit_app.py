import streamlit as st
import pandas as pd
import os
from odules.auth import init_auth, login_form, user_management, logout
from odules.database import init_database
from odules.products import product_management, get_low_stock_products
from odules.transactions import pos_interface, transaction_history, show_receipt
from odules.reports import reports_dashboard

# Page configuration
st.set_page_config(
    page_title="POS Maharani",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and authentication
init_database()
init_auth()

# Check authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# App layout
if not st.session_state.authenticated:
    login_form()
else:
    # Sidebar - navigation
    st.sidebar.title("POS Maharani")
    st.sidebar.image("https://img.freepik.com/free-vector/gradient-pos-logo-template_23-2149284672.jpg", width=200)
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Point of Sale", "Products", "Transactions", "Reports", "User Management"]
    )
    
    # Content based on selected page
    if page == "Point of Sale":
        # Show receipt if there's a transaction ID in session state, else the POS interface
        if st.session_state.get("show_receipt"):
            show_receipt(st.session_state.show_receipt)
        else:
            pos_interface()
    
    elif page == "Products":
        product_management()
    
    elif page == "Transactions":
        # Show receipt if there's a transaction ID in session state, else the transaction history
        if st.session_state.get("show_receipt"):
            show_receipt(st.session_state.show_receipt)
        else:
            transaction_history()
    
    elif page == "Reports":
        reports_dashboard()
    
    elif page == "User Management":
        if st.session_state.user.get("role") == "admin":
            user_management()
        else:
            st.warning("You don't have permission to access User Management")
    
    # Logout button
    logout()

    # Optional - Show low stock alert to admin users
    if st.session_state.user.get("role") == "admin":
        # Get low stock products
        low_stock_df = get_low_stock_products(threshold=10)
        
        if not low_stock_df.empty:
            with st.sidebar.expander("⚠️ Low Stock Alert"):
                st.warning(f"{len(low_stock_df)} products are low on stock!")
                
                for index, product in low_stock_df.iterrows():
                    st.write(f"**{product['name']}**: {product['stock']} left")
