import sqlite3

def init_db():

    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        course TEXT,
        total_fee INTEGER,
        paid_fee INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount INTEGER,
        date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarships(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()