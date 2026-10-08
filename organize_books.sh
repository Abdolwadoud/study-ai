#!/data/data/com.termux/files/usr/bin/bash

SOURCE="$HOME/storage/downloads"
DEST="$HOME/study-ai/books"

mkdir -p "$DEST/الإعدادي"
mkdir -p "$DEST/الثانوي"
mkdir -p "$DEST/غير_مصنف"

echo "================================"
echo "   ترتيب كتب Study AI"
echo "================================"
echo

if [ ! -d "$SOURCE" ]; then
    echo "لم يتم العثور على مجلد التنزيلات:"
    echo "$SOURCE"
    exit 1
fi

count=0

find "$SOURCE" -type f \( -iname "*.pdf" -o -iname "*.PDF" \) -print0 |
while IFS= read -r -d '' file; do

    name="$(basename "$file")"

    # نتجنب نسخ الكتب الموجودة أصلًا
    if [ -f "$DEST/$name" ] || \
       [ -f "$DEST/الإعدادي/$name" ] || \
       [ -f "$DEST/الثانوي/$name" ] || \
       [ -f "$DEST/غير_مصنف/$name" ]; then
        echo "موجود مسبقًا: $name"
        continue
    fi

    # الإعدادي
    if echo "$name" | grep -Eiq \
        '1AC|2AC|3AC|1.?COL|2.?COL|3.?COL|COLLEGE|COLLÈGE|إعدادي|اعدادي'; then

        cp -n "$file" "$DEST/الإعدادي/"
        echo "✓ إعدادي: $name"

    # الثانوي
    elif echo "$name" | grep -Eiq \
        '1AS|2AS|3AS|1.?LYC|2.?LYC|3.?LYC|LYCEE|LYCÉE|ثانوي|الثانوي'; then

        cp -n "$file" "$DEST/الثانوي/"
        echo "✓ ثانوي: $name"

    else

        cp -n "$file" "$DEST/غير_مصنف/"
        echo "? غير مصنف: $name"

    fi

    count=$((count + 1))

done

echo
echo "================================"
echo "انتهى ترتيب الملفات."
echo "================================"
echo
echo "الإعدادي:"
find "$DEST/الإعدادي" -type f | wc -l

echo "الثانوي:"
find "$DEST/الثانوي" -type f | wc -l

echo "غير مصنف:"
find "$DEST/غير_مصنف" -type f | wc -l
