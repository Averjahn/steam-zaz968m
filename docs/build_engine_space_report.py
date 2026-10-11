"""Create the concise PDF report for the bounded engine-space search."""
import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "engine-space-study.json").read_text())
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
pdfmetrics.registerFont(TTFont("Arial", FONT))
pdfmetrics.registerFont(TTFont("ArialBold", FONT_BOLD))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Ru", parent=styles["BodyText"], fontName="Arial", fontSize=9, leading=13, spaceAfter=7))
styles.add(ParagraphStyle(name="RuTitle", parent=styles["Title"], fontName="ArialBold", fontSize=19, leading=24, alignment=0, spaceAfter=12))
styles.add(ParagraphStyle(name="RuHead", parent=styles["Heading2"], fontName="ArialBold", fontSize=13, leading=17, spaceBefore=10, spaceAfter=7))
styles.add(ParagraphStyle(name="RuCell", parent=styles["BodyText"], fontName="Arial", fontSize=7.5, leading=10))

def f(n, places=2):
    return f"{n:,.{places}f}".replace(",", " ").replace(".", ",")

def para(text, style="Ru"):
    return Paragraph(text, styles[style])

best = DATA["best"]
unchanged = DATA["best_unchanged_equipment"]
baseline = {"bore_mm": 40, "stroke_mm": 45, "rod_mm": 9.6, "volume_L": 7 * math.pi * 40**2 / 4 * 45 / 1e6, "double_volume_L": 7 * math.pi * (2 * 40**2 - 9.6**2) / 4 * 45 / 1e6, "origin_mm": [3267.5, 0, 490], "size_mm": [569.8, 561.6, 374.6], "gaps": {"BODY": 18.0, "SUSP": 50}, "pipe_gap_mm": 0, "hits": []}
rows = []
for title, item in [("Исходная модель", baseline), ("Оборудование оставлено на местах", unchanged), ("Максимум проверенной выборки", best)]:
    collisions = sorted({h["id"] for h in item["hits"] if not h["connected"]})
    dimensions = " × ".join(f(x, 0) for x in item["size_mm"])
    rows.append([para(title, "RuCell"), para(f"Ø{f(item['bore_mm'], 0)} × {f(item['stroke_mm'], 2)} мм", "RuCell"), para(f"{f(item['volume_L'], 3)} л", "RuCell"), para(f"{dimensions} мм", "RuCell"), para(f"{f(item['gaps']['BODY'], 1)} мм", "RuCell"), para(", ".join(collisions) if collisions else "нет новых", "RuCell")])

story = [para("Свободное место для семицилиндровой паровой звезды", "RuTitle"),
         para("Ограниченный геометрический поиск по предоставленной модели кузова ЗАЗ-968М. Он сравнивает диаметр, ход и продольное положение с сохранением выбранной архитектуры коленвала. Это не глобальная оптимизация автомобиля и не проект для изготовления."),
         para("Сравнение вариантов", "RuHead")]
table = Table([[para(x, "RuCell") for x in ["Вариант", "Цилиндр", "Объём", "Габарит двигателя", "Кузов", "Новые пересечения"]]] + rows, colWidths=[112, 65, 48, 85, 45, 145], repeatRows=1)
table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dce8f2")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#b9c5ce")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
story.extend([table, Spacer(1, 10), para("Расчёт рабочего объёма", "RuHead"),
    para("V = N·π·D²·S / 4. Для максимума из прошедших динамический экран кандидатов: 7 × π × 99² × 51,75 / 4 / 10⁶ = <b>2,788 л</b>. Размеры D и S заданы в миллиметрах, 10⁶ мм³ = 1 л."),
    para("Для двойного действия суммарный вытесняемый объём двух сторон за оборот: V₂ = N·π·(2D² − dшт²)·S / 4 = 7 × π × (2 × 99² − 11,04²) × 51,75 / 4 / 10⁶ = <b>5,542 л</b>. Это геометрическое вытеснение; расход свежего пара дополнительно зависит от отсечки, наполнения, мёртвого объёма и потерь."),
    para("Ограничения максимального варианта", "RuHead"),
    para(f"Координата оси X = {f(best['origin_mm'][0], 0)} мм. Минимальный холодный зазор до кузовной сетки {f(best['gaps']['BODY'], 1)} мм, до статической подвески не менее {f(best['gaps']['SUSP'], 1)} мм, до оболочки труб с изоляцией {f(best['pipe_gap_mm'], 1)} мм. Проверено 72 положения для труб B, коллекторов и подвижных шатунов, штоков и крейцкопфов; у отобранного кандидата пересечений не обнаружено."),
    para("Для этого варианта трассы входа свежего пара и выпуска смещаются примерно на 68 мм; также пересекаются прежние правый и левый выхлопные узлы и дымоход. Их нужно переразвести, затем повторить проверку всех труб, фитингов, горячих зазоров, креплений и движения подвески. Вариант без новых пересечений с неподвижным окружением — Ø58 × 45 мм, 0,832 л, но это не проверяет силовую пригодность."),
    para("Давление само по себе не задаёт допустимость такого двигателя. Для Ø99 и штока 11,04 мм при 10 бар абсолютного на стороне подачи, 1,2 бар абсолютного на выпуске и 1 бар окружающего давления предварительная газовая сила на поршень составляет около 6,8 кН до учёта инерции, трения и шатуна."),
    para("Границы поиска", "RuHead"),
    para("Кинематический масштаб перебирался от 32 до 64 мм с основным шагом 2 мм; диаметры цилиндров ограничены 40–100 мм; положение по X выбиралось на конечной сетке и уточнялось для перспективной области. Для каждого кандидата проверялись поверхность кузова, статическая сетка подвески, трубки с теплоизоляцией и затем пересечения с неподвижным оборудованием. Семейство большего хода содержит только проверенные точки, поэтому результат — лучший найденный вариант в этой выборке, а не доказанный предел кузова."),
    para("Кузов — игровая триангулированная модель без измеренного внутреннего CAD. В проверке исключены штатный двигатель и заднее сиденье; не проверены нагрузки на пол и стойки, прочность усиленного механизма, горячее расширение, колебания кузова, уплотнения, клапанный привод и полный перенос КПП. Парогенератор и доступная тепловая мощность также не масштабируются вместе с рабочим объёмом."),
    para("Источник кузовной модели: yatloo, CC BY 4.0. Исходные кандидаты, критерии, допущения и контрольные суммы сохранены в engine-space-study.json."),
    ])

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Arial", 7); canvas.setFillColor(colors.HexColor("#64748b")); canvas.drawString(38, 22, "ЗАЗ-968М / предварительная геометрическая оценка / 11.10.2026 / не для изготовления"); canvas.drawRightString(A4[0]-38, 22, str(doc.page)); canvas.restoreState()

SimpleDocTemplate(str(ROOT / "engine-space-report.pdf"), pagesize=A4, leftMargin=38, rightMargin=38, topMargin=38, bottomMargin=35, title="Свободное место для семицилиндровой паровой звезды").build(story, onFirstPage=footer, onLaterPages=footer)
