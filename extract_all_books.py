from pathlib import Path
import subprocess

pdf_root = Path("books")
text_root = Path("book_texts")

pdfs = sorted(
    p for p in pdf_root.rglob("*")
    if p.is_file()
    and p.suffix.lower() == ".pdf"
    and not p.name.startswith(".trashed")
)

done = 0
skipped = 0
failed = []
empty = []

print(f"عدد ملفات PDF المراد فحصها: {len(pdfs)}", flush=True)

for i, pdf in enumerate(pdfs, 1):
    relative = pdf.relative_to(pdf_root).with_suffix(".txt")
    output = text_root / relative
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and output.stat().st_size > 0:
        skipped += 1
        continue

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8",
             str(pdf), str(output)],
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode != 0:
            failed.append(str(pdf))
            if output.exists() and output.stat().st_size == 0:
                output.unlink()
        elif not output.exists() or output.stat().st_size == 0:
            empty.append(str(pdf))
        else:
            done += 1

    except Exception as e:
        failed.append(f"{pdf}: {e}")

    if i % 10 == 0 or i == len(pdfs):
        print(
            f"التقدم: {i}/{len(pdfs)} | "
            f"استخراج جديد: {done} | "
            f"موجود مسبقًا: {skipped} | "
            f"فارغ: {len(empty)} | "
            f"فشل: {len(failed)}",
            flush=True
        )

print("\n=== انتهى الاستخراج ===")
print("استخراج جديد:", done)
print("تم تجاوز نصوص موجودة:", skipped)
print("ملفات PDF نتج عنها نص فارغ:", len(empty))
print("ملفات فشل استخراجها:", len(failed))

if empty:
    Path("empty_pdf_list.txt").write_text(
        "\n".join(empty), encoding="utf-8"
    )
if failed:
    Path("failed_pdf_list.txt").write_text(
        "\n".join(failed), encoding="utf-8"
    )
