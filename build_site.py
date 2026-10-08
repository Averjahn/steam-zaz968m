"""Build the public project website into docs/ using only the Python standard library."""
from pathlib import Path
import csv
import json
import re
import shutil
import zipfile
from html import escape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'docs'
WEB = ROOT / 'web'
REPO = 'https://github.com/Averjahn/steam-zaz968m'
SITE = 'https://averjahn.github.io/steam-zaz968m/'


def fmt(n, places=0):
    return f'{n:,.{places}f}'.replace(',', '\u202f').replace('.', ',')


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / '.nojekyll').write_text('')
    for name in ['style.css', 'site.js', 'concept.svg', 'favicon.svg', 'assembly.css', 'assembly.js', 'calculations.css', 'calculations.js', 'calculation-model.js', 'calculation-render.js']:
        shutil.copy2(WEB / name, OUT / name)
    for name in ['models', 'vendor']:
        shutil.copytree(ROOT / name, OUT / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.mesh.json', '__pycache__'))
    data = json.loads((ROOT / 'results.json').read_text())
    sources = {r['key']: r for r in csv.DictReader((ROOT / 'sources.csv').open())}
    records = []
    drawings = {
        '01-layout': ('Общая компоновка', 'Три проекции и целевые габариты агрегатов.'),
        '02-process': ('Паровой контур', 'Генератор, машина, конденсатор и возврат воды.'),
        '03-controls': ('Управление и защита', 'Регулирование процесса и независимая защитная цепь.'),
        '04-dashboard': ('Приборная панель', 'Предложение органов управления и индикации.'),
        '05-vw-inspired': ('Архитектура по примеру VW', 'Генератор вместо заднего сиденья, наружный конденсатор.'),
    }
    titles = {
        'report.html': 'Полный отчёт в браузере', 'report.pdf': 'Расчётный отчёт с формулами и подстановками',
        'index.html': '3D-компоновка и калькулятор', 'START.txt': 'Как использовать комплект',
        'assembly.scad': 'Основная компоновка · OpenSCAD', 'assembly-vw-inspired.scad': 'Компоновка по примеру VW · OpenSCAD',
        'assembly.obj': 'Габаритная 3D-модель · OBJ', 'assembly.mtl': 'Материалы модели · MTL',
        'inputs.json': 'Исходные допущения', 'results.json': 'Полные результаты расчёта',
        'layout.json': 'Основная компоновка · координаты', 'layout-vw-inspired.json': 'Компоновка по примеру VW · координаты',
        'measurements.csv': 'Ведомость необходимых обмеров', 'scenario_summary.csv': 'Сравнение сценариев',
        'road_load.csv': 'Дорожная мощность и скорость', 'sensitivity.csv': 'Чувствительность расчёта',
        'sources.csv': 'Реестр источников', 'verification.json': 'Проверка расчётных балансов',
        'geometry-checks.json': 'Проверка габаритных пересечений', 'browser-checks.json': 'Проверка исходного интерфейса',
        'requirements.txt': 'Зависимости расчётных скриптов', 'calculate.py': 'Термодинамический и дорожный расчёт',
        'verify.py': 'Проверки расчётной модели', 'build_geometry.py': 'Генерация 3D и компоновочных чертежей',
        'build_diagrams.py': 'Генерация схем и панели', 'build_report.py': 'Генерация отчёта',
        'build_viewer.py': 'Генерация интерактивной модели', 'build_site.py': 'Сборка этого сайта',
        'build_cad_assets.py': 'Преобразование заводского CAD в GLB',
        'convert_cad.js': 'Триангуляция заводского STEP',
        'build_workbook.mjs': 'Сборка формул для PDF и отчёта',
        'verify_calculations.mjs': 'Сверка формул с Python',
        'calculation-workbook.html': 'Формулы A/B/C · автономная версия',
        'calculation-workbook.json': 'Подстановки A/B/C · JSON',
        'calculation-workbook.pdf': 'Формулы и подстановки A/B/C · PDF',
        'calculation-checks.json': 'Сверка формул с Python',
    }
    candidates = sorted(p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.html', '.pdf', '.json', '.csv', '.scad', '.obj', '.mtl', '.py', '.js', '.mjs', '.txt'})
    candidates += sorted((ROOT / 'drawings').iterdir())
    for p in candidates:
        rel = p.relative_to(ROOT)
        dest = Path('lab.html') if p.name == 'index.html' else rel
        target = OUT / dest
        target.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(p, target)
        if p.name == 'index.html':
            s = target.read_text().replace('<nav>', '<nav><a href="index.html">← Проект</a><a href="assembly.html">Сборка из CAD-файлов</a><a href="library.html">Все материалы</a>')
            # Reuse the actual interactive model, keeping its calculation unchanged.
            s = s.replace('</head>', '<link rel="icon" href="favicon.svg"><style>body{background:#0b1117}header,main{max-width:1280px}.card{border-radius:8px;background:#111b23;min-width:0}@media(max-width:950px){.grid{grid-template-columns:minmax(0,1fr)}}a{color:#b8ef68}button{border-radius:4px}select{max-width:100%;min-width:0}@media(max-width:600px){header,main{padding:18px}.card{padding:17px}}</style></head>')
            s = s.replace('populate();update();', "populate();update();const requestedScenario=new URLSearchParams(location.search).get('scenario');if(['A','B','C'].includes(requestedScenario)){el('scenario').value=String(['A','B','C'].indexOf(requestedScenario));el('scenario').dispatchEvent(new Event('input'));el('scenario').scrollIntoView({block:'center'});}")
            target.write_text(s)
        if p.name == 'report.html':
            s = target.read_text().replace('<body>', '<body><nav style="display:flex;gap:20px;flex-wrap:wrap"><a href="index.html">← Проект</a><a href="library.html">Все материалы</a><a href="report.pdf">Скачать PDF</a></nav>')
            s = s.replace('<body>', '<body><p><a href="calculations.html">Все формулы и подстановки →</a></p>')
            s = re.sub(r'<h2>(\d+)\.', lambda m: f'<h2 id="section-{m[1]}">{m[1]}.', s)
            target.write_text(s)
        if p.parent.name == 'drawings':
            category = 'Чертежи'
            base = p.stem if p.stem in drawings else '01-layout'
            title = drawings[base][0] + ' · ' + p.suffix[1:].upper()
        elif p.suffix in {'.scad', '.obj', '.mtl'} or p.name.startswith('layout'):
            category = '3D'
            title = titles.get(p.name, p.name)
        elif 'checks' in p.name or p.name == 'verification.json':
            category = 'Проверки'; title = titles.get(p.name, p.name)
        elif p.suffix in {'.py', '.js', '.mjs'} or p.name == 'requirements.txt':
            category = 'Исходники'; title = titles.get(p.name, p.name)
        elif p.suffix in {'.csv', '.json'}:
            category = 'Расчёты'; title = titles.get(p.name, p.name)
        else:
            category = 'Документы'; title = titles.get(p.name, p.name)
        records.append({'path': dest.as_posix(), 'title': title, 'category': category,
                        'format': p.suffix[1:].upper(), 'size': target.stat().st_size})

    header = '''<a class="skip" href="#main">К содержимому</a><header class="site-header"><a class="brand" href="index.html" aria-label="ЗАЗ-968М: главная"><span class="brand-icon">S</span><span>ЗАЗ<span class="brand-light"> / STEAM</span></span></a><nav aria-label="Главная навигация"><a href="index.html#concept">Концепция</a><a href="calculations.html">Расчёты</a><a href="assembly.html">3D-модель</a><a href="library.html">Материалы</a></nav><a class="header-link" href="''' + REPO + '''" target="_blank" rel="noopener">GitHub ↗</a></header>'''
    footer = '''<footer class="site-footer"><div><a class="brand" href="index.html">ЗАЗ / STEAM</a><p>Исследование парового привода для ЗАЗ-968М.</p></div><div><span>Версия 08.10.2026</span><a href="library.html">Библиотека материалов →</a><a href="''' + REPO + '''" target="_blank" rel="noopener">Исходники на GitHub ↗</a></div></footer>'''
    def page(template, title, desc, **values):
        text = (WEB / template).read_text()
        vals = {'HEADER': header, 'FOOTER': footer, 'TITLE': title, 'DESCRIPTION': desc, **values}
        for k, v in vals.items(): text = text.replace('@@' + k + '@@', str(v))
        if re.search(r'@@[A-Z_]+@@', text): raise ValueError('Unfilled template field')
        return text

    (OUT / 'calculations.html').write_text(page('calculations.html', 'Формулы и подстановки — ЗАЗ / STEAM', 'Формула, исходные данные, подстановка и результат для каждого расчёта.'))
    (OUT / 'assembly.html').write_text(page('assembly.html', 'CAD-сборка — ЗАЗ / STEAM',
        'Заводская модель насоса, импорт кузова и агрегатов, измерения и проверка пересечений поверхностей.'))
    for path, title, cat in [
        ('calculations.html', 'Формулы, подстановки и сверка компонентов', 'Расчёты'),
        ('assembly.html', 'CAD-сборка: реальные файлы и проверка поверхностей', '3D'),
        ('models/cat-5cp2120w.glb', 'Cat Pumps 5CP2120W · заводской CAD в GLB', '3D'),
        ('models/cat-5cp2120w.step', 'Cat Pumps 5CP2120W · исходный заводской STEP', '3D'),
        ('models/registry.json', 'Происхождение и точность моделей', 'Документы')]:
        p = OUT / path
        records.append({'path': path, 'title': title, 'category': cat, 'format': p.suffix[1:].upper(), 'size': p.stat().st_size})

    scenario_cards = []
    for s in data['scenarios']:
        c, r, m = s['case'], s['rated'], s['mass']
        label = {'A': 'Малая мощность', 'B': 'Умеренная мощность', 'C': 'Эквивалент 40 л.с.'}[c['id']]
        rub = '–'.join(fmt(x / 1e6, 1) for x in c['budget_RUB'])
        eur = '–'.join(fmt(x / 1000) for x in c['budget_EUR'])
        note = {'A': 'Небольшая мощность сохраняет проблему теплоотвода.', 'B': 'Остаток до 1200 кг — около 55 кг с одним водителем.', 'C': 'Превышение условной полной массы — 18,4 кг.'}[c['id']]
        scenario_cards.append(f'''<article class="scenario {'featured' if c['id']=='B' else ''}"><div class="scenario-top"><span class="letter">{c['id']}</span><span>{label}</span></div><div class="scenario-power">{fmt(c['net_drive_kW'],1).removesuffix(',0')}<span>кВт к КПП</span></div><p class="scenario-speed">{c['target_kmh']} км/ч · цель расчётного сценария</p><dl><div><dt>Режим пара</dt><dd>{c['p_bar_abs']} бар abs / {c['T_C']} °C</dd></div><div><dt>Масса с водителем</dt><dd>{fmt(m['running_mass_kg'])} кг</dd></div><div><dt>Теплоотвод на номинале</dt><dd>{fmt(r['condenser_kW'])} кВт</dd></div><div><dt>Топливо на номинале</dt><dd>{fmt(r['diesel_L_h'],1)} л/ч</dd></div></dl><div class="scenario-budget"><b>{rub} млн ₽</b><span>{eur} тыс. €</span></div><p class="scenario-note">{note}</p><a class="text-link" href="lab.html?scenario={c['id']}">Исследовать вариант →</a></article>''')
    sheet_cards = ''.join(f'''<a class="sheet" href="drawings/{k}.pdf"><div class="sheet-preview"><img src="drawings/{k}.svg" alt="{escape(v[0])}"></div><div class="sheet-description"><span class="eyebrow">ЛИСТ {k[:2]} / PDF</span><h3>{v[0]}</h3><p>{v[1]}</p></div><span class="sheet-arrow">↗</span></a>''' for k, v in drawings.items())
    source_items = ''.join(f'<li><a href="{escape(sources[k]["url"])}" target="_blank" rel="noopener">{escape(sources[k]["title"])} ↗</a></li>' for k in ['manual', 'iapws', 'fin', 'rus', 'vwvideo'] if k in sources)
    (OUT / 'index.html').write_text(page('index.html', 'ЗАЗ / STEAM — проект парового автомобиля', 'Расчёты, 3D-компоновка и чертежи парового привода ЗАЗ-968М. Открытый предварительный инженерный проект.', SCENARIOS=''.join(scenario_cards), SHEETS=sheet_cards, SOURCES=source_items, FORMULA_COUNT=sum(len(c['steps']) for c in json.loads((ROOT/'calculation-workbook.json').read_text()))))

    filters = ''.join(f'<button class="filter" data-category="{cat}" aria-pressed="false">{cat}</button>' for cat in ['Документы', 'Чертежи', '3D', 'Расчёты', 'Исходники', 'Проверки'])
    rows = []
    for r in records:
        size = fmt(r['size'] / 1024, 1) + ' КБ'
        download = r['format'] not in {'HTML', 'PDF', 'SVG'}
        rows.append(f'''<article class="file-row" data-category="{r['category']}" data-search="{escape(r['title']+' '+r['path']+' '+r['category'],quote=True)}"><span class="file-format">{r['format']}</span><div class="file-description"><a href="{r['path']}" {'download' if download else ''}>{escape(r['title'])}</a><span>{r['path']}</span></div><span class="file-category">{r['category']}</span><span class="file-size">{size}</span><a class="file-action" href="{r['path']}" download aria-label="Скачать {escape(r['title'],quote=True)}">↓</a></article>''')
    (OUT / 'library.html').write_text(page('library.html', 'Материалы — ЗАЗ / STEAM', 'Полная библиотека расчётов, чертежей, моделей и исходников проекта.', FILTERS=filters, FILES=''.join(rows), COUNT=len(records)))
    # Download bundle intentionally excludes dependency caches and research transcripts.
    with zipfile.ZipFile(OUT / 'project-materials.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in candidates: z.write(p, 'steam-zaz968m/' + p.relative_to(ROOT).as_posix())
        for p in sorted(WEB.iterdir()):
            if p.is_file(): z.write(p, 'steam-zaz968m/web/' + p.name)
        for dirname in ['models', 'vendor']:
            for p in sorted((ROOT / dirname).rglob('*')):
                if p.is_file() and not p.name.endswith('.mesh.json'):
                    z.write(p, 'steam-zaz968m/' + p.relative_to(ROOT).as_posix())
    (OUT / 'catalog.json').write_text(json.dumps(records, ensure_ascii=False, indent=2))
    (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + SITE + 'sitemap.xml\n')
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>2026-10-08</lastmod></url>' for p in ['', 'library.html', 'lab.html', 'assembly.html', 'calculations.html', 'report.html']) + '</urlset>')
    (OUT / '404.html').write_text(page('404.html', 'Страница не найдена — ЗАЗ / STEAM', 'Перейти к материалам проекта.'))
    print(f'Built {OUT}: {len(records)} catalog entries and a downloadable bundle.')


if __name__ == '__main__': main()
