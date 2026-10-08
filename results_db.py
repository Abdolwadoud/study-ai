import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("results.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_number TEXT NOT NULL,
            competition TEXT NOT NULL,
            year TEXT NOT NULL,
            candidate_name TEXT,
            result TEXT,
            average TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def search_result(candidate_number):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM results
        WHERE candidate_number = ?
        ORDER BY year DESC
        LIMIT 1
    """, (candidate_number,)).fetchone()

    conn.close()

    return dict(row) if row else None


init_db()
