"""Independent literature audit. Requires CoolProp; never copies the supplied book."""
import argparse
import hashlib
import json
import math
from html import escape
from pathlib import Path
import CoolProp
from CoolProp.CoolProp import PropsSI as prop

ROOT = Path(__file__).resolve().parent
BASELINE = 'd320af01b22f12b44467789a4eb19972f16a3256'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book', type=Path, default=Path.home() / 'Desktop/steam_engines_part_1.pdf')
    args = parser.parse_args()
    data = json.loads((ROOT / 'simulation-data.json').read_text())
    k = data['defaults']
    p, T, back = 1e6, 523.15, 1.2e5
    h = prop('H', 'P', p, 'T', T, 'Water')
    u = prop('U', 'P', p, 'T', T, 'Water')
    rho = prop('D', 'P', p, 'T', T, 'Water')
    s = prop('S', 'P', p, 'T', T, 'Water')
    h2s = prop('H', 'P', back, 'S', s, 'Water')
    hf = prop('H', 'P', back, 'Q', 0, 'Water')
    hfeed = prop('H', 'P', 2e5, 'T', 333.15, 'Water')
    rhofeed = prop('D', 'P', 2e5, 'T', 333.15, 'Water')
    Tc = prop('T', 'P', back, 'Q', 0, 'Water') - 273.15
    admitted = k['admission']
    rend = rho * admitted
    pend = prop('P', 'D', rend, 'S', s, 'Water')
    uend = prop('U', 'D', rend, 'S', s, 'Water')
    finite_work = p / rho + u - uend - back / rend
    C = 1.18 * 1005 * k['airflow_m3_s']
    ntu = k['condenser_UA_W_K'] / C
    effectiveness = -math.expm1(-ntu)
    deltaT = Tc - k['ambient_C']
    old_cooling = min(k['condenser_UA_W_K'], C) * deltaT
    cooling = C * effectiveness * deltaT
    flow = 50000 / (h - hfeed)
    indicated = flow * (h - h2s) * k['isentropic_efficiency']
    shaft = indicated * k['mechanical_efficiency']
    cond = flow * (h - (h - h2s) * k['isentropic_efficiency'] - hf)
    subcool = flow * (hf - hfeed)
    pump = flow * (p - 2e5) / (rhofeed * .55)
    vd = k['cylinders'] * k['acting_sides'] * math.pi * k['engine_bore_m'] ** 2 / 4 * k['engine_stroke_m']
    geometric_flow = rho * vd * admitted * k['volumetric_efficiency'] * 2200 / 60
    wheel_rpm = 70 / 3.6 / (2 * math.pi * .28) * 60
    ratio = 1.409 * 4.125 * k['adapter']
    n3 = 2200 / ratio
    v3 = n3 / 60 * 2 * math.pi * .28 * 3.6
    p40 = prop('P', 'T', 313.15, 'Q', 0, 'Water')
    required_air = 357990 / (1.18 * 1005 * 25)
    face_speed = required_air / k['air_area_m2']
    # Independent sanity checks on thermodynamic identities, not model self-balances.
    assert 0 < finite_work < h - h2s
    assert pend > back
    assert 0 < cooling < min(C, k['condenser_UA_W_K']) * deltaT
    assert abs(50000 - indicated - cond - subcool) < 1e-8
    assert 100 < Tc < 110 and 600 < wheel_rpm < 700
    values = dict(inlet_h_J_kg=h, inlet_rho_kg_m3=rho, inlet_s_J_kgK=s,
                  isentropic_drop_J_kg=h-h2s, finite_expansion_work_J_kg=finite_work,
                  finite_end_pressure_Pa=pend, condensing_C=Tc, air_capacity_W_K=C,
                  NTU=ntu, effectiveness=effectiveness, old_cooling_W=old_cooling,
                  corrected_cooling_W=cooling, comparison_steam_kg_h=flow*3600,
                  comparison_shaft_W=shaft, comparison_condenser_W=cond,
                  missing_subcooler_W=subcool, comparison_pump_W=pump,
                  condenser_and_subcooler_W=cond+subcool,
                  comparison_cycle_residual_without_pump_W=50000-indicated-cond-subcool,
                  geometric_steam_kg_h=geometric_flow*3600, wheel_rpm_at_70=wheel_rpm,
                  speed_at_2200_gear3_kmh=v3, engine_rpm_at_70_gear4=wheel_rpm*.964*4.125*k['adapter'],
                  steam_saturation_pressure_at_40_Pa=p40,
                  air_speed_default_m_s=k['airflow_m3_s']/k['air_area_m2'],
                  legacy_B_air_m3_s=required_air, legacy_B_face_speed_m_s=face_speed)
    def f(x, n=2):
        return f'{x:,.{n}f}'.replace(',', '\u202f').replace('.', ',')
    findings = []
    def finding(id, title, state, basis, problem, formulas, action, code):
        findings.append(dict(id=id, title=title, status=state, book_basis=basis,
                             observation=problem, formulas=[dict(formula=a, substitution=b) for a,b in formulas],
                             next_action=action, code=code))
    finding('cooling', 'Теплоотвод конденсатора завышался', 'Исправлено в переходной симуляции',
            '§22, PDF 65; §26, PDF 75–76: отвод теплоты необходим. Формула ε–NTU — современный вывод для изотермической горячей стороны, дополненный справкой EES.',
            'min(UA, Cвозд)·ΔT — верхняя граница, а не теплоотдача при конечном нагреве воздуха. UA=2000 Вт/К остаётся гипотезой, не характеристикой выбранного радиатора.',
            [('Cвозд = ρвозд cp V̇', f'1,18 × 1005 × {f(k["airflow_m3_s"],5)} = {f(C)} Вт/К'),
             ('NTU = UA/Cвозд; ε = 1 − exp(−NTU)', f'2000 / {f(C)} = {f(ntu,4)}; ε = {f(effectiveness,4)}'),
             ('Q̇ = Cвозд ε (Tк − Tа)', f'{f(C)} × {f(effectiveness,4)} × ({f(Tc)} − 20) = {f(cooling/1000)} кВт; раньше {f(old_cooling/1000)} кВт (+{f((old_cooling/cooling-1)*100,1)}% к исправленному значению)')],
            'Получить карту UA и сопротивления реального теплообменника с вентиляторами; учесть воздух в паровой стороне, перегрев и отдельное охлаждение жидкости.',
            'web/steam-simulation.js: condenserHeatRate(), step(); verify_literature.mjs')
    finding('return_heat', 'В сравнительном цикле отсутствует охлаждение возврата', 'Не замкнут тепловой подбор оборудования',
            '§22, PDF 65; §44, PDF 144: тепловой баланс включает охлаждение конденсата.',
            'compareHeat вычитает энтальпию насыщенной жидкости при 104,78 °C, но подаёт в котёл воду с энтальпией 60 °C. Этот отвод теплоты не включён в подбор воздуха. Энергия насоса также должна быть согласована с энтальпией после насоса. Это относится к стационарной таблице; переходная модель отдельно считает энергию приёмника.',
            [('ṁ = Q̇котла/(h₁ − hпит)', f'50 000 / ({f(h,2)} − {f(hfeed,2)}) = {f(flow,6)} кг/с = {f(flow*3600)} кг/ч'),
             ('Q̇доохл = ṁ(hж,нас − hпит)', f'{f(flow,6)} × ({f(hf,2)} − {f(hfeed,2)}) / 1000 = {f(subcool/1000)} кВт'),
             ('Q̇отвод = Q̇конд + Q̇доохл', f'{f(cond/1000)} + {f(subcool/1000)} = {f((cond+subcool)/1000)} кВт; отдельно насос ≈ {f(pump,1)} Вт'),
             ('Q̇котла = Pинд + Q̇конд + Q̇доохл (без насоса)', f'50 = {f(indicated/1000)} + {f(cond/1000)} + {f(subcool/1000)} кВт')],
            'Выбрать температуру реального приёмника и теплообменник доохлаждения; пересчитать общий цикл с hпосле насоса и фактическими потерями.',
            'web/heat-comparison.js: compareHeat(); build_simulation_data.py: comparison_cycle')
    finding('expansion', 'Мощность цилиндра не подтверждена индикаторной диаграммой', 'Нужна модель парораспределения',
            '§6–8, PDF 16–22; §25, PDF 71–74; §28–34, PDF 81–100.',
            'Модель умножает полный изоэнтропический перепад энтальпии на ηis=0,5. Такой общий коэффициент допустим как оценка лишь после калибровки. Он не доказывает работу двигателя с отсечкой 30%. Геометрия штока, мёртвый объём, фазы клапанов, сжатие, дросселирование и теплообмен стенок не определены.',
            [('Wцикл = ∮ p dV; Pинд = (n/60) ΣWцикл', 'Суммировать обе стороны каждого цилиндра; для штоковой стороны A = π(D² − dшт²)/4. dшт и фазы пока не заданы.'),
             ('vкон = v₁/εотс; sкон = s₁; pкон = p(vкон,s₁)', f'εотс=0,30; кратность расширения=3,33; CoolProp даёт pкон={f(pend/1e5)} бар abs при pвып=1,20 бар abs'),
             ('wконеч = p₁v₁ + (u₁ − uкон) − pвып vкон', f'Идеализированный цикл без мёртвого объёма: {f(finite_work/1000)} кДж/кг против полного h₁−h₂s={f((h-h2s)/1000)} кДж/кг; разница {f((1-finite_work/(h-h2s))*100)}%')],
            'Это независимая верхняя оценка для заданной отсечки: постоянные давления впуска/выпуска, адиабатическое расширение, мгновенный сброс при неизменном объёме, без потерь стенок и клапанов. Не вычитать эти 5,85% повторно из эмпирического КПД, если он уже включает неполное расширение. Получить реальные p–V диаграммы и карту момента/расхода.',
            'web/steam-simulation.js: steamV, admission, flow, tauInd, pInd')
    finding('capacity', 'Производительность котла и расход двигателя — разные режимы', 'Требуется согласование мощности',
            '§7–10, PDF 20–26; §27, PDF 77–80; §40, PDF 125–127.',
            'Сравнение нагревателей при 50 кВт тепла не соответствует полному открытию условного двигателя при 2200 об/мин. Заявление «40 л.с.» нельзя переносить на такой режим.',
            [('Vраб/оборот = z a πD²S/4', f'2 × 2 × π × 0,1² × 0,12 / 4 = {f(vd*1000,3)} л/оборот (площадь штока пока не вычтена)'),
             ('ṁгеом = ρ₁ Vраб εотс ηоб n/60', f'{f(rho,4)} × {f(vd,6)} × 0,30 × 0,85 × 2200 / 60 × 3600 = {f(geometric_flow*3600)} кг/ч при полном открытии'),
             ('Pвал = ṁ Δhиз ηis ηмех', f'При 50 кВт в воде/паре: {f(flow,6)} × {f((h-h2s)/1000)} × 0,5 × 0,9 = {f(shaft/1000)} кВт до вспомогательных расходов; геометрический расход в {f(geometric_flow/flow)} раза больше')],
            'Согласовать графики котла, цилиндров и вспомогательного оборудования. Обороты допустимы лишь при рассчитанных клапанах, смазке, прочности и балансировке; средняя скорость поршня 2Sn/60 = 8,8 м/с сама по себе не является разрешением этих оборотов.',
            'simulation-data.json: defaults, comparison_cycle; web/heat-comparison.js')
    finding('air', 'Внутренний конденсатор не подтверждён для прежних 18 кВт', 'Основное ограничение компоновки',
            '§22, PDF 65; §26, PDF 75–76; §37, PDF 116–119.',
            'Сценарий B и текущая компактная симуляция используют разные тепловые нагрузки. Ранее рассчитанные 358 кВт конденсации не помещаются автоматически в показанные две узкие секции. Нулевые пересечения сеток не проверяют теплообмен.',
            [('V̇возд,min = Q̇/(ρcpΔTвозд)', f'357 990 / (1,18 × 1005 × 25) = {f(required_air)} м³/с'),
             ('Aсвоб = 2bh φ; v = V̇/Aсвоб', f'2 × 0,5 × 0,085 × 0,65 = {f(k["air_area_m2"],5)} м²; {f(required_air)} / {f(k["air_area_m2"],5)} = {f(face_speed)} м/с'),
             ('Q̇пред при V̇→∞ = UA(Tк−Tа)', f'При UA=2000 Вт/К и 1,2 бар: 2000 × {f(deltaT)} / 1000 = {f(2000*deltaT/1000)} кВт, ниже 358 кВт даже без ограничения воздуха')],
            'Пересчитать доступную фронтальную площадь, воздуховоды и карты вентиляторов. Для заданной внутренней компоновки ограничить мощность или изменить цикл/теплообменник после реального подбора; не масштабировать каталожный радиатор без расчёта.',
            'internal-feasibility.json; simulation-data.json: condenser_UA_W_K, air_area_m2')
    finding('pressure', 'Давление смеси нельзя считать давлением чистого пара', 'Нужна модель удаления воздуха',
            '§11–12, PDF 26–37; §26, PDF 75–76. Числа насыщения пересчитаны по IAPWS-95.',
            '1 бар abs при 40 °C допустим для смеси воздуха с водяным паром, но не для чистого насыщенного пара. Начальная модель действительно содержит воздух. Давление конденсатора 1,2 бар abs означает работу с противодавлением, а не вакуумный режим из примеров книги. При расчёте чистого пара сейчас используется полное давление смеси; при заметном воздухе результат недостоверен.',
            [('pсум = pводяного пара + pвоздуха', f'При 40 °C: pнас={f(p40/1e5,5)} бар; при pсум=1 бар на воздух приходится {f(1-p40/1e5,5)} бар'),
             ('Tконденсации = Tsat(pводяного пара)', f'После удаления воздуха при p=1,20 бар abs: Tsat={f(Tc)} °C, а не 40 °C')],
            'Проверять парциальные давления, перенос воздуха, реальное отделение/вентиляцию и падение UA из-за неконденсируемых газов. Графики всегда маркировать abs или изб.; атмосферу учитывать отдельно.',
            'web/steam-simulation.js: equilibrium(), steam(), ventMixed, ready()')
    finding('pump', 'Горячий конденсат и насосы требуют отдельной проверки', 'Не подобрано оборудование возврата',
            '§22 и §26 объясняют возврат и отвод теплоты. Температурный предел 82 °C взят из уже выбранного в проекте паспорта Cat, не из исторической книги.',
            'Насыщенный конденсат при 104,78 °C горячее выбранного входного предела Cat. Расчётный приёмник не гарантирует охлаждение до 82 °C. Возвратный насос имеет выдуманную карту 2,5 бар / 8,4 л/мин; кавитация и NPSH не рассчитаны.',
            [('NPSHa ≈ (pвс,abs − pнас(T))/(ρg) + z − hпотерь', 'При насыщении pвс≈pнас(T), первый член≈0 м. Нужны реальная высота затопления, доохлаждение и паспортный NPSHr; одного положительного перепада насоса недостаточно.')],
            'Подобрать насос горячего конденсата и условия всасывания; обеспечить температуру питания выбранного плунжерного насоса и пересчитать тепловой баланс приёмника.',
            'web/steam-simulation.js: receiver(), drainVolume, returnPower, r.T > 82; component-purchases.json')
    finding('phases', 'Таблицы насыщения имеют ограниченную область применимости', 'Не обработаны однофазные состояния сосудов',
            '§11–14, PDF 26–41: насыщенный и перегретый пар — разные состояния.',
            'В equilibrium качество x ограничивается 0…1, затем давление остаётся pнас(T). При полностью паровом или заполненном жидкостью сосуде этого уравнения недостаточно: нужно другое уравнение состояния. Проверка только границ температуры не выявляет этот выход из области модели.',
            [('x = (V/m − vж)/(vп − vж)', 'Двухфазная гипотеза применима при vж ≤ V/m ≤ vп. Выход за этот интервал следует отмечать как нерассчитанное состояние, а не скрывать clamp(0,1).')],
            'Добавить определение фазы и однофазные свойства или явный останов расчёта за областью двухфазной модели; отдельно учесть газовую подушку приёмника.',
            'web/steam-simulation.js: equilibrium(), state(), receiver()')
    finding('wheels', 'Обороты колёс согласуются с геометрией, доступная тяга пока нет', 'Кинематика подтверждается; двигатель не подтверждён',
            'Кинематика автомобиля — наш независимый расчёт, не тема книги. §7–8 помогают отделить мощность цилиндра от полезной мощности на валу.',
            'Само число оборотов колёс не выглядит нереальным: для радиуса 0,28 м при 70 км/ч получается около 663 об/мин. Скорость под нагрузкой требует момента двигателя и баланса дорожных сопротивлений.',
            [('nкол = 60 v/(2πr)', f'60 × (70/3,6) / (2π × 0,28) = {f(wheel_rpm)} об/мин'),
             ('nкол = nдв/(iКПП iглав iадапт); v = 2πr nкол/60 × 3,6', f'III: 2200 / (1,409 × 4,125 × {f(k["adapter"],2)}) = {f(n3)} об/мин; v = {f(v3)} км/ч')],
            'Уточнить нагруженный радиус шин и передаточные числа конкретной КПП; затем совместно рассчитывать тягу, обороты, расход и устойчивый тепловой режим. Нагрузки колёс требуют фактических масс и кинематики подвески.',
            'web/steam-simulation.js: ratio, radius; web/calculation-model.js; web/wheel-loads.js')
    finding('validation', 'Баланс и анимация не заменяют испытания установки', 'Конструкция остаётся исследовательской',
            '§8, PDF 21–23; §34, PDF 96–100; §39–41, PDF 122–132.',
            'Нулевая невязка энергии подтверждает реализацию принятых уравнений. Книга сопоставляет расчёты с измерениями давлений, температур, расхода и полезной мощности. Для нашего двигателя такой карты нет. КПД источников, возврат 99,9%, газовая подушка, теплопотери и прочность стыков пока предположены.',
            [('ηобщ = (Pвал − Pвспом)/(ṁтопл Hᵤ); ηмех = Pвал/Pинд', 'Не путать ηкотла=0,85 с общим КПД машины; сравнивать разные источники при одинаковой полезной мощности и границах системы.'),
             ('ΔU = Qвход − Qвыход − W + Σmвх hвх − Σmвых hвых', 'Проверять воду/пар, металл, топку, возврат, вентиляцию и вспомогательные потребители. Замкнутая вода не означает отсутствие расхода топлива или отвода теплоты.')],
            'Сначала закрыть тепловой и гидравлический подбор, затем паспортные/прочностные расчёты, подтверждённые обмеры и стендовая калибровка. Старые проценты КПД и примеры стационарных машин не являются паспортом автомобильных агрегатов.',
            'verify_simulation.mjs; models/*checks.json; simulation-data.json: defaults')
    sections = [
        ('Единицы и обозначения', '§1–4, PDF 8–14', 'В историческом тексте давление часто манометрическое; атмосфера, кгс·м, килограмм-калория, метрическая л.с. Использовать современные SI и явно различать abs/изб.'),
        ('Цилиндр, работа, мощность и регулирование', '§5–10, PDF 14–26', 'Площадь p–V диаграммы — работа; полезная мощность меньше индикаторной. Отсечка и дросселирование дают разные режимы.'),
        ('Свойства пара и термодинамические диаграммы', '§11–18, PDF 26–53', 'Насыщение связывает давление и температуру; перегрев задаётся отдельно. h–s помогает оценить предельную работу.'),
        ('Идеальная машина, подвод и отвод теплоты', '§19–27, PDF 54–80', 'Полное и неполное расширение различаются. Уменьшение противодавления увеличивает потенциальную работу, но не гарантирует её получение в конечном цилиндре.'),
        ('Действительная машина', '§28–36, PDF 81–115', 'Падение давления впуска/выпуска, сжатие, мёртвый объём, обмен теплотой со стенками и многоступенчатое расширение меняют диаграмму и расход.'),
        ('Потери и сопоставление с опытом', '§37–41, PDF 115–132', 'Отделять КПД котла, двигателя и всей установки. Исторические испытания относятся к указанным машинам и условиям, а не к нашему макету.'),
        ('Использование отработавшего пара', '§42–44, PDF 132–148', 'Большая доля теплоты остаётся в отработавшем паре. Возврат конденсата уменьшает расход воды, но тепло всё равно нужно отвести или использовать.'),
        ('Турбина отработавшего пара', '§45, PDF 148–149', 'Дополнительная ступень — отдельный агрегат; этот раздел не подтверждает эффективность малой автомобильной машины.')]
    book_sha = hashlib.sha256(args.book.read_bytes()).hexdigest() if args.book.exists() else None
    sources = [dict(id='book', title='Фр. Барт. Паровыя машины. Часть I. Термодинамическія и паро-техническія основанія экономіи (по обложке)',
                    file='steam_engines_part_1.pdf', pages=152, sha256=book_sha,
                    access='Локальный PDF: разобраны ключевые разделы работы, свойств пара, идеального/реального цикла, потерь и испытаний. Год издания не установлен; ссылки даны на страницы PDF, не на печатную нумерацию. OCR сверялся с изображениями выбранных страниц.'),
               dict(id='bmstu', title='БМСТУ: подборка «Тепловые двигатели. Получение, распределение и использование пара»',
                    url='https://library.bmstu.ru/Pages/Edu/Books/3kurs/teplovye_dvigateli_poluchenie_raspredelenie_i_ispolzovanie_para',
                    access='Прочитаны каталог, библиографические записи и аннотации. Перечислены «Теплотехника» и «Теория тепломассообмена». Полные тексты этих учебников не получены и не считаются изученными.'),
               dict(id='bmstu-thermal', title='БМСТУ: «Теплотехника», карточка издания', url='https://library.bmstu.ru/Catalog/Details/541910', access='Библиографическая карточка; ссылка Лань ведёт к электронной записи книги 222920, доступный ответ не содержит глав учебника.'),
               dict(id='bmstu-transfer', title='БМСТУ: «Теория тепломассообмена», карточка издания', url='https://library.bmstu.ru/Catalog/Details/514731', access='Библиографическая карточка и аннотация; полный текст не получен.'),
               dict(id='properties', title='CoolProp: Water (IAPWS-95)', url='https://coolprop.org/fluid_properties/fluids/Water.html', access=f'Независимый пересчёт свойств: локальная версия CoolProp {CoolProp.__version__}, HEOS Water, единицы SI.'),
               dict(id='ntu', title='F-Chart/EES: Effectiveness–NTU', url='https://fchartsoftware.com/ees/heat_transfer_library/heat_exchangers/hs1000.htm', access='Современная справка разработчика: NTU, теплоёмкостные расходы и изотермический предел конденсатора. Формула выведена ниже для нашей упрощённой горячей стороны.')]
    result = dict(date='2026-10-09', baseline_commit=BASELINE, status='Есть принципиальные неподтверждённые узлы; проверка не подтверждает работоспособность автомобиля',
                  sources=sources, reading_map=[dict(topic=a,pages=b,application=c) for a,b,c in sections], findings=findings, independent_results=values,
                  input_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['simulation-data.json','inputs.json','internal-feasibility.json','web/steam-simulation.js','web/heat-comparison.js']},
                  scope='Уравнения и физический смысл исследовательского проекта; без реальных испытаний, обмеров, прочностной экспертизы и доступа к полным учебникам БМСТУ.')
    (ROOT/'literature-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    cards = ''
    for row in findings:
        forms = ''.join('<div class="formula-card"><code>'+escape(x['formula'])+'</code><p>'+escape(x['substitution'])+'</p></div>' for x in row['formulas'])
        cards += f'<section id="{row["id"]}"><h2>{escape(row["title"])}</h2><p class="tag">{escape(row["status"])}</p><p>{escape(row["observation"])}</p><p class="source">Основание: {escape(row["book_basis"])}</p><div class="formula-grid">{forms}</div><p><strong>Что требуется:</strong> {escape(row["next_action"])}</p><p class="source">Проверяемый код: {escape(row["code"])}</p></section>'
    refs=''.join('<li>'+('<a href="'+escape(x['url'],quote=True)+'">'+escape(x['title'])+'</a>' if x.get('url') else escape(x['title']))+'<p>'+escape(x['access'])+'</p></li>' for x in sources)
    reading=''.join('<tr><td>'+escape(a)+'</td><td>'+escape(b)+'</td><td>'+escape(c)+'</td></tr>' for a,b,c in sections)
    contents=''.join(f'<li><a href="#{x["id"]}">{escape(x["title"])}</a></li>' for x in findings)
    svg=f'''<svg role="img" aria-label="Сравнение теплоотвода, кВт: прежняя формула 109, исправленная 86, сценарий B 358" viewBox="0 0 720 175"><g fill="currentColor" font-family="sans-serif" font-size="16"><text x="0" y="25">Прежняя формула</text><text x="0" y="80">Исправленная ε–NTU</text><text x="0" y="135">Прежний сценарий B</text></g><rect x="250" y="8" width="{old_cooling/1000}" height="27" fill="#dca852"/><rect x="250" y="63" width="{cooling/1000}" height="27" fill="#95cc65"/><rect x="250" y="118" width="358" height="27" fill="#db7272"/><g fill="currentColor" font-family="sans-serif" font-size="16"><text x="{260+old_cooling/1000}" y="28">{f(old_cooling/1000)} кВт</text><text x="{260+cooling/1000}" y="83">{f(cooling/1000)} кВт</text><text x="618" y="138">358 кВт</text></g></svg>'''
    body=f'''<span class="eyebrow">ПРОВЕРКА ПО ЛИТЕРАТУРЕ · 09.10.2026</span><h1>Паровой цикл: что подтверждается, что нужно пересчитать.</h1><p><a class="button secondary" href="literature-audit.json" download>Исходные данные и выводы JSON ↓</a> <a href="literature-audit.pdf">Отчёт PDF ↓</a></p><div class="status-note"><p>После проверки конструкцию нельзя считать готовой к сборке: теплоотвод, возврат горячего конденсата и работа реального цилиндра пока не согласованы. Исправлена формула охлаждения переходной модели; остальные найденные ограничения показаны явно.</p></div><p>Разобраны ключевые разделы предоставленного 152-страничного PDF. По ссылке БМСТУ доступны каталог и аннотации; полные учебники не получены. Поэтому выводы не выдаются за проверку по их недоступному тексту. Исторические проценты и габариты стационарных машин не перенесены в наш проект как паспортные значения.</p><p>Проверяемая исходная версия проекта: <code>{BASELINE[:12]}</code>. Координаты кузова и деталей не изменены. Числа ниже относятся к конкретно указанным режимам; сценарий B и сравнение при 50 кВт — разные условия.</p><h2>Главное ограничение — отвод теплоты</h2>{svg}<p>Две верхние строки: 1,2 бар abs, 104,78 °C, воздух 20 °C, расход 1,0829 м³/с, UA=2000 Вт/К. Нижняя строка — необходимый теплоотвод старого сценария B, а не возможность этого радиатора.</p><details><summary>Вывод формулы ε–NTU</summary><p>При постоянной температуре горячей стороны Tк: Cвозд dTвозд = (Tк − Tвозд) d(UA). Интегрирование даёт Tвых = Tк − (Tк − Tвх) exp(−UA/Cвозд). Тогда Q̇ = Cвозд(Tвых − Tвх). Это модель изотермической поверхности, без измеренной карты реального радиатора и влияния воздуха на паровой стороне.</p></details><ol>{contents}</ol>{cards}<h2>Как физически работает замкнутый контур</h2><p>Приёмник → питательный насос → генератор → перегреватель → впуск и расширение в цилиндрах → конденсатор → насос возврата и доохлаждение → приёмник. Движение создаётся перепадами давления и работой насосов; в цилиндре давление совершает работу над поршнем. При конденсации скрытая теплота фазового перехода передаётся воздуху, а вода возвращается. У топливных вариантов дымовой тракт — отдельный путь камеры сгорания; дым не должен попадать в воду или салон.</p><p>При прогреве вода и металл накапливают энергию, присутствует воздух, температуры узлов различаются. В установившемся режиме расход генератора и цилиндров, работа вала, возврат воды и теплоотвод должны одновременно согласоваться. Анимация объясняет направление, но расход и скорость жидкости нужно получать из расчёта, а не из скорости стрелок.</p><h2>Карта разобранных разделов книги</h2><div class="physics-table"><table><thead><tr><th>Раздел</th><th>Страницы PDF</th><th>Применение</th></tr></thead><tbody>{reading}</tbody></table></div><p>Нумерация здесь — страницы файла PDF. Обложка — PDF 1; печатная нумерация отличается. На обложке указан Фр. Барт; год не установлен. SHA-256 локального файла: <code class="digest">{book_sha or 'файл не найден при повторной сборке'}</code>. Сам PDF и полный OCR не опубликованы.</p><h2>Что проверено и что дальше</h2><p>Независимые значения свойств рассчитаны CoolProp {CoolProp.__version__} / IAPWS-95. Отдельные проверки охватывают конечное расширение, тепловую невязку сравнения и кинематику. Проверки симуляции после исправления отдельно оценивают сохранение воды/энергии, переходы и модельные остановы. Эти проверки не измеряют реальный КПД и не подтверждают прочность компонентов.</p><ol><li>Зафиксировать целевую полезную мощность и один согласованный набор давлений, температур, отсечки и расхода.</li><li>Подобрать двигатель с картой расхода/момента либо рассчитать p–V цикл с реальными размерами и клапанами.</li><li>Подобрать конденсатор, доохладитель и вентиляторы по картам, затем проверить их посадку в кузов.</li><li>Подобрать оба насоса с температурными пределами и проверкой всасывания; рассчитать газовую подушку и отделение воздуха.</li><li>Обновить реестр масс, все варианты источников тепла, трубопроводы, силовые крепления и динамические зазоры подвески.</li></ol><h2>Источники и доступность</h2><ol>{refs}</ol>'''
    style='<style>.source{color:var(--muted,#aab4bd);font-size:.9rem}.tag{font-weight:700}.digest{overflow-wrap:anywhere}section{margin:3rem 0}svg{width:100%;max-width:850px}code{white-space:normal}@media print{:root{color-scheme:light!important;background:white!important}html{background:white!important;color:#111!important}.status-note{display:block!important}.page-main h1{font-size:26pt}a[href="literature-audit.pdf"]{display:none!important}.site-header,.site-footer,.skip,.button{display:none!important}body,.page-main{background:white!important;color:#111!important;max-width:none!important;padding:0!important}.source{color:#444}.formula-card,.status-note{background:#f6f6f6!important;border:1px solid #aaa!important;color:#111!important}.formula-card{break-inside:avoid}a{color:#111}section{margin:1rem 0}h2{break-after:avoid}table{font-size:10pt}svg{max-height:140px}}</style>'
    template='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>@@TITLE@@</title><meta name="description" content="@@DESCRIPTION@@"><link rel="icon" href="favicon.svg"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="calculations.css"><link rel="stylesheet" href="systems.css">'+style+'</head><body>@@HEADER@@<main id="main" class="page-main">'+body+'</main>@@FOOTER@@</body></html>'
    (ROOT/'web/literature.html').write_text(template)
    standalone=template.replace('@@TITLE@@','Проверка парового ЗАЗ по литературе').replace('@@DESCRIPTION@@','Проверка физического смысла расчётов').replace('@@HEADER@@','').replace('@@FOOTER@@','')
    for sheet in ['style.css','calculations.css','systems.css']:
        standalone=standalone.replace('<link rel="stylesheet" href="'+sheet+'">','<style>'+(ROOT/'web'/sheet).read_text()+'</style>')
    (ROOT/'literature-audit.html').write_text(standalone)
    print(json.dumps(dict(findings=len(findings), corrected_cooling_kW=cooling/1000, missing_subcool_kW=subcool/1000, book_sha256=book_sha)))

if __name__ == '__main__':
    main()
