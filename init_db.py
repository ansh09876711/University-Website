import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# ATTENDANCE
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject TEXT,
    attended INTEGER,
    total INTEGER
)
""")

# RESULTS
cur.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    subject TEXT,
    marks INTEGER
)
""")

# DUMMY USERS
cur.execute(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
    ("student1", generate_password_hash("123"), "student")
)

cur.execute(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
    ("teacher1", generate_password_hash("123"), "teacher")
)

cur.execute(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
    ("admin1", generate_password_hash("123"), "admin")
)

conn.commit()
conn.close()

print("✅ Database Ready")
