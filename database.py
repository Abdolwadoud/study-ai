import os
import re
import sqlite3
from urllib.parse import urlparse, unquote


class HybridRow:
    """يسمح بقراءة الصف باسم العمود أو برقمه."""

    def __init__(self, columns, values):
        self._columns = [col[0] for col in columns]
        self._values = tuple(values)
        self._mapping = dict(zip(self._columns, self._values))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._mapping[key]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def keys(self):
        return self._columns


class CursorAdapter:
    """يوحّد قراءة نتائج PostgreSQL مع SQLite."""

    def __init__(self, cursor, postgres=False):
        self.cursor = cursor
        self.postgres = postgres

    def _convert(self, row):
        if row is None or not self.postgres:
            return row
        return HybridRow(self.cursor.description, row)

    def fetchone(self):
        return self._convert(self.cursor.fetchone())

    def fetchall(self):
        return [self._convert(row) for row in self.cursor.fetchall()]

    def fetchmany(self, size=None):
        rows = self.cursor.fetchmany() if size is None else self.cursor.fetchmany(size)
        return [self._convert(row) for row in rows]

    def __iter__(self):
        for row in self.cursor:
            yield self._convert(row)

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class DatabaseConnection:
    """واجهة مشتركة لاتصالات SQLite وPostgreSQL."""

    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres

    def execute(self, sql, params=()):
        if not self.postgres:
            return CursorAdapter(self.connection.execute(sql, params))

        # تحويل صيغة إنشاء المفاتيح التلقائية من SQLite إلى PostgreSQL.
        sql = re.sub(
            r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
            "BIGSERIAL PRIMARY KEY",
            sql,
            flags=re.IGNORECASE,
        )

        # تحويل علامات المعاملات من ? إلى %s.
        sql = re.sub(r"\?", "%s", sql)

        cursor = self.connection.cursor()
        cursor.execute(sql, tuple(params))
        return CursorAdapter(cursor, postgres=True)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def get_connection(sqlite_path):
    """
    يستخدم SQLite محليًا إذا لم توجد DATABASE_URL،
    ويستخدم PostgreSQL إذا تم ضبط DATABASE_URL.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        connection = sqlite3.connect(str(sqlite_path))
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return DatabaseConnection(connection)

    parsed = urlparse(database_url)

    if parsed.scheme not in ("postgres", "postgresql"):
        raise ValueError("DATABASE_URL يجب أن يكون رابط PostgreSQL صالحًا.")

    if not parsed.hostname or not parsed.path.strip("/"):
        raise ValueError("رابط DATABASE_URL ينقصه اسم المضيف أو قاعدة البيانات.")

    import pg8000.dbapi

    connection = pg8000.dbapi.connect(
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=unquote(parsed.path.lstrip("/")),
        ssl_context=True,
        timeout=15,
    )

    return DatabaseConnection(connection, postgres=True)
