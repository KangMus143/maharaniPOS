import os
import sqlite3
import streamlit as st
from contextlib import contextmanager
from typing import Optional, Dict, Any

class DatabaseConnection:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._connection:
            self._initialize_connection()

    def _initialize_connection(self):
        """Initialize database connection"""
        os.makedirs('data', exist_ok=True)
        self._connection = sqlite3.connect('data/pos_database.db', check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with self.get_cursor() as cursor:
            # Create users table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                cashier_id INTEGER NOT NULL,
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

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple = ()) -> Optional[list]:
        """Execute a query and return results"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return None

    def execute_many(self, query: str, params_list: list) -> bool:
        """Execute multiple queries"""
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, params_list)
            return True
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return False

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert data into a table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, list(data.values()))
                return cursor.lastrowid
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return None

    def update(self, table: str, data: Dict[str, Any], condition: str, params: tuple) -> bool:
        """Update data in a table"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        all_params = tuple(data.values()) + params
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, all_params)
            return True
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return False

    def delete(self, table: str, condition: str, params: tuple) -> bool:
        """Delete data from a table"""
        query = f"DELETE FROM {table} WHERE {condition}"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
            return True
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            return False

def get_db_connection():
    """Get database connection singleton"""
    return DatabaseConnection()

def init_database():
    """Initialize the database"""
    db = get_db_connection()
    st.sidebar.success("Connected to local SQLite database")