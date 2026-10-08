import os

TEXT_FOLDER = "book_texts"

def load_books():
    books = {}

    for filename in os.listdir(TEXT_FOLDER):
        if filename.endswith(".txt"):
            path = os.path.join(TEXT_FOLDER, filename)

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()

            if text:
                books[filename] = text

    return books


if __name__ == "__main__":
    books = load_books()

    print("📚 عدد الكتب التي تم تحميلها:", len(books))

    for name, text in books.items():
        print(f"✅ {name} — {len(text):,} حرف")
