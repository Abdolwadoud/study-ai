from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
import re
import requests
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import html as html_lib
from auth import auth
app = Flask(__name__)

app.secret_key = os.environ.get(
    "STUDY_AI_SECRET_KEY",
    "change-this-secret-key"
)

app.register_blueprint(auth)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_FOLDER = os.path.join(BASE_DIR, "books")
TEXT_FOLDER = os.path.join(BASE_DIR, "book_texts")
PAST_PAPERS_FOLDER = os.path.join(BASE_DIR, "past_papers")

os.makedirs(BOOKS_FOLDER, exist_ok=True)


chat_memory = {}


# =========================
# الصفحات
# =========================

@app.route("/")
def home():
    from auth import get_db
    from datetime import datetime, timezone

    visitor_key = session.get("user_id")
    if visitor_key is None:
        visitor_key = session.get("visitor_id")
        if visitor_key is None:
            import secrets
            visitor_key = secrets.token_urlsafe(24)
            session["visitor_id"] = visitor_key
    else:
        visitor_key = f"user:{visitor_key}"

    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS site_activity (
            visitor_key TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO site_activity (visitor_key, last_seen)
        VALUES (?, ?)
        ON CONFLICT(visitor_key)
        DO UPDATE SET last_seen = excluded.last_seen
    """, (str(visitor_key), now))
    conn.commit()
    conn.close()

    return render_template("index.html")


@app.route("/api/online-count")
def online_count():
    from auth import get_db
    from datetime import datetime, timedelta, timezone

    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS site_activity (
            visitor_key TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL
        )
    """)
    count = conn.execute(
        "SELECT COUNT(*) FROM site_activity WHERE last_seen >= ?",
        (cutoff,)
    ).fetchone()[0]
    conn.close()
    return jsonify({"online": count})


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/past-papers")
def past_papers():
    years = []

    if os.path.isdir(PAST_PAPERS_FOLDER):
        for year in sorted(os.listdir(PAST_PAPERS_FOLDER), reverse=True):
            year_path = os.path.join(PAST_PAPERS_FOLDER, year)

            if not os.path.isdir(year_path):
                continue

            files = []

            for filename in sorted(os.listdir(year_path)):
                if filename.lower().endswith(".pdf"):
                    files.append({
                        "name": filename,
                        "year": year
                    })

            if files:
                years.append({
                    "name": year,
                    "files": files
                })

    return render_template(
        "past_papers.html",
        years=years
    )


@app.route("/past-papers/<year>/<filename>")
def open_past_paper(year, filename):
    year_path = os.path.join(
        PAST_PAPERS_FOLDER,
        year
    )

    return send_from_directory(year_path, filename)


@app.route("/competitions")
def competitions():
    return render_template("competitions.html")

@app.route("/lessons")
def lessons():
    categories = []

    # =========================
    # الابتدائي
    # =========================
    primary_books = []

    for filename in sorted(os.listdir(BOOKS_FOLDER)) if os.path.isdir(BOOKS_FOLDER) else []:
        file_path = os.path.join(BOOKS_FOLDER, filename)

        if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
            primary_books.append({
                "name": filename,
                "path": filename
            })

    if primary_books:
        categories.append({
            "name": "الابتدائي",
            "years": [{
                "name": "كتب المرحلة الابتدائية",
                "books": primary_books
            }]
        })

    # =========================
    # الإعدادي والثانوي
    # =========================
    for level in ["الإعدادي", "الثانوي"]:
        level_path = os.path.join(BOOKS_FOLDER, level)

        if not os.path.isdir(level_path):
            continue

        years = []

        for year in sorted(os.listdir(level_path)):
            year_path = os.path.join(level_path, year)

            if not os.path.isdir(year_path):
                continue

            books = []

            for filename in sorted(os.listdir(year_path)):
                if filename.lower().endswith(".pdf"):
                    books.append({
                        "name": filename,
                        "path": os.path.join(
                            level,
                            year,
                            filename
                        )
                    })

            if books:
                years.append({
                    "name": year,
                    "books": books
                })

        if years:
            categories.append({
                "name": level,
                "years": years
            })

    return render_template(
        "lessons.html",
        categories=categories
    )
@app.route("/books/<path:filename>")
def open_book(filename):
    return send_from_directory(BOOKS_FOLDER, filename)


def quizzes():
    return render_template("quizzes.html")
@app.route("/quizzes")
def quizzes():
    return render_template("quizzes.html")


@app.route("/api/quiz/question")
def quiz_question():
    from ai_engine import generate_quiz_question

    subject = request.args.get("subject", "").strip()
    stage = request.args.get("stage", "").strip()
    level = request.args.get("level", "").strip()
    term = request.args.get("term", "").strip()

    if not subject:
        return jsonify({
            "success": False,
            "error": "لم يتم تحديد المادة"
        }), 400

    question = generate_quiz_question(
        subject,
        stage=stage,
        level=level,
        term=term
    )

    if not question:
        return jsonify({
            "success": False,
            "error": "لم أجد كتابًا أو أسئلة مناسبة لهذه المرحلة والسنة والمادة"
        }), 404

    return jsonify({
        "success": True,
        "question": question
    })

@app.route("/flashcards")
def flashcards():
    return render_template("flashcards.html")


@app.route("/summarize")
def summarize():
    return render_template("summarize.html")


@app.route("/progress")
def progress():
    return render_template("progress.html")


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    return render_template("search.html", query=query)


@app.route("/settings")
def settings():
    return render_template("settings.html")


# =========================
# قراءة الكتب
# =========================

def load_books():
    books = {}

    if not os.path.isdir(TEXT_FOLDER):
        return books

    # قراءة ملفات TXT من المجلد الرئيسي وجميع المجلدات الفرعية
    for root, dirs, filenames in os.walk(TEXT_FOLDER):
        for filename in filenames:
            if not filename.lower().endswith(".txt"):
                continue

            path = os.path.join(root, filename)
            relative_path = os.path.relpath(path, TEXT_FOLDER)

            try:
                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:
                    text = file.read()

                if text.strip():
                    books[relative_path] = text

            except Exception as error:
                print("خطأ في قراءة:", path)
                print(error)

    print(f"📚 عدد الكتب النصية المحمّلة: {len(books)}")
    return books


# =========================
# تنظيف النص
# =========================

def clean_text(text):

    text = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\ufeff]",
        "",
        text
    )

    text = text.replace("�", "")

    text = re.sub(r"\bIP\b", " ", text)
    text = re.sub(r"\bN\b", " ", text)

    text = text.replace("التـلميذ", "التلميذ")
    text = text.replace("التعـليم", "التعليم")
    text = text.replace("التـاريخ", "التاريخ")
    text = text.replace("التـربوي", "التربوي")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# =========================
# توحيد العربية
# =========================

def normalize_arabic(text):

    text = text.lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

        text = text.replace(old, new)

    text = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        text
    )

    return text


# =========================
# ذاكرة المحادثة
# =========================

def get_session_id(request):

    return request.headers.get(
        "X-Study-Session",
        "default"
    )


def remember(session_id, question, answer):

    if session_id not in chat_memory:
        chat_memory[session_id] = []

    chat_memory[session_id].append({
        "question": question,
        "answer": answer
    })

    chat_memory[session_id] = \
        chat_memory[session_id][-10:]


# =========================
# المحادثة الطبيعية
# =========================

def conversation_reply(question):

    q = normalize_arabic(question).strip()

    greetings = [
        "مرحبا",
        "السلام عليكم",
        "اهلا",
        "اهلا بك",
        "صباح الخير",
        "مساء الخير",
        "hello"
    ]

    thanks = [
        "شكرا",
        "شكرا لك",
        "بارك الله فيك",
        "ممتاز",
        "رائع"
    ]

    if any(word in q for word in greetings):

        return (
            "وعليكم السلام ورحمة الله وبركاته 🌟\n\n"
            "أهلًا بك في Study AI 👋\n"
            "أنا مساعدك الدراسي.\n"
            "يمكنني مساعدتك في فهم الدروس "
            "والبحث داخل كتبك والتدرب عليها. 📚"
        )

    if any(word in q for word in thanks):

        return (
            "العفو! 😊\n"
            "أنا سعيد بمساعدتك في دراستك.\n"
            "اسألني أي سؤال عندما تريد 📚"
        )

    if q in [
        "من انت",
        "ما اسمك",
        "من هو study ai"
    ]:

        return (
            "أنا Study AI 🤖📚\n\n"
            "مساعدك الدراسي.\n"
            "أبحث في كتبك المدرسية وأساعدك "
            "على فهم الدروس والمراجعة والتدرب."
        )

    if "ماذا تستطيع" in q or "ماذا يمكنك" in q:

        return (
            "أستطيع مساعدتك في:\n\n"
            "📚 البحث في الكتب\n"
            "🧠 شرح الدروس\n"
            "❓ الإجابة عن الأسئلة\n"
            "📝 التدريب والمراجعة\n"
            "🎯 تصحيح الأخطاء"
        )

    return None


# =========================
# فهم نوع السؤال
# =========================

def detect_question_type(question):

    q = normalize_arabic(question)

    # سؤال الاستقلال
    if (
        "استقلت موريتانيا" in q
        or "استقلال موريتانيا" in q
        or "نالت موريتانيا استقلال" in q
        or "استقلت" in q and "موريتانيا" in q
    ):
        return "independence"

    # سؤال المستعمر
    if (
        "من استعمر موريتانيا" in q
        or "من استعمرها" in q
        or "من احتل موريتانيا" in q
        or "من احتلها" in q
        or "المستعمر" in q
        or "المحتل" in q
    ):
        return "colonizer"

    # بداية الاحتلال
    if (
        "متى بدا الاحتلال" in q
        or "متى بدأ الاحتلال" in q
        or "متى بدا الاستعمار" in q
        or "متى بدأ الاستعمار" in q
    ):
        return "occupation_start"

    # دوافع الاستعمار
    if (
        "دوافع الاستعمار" in q
        or "سبب الاستعمار" in q
        or "لماذا استعمرت" in q
        or "لماذا احتلت" in q
    ):
        return "colonization_reasons"

   # المقاومة
    # سؤال بداية الاحتلال
    if (
        "متى بدا الاحتلال" in q
        or "متى بدا الاستعمار" in q
        or "بدا الاحتلال" in q
        or "بدا الاستعمار" in q
    ):
        return "occupation_start"  

    if (
        "مقاومه الاستعمار" in q
        or "مقاومة الاستعمار" in q
        or "قاوم" in q
        or "المقاومه" in q
        or "المقاومة" in q
    ):
        return "resistance"

    return "general"


# =========================
# تحديد المادة
# =========================

def detect_subject(question):

    q = normalize_arabic(question)

    subjects = {

        "arabic": [
            "اللغه العربيه",
            "عربي",
            "نحو",
            "قواعد",
            "املاء",
            "صرف",
            "قراءه",
            "ادب"
        ],

        "math": [
            "رياضيات",
            "حساب",
            "جمع",
            "طرح",
            "ضرب",
            "قسمه",
            "معادله",
            "هندسه",
            "مساحه",
            "محيط",
            "كسر"
        ],

        "french": [
            "فرنسيه",
            "الفرنسيه",
            "francais",
            "français"
        ],

        "history": [
            "تاريخ",
            "استقلال",
            "استقلت",
            "استعمار",
            "احتلال",
            "الحرب",
            "الفتح",
            "اسلام",
            "موريتانيا",
            "مقاومه",
            "مقاومة"
        ],

        "geography": [
            "جغرافيا",
            "المناخ",
            "القاره",
            "القارات",
            "السكان",
            "الخريطه",
            "الموقع الجغرافي"
        ],

        "science": [
            "علوم",
            "علم",
            "جسم الانسان",
            "النبات",
            "الحيوان",
            "الطاقه",
            "الماء",
            "البيئه",
            "الكهرباء"
        ]
    }

    for subject, words in subjects.items():

        if any(word in q for word in words):
            return subject

    return None


# =========================
# اختيار الكتب
# =========================

def get_subject_prefixes(subject):

    subjects = {

        "arabic": [
            "AR-",
            "MART05",
            "Manuel_Arabe",
            "Cahier_Arabe"
        ],

        "math": [
            "MA-",
            "MATHE-",
            "Math_"
        ],

        "french": [
            "FR-",
            "MART08"
        ],

        "history": [
            "HIST-"
        ],

        "geography": [
            "GEO-"
        ],

        "science": [
            "SN-",
            "IC"
        ]
    }

    return subjects.get(subject, [])


def select_books(books, subject):

    prefixes = get_subject_prefixes(subject)

    if not prefixes:
        return books

    selected = {}

    for filename, text in books.items():

        if any(
            filename.startswith(prefix)
            for prefix in prefixes
        ):
            selected[filename] = text

    return selected


# =========================
# كلمات البحث
# =========================

STOP_WORDS = {
    "ما",
    "ماذا",
    "ماهي",
    "ماهو",
    "هي",
    "هو",
    "من",
    "في",
    "على",
    "عن",
    "الى",
    "إلى",
    "هل",
    "كيف",
    "لماذا",
    "متى",
    "اين",
    "أين",
    "و",
    "او",
    "أو",
    "يا",
    "ان",
    "أن",
    "انا",
    "أنا",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "كان",
    "كانت"
}


def get_keywords(question):

    question = normalize_arabic(question)

    words = re.findall(
        r"[\u0600-\u06FFa-zA-Z0-9]+",
        question
    )

    keywords = []

    for word in words:

        if len(word) < 3:
            continue

        if word in STOP_WORDS:
            continue

        keywords.append(word)

        if word.startswith("ال") and len(word) > 4:
            keywords.append(word[2:])

    return list(dict.fromkeys(keywords))


# =========================
# تقسيم النص
# =========================

def make_chunks(text):

    text = clean_text(text)

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    chunks = []

    for paragraph in paragraphs:

        paragraph = clean_text(paragraph)

        if len(paragraph) < 30:
            continue

        words = paragraph.split()

        if len(words) > 120:

            for i in range(
                0,
                len(words),
                60
            ):

                part = " ".join(
                    words[i:i + 60]
                )

                if len(part) >= 30:
                    chunks.append(part)

        else:

            chunks.append(paragraph)

    return chunks


# =========================
# تقييم النتيجة
# =========================

def calculate_score(question, chunk):

    q = normalize_arabic(question)
    c = normalize_arabic(chunk)

    question_type = detect_question_type(q)

    score = 0

    # الكلمات العامة
    for word in get_keywords(question):

        if word in c:
            score += 3

    # =====================
    # الاستقلال
    # =====================

    if question_type == "independence":

        if "1960" in c:
            score += 200

        if "28 نوفمبر" in c:
            score += 150

        if "استقلال" in c:
            score += 80

        if "فرنسا" in c:
            score += 50

    # =====================
    # المستعمر
    # =====================

    elif question_type == "colonizer":

        if "الاحتلال الفرنسي" in c:
            score += 200

        if "الاستعمار الفرنسي" in c:
            score += 200

        if "فرنسا" in c:
            score += 100

        if "الفرنسي" in c:
            score += 70

        if "موريتانيا" in c:
            score += 30

        # نفضل الفقرات التي تجيب مباشرة
        if "دخل الاستعمار" in c:
            score += 80

        if "دخول الاستعمار" in c:
            score += 80

    # =====================
    # بداية الاحتلال
    # =====================

    elif question_type == "occupation_start":

        if "بدأ الاحتلال الفرنسي" in c:
            score += 200

        if "بداية الاحتلال" in c:
            score += 120

        if "الاحتلال الفرنسي" in c:
            score += 100

        if "موريتانيا" in c:
            score += 30

    # =====================
    # دوافع الاستعمار
    # =====================

    elif question_type == "colonization_reasons":

        if "دوافع الاستعمار" in c:
            score += 220

        if "الاستعمار الفرنسي" in c:
            score += 100

        if "فرنسا" in c:
            score += 60

    # =====================
    # المقاومة
    # =====================

    elif question_type == "resistance":

        if "مقاومة الاستعمار" in c:
            score += 200

        if "المقاومة" in c:
            score += 100

        if "الاستعمار الفرنسي" in c:
            score += 80

    return score


# =========================
# استخراج إجابة حسب نوع السؤال
# =========================

def make_answer(question, text):

    clean = clean_text(text)

    question_type = detect_question_type(
        question
    )

    normalized = normalize_arabic(clean)

    # =====================
    # الاستقلال
    # =====================

    if question_type == "independence":
        return (
            "🇲🇷 حصلت موريتانيا على استقلالها "
            "عن فرنسا في 28 نوفمبر 1960م."
            "\n📖 المصدر: HIST-6AF-M.txt"
        )

    # =====================
    # المستعمر
    # =====================

    if question_type == "colonizer":
        return (
            "🇲🇷 استعمرت فرنسا موريتانيا، "
            "وبدأ الاحتلال الفعلي سنة 1902م."
            "\n📖 المصدر: HIST-6AF-M.txt"
        )

    # =====================
    # بداية الاحتلال
    # =====================

    if question_type == "occupation_start":
        return (
            "🇲🇷 بدأ الاحتلال الفعلي لموريتانيا "
            "سنة 1902م انطلاقًا من نهر السنغال."
            "\n📖 المصدر: HIST-6AF-M.txt"
        )

    # =====================
    # دوافع الاستعمار
    # =====================

    if question_type == "colonization_reasons":
        return (
            "🇲🇷 من دوافع الاستعمار الفرنسي لموريتانيا:\n"
            "• الربط بين مستعمراتها في شمال وغرب إفريقيا.\n"
            "• استغلال الثروات والمواد الأولية والبحث عن الأسواق.\n"
            "• نشر الثقافة والقيم الفرنسية."
            "\n📖 المصدر: HIST-6AF-M.txt"
        )

    # =====================
    # الإجابة العامة
    # =====================

    if len(clean) <= 450:
        return clean
    question_type = detect_question_type(
        question
    )

    normalized = normalize_arabic(clean)

    # =====================
    # الاستقلال
    # =====================

    if question_type == "independence":

        match = re.search(
            r".{0,100}28\s*نوفمب.{0,220}",
            clean
        )

        if match:

            return (
                "🇲🇷 حصلت موريتانيا على "
                "استقلالها عن فرنسا في "
                + match.group(0).strip()
            )

        if "1960" in clean:

            return (
                "🇲🇷 حصلت موريتانيا على "
                "استقلالها عن فرنسا سنة 1960م."
            )

    # =====================
    # المستعمر
    # =====================

    if question_type == "colonizer":

        if (
            "الاحتلال الفرنسي" in normalized
            or "الاستعمار الفرنسي" in normalized
        ):

            return (
                "🇲🇷 استعمرت فرنسا موريتانيا، "
                "وكان الاحتلال الفرنسي لموريتانيا "
                "جزءًا من التوسع الاستعماري الفرنسي "
                "في المنطقة."
            )

        if "فرنسا" in clean:

            return (
                "🇲🇷 المستعمر هو فرنسا."
            )

    # =====================
    # الإجابة العامة
    # =====================

    if len(clean) <= 450:
        return clean

    sentences = re.split(
        r"(?<=[.!؟])\s+",
        clean
    )

    keywords = get_keywords(question)

    useful = []

    for sentence in sentences:

        ns = normalize_arabic(sentence)

        matches = sum(
            1
            for word in keywords
            if word in ns
        )

        if matches:
            useful.append(
                (matches, sentence)
            )

    useful.sort(
        key=lambda item: item[0],
        reverse=True
    )

    if useful:

        return " ".join(
            item[1]
            for item in useful[:2]
        )

    return clean[:450] + "..."


# =========================
# تحسين السؤال التابع
# =========================

def improve_followup(question, session_id):

    q = normalize_arabic(question)

    history = chat_memory.get(
        session_id,
        []
    )

    if not history:
        return question

    last_question = normalize_arabic(
        history[-1]["question"]
    )

    # من استعمرها؟
    if (
        ("استعمر" in q or "احتل" in q)
        and "موريتانيا" not in q
        and "موريتانيا" in last_question
    ):

        return question + " موريتانيا"

    # متى بدأ؟
    if (
        ("بدا" in q or "بدأ" in q)
        and "موريتانيا" not in q
        and "موريتانيا" in last_question
    ):

        return question + " موريتانيا"

    return question


# =========================
# البحث
# =========================

def search_books(question, books):

    subject = detect_subject(question)

    selected_books = select_books(
        books,
        subject
    )

    if not selected_books:
        selected_books = books

    results = []

    for filename, text in selected_books.items():

        for chunk in make_chunks(text):

            score = calculate_score(
                question,
                chunk
            )

            if score > 0:

                results.append({
                    "score": score,
                    "book": filename,
                    "text": chunk
                })

    if not results:
        return None

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    # لا نقبل مقطعًا ضعيف المطابقة
    if results[0]["score"] < 10:
        return None

    return results[0]



# =========================
# البحث الاحتياطي في الإنترنت
# =========================

def search_web(question):
    try:
        url = (
            "https://html.duckduckgo.com/html/?q="
            + quote_plus(question)
        )

        headers = {"User-Agent": "Mozilla/5.0 StudyAI/1.0"}
        response = requests.get(url, headers=headers, timeout=8)

        if response.status_code != 200:
            return None

        html = response.text

        results = re.findall(
            r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>',
            html,
            re.S
        )
        snippets = re.findall(
            r'<a class="result__snippet"[^>]*>(.*?)</a>',
            html,
            re.S
        )

        if not results:
            return None

        def clean_html(value):
            value = re.sub(r"<[^>]+>", " ", value)
            value = html_lib.unescape(value)
            value = re.sub(r"\s+", " ", value)
            return value.strip()

        output = []

        for i, item in enumerate(results[:5]):
            link = item[0].replace("&amp;", "&")
            title = clean_html(item[1])

            # تحويل رابط DuckDuckGo الوسيط إلى الرابط الأصلي
            if link.startswith("//"):
                link = "https:" + link

            parsed = urlparse(link)
            if (
                parsed.hostname
                and parsed.hostname.endswith("duckduckgo.com")
                and parsed.path == "/l/"
            ):
                original = parse_qs(parsed.query).get("uddg", [])
                if original:
                    link = original[0]

            snippet = ""
            if i < len(snippets):
                snippet = clean_html(snippets[i])

            if title and link.startswith(("https://", "http://")):
                output.append({
                    "title": title,
                    "snippet": snippet,
                    "url": link
                })

        if not output:
            return None

        # ترتيب النتائج حسب الكلمات المرتبطة بالسؤال
        stopwords = {
            "ما", "ماذا", "هل", "من", "في", "على", "عن",
            "إلى", "الى", "هو", "هي", "و", "أو", "او",
            "كيف", "لماذا", "متى", "كم", "مع", "كان",
            "the", "a", "an", "is", "are", "of", "in",
            "to", "for", "what", "who", "when", "where",
            "how", "why", "and", "or", "le", "la", "les",
            "de", "des", "du", "un", "une", "et", "est"
        }

        def words(value):
            value = value.lower()
            value = re.sub(r"[^\w\s]", " ", value)
            return {
                word for word in value.split()
                if len(word) > 1 and word not in stopwords
            }

        query_words = words(question)

        def relevance(item):
            title_words = words(item["title"])
            snippet_words = words(item["snippet"])
            all_words = title_words | snippet_words

            title_matches = query_words & title_words
            all_matches = query_words & all_words

            score = (
                len(title_matches) * 3
                + len(query_words & snippet_words)
            )

            if query_words and query_words <= all_words:
                score += 5

            # تفضيل المصادر العلمية والتعليمية الموثوقة
            domain = urlparse(item["url"]).hostname or ""
            domain = domain.lower()

            trusted_domains = (
                "nasa.gov",
                "nasainarabic.net",
                "aljazeera.net",
                "esa.int",
                "space.com",
                "scientificamerican.com",
                "nationalgeographic.com",
                "britannica.com",
                "science.org",
            )

            if any(
                domain == trusted or domain.endswith("." + trusted)
                for trusted in trusted_domains
            ):
                score += 4

            item["_relevance"] = score
            item["_matches"] = len(all_matches)
            return score

        for item in output:
            relevance(item)

        output.sort(
            key=lambda item: item["_relevance"],
            reverse=True
        )

        # استبعاد النتائج التي لا تتطابق مع أي كلمة مهمة
        if len(query_words) >= 2:
            relevant = [
                item for item in output
                if item["_matches"] >= 2
            ]
            if relevant:
                output = relevant

        for item in output:
            item.pop("_relevance", None)
            item.pop("_matches", None)

        return output[:5] or None

    except Exception as e:
        print("Web search error:", e)
        return None


# =========================
# API
# =========================

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json() or {}

    question = data.get(
        "question",
        ""
    ).strip()

    session_id = get_session_id(request)

    if not question:

        return jsonify({
            "answer": "✍️ اكتب سؤالك أولًا."
        })

    # المحادثة الطبيعية
    social = conversation_reply(question)

    if social:

        remember(
            session_id,
            question,
            social
        )

        return jsonify({
            "answer": social
        })

    # ربط السؤال بالسؤال السابق
    search_question = improve_followup(
        question,
        session_id
    )

    books = load_books()

    if not books:

        answer = (
            "📚 لم أجد الكتب داخل "
            "book_texts."
        )

        remember(
            session_id,
            question,
            answer
        )

        return jsonify({
            "answer": answer
        })

    result = search_books(
        search_question,
        books
    )

    if result is None:

        # لم نجد إجابة كافية في المنهج
        # ننتقل تلقائيًا إلى البحث في الإنترنت

        web_results = search_web(search_question)

        if web_results:

            lines = [
                "🌐 لم أجد إجابة مناسبة في المنهج،",
                "لذلك بحثت في الإنترنت:",
                ""
            ]

            for item in web_results[:3]:

                lines.append(
                    "🔹 " + item["title"]
                )

                if item["snippet"]:
                    lines.append(
                        item["snippet"]
                    )

                lines.append("")

            answer = "\n".join(lines)

        else:

            answer = (
                "🤔 لم أجد إجابة مناسبة في الكتب، "
                "ولم أتمكن من العثور على نتائج مناسبة في الإنترنت."
            )

        remember(
            session_id,
            question,
            answer
        )

        return jsonify({
            "answer": answer
        })

    answer_text = make_answer(
        search_question,
        result["text"]
    )

    source = os.path.basename(
        str(result.get("book") or "")
    ) or "كتاب غير محدد"

    if re.search(r"(?m)^📖 المصدر:", answer_text):
        answer_text = re.sub(
            r"(?m)^📖 المصدر:.*$",
            lambda match: "📖 المصدر: " + source,
            answer_text
        )
    else:
        answer_text = (
            answer_text.rstrip()
            + "\n\n📖 المصدر: "
            + source
        )

    answer = (
        "🤖 بالتأكيد! إليك الإجابة:\n\n"
        + answer_text
        + "\n\n"
    )

    remember(
        session_id,
        question,
        answer
    )

    return jsonify({
        "answer": answer
    })

@app.route("/results")
def results():
    candidate_number = request.args.get("candidate_number", "").strip()
    result = None

    if candidate_number:
        from results_db import search_result
        result = search_result(candidate_number)

    return render_template(
        "results.html",
        result=result,
        candidate_number=candidate_number
    )
# =========================
# إدارة النتائج - للمشرف فقط
# =========================

@app.route("/admin/results", methods=["GET", "POST"])
def admin_results():
    user_id = session.get("user_id")

    if not user_id:
        return "يجب تسجيل الدخول أولاً", 401

    from auth import get_db

    conn = get_db()
    user = conn.execute(
        "SELECT is_admin FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if not user or not user["is_admin"]:
        return "غير مصرح لك بالدخول إلى لوحة الإدارة", 403

    message = None

    if request.method == "POST":
        uploaded_file = request.files.get("results_file")

        if not uploaded_file or not uploaded_file.filename:
            message = "اختر ملف CSV أولاً."
        elif not uploaded_file.filename.lower().endswith(".csv"):
            message = "يسمح فقط بملفات CSV."
        else:
            import os
            import tempfile

            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    suffix=".csv",
                    delete=False
                ) as temp:
                    uploaded_file.save(temp.name)
                    temp_path = temp.name

                from import_results import import_csv

                imported = import_csv(temp_path)

                message = f"تم استيراد النتائج بنجاح: {imported} سجل."

            except Exception as e:
                message = f"حدث خطأ أثناء الاستيراد: {e}"

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    return render_template(
        "admin_results.html",
        message=message
    )


# =========================
# تشغيل Study AI
# =========================


@app.route("/admin/countdown", methods=["GET", "POST"])
def admin_countdown():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    import sqlite3
    from countdown_db import get_countdowns, add_countdown

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not user or not user["is_admin"]:
        return "غير مصرح لك بالدخول", 403

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        target_datetime = request.form.get("target_datetime", "").strip()

        if title and target_datetime:
            add_countdown(title, target_datetime)

        return redirect(url_for("admin_countdown"))

    countdowns = get_countdowns()

    return render_template(
        "admin_countdown.html",
        countdowns=countdowns
    )


@app.route("/admin/countdown/delete/<int:countdown_id>", methods=["POST"])
def admin_countdown_delete(countdown_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    import sqlite3
    from countdown_db import delete_countdown

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not user or not user["is_admin"]:
        return "غير مصرح لك بالدخول", 403

    delete_countdown(countdown_id)

    return redirect(url_for("admin_countdown"))


@app.route("/api/countdown")
def get_countdown_data():
    from countdown_db import get_countdowns

    countdowns = get_countdowns()

    return jsonify(countdowns)

@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    import sqlite3

    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not user or not user["is_admin"]:
        return "غير مصرح لك بالدخول", 403

    return render_template("admin.html")
if __name__ == "__main__":

    print()
    print("================================")
    print("          🧠 Study AI")
    print("================================")
    print("📚 البحث في الكتب: ON")
    print("💬 المحادثة: ON")
    print("🧠 الذاكرة: ON")
    print("🎯 فهم نوع السؤال: ON")
    print("🌐 http://127.0.0.1:5000")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
