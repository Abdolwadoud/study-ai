from dotenv import load_dotenv
load_dotenv()

import os
import requests
import re
import sqlite3
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash


auth = Blueprint("auth", __name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            is_suspended INTEGER DEFAULT 0
        )
    """)

    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }
    if "is_suspended" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_suspended INTEGER DEFAULT 0"
        )

    # ترحيل آمن لقواعد البيانات القديمة
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(users)").fetchall()
    }

    if "is_admin" not in columns:
        conn.execute(
            "ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0"
        )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    admin_email = os.getenv("STUDY_ADMIN_EMAIL", "").strip().lower()
    if admin_email:
        admin_user = conn.execute(
            "SELECT id FROM users WHERE lower(email) = ?",
            (admin_email,)
        ).fetchone()

        if admin_user:
            conn.execute(
                "UPDATE users SET is_admin = 1 WHERE id = ?",
                (admin_user["id"],)
            )
            print("تم التأكد من صلاحية المسؤول للحساب المحدد.")
        else:
            print("STUDY_ADMIN_EMAIL: لم يُعثر على الحساب المحدد.")

    conn.commit()
    conn.close()


def create_otp():
    return f"{secrets.randbelow(1000000):06d}"


def send_email_otp(email, code):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")

    if not api_key or not from_email:
        print("EMAIL OTP ERROR: Missing Resend configuration")
        return False

    payload = {
        "from": from_email,
        "to": [email],
        "subject": "رمز التحقق - Study AI",
        "text": f"""مرحبًا بك في Study AI.

رمز التحقق الخاص بك هو:

{code}

الرمز صالح لمدة 10 دقائق.

إذا لم تطلب إنشاء هذا الحساب، فتجاهل هذه الرسالة.
"""
    }

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )

        if response.status_code in (200, 201):
            print("EMAIL SENT SUCCESSFULLY TO:", email)
            return True

        print(
            "EMAIL OTP ERROR: Resend HTTP",
            response.status_code,
            response.text[:500]
        )
        return False

    except requests.RequestException as e:
        print("EMAIL OTP ERROR:", type(e).__name__, str(e))
        return False

def send_sms_otp(phone, code):
    return False


def send_otp(user_id, email=None, phone=None):
    code = create_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    conn = get_db()

    conn.execute(
        "DELETE FROM otp_codes WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        """
        INSERT INTO otp_codes
        (user_id, code, expires_at)
        VALUES (?, ?, ?)
        """,
        (user_id, code, expires_at.isoformat())
    )

    conn.commit()
    conn.close()

    if email:
        return send_email_otp(email, code)

    if phone:
        return send_sms_otp(phone, code)

    return False


# =========================
# التسجيل
# =========================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")

    if not email and not phone:
        flash("أدخل البريد الإلكتروني أو رقم الهاتف.")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        flash("كلمة المرور يجب أن تكون 8 أحرف على الأقل.")
        return redirect(url_for("auth.register"))

    if email and not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email
    ):
        flash("البريد الإلكتروني غير صحيح.")
        return redirect(url_for("auth.register"))

    conn = get_db()

    if email:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()
    else:
        existing = conn.execute(
            "SELECT id FROM users WHERE phone = ?",
            (phone,)
        ).fetchone()

    if existing:
        conn.close()
        flash("هذا الحساب موجود بالفعل.")
        return redirect(url_for("auth.login"))

    cursor = conn.execute(
        """
        INSERT INTO users
        (email, phone, password_hash, verified, created_at)
        VALUES (?, ?, ?, 1, ?)
        """,
        (
            email or None,
            phone or None,
            generate_password_hash(password),
            datetime.now(timezone.utc).isoformat()
        )
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    session.pop("verify_user_id", None)
    session["user_id"] = user_id

    return redirect(url_for("home"))


# =========================
# التحقق من OTP
# =========================

@auth.route("/verify", methods=["GET", "POST"])
def verify():

    user_id = session.get("verify_user_id")

    if not user_id:
        return redirect(url_for("auth.register"))

    if request.method == "GET":
        return render_template("verify.html")

    code = request.form.get("code", "").strip()

    conn = get_db()

    otp = conn.execute(
        """
        SELECT *
        FROM otp_codes
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if not otp:
        conn.close()
        flash("رمز التحقق غير موجود.")
        return redirect(url_for("auth.verify"))

    expires_at = datetime.fromisoformat(otp["expires_at"])

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        conn.close()
        flash("انتهت صلاحية الرمز. اطلب رمزًا جديدًا.")
        return redirect(url_for("auth.verify"))

    if not secrets.compare_digest(code, otp["code"]):
        conn.close()
        flash("رمز التحقق غير صحيح.")
        return redirect(url_for("auth.verify"))

    conn.execute(
        "UPDATE users SET verified = 1 WHERE id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM otp_codes WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    session.pop("verify_user_id", None)
    session["user_id"] = user_id

    return redirect(url_for("auth.account"))


# =========================
# تسجيل الدخول
# =========================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    identity = request.form.get("identity", "").strip().lower()
    password = request.form.get("password", "")

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
           OR phone = ?
        """,
        (identity, identity)
    ).fetchone()

    conn.close()

    if not user:
        flash("البريد أو رقم الهاتف غير موجود.")
        return redirect(url_for("auth.login"))

    if user["is_suspended"]:
        flash("هذا الحساب موقوف حاليًا. تواصل مع إدارة الموقع.")
        return redirect(url_for("auth.login"))

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        flash("كلمة المرور غير صحيحة.")
        return redirect(url_for("auth.login"))

    session.pop("verify_user_id", None)
    session["user_id"] = user["id"]

    return redirect(url_for("home"))


# =========================
# الدخول كزائر
# =========================

@auth.route("/guest")
def guest():
    session.clear()
    session["guest"] = True
    return redirect(url_for("home"))


# =========================
# الحساب
# =========================

@auth.route("/account")
def account():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT id, email, phone, verified, is_admin
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    return render_template(
        "account.html",
        user=user
    )


# =========================
# تسجيل الخروج
# =========================

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))


init_db()
