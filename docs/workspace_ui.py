"""Apply the project workspace to every generated HTML page (standard library)."""
from pathlib import Path
from html import escape
import hashlib
import re

NAV = [
    ('Рабочая среда', [
        ('index.html', 'Обзор проекта', 'home'),
        ('assembly.html', '3D-мастерская', 'cube'),
        ('calculations.html', 'Расчёты', 'calculator'),
        ('knowledge.html', 'Поиск по знаниям', 'search'),
    ]),
    ('Устройство автомобиля', [
        ('heat.html', 'Источники тепла', 'flame'),
        ('physics.html', 'Физика и подвеска', 'activity'),
        ('compact-radial.html', 'Компактная звезда в кузове', 'star'),
        ('radial-engine.html', 'Семицилиндровая звезда', 'star'),
        ('aging.html', 'Ресурс и зимняя эксплуатация', 'activity'),
        ('engine-sizing.html', 'Подбор объёма и мощности', 'calculator'),
        ('piping.html', 'Трубопроводы', 'route'),
        ('procurement.html', 'Комплектующие', 'box'),
    ]),
    ('Документы и геометрия', [
        ('library.html', 'Все материалы', 'folder'),
        ('literature.html', 'Проверка по книгам', 'book'),
        ('packaging.html', 'Проверка компоновки', 'layers'),
        ('internal.html', 'Внутренняя сборка', 'wrench'),
        ('user-model.html', 'Кузов ЗАЗ-968М', 'car'),
        ('report.html', 'Полный отчёт', 'file'),
    ]),
]
PATHS = {
    'home':'M3 10 12 3l9 7v11h-6v-7H9v7H3Z',
    'cube':'m12 2 9 5v10l-9 5-9-5V7Zm-9 5 9 5 9-5M12 12v10',
    'calculator':'M5 3h14v18H5ZM8 7h8M8 11h2m4 0h2m-8 4h2m4 0h2m-8 4h2m4 0h2',
    'search':'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
    'flame':'M12 3c1 5-5 5-5 11a5 5 0 0 0 10 0c0-3-1-4-2-6 0 3-2 4-3 5 1-4 2-6 0-10Z',
    'activity':'M2 12h5l3-9 4 18 3-9h5',
    'route':'M4 4h9a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h11m-4-4 4 4-4 4',
    'box':'M3 7h18v14H3ZM2 3h20v4H2ZM9 12h6',
    'folder':'M3 5h7l2 3h9v13H3Z',
    'book':'M12 5C8 2 4 3 2 4v16c4-2 7-1 10 1 3-2 6-3 10-1V4c-3-1-6-2-10 1Zm0 0v16',
    'layers':'m12 3 10 5-10 5L2 8Zm-10 10 10 5 10-5M2 18l10 5 10-5',
    'wrench':'m14 6 4 4 4-4a6 6 0 0 1-8 8l-8 8-4-4 8-8a6 6 0 0 1 8-8Z',
    'car':'M3 11l3-7h12l3 7v7H3Zm0 0h18M6 18v3m12-3v3M6 14h2m8 0h2',
    'file':'M5 2h9l5 5v15H5Zm9 0v6h5M8 12h8m-8 4h8',
    'menu':'M3 6h18M3 12h18M3 18h18',
    'list':'M8 5h13M8 12h13M8 19h13M3 5h1m-1 7h1m-1 7h1',
    'star':'m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z',
    'arrow':'M5 12h14m-6-6 6 6-6 6',
}

def icon(name):
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="'+PATHS.get(name,PATHS['file'])+'"/></svg>'

def shell(filename):
    label = next((title for _,items in NAV for url,title,_ in items if url==filename), 'Материалы проекта')
    links = ''.join('<div class="nav-group"><span>'+escape(group)+'</span>'+''.join(
        '<a href="'+url+'"'+(' aria-current="page"' if filename==url else '')+'>'+icon(sym)+'<span>'+title+'</span></a>'
        for url,title,sym in items)+'</div>' for group,items in NAV)
    return '''<a class="skip" href="#main">К содержимому</a>
<aside class="app-sidebar" id="appSidebar" aria-label="Разделы проекта">
<a class="workspace-brand" href="index.html"><span class="workspace-mark">S</span><span>ЗАЗ / STEAM<small>Инженерная мастерская</small></span></a>
<nav>'''+links+'''</nav><div class="sidebar-bottom"><span class="project-dot"></span> Исследовательский проект<a href="https://github.com/Averjahn/steam-zaz968m" target="_blank" rel="noopener">GitHub ↗</a></div></aside>
<button class="sidebar-backdrop" id="sidebarBackdrop" aria-label="Закрыть навигацию" hidden></button>
<header class="app-topbar">
<button class="icon-button" id="navToggle" aria-label="Открыть разделы" aria-controls="appSidebar" aria-expanded="false">'''+icon('menu')+'''</button>
<div class="workspace-crumb"><span>Проект ЗАЗ-968М</span><strong>'''+label+'''</strong></div>
<button class="global-search-button" id="openSearch">'''+icon('search')+'''<span>Найти в проекте</span><kbd>⌘ K</kbd></button>
<button class="icon-button outline-button" id="openOutline" aria-label="Оглавление и закладки">'''+icon('list')+'''<span>Оглавление</span></button>
<label class="theme-label"><span class="sr-only">Цветовая тема</span><select id="themeSelect" aria-label="Цветовая тема"><option value="system">Системная</option><option value="light">Светлая</option><option value="dark">Тёмная</option><option value="blueprint">Чертёжная</option></select></label>
</header>
<dialog id="searchDialog" class="workspace-dialog" aria-labelledby="searchTitle"><div class="dialog-heading"><div><span class="eyebrow">БЫСТРЫЙ ДОСТУП</span><h2 id="searchTitle">Найти в проекте</h2></div><button data-close-dialog aria-label="Закрыть поиск">×</button></div><label class="search-input-wrap">'''+icon('search')+'''<input id="globalQuery" type="search" placeholder="Раздел, компонент или вопрос…" autocomplete="off" aria-label="Поиск по проекту"></label><div class="search-scopes" id="globalScopes"><button data-scope="all" aria-pressed="true">Всё</button><button data-scope="navigation" aria-pressed="false">Разделы</button><button data-scope="documents" aria-pressed="false">Документы</button></div><p id="globalSearchStatus" class="search-status" role="status"></p><div id="globalSearchResults" class="search-results"></div><div class="dialog-footer"><span>↑ ↓ выбор · Enter открыть · Esc закрыть</span><a href="knowledge.html">База знаний →</a></div></dialog>
<dialog id="outlineDialog" class="workspace-dialog outline-dialog" aria-labelledby="outlineTitle"><div class="dialog-heading"><div><span class="eyebrow">НА ЭТОЙ СТРАНИЦЕ</span><h2 id="outlineTitle">Оглавление и закладки</h2></div><button data-close-dialog aria-label="Закрыть оглавление">×</button></div><div class="outline-density"><label>Плотность интерфейса<select id="densitySelect"><option value="comfortable">Обычная</option><option value="compact">Компактная</option></select></label></div><div id="pageOutline"></div><div class="saved-heading">Сохранённые места</div><div id="savedPlaces"></div></dialog>'''

def prepare_workspace(out, web):
    for name in ['workspace.css','workspace.js','knowledge.js','search-core.js','search-worker.js','workspace-concept.svg']:
        (out/name).write_bytes((web/name).read_bytes())
    digest = lambda name: hashlib.sha256((out/name).read_bytes()).hexdigest()[:12]
    # Pin transitive search modules and worker so an old tab cannot combine two indexes.
    for name in ['search-worker.js','knowledge.js']:
        text=(out/name).read_text().replace("'./search-core.js'", "'./search-core.js?v="+digest('search-core.js')+"'")
        if name=='knowledge.js':text=text.replace("'./search-worker.js'", "'./search-worker.js?v="+digest('search-worker.js')+"'")
        (out/name).write_text(text)
    text=(out/'workspace.js').read_text().replace("'./knowledge.js'", "'./knowledge.js?v="+digest('knowledge.js')+"'")
    (out/'workspace.js').write_text(text)
    for p in sorted(out.glob('*.html')):
        text=p.read_text()
        # Some early exported reports relied on the browser's implicit <head>.
        # Normalize it before attaching shared assets, including mobile viewport.
        if '</head>' not in text:
            if '<head>' not in text:text=re.sub(r'(<html\b[^>]*>)',r'\1<head>',text,count=1)
            text=text.replace('<body','</head><body',1)
        if 'name="viewport"' not in text:text=text.replace('</head>','<meta name="viewport" content="width=device-width,initial-scale=1"></head>')
        if not re.search(r'href="style\.css(?:\?|\")',text):text=text.replace('</head>','<link rel="stylesheet" href="style.css?v='+digest('style.css')+'"></head>')
        used=set(re.findall(r'\bid="([^"]+)"',text))
        n=0
        def anchor(m):
            nonlocal n
            n+=1
            if re.search(r'\bid=',m.group(2)):return m.group(0)
            name='topic-'+str(n)
            while name in used:name+='a'
            used.add(name)
            return '<'+m.group(1)+m.group(2)+' id="'+name+'">'
        text=re.sub(r'<(h[23]|details)\b([^>]*)>',anchor,text)
        text=re.sub(r'<a class="skip".*?</header>', '',text,flags=re.S)
        text=re.sub(r'<footer class="site-footer">.*?</footer>','<footer class="workspace-footer">ЗАЗ / STEAM · Предварительный инженерный проект <a href="library.html">Все материалы</a><a href="knowledge.html">Поиск с источниками</a></footer>',text,flags=re.S)
        # Standalone legacy reports get the same navigation and theme as modern pages.
        if '<main' not in text:
            text=re.sub(r'(<body[^>]*>)',r'\1<main id="main" class="legacy-content">',text,count=1)
            text=text.replace('</body>','</main></body>')
        elif not re.search(r'<main[^>]*\bid=',text):text=text.replace('<main','<main id="main"',1)
        text=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+shell(p.name),text,count=1)
        bootstrap="<script>try{const t=localStorage.getItem('zaz-theme')||'system';document.documentElement.dataset.theme=['light','dark','blueprint'].includes(t)?t:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');document.documentElement.dataset.density=localStorage.getItem('zaz-density')||'comfortable'}catch(e){document.documentElement.dataset.theme='light'}</script>"
        text=text.replace('</head>',bootstrap+'<link rel="stylesheet" href="workspace.css?v='+digest('workspace.css')+'"><script type="module" src="workspace.js?v='+digest('workspace.js')+'"></script></head>')
        text=text.replace('<html lang="ru">','<html lang="ru" data-workspace="v2">')
        p.write_text(text)
