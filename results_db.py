
from pathlib import Path
from database import get_connection as get_database_connection

DB_PATH = Path(__file__).with_name("results.db")


def get_connection():
    return get_database_connection(DB_PATH)


def init_db():
    conn = get_connection()
    try:
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
    finally:
        conn.close()


def search_result(candidate_number):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT *
            FROM results
            WHERE candidate_number = ?
            ORDER BY year DESC
            LIMIT 1
        """, (candidate_number,)).fetchone()

        if row is None:
            return None

        return {key: row[key] for key in row.keys()}
    finally:
        conn.close()


init_db()
