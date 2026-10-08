import csv
from pathlib import Path
from results_db import get_connection

REQUIRED_COLUMNS = {
    "candidate_number",
    "competition",
    "year",
    "candidate_name",
    "result",
    "average",
    "status",
}


def import_csv(csv_file):
    csv_path = Path(csv_file)

    if not csv_path.is_file():
        print("❌ الملف غير موجود:", csv_file)
        return 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            print("❌ ملف CSV فارغ أو بدون عناوين.")
            return 0

        columns = {c.strip() for c in reader.fieldnames}

        missing = REQUIRED_COLUMNS - columns

        if missing:
            print("❌ أعمدة ناقصة:")
            for column in sorted(missing):
                print("   -", column)
            return 0

        conn = get_connection()

        added = 0
        updated = 0
        skipped = 0

        for row in reader:
            candidate_number = row["candidate_number"].strip()

            if not candidate_number:
                skipped += 1
                continue

            data = (
                candidate_number,
                row["competition"].strip(),
                row["year"].strip(),
                row["candidate_name"].strip(),
                row["result"].strip(),
                row["average"].strip(),
                row["status"].strip(),
            )

            existing = conn.execute(
                """
                SELECT id
                FROM results
                WHERE candidate_number = ?
                  AND competition = ?
                  AND year = ?
                """,
                (
                    candidate_number,
                    data[1],
                    data[2],
                )
            ).fetchone()

            if existing:
                conn.execute("""
                    UPDATE results
                    SET competition = ?,
                        year = ?,
                        candidate_name = ?,
                        result = ?,
                        average = ?,
                        status = ?
                    WHERE candidate_number = ?
                """, (
                    data[1],
                    data[2],
                    data[3],
                    data[4],
                    data[5],
                    data[6],
                    data[0],
                ))
                updated += 1

            else:
                conn.execute("""
                    INSERT INTO results
                    (
                        candidate_number,
                        competition,
                        year,
                        candidate_name,
                        result,
                        average,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, data)
                added += 1

        conn.commit()
        conn.close()

    print("✅ اكتمل الاستيراد")
    print("➕ تمت إضافة:", added)
    print("🔄 تم تحديث:", updated)
    print("⏭️ تم تجاهل:", skipped)

    return added + updated


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("الاستخدام:")
        print("python import_results.py results.csv")
    else:
        import_csv(sys.argv[1])
