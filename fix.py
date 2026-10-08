import re

def normalize_arabic(text):
    text = text.lower()

    text = re.sub(r"[\u200e\u200f\u202a-\u202e\ufeff]", "", text)

    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ى", "ي")

    # إصلاح أخطاء OCR المحددة فقط
    text = text.replace("االاستعمار", "الاستعمار")
    text = text.replace("االحتلال", "الاحتلال")
    text = text.replace("االستقلال", "الاستقلال")
    text = text.replace("االستعمار", "الاستعمار")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


text = "االستعمار الفرنسي االحتلال االستقلال"

print(normalize_arabic(text))
