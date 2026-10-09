
from pathlib import Path
from database import get_connection as get_database_connection

DB_PATH = Path(__file__).with_name("countdown.db")


def get_connection():
    return get_database_connection(DB_PATH)


def init_db():
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS countdowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target_datetime TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ترحيل الجدول القديم في SQLite المحلي فقط.
        # لا نحذف أي جدول قديم في PostgreSQL تلقائيًا.
        if not conn.postgres:
            old_table = conn.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'countdown'
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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_countdowns():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT id, title, target_datetime, created_at
            FROM countdowns
            ORDER BY id DESC
        """).fetchall()

        return [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
    finally:
        conn.close()


def add_countdown(title, target_datetime):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO countdowns (title, target_datetime)
            VALUES (?, ?)
        """, (title, target_datetime))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_countdown(countdown_id):
    conn = get_connection()
    try:
        conn.execute("""
            DELETE FROM countdowns
            WHERE id = ?
        """, (countdown_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_active_countdowns():
    return get_countdowns()


init_db()
