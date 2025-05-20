import os
import sqlite3
import streamlit as st
from supabase import create_client, Client

def get_db_connection():
    """
    Get database connection - returns either Supabase or SQLite connection
    based on environment
    """
    # Try to use Supabase if environment variables are available
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if supabase_url and supabase_key:
        # Return Supabase client for production
        return create_supabase_client()
    else:
        # Use SQLite for local development/fallback
        return create_sqlite_connection()

def create_supabase_client() -> Client:
    """Create and return a Supabase client"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    # Create Supabase client
    return create_client(supabase_url, supabase_key)

def create_sqlite_connection():
    """Create and return a SQLite connection"""
    # Create database directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('data/pos_database.db')
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    
    # Create tables if they don't exist
    init_sqlite_database(conn)
    
    return conn

def init_sqlite_database(conn):
    """Initialize SQLite database with required tables"""
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'cashier')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL CHECK (price >= 0),
        stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
        category TEXT NOT NULL,
        description TEXT,
        barcode TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        total_amount REAL NOT NULL CHECK (total_amount >= 0),
        payment_amount REAL NOT NULL CHECK (payment_amount >= 0),
        payment_method TEXT NOT NULL,
        cashier_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cashier_id) REFERENCES users (id)
    )
    ''')
    
    # Create transaction_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        price_per_unit REAL NOT NULL CHECK (price_per_unit >= 0),
        subtotal REAL NOT NULL CHECK (subtotal >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transactions (invoice_number),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    conn.commit()

def init_database():
    """Initialize the database (either Supabase or SQLite)"""
    # First check if we can use Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if supabase_url and supabase_key:
        # Using Supabase - the migrations will handle table creation
        st.sidebar.success("Connected to Supabase database!")
    else:
        # Using SQLite - initialize the database
        conn = create_sqlite_connection()
        conn.close()
        st.sidebar.info("Using local SQLite database (development mode)")
