import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("countdown.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    # إنشاء النظام الجديد إذا لم يكن موجودًا
    conn.execute("""
        CREATE TABLE IF NOT EXISTS countdowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_datetime TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ترحيل الإعلان القديم إن كان موجودًا
    old_table = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='countdown'
    """).fetchone()

    if old_table:
        old = conn.execute("""
            SELECT title, target_datetime
            FROM countdown
            WHERE id = 1
        """).fetchone()

        if old and old["title"] and old["target_datetime"]:
            exists = conn.execute("""
                SELECT id FROM countdowns
                WHERE title = ? AND target_datetime = ?
            """, (old["title"], old["target_datetime"])).fetchone()

            if not exists:
                conn.execute("""
                    INSERT INTO countdowns (title, target_datetime)
                    VALUES (?, ?)
                """, (old["title"], old["target_datetime"]))

        conn.execute("DROP TABLE countdown")

    conn.commit()
    conn.close()


def get_countdowns():
    conn = get_connection()

    rows = conn.execute("""
        SELECT id, title, target_datetime, created_at
        FROM countdowns
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def add_countdown(title, target_datetime):
    conn = get_connection()

    conn.execute("""
        INSERT INTO countdowns (title, target_datetime)
        VALUES (?, ?)
    """, (title, target_datetime))

    conn.commit()
    conn.close()


def delete_countdown(countdown_id):
    conn = get_connection()

    conn.execute("""
        DELETE FROM countdowns
        WHERE id = ?
    """, (countdown_id,))

    conn.commit()
    conn.close()


def get_active_countdowns():
    return get_countdowns()


init_db()
