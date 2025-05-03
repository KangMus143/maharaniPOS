import sqlite3
import os
import streamlit as st
import pandas as pd

# Ensure the data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

def get_db_connection():
    """Create a database connection to the SQLite database"""
    conn = sqlite3.connect('data/maharani.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create products table
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
    
    # Create transactions table
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
    
    # Create transaction_items table
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
    """Execute a database query"""
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
    """Execute a query and return the results as a pandas DataFrame"""
    conn = get_db_connection()
    return pd.read_sql_query(query, conn, params=params)

def backup_database():
    """Backup the database to a CSV file"""
    conn = get_db_connection()
    
    # Backup products
    products_df = pd.read_sql_query("SELECT * FROM products", conn)
    products_df.to_csv("data/backup_products.csv", index=False)
    
    # Backup transactions
    transactions_df = pd.read_sql_query("SELECT * FROM transactions", conn)
    transactions_df.to_csv("data/backup_transactions.csv", index=False)
    
    # Backup transaction items
    transaction_items_df = pd.read_sql_query("SELECT * FROM transaction_items", conn)
    transaction_items_df.to_csv("data/backup_transaction_items.csv", index=False)
    
    # Backup users
    users_df = pd.read_sql_query("SELECT id, username, role, created_at FROM users", conn)
    users_df.to_csv("data/backup_users.csv", index=False)
    
    conn.close()
    return True
