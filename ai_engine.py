import os
import random
import re

TEXT_FOLDER = "book_texts"


# =========================
# تحميل الكتب
# =========================

def load_books():
    books = {}

    if not os.path.exists(TEXT_FOLDER):
        return books

    # قراءة جميع ملفات TXT داخل book_texts والمجلدات الفرعية
    for root, dirs, files in os.walk(TEXT_FOLDER):
        for filename in files:

            if not filename.lower().endswith(".txt"):
                continue

            path = os.path.join(root, filename)

            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    text = file.read().strip()

                if text:
                    # المفتاح يحتوي على المسار النسبي حتى لا تختلط الكتب
                    relative_path = os.path.relpath(path, TEXT_FOLDER)
                    books[relative_path] = text

            except Exception as error:
                print("⚠️ تعذر قراءة:", path)
                print(error)

    return books


# =========================
# تنظيف النص
# =========================

def clean_text(text):

    # محارف BOM والمسافات الصفرية
    remove_chars = [
        "\ufeff",
        "\u200b",
        "\u200c",
        "\u200d",
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u2060",
        "\u2061",
        "\u2062",
        "\u2063",
        "\u2064",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
        "\u206a",
        "\u206b",
        "\u206c",
        "\u206d",
        "\u206e",
        "\u206f"
    ]

    for char in remove_chars:
        text = text.replace(char, " ")

    # تنظيف رموز التحكم الغريبة
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)

    # إزالة نقاط/رموز PDF التي تظهر داخل الكلمات
    text = text.replace("•", " ")
    text = text.replace("▪", " ")
    text = text.replace("▫", " ")
    text = text.replace("◦", " ")

    # توحيد بعض علامات الترقيم
    text = text.replace("ـ", "")
    text = text.replace("،", "، ")
    text = text.replace("؛", "؛ ")
    text = text.replace("؟", "؟ ")

    # إزالة المسافات المتكررة
    text = re.sub(r"[ \t]+", " ", text)

    # إزالة المسافات قبل علامات الترقيم
    text = re.sub(r"\s+([،؛؟!.,:;])", r"\1", text)

    # إضافة مسافة بعد علامات الترقيم عند الحاجة
    text = re.sub(r"([،؛؟!.,:;])(?=\S)", r"\1 ", text)

    # توحيد الأسطر
    text = re.sub(r"\n+", "\n", text)

    return text.strip()

# =========================
# فحص جودة الجملة
# =========================

def good_sentence(sentence):

    sentence = sentence.strip()

    if len(sentence) < 40:
        return False

    if len(sentence) > 250:
        return False

    words = sentence.split()

    if len(words) < 8:
        return False

    # عدد الحروف العربية
    arabic_letters = len(
        re.findall(r"[\u0600-\u06FF]", sentence)
    )

    # عدد الحروف اللاتينية
    latin_letters = len(
        re.findall(r"[A-Za-zÀ-ÿ]", sentence)
    )

    # النص يجب أن يحتوي على عدد معقول من الحروف
    if arabic_letters < 15 and latin_letters < 15:
        return False

    # كلمات غالبًا تظهر في صفحات بيانات الكتاب
    bad_phrases = [
        "المؤلفون",
        "المدققون",
        "المصححون",
        "تصميم وإخراج",
        "المراجعة اللغوية",
        "وزارة التربية",
        "أستاذ تعليم",
        "مفتش تعليم",
        "حقوق الطبع",
        "جميع الحقوق محفوظة",
        "République",
        "Ministère",
        "Auteurs",
        "Inspecteur"
    ]

    for phrase in bad_phrases:
        if phrase.lower() in sentence.lower():
            return False

    # إذا كان النص مليئًا بالرموز الغريبة
    strange = len(
        re.findall(
            r"[^\w\s\u0600-\u06FFÀ-ÿ.,،؛؟!?()\-]",
            sentence
        )
    )

    if strange > len(sentence) * 0.15:
        return False

    return True


# =========================
# إنشاء الأسئلة
# =========================
def fix_reversed_arabic(text):
    replacements = {
        "ينطولا": "الوطني",
        "يوبرتلا": "التربوي",
        "دهعملا": "المعهد",
        "ةيناثلا": "الثانية",
        "ةيدادعلإا": "الإعدادية",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text
def make_questions(text):

    text = clean_text(text)
    text = fix_reversed_arabic(text)
    # تقسيم النص إلى جمل
    sentences = re.split(
        r"[.!؟؛:\n]+",
        text
    )

    questions = []

    for sentence in sentences:

        sentence = sentence.strip()

        if not good_sentence(sentence):
            continue

        words = sentence.split()

        candidates = []

        for index, word in enumerate(words):

            clean_word = re.sub(
                r"[^\w\u0600-\u06FFÀ-ÿ-]",
                "",
                word
            )

            # لا نختار أول أو آخر الكلمات
            if index <= 2:
                continue

            if index >= len(words) - 2:
                continue

            # كلمة مناسبة للسؤال
            if len(clean_word) < 4:
                continue

            # نتجنب الكلمات التي تحتوي رموزًا كثيرة
            if not re.search(
                r"[\u0600-\u06FFA-Za-zÀ-ÿ]",
                clean_word
            ):
                continue

            candidates.append(
                (index, clean_word)
            )

        if not candidates:
            continue

        index, answer = random.choice(candidates)

        question_words = words.copy()

        question_words[index] = "________"

        question = "أكمل الجملة:\n" + " ".join(
            question_words
        )

        questions.append({
            "question": question,
            "answer": answer,
            "source": sentence
        })

    return questions


# =========================
# اختيار كتب المادة
# =========================

def get_subject_books(books, topic):

    topic = topic.strip().lower()

    # اللغة العربية
    if (
        "عرب" in topic
        or "لغة عربية" in topic
    ):

        prefixes = [
            "AR-",
            "MART05",
            "Manuel_Arabe",
            "Cahier_Arabe"
        ]

    # الرياضيات
    elif (
        "رياض" in topic
        or "math" in topic
        or "maths" in topic
    ):

        prefixes = [
            "MA-",
            "MATHE-",
            "Math_"
        ]

    # الفرنسية
    elif (
        "فرنس" in topic
        or "français" in topic
        or "francais" in topic
    ):

        prefixes = [
            "FR-",
            "MART08"
        ]

    # التاريخ
    elif "تاريخ" in topic:

        prefixes = [
            "HIST-"
        ]

    # الجغرافيا
    elif "جغراف" in topic:

        prefixes = [
            "GEO-"
        ]

    # العلوم
    elif "علوم" in topic:

        prefixes = [
            "SN-",
            "IC"
        ]

    else:
        return {}

    selected = {}

    for filename, text in books.items():

        if any(
            filename.startswith(prefix)
            for prefix in prefixes
        ):
            selected[filename] = text

    return selected


# =========================
# التدريب
# =========================

def training(books):

    print()
    topic = input("📚 المادة: ").strip()

    if not topic:
        print("⚠️ اكتب اسم المادة.")
        return

    selected_books = get_subject_books(
        books,
        topic
    )

    if not selected_books:

        print()
        print("❌ لم أجد كتبًا لهذه المادة.")
        print()
        print("المواد المتاحة:")
        print("📖 اللغة العربية")
        print("📐 الرياضيات")
        print("🇫🇷 الفرنسية")
        print("📜 التاريخ")
        print("🌍 الجغرافيا")
        print("🔬 العلوم")
        print()

        return

    print()
    print(
        "📚 تم اختيار",
        len(selected_books),
        "كتابًا"
    )

    all_questions = []

    for filename, text in selected_books.items():

        questions = make_questions(text)

        for question in questions:

            question["book"] = filename

            all_questions.append(
                question
            )

    if not all_questions:

        print()
        print(
            "❌ لم أجد جملًا مناسبة للتدريب."
        )
        print(
            "⚠️ قد يكون الكتاب عبارة عن صور ممسوحة ضوئيًا."
        )
        print()

        return

    # اختيار سؤال عشوائي
    question = random.choice(
        all_questions
    )

    print()
    print("━━━━━━━━━━━━━━━━━━━━")
    print("📖 المصدر:", question["book"])
    print("━━━━━━━━━━━━━━━━━━━━")
    print()
    print("❓ السؤال:")
    print(question["question"])
    print()

    answer = input("✍️ إجابتك: ").strip()

    user_answer = re.sub(
        r"[^\w\u0600-\u06FFÀ-ÿ-]",
        "",
        answer
    ).lower()

    correct_answer = re.sub(
        r"[^\w\u0600-\u06FFÀ-ÿ-]",
        "",
        question["answer"]
    ).lower()

    print()

    if user_answer == correct_answer:

        print("✅ إجابة صحيحة!")
        print("🎉 أحسنت!")

    else:

        print("❌ الإجابة غير صحيحة.")
        print(
            "💡 الإجابة الصحيحة:",
            question["answer"]
        )

    print()
    print("📚 الجملة من الكتاب:")
    print(question["source"])
    print()


# =========================
# البرنامج الرئيسي
# =========================

def main():

    print()
    print("🧠 Study AI")
    print("📚 جاري تحميل الكتب...")
    print()

    books = load_books()

    print(
        "✅ تم تحميل",
        len(books),
        "كتابًا"
    )

    print()

    while True:

        print("━━━━━━━━━━━━━━━━━━━━")
        print("1️⃣ التدريب الذكي")
        print("2️⃣ خروج")
        print("━━━━━━━━━━━━━━━━━━━━")

        choice = input("اختر: ").strip()

        if choice == "1":

            training(books)

        elif choice == "2":

            print()
            print("👋 تم إيقاف Study AI")
            break

        else:

            print()
            print("⚠️ اختر 1 أو 2.")
            print()


# =========================
# تشغيل البرنامج
# =========================

if __name__ == "__main__":
    main()
# =========================
# توليد سؤال للاختبارات
# =========================

def _level_subject_books(books, stage, level, subject):
    """اختيار كتب المرحلة والسنة والمادة."""

    stage = (stage or "").strip().lower()
    level = str(level or "").strip()
    subject = (subject or "").strip().lower()

    # أسماء المواد بالعربية والإنجليزية
    subject_aliases = {
        "arabic": ["arabic", "عرب"],
        "math": ["math", "رياض"],
        "french": ["french", "français", "francais", "فرنس"],
        "english": ["english", "انكليزي", "انجليزية", "إنكليزية", "إنجليزية"],
        "science": ["science", "علوم"],
        "history": ["history", "hist", "تاريخ"],
        "geography": ["geography", "geo", "جغراف"],
        "islamic": ["islamic", "اسلام", "إسلام"],
        "civics": ["civics", "مدنية", "مدني"],
        "physics": ["physics", "phys", "فيزياء", "فيزيا"],
        "chemistry": ["chemistry", "chem", "كيمياء"],
        "philosophy": ["philosophy", "فلسفة"],
        "fiqh": ["fiqh", "فقه"],
    }

    aliases = subject_aliases.get(subject, [subject])

    selected = {}

    for filename, text in books.items():
        name = filename.lower()

        # -------------------------
        # الإعدادي
        # -------------------------
        if stage in ("middle", "college", "إعدادي", "الإعدادي", "الاعدادي"):
            if "college" not in name:
                continue

            # السنة
            level_patterns = {
                "1": ["arabic_1_college", "السنة-الاولى-الاعدادية",
                      "السنة-الأولى-الاعدادية"],
                "2": ["arabic_2_college", "السنة-الثانية-الاعدادية",
                      "السنة-الثانية-الإعدادية"],
                "3": ["arabic_3_college", "السنة-الثالثة-الاعدادية",
                      "السنة-الثالثة-الإعدادية"],
                "4": ["arabic_4_college", "السنة-الرابعة-الاعدادية",
                      "السنة-الرابعة-الإعدادية"],
            }

            patterns = level_patterns.get(level, [])

            # العربية لها أسماء استخراج مختصرة مثل arabic_2_college
            if subject in ("arabic", "عربي", "العربية"):
                if patterns and not any(x in name for x in patterns):
                    continue
            else:
                # بالنسبة لبقية المواد نتحقق من اسم المادة والسنة
                if not any(alias in name for alias in aliases):
                    continue

                year_words = {
                    "1": ["الاولى", "الأولى", "_1_", "-1-", "1_college"],
                    "2": ["الثانية", "_2_", "-2-", "2_college"],
                    "3": ["الثالثة", "_3_", "-3-", "3_college"],
                    "4": ["الرابعة", "_4_", "-4-", "4_college"],
                }

                if level in year_words:
                    if not any(x in name for x in year_words[level]):
                        continue

            selected[filename] = text

        # -------------------------
        # الثانوي
        # -------------------------
        elif stage in ("secondary", "high", "ثانوي", "الثانوي"):
            if "secondaire" not in name:
                continue

            if not any(alias in name for alias in aliases):
                continue

            year_words = {
                "5": ["الخامسة", "5as", "5-"],
                "6": ["السادسة", "6as", "6-"],
                "7": ["السابعة", "7as", "7-"],
            }

            if level in year_words:
                if not any(x in name for x in year_words[level]):
                    continue

            selected[filename] = text

    return selected


def generate_quiz_question(subject, stage=None, level=None, term=None):
    books = load_books()

    # إذا أرسلت المرحلة والسنة، استخدم الكتاب المطابق لهما
    if stage and level:
        selected_books = _level_subject_books(
            books,
            stage,
            level,
            subject
        )

    # توافق مع النظام القديم
    else:
        selected_books = get_subject_books(books, subject)

    if not selected_books:
        return None

    all_questions = []

    for filename, text in selected_books.items():
        questions = make_questions(text)

        for question in questions:
            question["book"] = filename
            all_questions.append(question)

    if not all_questions:
        return None

    question = random.choice(all_questions)

    answers = list({
        q["answer"]
        for q in all_questions
        if q["answer"] != question["answer"]
        and len(q["answer"].strip()) >= 2
    })

    random.shuffle(answers)

    options = [question["answer"]] + answers[:3]

    while len(options) < 4:
        options.append("لا توجد إجابة")

    random.shuffle(options)

    return {
        "question": question["question"],
        "options": options,
        "answer": options.index(question["answer"]),
        "source": question["book"]
    }

