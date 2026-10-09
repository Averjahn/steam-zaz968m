"""Default exposure results remain readable without JavaScript and in the local index."""
from html import escape


def aging_page_values(data):
    def f(x, n=2):
        return 'не определено' if x is None else f'{x:,.{n}f}'.replace(',', '\u202f').replace('.', ',')

    s = data['default_run']['summary']
    parts = data['input']['parts']
    summary = f"<p>{f(s['km'], 0)} км; поездки {f(s['planned_driving_h'], 0)} ч, горячее состояние с прогревом {f(s['planned_hot_h'], 1)} ч. {s['starts']} пусков. Каждый цилиндр: <strong>{f(s['crank_cycles_per_cylinder'], 0)} полных циклов</strong> при {f(data['input']['crank_rpm'], 0)} об/мин; общий вал {f(s['output_turns'], 0)} оборотов. Стоянок с воздухом ниже нуля: {s['frost_exposure_days']}. Срок службы неизвестен.</p>"
    rows = ''
    for p, v in zip(parts, s['parts']):
        rows += '<tr><td>'+escape(p['name'])+'</td><td>'+f(v['initial_wall_mm'])+' → '+f(v['wall_mm'])+' мм</td><td>'+f(v['hoop_MPa'])+' МПа</td><td>'+f(v['thermal_axial_range_MPa'])+' МПа · гипотеза</td></tr>'
    climate = {'seasonal': 'Сезоны −25…+35 °C', 'hot': 'Постоянно +35 °C', 'cold': 'Постоянно −25 °C'}
    winter = {'filled': 'Вода без защиты', 'drained': 'Полное осушение', 'heated': 'Поддержание ≥+5 °C'}
    scenarios = ''
    for v in data['scenarios']:
        t = v['summary']
        scenarios += '<tr><td>'+climate[v['climate']]+'</td><td>'+winter[v['winter']]+'</td><td>'+str(t['frost_exposure_days'])+'</td><td>'+str(t['unprotected_water_days'])+' стоянок</td><td>'+f(t['protection_kWh'], 1)+' кВт·ч</td></tr>'
    corrosion = ''
    for v in data['corrosion_sensitivity']:
        p = v['summary']['parts'][0]
        corrosion += '<tr><td>'+f(v['rate_mm_year'])+'</td><td>'+f(v['rate_mm_year']*2)+' мм</td><td>'+f(p['wall_mm'])+' мм</td><td>'+f(p['hoop_MPa'])+' МПа</td></tr>'
    def card(title, equation, sub, result):
        return '<article class="formula-card"><h3>'+title+'</h3><p class="formula">'+equation+'</p><p>'+sub+'</p><strong>'+result+'</strong></article>'
    p = s['parts'][0]
    formulas = ''.join([
        card('Пробег', 'L = d × Lсут', '730 × 50', f(s['km'], 0)+' км'),
        card('Циклы каждого цилиндра', 'n = (L / v) × 60 × nкрив', '36500 / 50 × 60 × '+f(data['input']['crank_rpm'], 4), f(s['crank_cycles_per_cylinder'], 0)+' полных циклов'),
        card('Потеря стенки', 'tст = t₀ − c × d/365', '4 − 0,1 × 730/365', '3,8 мм'),
        card('Ламе: давление на прямую трубу', 'σθ = Δp (a² + b²) / (b² − a²)', '0,9 МПа × (20² + 23,8²) / (23,8² − 20²)', f(p['hoop_MPa'])+' МПа'),
        card('Термический осевой диапазон · крайний холод', '|ΔσT| = χ E α ΔT', '0,1 × 200000 МПа × 12·10⁻⁶ × (250 − (−25))', '66 МПа · упругая гипотеза, не допускаемое напряжение'),
        card('Ползучесть', 'tгор = d (Lсут/v + tпрогр/60)', '730 × (50/50 + 15/60)', f(s['planned_hot_h'], 1)+' ч; повреждение не определено'),
        card('Усталость', 'D = Σ nᵢ/Nᵢ', 'Пуски 730; Nᵢ по материалу и напряжениям не задано', 'Не определено; нулевое повреждение не назначено'),
    ])
    return {'AGING_SUMMARY': summary, 'AGING_PARTS': rows, 'AGING_SCENARIOS': scenarios,
            'AGING_CORROSION': corrosion, 'AGING_FORMULAS': formulas,
            'AGING_LIMITATIONS': ''.join('<li>'+escape(v)+'</li>' for v in data['limitations']),
            'AGING_SOURCES': ' · '.join('<a href="'+escape(v['url'], quote=True)+'">'+escape(v['title'])+'</a>' for v in data['sources'])}
