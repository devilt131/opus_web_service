import os
from datetime import datetime
from xml.sax.saxutils import escape

FONT_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"),
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
]


def find_cyrillic_font() -> str | None:
    for path in FONT_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return None


def _pdf_escape(text: str) -> str:
    if not text:
        return ""
    return escape(str(text)).replace("\n", "<br/>")


def register_pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_path = find_cyrillic_font()
    if not font_path:
        return None, None
    pdfmetrics.registerFont(TTFont("OpusFont", font_path))
    pdfmetrics.registerFont(TTFont("OpusFont-Bold", font_path))
    return "OpusFont", "OpusFont-Bold"


def build_pdf_report(res: dict, filepath: str) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font_name, _ = register_pdf_font()
    if not font_name:
        raise RuntimeError(
            "Cyrillic font not found. Install dejavu-fonts or place DejaVuSans.ttf in backend/fonts/"
        )

    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Heading1"],
            fontName=font_name,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=12,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=14,
        ),
    }

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    plag = res.get("plagiarism") or {}
    entities = res.get("entities") or {}
    stats = res.get("stats") or {}

    def section(title: str, body: str):
        story.append(Paragraph(_pdf_escape(title), styles["heading"]))
        story.append(Paragraph(_pdf_escape(body), styles["body"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph(_pdf_escape("OPUS — отчёт по анализу"), styles["title"]))
    story.append(Spacer(1, 12))

    section("Заголовок", res.get("title", ""))
    section("Краткое содержание", res.get("summary", ""))
    section("Сжатие", f"{res.get('compression', 0)}%")

    keywords = res.get("keywords") or []
    if keywords:
        kw_lines = [
            f"{k.get('word', '')} — частота {k.get('freq', 0)}, вес {round((k.get('score') or 0) * 100, 1)}%"
            for k in keywords
        ]
        section("Ключевые слова", "\n".join(kw_lines))

    section("План", res.get("plan", ""))

    stats_text = (
        f"Символов: {stats.get('chars', 0)}\n"
        f"Без пробелов: {stats.get('chars_no_space', 0)}\n"
        f"Слов: {stats.get('words', 0)}\n"
        f"Предложений: {stats.get('sentences', 0)}\n"
        f"Уникальных слов: {stats.get('unique', 0)}\n"
        f"Средняя длина слова: {stats.get('avg_w_len', 0)}\n"
        f"Средняя длина предложения: {stats.get('avg_s_len', 0)}"
    )
    section("Статистика", stats_text)

    ner_parts = []
    for label, key in (
        ("Персоны", "persons"),
        ("Организации", "orgs"),
        ("Локации", "locs"),
        ("Даты", "dates"),
    ):
        items = entities.get(key) or []
        if items:
            ner_parts.append(f"{label}: {', '.join(i['text'] for i in items)}")
    if ner_parts:
        section("Именованные сущности", "\n".join(ner_parts))

    if plag.get("uniqueness") is not None:
        plag_text = (
            f"Уникальность: {plag.get('uniqueness')}%"
            f"\nСхожесть: {plag.get('similarity', 0)}"
        )
        common = plag.get("common") or []
        if common:
            plag_text += f"\nОбщие слова: {', '.join(common)}"
        section("Проверка на плагиат", plag_text)

    section("Дата формирования", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    doc.build(story)
