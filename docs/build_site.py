"""Build the public workspace; NumPy fits its local document-search vectors."""
from pathlib import Path
import csv
import hashlib
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
    for name in ['engine-strength.js','engine-strength-model.js','shared-radial-model.js','shared-radial-geometry.js','camera-look.js','fitted-radial-view.js','fitted-installation.js','fitted-radial-geometry.js','compact-radial-model.js', 'compact-radial-geometry.js', 'compact-radial.js', 'aging-model.js', 'aging.js', 'aging.css', 'engine-sizing-model.js', 'engine-sizing.js', 'radial-engine-model.js', 'radial-engine.js', 'radial-engine.css', 'style.css', 'site.js', 'concept.svg', 'favicon.svg', 'assembly.css', 'assembly.js', 'component-purchases.js', 'procurement.js', 'assembly-systems.js', 'steam-simulation.js', 'wheel-loads.js', 'physics-page.js', 'systems.css', 'heat-geometry.js', 'cycle-animation.js', 'double-acting-cycle.js', 'crank-mechanism-model.js', 'crank-mechanism.js', 'double-acting-hardware.js', 'double-acting-view.js', 'piston-force-model.js', 'piston-force-view.js', 'piston-force-ui.js', 'steam-cloud-model.js', 'steam-cloud.js', 'double-acting.css', 'thermal-model.js', 'thermal-view.js', 'thermal-view.css', 'connection-data.js', 'pipe-joints.js', 'pipe-arrows.js', 'component-flow.js', 'viewer-fullscreen.js', 'heat-comparison.js', 'heat-page.js', 'internal-assembly.js', 'pipe-data.js', 'pipe-path.js', 'user-body-converter.js', 'packaging-audit.js', 'calculations.css', 'calculations.js', 'calculation-model.js', 'calculation-render.js']:
        shutil.copy2(WEB / name, OUT / name)
    purchase_digest=hashlib.sha256((ROOT/'component-purchases.json').read_bytes()).hexdigest()[:12]
    p=(OUT/'component-purchases.js').read_text().replace("'component-purchases.json'","'component-purchases.json?v="+purchase_digest+"'")
    (OUT/'component-purchases.js').write_text(p)
    component_digest=hashlib.sha256((OUT/'component-purchases.js').read_bytes()).hexdigest()[:12]
    for module in ['assembly.js','procurement.js']:
        p=(OUT/module).read_text().replace("'./component-purchases.js'","'./component-purchases.js?v="+component_digest+"'")
        (OUT/module).write_text(p)
    # Version system data and transitive modules together for existing visitors.
    for module in ['compact-radial.js','aging.js','assembly-systems.js','physics-page.js','heat-page.js','engine-sizing.js','radial-engine.js']:
        p=(OUT/module).read_text()
        for asset in ['fitted-engine-fit.json','compact-radial-fit.json','aging-study.json','simulation-data.json','pipe-engineering.json','internal-fit-audit.json','heat-fit-audit.json','engine-sizing.json','radial-engine-spec.json']:
            version=hashlib.sha256((ROOT/asset).read_bytes()).hexdigest()[:12]
            p=p.replace("'"+asset+"'","'"+asset+"?v="+version+"'")
        (OUT/module).write_text(p)
    for module,dependencies in [('compact-radial-model.js',['radial-engine-model.js']),('aging.js',['aging-model.js']),('engine-sizing-model.js',['radial-engine-model.js']),('engine-sizing.js',['engine-sizing-model.js']),('radial-engine.js',['radial-engine-model.js','pipe-path.js','pipe-arrows.js']),('pipe-joints.js',['connection-data.js','pipe-path.js']),('crank-mechanism-model.js',['double-acting-cycle.js']),('crank-mechanism.js',['double-acting-cycle.js','crank-mechanism-model.js']),('double-acting-hardware.js',['pipe-joints.js','double-acting-cycle.js']),('fitted-installation.js',['connection-data.js','pipe-data.js','pipe-path.js','pipe-joints.js']),('fitted-radial-geometry.js',['compact-radial-model.js','pipe-path.js','pipe-joints.js','pipe-arrows.js']),('shared-radial-geometry.js',['shared-radial-model.js','compact-radial-model.js','pipe-path.js','pipe-joints.js','pipe-arrows.js']),('internal-assembly.js',['shared-radial-geometry.js','fitted-radial-geometry.js','fitted-installation.js','pipe-data.js','pipe-path.js','pipe-joints.js','connection-data.js','double-acting-hardware.js','double-acting-cycle.js','crank-mechanism.js']),('thermal-view.js',['thermal-model.js']),('steam-cloud-model.js',['double-acting-cycle.js']),('steam-cloud.js',['steam-cloud-model.js','double-acting-cycle.js']),('piston-force-model.js',['double-acting-cycle.js']),('piston-force-view.js',['double-acting-cycle.js','piston-force-model.js']),('double-acting-view.js',['piston-force-view.js','pipe-arrows.js','double-acting-cycle.js','thermal-model.js','steam-cloud.js','crank-mechanism.js']),('fitted-radial-view.js',['thermal-model.js']),('cycle-animation.js',['shared-radial-model.js','shared-radial-geometry.js','camera-look.js','fitted-radial-view.js','double-acting-view.js','thermal-model.js']),('heat-geometry.js',['pipe-path.js','pipe-joints.js','connection-data.js','internal-assembly.js']),('heat-page.js',['heat-comparison.js','steam-simulation.js']),('assembly-systems.js',['piston-force-ui.js','thermal-view.js','double-acting-cycle.js','steam-simulation.js','pipe-path.js','pipe-joints.js','pipe-arrows.js','component-flow.js','cycle-animation.js','heat-comparison.js']),('physics-page.js',['wheel-loads.js']),('compact-radial-geometry.js',['compact-radial-model.js','pipe-path.js','pipe-joints.js','pipe-arrows.js']),('compact-radial.js',['compact-radial-geometry.js','compact-radial-model.js','packaging-audit.js']),('assembly.js',['shared-radial-model.js','shared-radial-geometry.js','camera-look.js','assembly-systems.js','heat-geometry.js','pipe-joints.js','internal-assembly.js','packaging-audit.js','viewer-fullscreen.js'])]:
        p=(OUT/module).read_text()
        for asset in dependencies:
            version=hashlib.sha256((OUT/asset).read_bytes()).hexdigest()[:12]
            p=p.replace("'./"+asset+"'","'./"+asset+"?v="+version+"'")
        (OUT/module).write_text(p)
    s=(OUT/'assembly.js').read_text()
    for path in ['layout-internal.json','layout-fitted.json','layout-geared.json']:
        version=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()[:12]
        s=s.replace("'"+path+"'","'"+path+"?v="+version+"'")
    registry_digest=hashlib.sha256((ROOT/'models/registry.json').read_bytes()).hexdigest()[:12]
    s=s.replace("'models/registry.json'","'models/registry.json?v="+registry_digest+"'")
    (OUT/'assembly.js').write_text(s)
    # Version transitive imports as well as the entry script for existing visitors.
    for name in ['calculation-render.js','calculations.js']:
        text=(OUT/name).read_text()
        for dependency in ['calculation-model.js','calculation-render.js']:
            if dependency==name: continue
            digest=hashlib.sha256((OUT/dependency).read_bytes()).hexdigest()[:12]
            text=text.replace("'./"+dependency+"'", "'./"+dependency+'?v='+digest+"'")
        (OUT/name).write_text(text)
    for name in ['models', 'vendor']:
        shutil.copytree(ROOT / name, OUT / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.mesh.json', '__pycache__'))
    data = json.loads((ROOT / 'results.json').read_text())
    sources = {r['key']: r for r in csv.DictReader((ROOT / 'sources.csv').open())}
    records = []
    drawings = {
        '11-fitted-radial': ('Звезда по свободному месту в кузове', 'Семь Ø40 × 45, проверенная сетка и размерная схема; не изготовительный чертёж.'),
        '09-radial-engine': ('Семицилиндровая паровая звезда', 'Размерный эскиз сверху, ход, диаметры, объём и резерв; не чертёж для изготовления.'),
        '01-layout': ('Общая компоновка', 'Три проекции и целевые габариты агрегатов.'),
        '02-process': ('Паровой контур', 'Генератор, машина, конденсатор и возврат воды.'),
        '03-controls': ('Управление и защита', 'Регулирование процесса и независимая защитная цепь.'),
        '04-dashboard': ('Приборная панель', 'Предложение органов управления и индикации.'),
        '08-pipe-routing': ('Трубопроводы с изоляцией', 'Проекции и таблица ID/OD, полного диаметра, радиусов, скоростей и теплопотерь; концепт.'),
        '08-section-pipe_steam': ('Поперечный разрез свежего пара', 'ID40 / OD48 + аэрогель30 + кожух0,6 мм.'),
        '08-section-pipe_flue': ('Поперечный разрез дымового канала', 'Компактный дизель: ID80 / OD82 + аэрогель35 + кожух0,6 мм.'),
        '07-internal-assembly': ('Внутренняя детальная сборка', 'Резервные габариты в трёх проекциях; не чертёж для изготовления.'),
        '06-revised-layout': ('Переработанная компоновка', 'Два места, отдельная горелка, наружный конденсатор и координаты.'),
        '05-vw-inspired': ('Архитектура по примеру VW', 'Генератор вместо заднего сиденья, наружный конденсатор.'),
    }
    titles = {
        'engine-strength-study.json':'Увеличение цилиндров · силы, инерция и прочностной экран',
        'engine-bore-fit.json':'Диаметр отдельно от хода · аудит геометрии и труб',
        'engine-strength-report.pdf':'Увеличение цилиндров и прочность · расчёт PDF',
        'engine-strength-checks.json':'Прочностной расчёт · независимые проверки равновесия и формул',
        'build_engine_strength.mjs':'Воспроизводимый расчёт увеличения цилиндров и прочности',
        'fitted-engine-study.json':'Звезда по кузову · объём, обороты, мощность и ограничения охлаждения',
        'fitted-engine-fit.json':'Звезда по кузову · аудит полной сборки и контактов пола',
        'fitted-engine-screen.json':'Сравнение размеров звезды в кузове с дизельным каналом',
        'layout-fitted.json':'Основная сборка · семицилиндровый двигатель по свободному месту',
        'build_fitted_engine.mjs':'Воспроизводимый расчёт звезды по свободному месту',
        'compact-radial-fit.json': 'Компактная звезда · пересечения кузова, подвески и опоры',
        'compact-radial-checks.json': 'Компактная звезда · кинематика, габариты, порты и браузер',
        'aging-study.json': 'Металл за два года · девять сценариев, циклы, стенки и зима',
        'aging-checks.json': 'Проверки модели старения · физика, границы и интерфейс',
        'aging-fatigue-template.json': 'Шаблон испытательной кривой S–N · без придуманных точек',
        'engine-sizing.json': 'Подбор двигателя под место · объём, мощность и охлаждение',
        'engine-sizing-checks.json': 'Подбор двигателя · геометрия, масса, энергия и пределы расчёта',
        'radial-engine-spec.json': 'Семицилиндровая звезда · размеры, объём и потребность в паре',
        'radial-engine-checks.json': 'Семь кривошипов · ходы, фазы, передача, объёмы и браузер',
        'workspace_ui.py': 'Генератор общего интерфейса, тем и навигации',
        'build_knowledge.py': 'Воспроизводимый векторный индекс материалов · TF-IDF / LSA',
        'verify_knowledge.mjs': 'Проверка векторного поиска, источников и типовых вопросов',
        'knowledge-checks.json': 'База знаний · релевантность, контрольные суммы и границы поиска',
        'workspace-checks.json': 'Редизайн · темы, мобильная навигация, панели и регрессия 3D',
        'piston-force-checks.json': 'Силы на поршнях · давления, ускорения, баланс и стрелки',
        'crank-mechanism-checks.json': 'Коленвал и крейцкопф · полный оборот, пересечения и сопряжение',
        'steam-cloud-checks.json': 'Анимация пара · границы камер, пауза, клапаны и 3D',
        'double-acting-checks.json': 'Двойное действие · камеры, переключение клапанов и обратимые стрелки',
        'thermal-reference.json': 'Белов · изученные разделы и границы теплового расчёта',
        'thermal-validation-data.json': 'Независимые контрольные состояния воды и пара · CoolProp',
        'verify_thermal_view.mjs': 'Проверки тепловых профилей и показанных энергетических балансов',
        'thermal-view-checks.json': 'Тепловые профили · проверки по балансу энтальпии и таблицам воды',
        'thermal-flicker-checks.json': 'Температурная карта · стабильность кадров и восстановление материалов',
        'thermal-presentation-checks.json': 'Отдельные компоненты, жидкости, тепловая карта и прежние режимы · проверки браузера',
        'double-acting-view-checks.json': 'Двойное действие · проверки 3D, стрелок и полноэкранного режима',
        'verify_double_acting.mjs': 'Проверка геометрии и переключения рабочих камер',
        'literature-audit.html': 'Проверка по книге Фр. Барта и источникам · полный отчёт',
        'literature-audit.pdf': 'Проверка парового цикла по литературе · PDF',
        'literature-audit.json': 'Независимый расчёт и 10 выводов проверки по литературе',
        'literature-checks.json': 'Проверки теплообмена и независимых физических оценок',
        'audit_literature.py': 'Воспроизводимая проверка физических оценок по литературе',
        'verify_literature.mjs': 'Сверка переходной модели с независимым расчётом',
        'viewer-checks.json': 'Все стрелки, расчётный поток и полноэкранный просмотр · проверки',
        'connection-specs.json': 'Патрубки, оси, проходные диаметры и варианты подключения',
        'connection-checks.json': 'Проверка геометрии стыков и переключения нагревателей',
        'build_connection_specs.py': 'Воспроизводимый реестр патрубков и трасс',
        'pipe-arrow-checks.json': 'Стрелки на трубах · видимость, анимация и срезы',
        'heat-sources.json':'Параметры пяти источников тепла и первичные документы','heat-fit-audit.json':'Пересечения пяти вариантов источника','heat-browser-checks.json':'Анимации, выбор источника и браузерные проверки','heat-comparison-results.json':'Сравнение расходов и общего КПД','build_heat_sources.py':'Генератор источников тепла и масс труб','simulation-checks.json': 'Проверка балансов, остановов и четырёх колёс', 'verify_simulation.mjs': 'Проверка физической исследовательской модели', 'simulation-data.json': 'Свойства воды, гипотезы симуляции и массы', 'build_simulation_data.py': 'Генератор свойств IAPWS-95 и физических описаний',
        'component-purchases.json': 'Комплектующие · ссылки на покупку и материалы', 'build_procurement.py': 'Генератор реестра комплектующих',
        'report.html': 'Полный отчёт в браузере', 'report.pdf': 'Расчётный отчёт с формулами и подстановками',
        'index.html': '3D-компоновка и калькулятор', 'START.txt': 'Как использовать комплект',
        'assembly.scad': 'Основная компоновка · OpenSCAD', 'assembly-vw-inspired.scad': 'Компоновка по примеру VW · OpenSCAD',
        'assembly.obj': 'Габаритная 3D-модель · OBJ', 'assembly.mtl': 'Материалы модели · MTL',
        'inputs.json': 'Исходные допущения', 'results.json': 'Полные результаты расчёта',
        'pipe-routes-input.json': 'Исходные точки трасс · мм', 'pipe-engineering.json': 'Трубопроводы · поток, изгибы и тепловой экран', 'build_pipe_engineering.py': 'Воспроизводимый расчёт труб и изоляции', 'build_pipe_materials.py': 'Формулы, сечения и трубопроводный чертёж', 'build_internal_assets.mjs': 'Экспорт полной детальной сборки GLB', 'build_internal_materials.py': 'Материалы внутренней компоновки', 'build_mount_register.py': 'Контакт опор с игровым полом', 'layout-internal.json': 'Внутренняя детальная сборка · координаты и допущения', 'internal-feasibility.json': 'Внутренняя сборка · тепловая проверка и формулы', 'internal-fit-audit.json': 'Внутренняя сборка · пересечения показанной геометрии', 'layout-revised.json': 'Переработанная компоновка · координаты', 'packaging-audit.json': 'Пересечения и зазоры · сравнение трёх компоновок', 'build_packaging_sheet.py': 'Компоновочный чертёж переработанного варианта',
        'layout.json': 'Основная компоновка · координаты', 'layout-vw-inspired.json': 'Компоновка по примеру VW · координаты',
        'measurements.csv': 'Ведомость необходимых обмеров', 'scenario_summary.csv': 'Сравнение сценариев',
        'road_load.csv': 'Дорожная мощность и скорость', 'sensitivity.csv': 'Чувствительность расчёта',
        'sources.csv': 'Реестр источников', 'verification.json': 'Проверка расчётных балансов',
        'geometry-checks.json': 'Проверка габаритных пересечений', 'browser-checks.json': 'Проверка исходного интерфейса',
        'requirements.txt': 'Зависимости расчётных скриптов', 'calculate.py': 'Термодинамический и дорожный расчёт',
        'verify.py': 'Проверки расчётной модели', 'build_geometry.py': 'Генерация 3D и компоновочных чертежей',
        'build_diagrams.py': 'Генерация схем и панели', 'build_report.py': 'Генерация отчёта',
        'build_viewer.py': 'Генерация интерактивной модели', 'build_site.py': 'Сборка этого сайта',
        'build_user_body.py': 'Преобразование пользовательского архива FBX/ZIP',
        'build_user_body.mjs': 'Преобразование предоставленного FBX в GLB',
        'build_stock_suspension.py': 'Генератор штатной подвески · предварительная геометрия',
        'build_reconstruction.py': 'Генератор кузова по фотографиям',
        'build_cad_assets.py': 'Преобразование заводского CAD в GLB',
        'convert_cad.js': 'Триангуляция заводского STEP',
        'build_workbook.mjs': 'Сборка формул для PDF и отчёта',
        'verify_calculations.mjs': 'Сверка формул с Python',
        'calculation-workbook.html': 'Формулы A/B/C · автономная версия',
        'calculation-workbook.json': 'Подстановки A/B/C · JSON',
        'calculation-workbook.pdf': 'Формулы и подстановки A/B/C · PDF',
        'calculation-checks.json': 'Сверка формул с Python',
        'physics-audit.json': 'Физический аудит: обороты и паспортные ограничения',
        'build_physics_audit.mjs': 'Формирование физического аудита',
    }
    candidates = sorted(p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.html', '.pdf', '.json', '.csv', '.scad', '.obj', '.mtl', '.py', '.js', '.mjs', '.cjs', '.txt'})
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
        elif p.suffix in {'.py', '.js', '.mjs', '.cjs'} or p.name == 'requirements.txt':
            category = 'Исходники'; title = titles.get(p.name, p.name)
        elif p.suffix in {'.csv', '.json'}:
            category = 'Расчёты'; title = titles.get(p.name, p.name)
        else:
            category = 'Документы'; title = titles.get(p.name, p.name)
        records.append({'path': dest.as_posix(), 'title': title, 'category': category,
                        'format': p.suffix[1:].upper(), 'size': target.stat().st_size})

    header = '''<a class="skip" href="#main">К содержимому</a><header class="site-header"><a class="brand" href="index.html" aria-label="ЗАЗ-968М: главная"><span class="brand-icon">S</span><span>ЗАЗ<span class="brand-light"> / STEAM</span></span></a><nav aria-label="Главная навигация"><a href="index.html#concept">Концепция</a><a href="calculations.html">Расчёты</a><a href="assembly.html">3D-модель</a><a href="heat.html">Источники тепла</a><a href="physics.html">Физика узлов</a><a href="library.html">Материалы</a></nav><a class="header-link" href="''' + REPO + '''" target="_blank" rel="noopener">GitHub ↗</a></header>'''
    footer = '''<footer class="site-footer"><div><a class="brand" href="index.html">ЗАЗ / STEAM</a><p>Исследование парового привода для ЗАЗ-968М.</p></div><div><span>Версия 10.10.2026</span><a href="literature.html">Проверка по литературе →</a><a href="library.html">Библиотека материалов →</a><a href="''' + REPO + '''" target="_blank" rel="noopener">Исходники на GitHub ↗</a></div></footer>'''
    def page(template, title, desc, **values):
        text = (WEB / template).read_text()
        vals = {'HEADER': header, 'FOOTER': footer, 'TITLE': title, 'DESCRIPTION': desc, **values}
        for k, v in vals.items(): text = text.replace('@@' + k + '@@', str(v))
        if re.search(r'@@[A-Z_]+@@', text): raise ValueError('Unfilled template field')
        # Existing visitors must receive JS matching the new controls after deployment.
        for asset in ['engine-strength.js','engine-strength-model.js','shared-radial-model.js','shared-radial-geometry.js','camera-look.js','fitted-radial-view.js','fitted-installation.js','fitted-radial-geometry.js','compact-radial-model.js', 'compact-radial-geometry.js', 'compact-radial.js', 'aging-model.js', 'aging.js', 'aging.css', 'engine-sizing-model.js', 'engine-sizing.js', 'radial-engine-model.js', 'radial-engine.js', 'radial-engine.css', 'style.css', 'site.js', 'assembly.css', 'assembly.js', 'component-purchases.js', 'procurement.js', 'assembly-systems.js', 'steam-simulation.js', 'wheel-loads.js', 'physics-page.js', 'systems.css', 'heat-geometry.js', 'cycle-animation.js', 'double-acting-cycle.js', 'crank-mechanism-model.js', 'crank-mechanism.js', 'double-acting-hardware.js', 'double-acting-view.js', 'piston-force-model.js', 'piston-force-view.js', 'piston-force-ui.js', 'steam-cloud-model.js', 'steam-cloud.js', 'double-acting.css', 'thermal-model.js', 'thermal-view.js', 'thermal-view.css', 'connection-data.js', 'pipe-joints.js', 'pipe-arrows.js', 'component-flow.js', 'viewer-fullscreen.js', 'heat-comparison.js', 'heat-page.js', 'internal-assembly.js', 'pipe-data.js', 'pipe-path.js', 'user-body-converter.js', 'packaging-audit.js', 'calculations.css', 'calculations.js']:
            digest = hashlib.sha256((OUT / asset).read_bytes()).hexdigest()[:12]
            text = text.replace('href="'+asset+'"', 'href="'+asset+'?v='+digest+'"').replace('src="'+asset+'"', 'src="'+asset+'?v='+digest+'"')
        return text

    from engine_strength_page import content as strength_content
    strength=json.loads((ROOT/'engine-strength-study.json').read_text())
    (OUT/'engine-strength.html').write_text(page('engine-strength.html','Увеличение цилиндров и прочность — ЗАЗ / STEAM','Независимый подбор диаметра при ходе45 мм, силы пара, инерция, шатуны, пальцы, вал и границы прочности.',STRENGTH_CONTENT=strength_content(strength)))
    from fitted_engine_page import content as fitted_content
    fitted=json.loads((ROOT/'fitted-engine-study.json').read_text())
    fitted_fit=json.loads((ROOT/'fitted-engine-fit.json').read_text())
    (OUT/'fitted-engine.html').write_text(page('fitted-engine.html','Семь цилиндров под кузов — ЗАЗ / STEAM','Выбор Ø40 × 45 по кузову, подвеске, соседям и газовому каналу; объём, обороты и полезная мощность.',FITTED_CONTENT=fitted_content(fitted,fitted_fit)))
    compact_fit=json.loads((ROOT/'compact-radial-fit.json').read_text())
    fit_summary=compact_fit.get('publication_summary','Двигатель построен; проверка посадки ожидается.')
    (OUT/'compact-radial.html').write_text(page('compact-radial.html','Компактная паровая звезда внутри ЗАЗ — ЗАЗ / STEAM','Семь цилиндров Ø32 × 36 мм: полная геометрия, коллекторы, изоляция, опоры и проверка внутри кузова.',COMPACT_FIT=escape(fit_summary)))
    from aging_page import aging_page_values
    aging=json.loads((ROOT/'aging-study.json').read_text())
    (OUT/'aging.html').write_text(page('aging.html','Старение металла за два года — ЗАЗ / STEAM','730 дней, 50 км в день, −25…+35 °C: циклы, коррозия, напряжения и зимняя стоянка.',**aging_page_values(aging)))
    from engine_sizing_page import sizing_page_values
    sizing=json.loads((ROOT/'engine-sizing.json').read_text())
    (OUT/'engine-sizing.html').write_text(page('engine-sizing.html','Объём и мощность под место в ЗАЗ — ЗАЗ / STEAM','Подбор семицилиндровой звезды под размерный резерв, пар, мощность, охлаждение и пределы установки.',**sizing_page_values(sizing)))
    (OUT / 'radial-engine.html').write_text(page('radial-engine.html','Семицилиндровая паровая звезда — ЗАЗ / STEAM','Рабочий объём, семь горизонтальных цилиндров, фазированная кинематика, расход пара и габариты.'))
    (OUT / 'heat.html').write_text(page('heat.html','Источники тепла и замкнутый цикл — ЗАЗ / STEAM','Дизель, дрова, пеллеты, газ и электричество: физические формулы и сравнительные симуляции.'))
    (OUT / 'physics.html').write_text(page('physics.html','Физика узлов и нагрузка на четыре колеса — ЗАЗ / STEAM','Законы узлов, переходные процессы, распределение веса и нагрузки рычагов.'))
    (OUT / 'literature.html').write_text(page('literature.html','Проверка парового цикла по литературе — ЗАЗ / STEAM','Разбор книги Фр. Барта, независимые физические оценки и найденные ограничения проекта.'))
    (OUT / 'procurement.html').write_text(page('procurement.html','Комплектующие и материалы — ЗАЗ / STEAM','Товары, материалы, каталоги и изготовители для 32 узлов внутренней сборки.'))
    (OUT / 'calculations.html').write_text(page('calculations.html', 'Формулы и подстановки — ЗАЗ / STEAM', 'Формула, исходные данные, подстановка и результат для каждого расчёта.'))
    (OUT / 'assembly.html').write_text(page('assembly.html', 'CAD-сборка — ЗАЗ / STEAM',
        'Заводская модель насоса, импорт кузова и агрегатов, измерения и проверка пересечений поверхностей.'))
    reconstruction=json.loads((ROOT/'models/zaz-968m-reconstruction.json').read_text())
    names={'length':'Длина','width':'Ширина','height':'Высота сцены','loaded_height_documented':'Высота с нагрузкой','wheelbase':'Колёсная база','front_track':'Передняя колея','rear_track':'Задняя колея','front_axle_x':'Передняя ось X','tyre_radius':'Радиус колеса','arch_radius':'Радиус арки','cabin_floor_z':'Пол салона Z','rear_bulkhead_x':'Задняя перегородка X','wheelhouse_inner_y':'Внутренняя ниша |Y|'}
    kinds={'documented':'Документация','project_reference':'Габарит проекта','photo_estimate':'Оценка по фото','project_assumption':'Допущение проекта','internal_hypothesis':'Внутренняя гипотеза'}
    dimension_rows=''.join('<tr><td>'+names[k]+'</td><td>'+fmt(v['value'])+'</td><td>'+kinds[v['kind']]+'</td><td>'+escape(v['note'])+'</td></tr>' for k,v in reconstruction['parameters_mm'].items())
    photos=''.join('<figure><img loading="lazy" src="models/'+r['file']+'" alt="'+escape(r['notes'],quote=True)+'"><figcaption>'+escape(r['notes'])+'<br>'+escape(r['author'])+' · <a href="'+r['license_url']+'">'+escape(r['license'])+'</a><br><a href="'+r['source']+'" target="_blank" rel="noopener">Страница автора и оригинал ↗</a></figcaption></figure>' for r in reconstruction['references'])
    registration=reconstruction['photo_registration']
    (OUT/'reconstruction.html').write_text(page('reconstruction.html','Кузов по фотографиям — ЗАЗ / STEAM','Параметрическая реконструкция ЗАЗ-968М: модель, фотографии, происхождение размеров и ограничения точности.',PARAMETER_ROWS=dimension_rows,PHOTOS=photos,SIDE_SOURCE=reconstruction['references'][0]['source'],SCALE_SUBSTITUTION=registration['substitution'],OVERHANG=registration['projected_front_overhang_mm'],PHOTO_LENGTH=registration['projected_length_mm']))
    user_model=json.loads((ROOT/'models/zaz-968m-yatloo.json').read_text())
    user_audit=json.loads((ROOT/'user-body-audit.json').read_text())
    user_conflicts=''.join('<tr><td>'+escape(p['id']+' · '+p['name'])+'</td><td>'+escape(', '.join(p['body_intersections']).replace('_',' '))+'</td></tr>' for p in user_audit.get('cases',{}).get('revised',{}).get('parts',[]) if p['body_intersections'])
    (OUT/'piping.html').write_text(page('piping.html','Трубопроводы — ЗАЗ / STEAM','Диаметры, изоляция, отводы, скорости и условные потери.'))
    (OUT/'internal.html').write_text(page('internal.html','Внутренняя паровая сборка — ЗАЗ / STEAM','Детальная внутренняя сборка: двигатель, конденсаторы, трубопроводы, опоры и проверка теплоотвода.'))
    (OUT/'user-model.html').write_text(page('user-model.html','Ваша модель ЗАЗ-968М — ЗАЗ / STEAM','Модель yatloo из предоставленного FBX, масштаб по базе, внутренние панели и проверка пересечений.',USER_SCALE=user_model['registration']['substitution'],USER_DIMENSIONS=' × '.join(fmt(v) for v in user_model['size_mm']),USER_CONFLICT_ROWS=user_conflicts))
    packing=json.loads((ROOT/'packaging-audit.json').read_text())
    revised=json.loads((ROOT/'layout-revised.json').read_text())
    comparison_rows=''.join('<tr><td>'+label+'</td><td>'+(', '.join(packing['cases'][key]['summary']['body_conflicts']) or 'Нет')+'</td><td>'+(', '.join(' / '.join(pair) for pair in packing['cases'][key]['summary']['unplanned_envelope_overlaps']) or 'Нет')+'</td><td>'+(', '.join(packing['cases'][key]['summary']['stock_conflicts']) or 'Нет')+'</td></tr>' for key,label in [('original','Исходный задний блок'),('vw','Прежний крупный блок по примеру VW'),('revised','Переработанный вариант')])
    actual={p['id']:p for p in packing['cases']['revised']['parts']}
    packing_parts=[*revised['parts'],{'id':'PMP','name':'Cat Pumps 5CP2120W','xyz':revised['pump_xyz'],'size':[259.25,254,146.2],'role':'Заводской CAD перенесён над водяным баком. Мотор, кронштейн и фитинги требуют места.'}]
    placement_rows=''.join('<tr><td>'+p['id']+' · '+escape(p['name'])+'</td><td>'+' × '.join(fmt(v,2).removesuffix(',00') for v in p['size'])+'</td><td>'+' × '.join(fmt(v,1).removesuffix(',0') for v in actual[p['id']]['size_mm'])+'</td><td>'+' / '.join(fmt(v,0) for v in actual[p['id']]['min_xyz_mm'])+'</td><td>'+escape(p['role'])+'</td></tr>' for p in packing_parts)
    (OUT/'packaging.html').write_text(page('packaging.html','Переработанная компоновка — ЗАЗ / STEAM','Округлый кузов, новая расстановка агрегатов, проверка пересечений и компоновочный чертёж.',USER_CONFLICT_ROWS=user_conflicts,COMPARISON_ROWS=comparison_rows,PLACEMENT_ROWS=placement_rows,OPEN_ISSUES=''.join('<li>'+escape(t)+'</li>' for t in revised['open_issues'])))
    for path, title, cat in [
        ('engine-strength.html', 'Увеличение цилиндров и прочность механизма', 'Расчёты'),
        ('fitted-engine.html', 'Семицилиндровый двигатель по свободному месту', '3D'),
        ('compact-radial.html', 'Компактная семицилиндровая звезда в кузове', '3D'),
        ('aging.html', 'Металл за два года · 50 км/день, мороз и тепло', 'Расчёты'),
        ('engine-sizing.html', 'Объём и мощность под место в автомобиле', 'Расчёты'),
        ('radial-engine.html', 'Семицилиндровая звезда · объём и 3D-механизм', '3D'),
        ('calculations.html', 'Формулы, подстановки и сверка компонентов', 'Расчёты'),
        ('assembly.html', '3D-сборка: реконструкция кузова и агрегаты', '3D'),
        ('user-model.html', 'Ваша модель · масштаб, панели и конфликты', 'Документы'),
        ('packaging.html', 'Новая расстановка · зазоры и открытые вопросы', '3D'),
        ('reconstruction.html', 'Кузов по фотографиям: источники и точность', 'Документы'),
        ('models/zaz-968m-reconstructed.glb', 'ЗАЗ-968М · приближённая реконструкция GLB', '3D'),
        ('models/zaz-968m-reconstructed.obj', 'ЗАЗ-968М · приближённая реконструкция OBJ', '3D'),
        ('models/zaz-968m-reconstructed.mtl', 'ЗАЗ-968М · материалы реконструкции', '3D'),
        ('models/zaz-968m-reconstruction.json', 'Реконструкция · параметры и источники', 'Документы'),
        ('models/reconstruction-dimensions.csv', 'Реконструкция · ведомость размеров', 'Документы'),
        ('models/reconstruction-checks.json', 'Реконструкция · проверка построенной сетки', 'Проверки'),
        ('models/reconstruction-browser-checks.json', 'Реконструкция · проверки интерфейса и импорта', 'Проверки'),
        ('models/references/ATTRIBUTION.txt', 'Фотографии кузова · авторы и лицензии', 'Документы'),
        ('models/cat-5cp2120w.glb', 'Cat Pumps 5CP2120W · заводской CAD в GLB', '3D'),
        ('models/cat-5cp2120w.step', 'Cat Pumps 5CP2120W · исходный заводской STEP', '3D'),
        ('models/stock-suspension.glb', 'Штатная подвеска · гипотеза GLB', '3D'),
        ('models/stock-suspension.obj', 'Штатная подвеска · гипотеза OBJ', '3D'),
        ('models/stock-suspension.mtl', 'Материалы подвески', '3D'),
        ('models/stock-suspension.json', 'Подвеска · источники и допущения', 'Документы'),
        ('models/stock-suspension-checks.json', 'Подвеска · проверка сетки', 'Проверки'),
        ('models/zaz-968m-yatloo.glb', 'Ваша модель ЗАЗ-968М / yatloo · GLB', '3D'),
        ('models/user-model-checks.json', 'Ваша модель · проверка геометрии и привязки', 'Проверки'),
        ('models/user-model-browser-checks.json', 'Ваша модель · проверки интерфейса и экспорта', 'Проверки'),
        ('models/zaz-968m-yatloo.json', 'Ваша модель · привязка и ограничения', 'Документы'),
        ('user-body-audit.json', 'Ваша модель · проверка трёх компоновок', 'Проверки'),
        ('heat.html', 'Источники тепла · пять вариантов, расход и КПД', 'Расчёты'),
        ('physics.html', 'Физика узлов · массы, рычаги и четыре колеса', 'Расчёты'),
        ('literature.html', 'Проверка по литературе · формулы и ограничения цикла', 'Расчёты'),
        ('procurement.html', 'Комплектующие · покупка и изготовление', 'Документы'),
        ('piping.html', 'Трубопроводы · формулы, диаметры и изоляция', 'Документы'),
        ('internal.html', 'Внутренняя сборка · детали, крепления и тепловые ограничения', '3D'),
        ('models/steam-internal-assembly.glb', 'Полная внутренняя детальная сборка GLB', '3D'),
        ('models/steam-internal-assembly.json', 'Внутренняя сборка · детали и габариты', 'Документы'),
        ('models/pipe-engineering-checks.json', 'Проверки теплового баланса, расходов и диаметров', 'Проверки'),
        ('models/internal-browser-checks.json', 'Внутренняя сборка · проверки интерфейса и геометрии', 'Проверки'),
        ('models/internal-mounts.json', '56 контактов опор с игровым полом · координаты', 'Документы'),
        ('models/internal-rear.png', 'Рендер заднего отсека · проект', 'Изображения'),
        ('models/internal-boiler.png', 'Рендер генератора за сиденьями · проект', 'Изображения'),
        ('models/internal-front.png', 'Рендер передних резервуаров · проект', 'Изображения'),
        ('models/internal-routes.json', 'Пар, вода, топливо, дым и управление · трассы', 'Документы'),
        ('models/registry.json', 'Происхождение и точность моделей', 'Документы')]:
        p = OUT / path
        if not p.exists(): continue
        records.append({'path': path, 'title': title, 'category': cat, 'format': p.suffix[1:].upper(), 'size': p.stat().st_size})

    scenario_cards = []
    for s in data['scenarios']:
        c, r, m = s['case'], s['rated'], s['mass']
        label = {'A': 'Малая мощность', 'B': 'Умеренная мощность', 'C': 'Эквивалент 40 л.с.'}[c['id']]
        rub = '–'.join(fmt(x / 1e6, 1) for x in c['budget_RUB'])
        eur = '–'.join(fmt(x / 1000) for x in c['budget_EUR'])
        note = {'A': 'Небольшая мощность сохраняет проблему теплоотвода.', 'B': 'Остаток до 1200 кг — около 55 кг с одним водителем.', 'C': 'Превышение условной полной массы — 18,4 кг.'}[c['id']]
        scenario_cards.append(f'''<article class="scenario {'featured' if c['id']=='B' else ''}"><div class="scenario-top"><span class="letter">{c['id']}</span><span>{label}</span></div><div class="scenario-power">{fmt(c['net_drive_kW'],1).removesuffix(',0')}<span>кВт к КПП</span></div><p class="scenario-speed">{c['target_kmh']} км/ч · цель расчётного сценария</p><dl><div><dt>Режим пара</dt><dd>{c['p_bar_abs']} бар abs / {c['T_C']} °C</dd></div><div><dt>Масса с водителем</dt><dd>{fmt(m['running_mass_kg'])} кг</dd></div><div><dt>Теплоотвод на номинале</dt><dd>{fmt(r['condenser_kW'])} кВт</dd></div><div><dt>Топливо на номинале</dt><dd>{fmt(r['diesel_L_h'],1)} л/ч</dd></div></dl><div class="scenario-budget"><b>{rub} млн ₽</b><span>{eur} тыс. €</span></div><p class="scenario-note">{note}</p><a class="text-link" href="lab.html?scenario={c['id']}">Исследовать вариант →</a></article>''')
    sheet_cards = ''.join(f'''<a class="sheet" href="drawings/{k}.pdf"><div class="sheet-preview"><img src="drawings/{k}.svg" alt="{escape(v[0])}"></div><div class="sheet-description"><span class="eyebrow">ЛИСТ {k[:2]} / PDF</span><h3>{v[0]}</h3><p>{v[1]}</p></div><span class="sheet-arrow">↗</span></a>''' for k, v in sorted(drawings.items()) if (ROOT/'drawings'/f'{k}.pdf').exists() and (ROOT/'drawings'/f'{k}.svg').exists())
    source_items = ''.join(f'<li><a href="{escape(sources[k]["url"])}" target="_blank" rel="noopener">{escape(sources[k]["title"])} ↗</a></li>' for k in ['manual', 'iapws', 'fin', 'rus', 'vwvideo'] if k in sources)
    (OUT / 'index.html').write_text(page('index.html', 'ЗАЗ / STEAM — проект парового автомобиля', 'Расчёты, 3D-компоновка и чертежи парового привода ЗАЗ-968М. Открытый предварительный инженерный проект.', SCENARIOS=''.join(scenario_cards), SHEETS=sheet_cards, SOURCES=source_items, FORMULA_COUNT=sum(len(c['steps']) for c in json.loads((ROOT/'calculation-workbook.json').read_text()))))

    filters = ''.join(f'<button class="filter" data-category="{cat}" aria-pressed="false">{cat}</button>' for cat in ['Документы', 'Чертежи', '3D', 'Расчёты', 'Исходники', 'Проверки'])
    rows = []
    for r in records:
        size = fmt(r['size'] / 1024, 1) + ' КБ'
        download = r['format'] not in {'HTML', 'PDF', 'SVG'}
        rows.append(f'''<article class="file-row" data-bytes="{r['size']}" data-category="{r['category']}" data-search="{escape(r['title']+' '+r['path']+' '+r['category'],quote=True)}"><span class="file-format">{r['format']}</span><div class="file-description"><a href="{r['path']}" {'download' if download else ''}>{escape(r['title'])}</a><span>{r['path']}</span></div><span class="file-category">{r['category']}</span><span class="file-size">{size}</span><a class="file-action" href="{r['path']}" download aria-label="Скачать {escape(r['title'],quote=True)}">↓</a></article>''')
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
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>2026-10-10</lastmod></url>' for p in ['', 'engine-strength.html', 'library.html', 'knowledge.html', 'lab.html', 'fitted-engine.html', 'compact-radial.html', 'aging.html', 'engine-sizing.html', 'radial-engine.html', 'assembly.html', 'heat.html', 'physics.html', 'literature.html', 'procurement.html', 'internal.html', 'piping.html', 'packaging.html', 'reconstruction.html', 'calculations.html', 'report.html']) + '</urlset>')
    (OUT / '404.html').write_text(page('404.html', 'Страница не найдена — ЗАЗ / STEAM', 'Перейти к материалам проекта.'))
    (OUT / 'knowledge.html').write_text(page('knowledge.html', 'Поиск по знаниям — ЗАЗ / STEAM', 'Векторный поиск по документам проекта, формулам и разборам литературы с точными ссылками на источники.'))
    from workspace_ui import prepare_workspace
    from build_knowledge import build_knowledge
    prepare_workspace(OUT, WEB)
    manifest = build_knowledge(ROOT, OUT)
    p=OUT/'knowledge.html';text=p.read_text();digest=hashlib.sha256((OUT/'knowledge.js').read_bytes()).hexdigest()[:12]
    p.write_text(text.replace('src="knowledge.js"','src="knowledge.js?v='+digest+'"'))
    with zipfile.ZipFile(OUT/'project-materials.zip','a',zipfile.ZIP_DEFLATED) as z:
        z.write(OUT/'knowledge-manifest.json','steam-zaz968m/docs/knowledge-manifest.json')
        for p in sorted((OUT/'knowledge').iterdir()):z.write(p,'steam-zaz968m/docs/knowledge/'+p.name)
    print(f'Built {OUT}: {len(records)} catalog entries and a downloadable bundle.')


if __name__ == '__main__': main()
