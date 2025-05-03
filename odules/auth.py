import streamlit as st
import hashlib
import sqlite3
from .database import get_db_connection

def make_hash(password):
    """Create a SHA256 hash of the password"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user_table():
    """Create user table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def create_default_user():
    """Create default admin user if no users exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_username = "admin"
        default_password = "admin123"
        hashed_password = make_hash(default_password)
        
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (default_username, hashed_password, "admin")
        )
        conn.commit()
    
    conn.close()

def login(username, password):
    """Verify login credentials"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = make_hash(password)
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {"id": user[0], "username": user[1], "role": user[2]}
    return None

def add_user(username, password, role):
    """Add a new user to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        hashed_password = make_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        success = True
        message = f"User {username} added successfully"
    except sqlite3.IntegrityError:
        success = False
        message = f"Username {username} already exists"
    except Exception as e:
        success = False
        message = f"Error: {str(e)}"
    
    conn.close()
    return success, message

def get_users():
    """Get all users from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, role, created_at FROM users")
    users = cursor.fetchall()
    conn.close()
    
    return users

def delete_user(user_id):
    """Delete a user from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def change_password(user_id, new_password):
    """Change a user's password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = make_hash(new_password)
    cursor.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (hashed_password, user_id)
    )
    conn.commit()
    conn.close()

def init_auth():
    """Initialize authentication"""
    create_user_table()
    create_default_user()

def login_form():
    """Display the login form"""
    st.title("POS Maharani - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
                
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.session_state.authenticated = True
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
                return True
            else:
                st.error("Invalid username or password")
                return False
    
    return False

def user_management():
    """User management interface"""
    if not st.session_state.get("authenticated", False) or st.session_state.user["role"] != "admin":
        st.warning("Unauthorized access")
        return
    
    st.subheader("User Management")
    
    # Add new user
    with st.expander("Add New User"):
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "cashier"])
            
            submitted = st.form_submit_button("Add User")
            if submitted:
                if not new_username or not new_password:
                    st.error("Please fill all fields")
                else:
                    success, message = add_user(new_username, new_password, new_role)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # List users
    st.subheader("User List")
    users = get_users()
    
    for user in users:
        user_id, username, role, created_at = user
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{username}** ({role})")
        
        with col2:
            if st.button("Reset Password", key=f"reset_{user_id}"):
                new_pass = "password123"
                change_password(user_id, new_pass)
                st.info(f"Password reset to: {new_pass}")
        
        with col3:
            if username != "admin" and st.button("Delete", key=f"delete_{user_id}"):
                delete_user(user_id)
                st.success(f"User {username} deleted")
                st.experimental_rerun()
        
        st.divider()

def logout():
    """Log out the current user"""
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.experimental_rerun()
