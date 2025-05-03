from modules.database import get_connection

def init_users():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel user
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # Insert user default jika belum ada
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("kasir", "kasir123", "kasir"))
        conn.commit()
        print("✅ User default dibuat: admin/admin123 dan kasir/kasir123")

    conn.close()

def login():
    username = input("Username: ")
    password = input("Password: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"✅ Login berhasil sebagai {username} ({result[0]})")
        return {"username": username, "role": result[0]}
    else:
        print("❌ Login gagal.")
        return None
