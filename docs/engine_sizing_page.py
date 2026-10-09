"""Render the default study for static browsing, search and printing."""
from html import escape


def sizing_page_values(data):
    def f(x, n=2):
        return 'Вне области модели' if x is None else f'{x:,.{n}f}'.replace(',', '\u202f').replace('.', ',')

    engines = ''
    for c, r in zip(data['candidates'], data['default_rows']):
        dimensions = ' × '.join(f(x, 0) for x in c.get('size_mm', c.get('budget_mm', [])))
        label = ('Габарит' if 'size_mm' in c else 'Бюджет новой сборки') + ': ' + dimensions + ' мм. '
        engines += '<tr><td>'+escape(c['name'])+'</td><td>'+str(c['count'])+' × Ø'+f(c['bore'], 0)+' / ход '+f(c['stroke'], 0)+' мм<br><strong>'+f(r['geometry']['swept_L'], 3)+' л</strong></td><td>'+f(r['geometry']['double_L'], 3)+' л</td><td>'+escape(label+c['fit_status'])+'</td><td>'+f(r['crank_rpm'], 0)+' об/мин кривошипов<br>'+f(r['output_rpm'], 0)+' об/мин выхода</td></tr>'
    heat_rows = ''
    for r in data['heat_rows']:
        flag = '' if r['engine_speed_study_ok'] else '<br>Выше исследовательского предела'
        heat_rows += '<tr><td>'+f(r['heat_kW'], 0)+' кВт</td><td>'+f(r['shaft_kW'])+' кВт / '+f(r['shaft_hp'])+' л.с.</td><td>'+f(r['crank_rpm'], 0)+' об/мин'+flag+'</td><td>'+f(r['reject_kW'])+' кВт</td><td>'+f(r['air_m3_s'], 3)+' м³/с / '+f(r['air_m_s'])+' м/с</td><td>'+f(r['fan_kW'])+' кВт</td><td>'+f(r['net_kW'])+' кВт</td></tr>'
    air_rows = ''.join('<tr><td>'+f(r['assumptions']['air_rise_K'], 0)+' К / '+f(r['air_out_C'], 0)+' °C</td><td>'+f(r['air_m3_s'], 3)+' м³/с / '+f(r['air_m_s'])+' м/с</td><td>'+f(r['fan_kW'])+' кВт</td><td>'+f(r['net_kW'])+' кВт / '+f(r['net_hp'])+' л.с.</td></tr>' for r in data['air_rows'])
    r = data['default_rows'][2]
    def card(title, equation, sub, value):
        return '<article class="formula-card"><h3>'+title+'</h3><p class="formula">'+equation+'</p><p>'+sub+'</p><strong>'+value+'</strong></article>'
    formulas = ''.join([
        card('Рабочий объём', 'V = NπD²S / 4', '7 × π × (0,032 м)² × 0,036 м / 4 × 1000', f(r['geometry']['swept_L'], 3)+' л'),
        card('Расход пара', 'ṁ = Q̇ / (hвх − hпит − wнас)', '50 / (2943,122 − 251,332 − 1,479) × 3600', f(r['mass_kg_h'], 2)+' кг/ч'),
        card('Мощность на валу', 'Pвал = ṁ × Δhиз × ηis × ηмех', f(r['mass_kg_h']/3600, 6)+' × 400,354 × 0,50 × 0,90', f(r['shaft_kW'])+' кВт / '+f(r['shaft_hp'])+' л.с.'),
        card('Замкнутый водяной тепловой баланс', 'Q̇воды = Q̇ген + Pнас − Pинд', '50 + '+f(r['pump_kW'], 3)+' − '+f(r['indicated_kW'], 3), f(r['reject_kW'])+' кВт'),
        card('Граница механического ядра', 'Dядра ≤ 2√(Rопоры² + (bопоры/2)²)', '2 × √(205,5² + 7,2²)', f(data['candidates'][2]['core_radius_bound_mm']*2)+' мм · без коллекторов и труб'),
    ])
    target = data['target_40_hp']
    target_text = '<p>40 л.с. = 40 × 735,49875 = <strong>'+f(target['shaft_kW'])+' кВт</strong> на валу. Формула: Q̇ = Pвал × (hвх − hпит − wнас) / (Δhиз × ηis × ηмех).</p><p>Подстановка: '+f(target['shaft_kW'], 4)+' × (2943,122 − 251,332 − 1,479) / (400,354 × 0,50 × 0,90) = <strong>'+f(target['heat_kW'], 1)+' кВт тепла</strong>. Потребность в паре '+f(target['mass_kg_h'], 0)+' кг/ч; водяной контур должен отвести '+f(target['reject_kW'], 1)+' кВт. При ηкотла=0,85 это '+f(target['fuel_input_kW'], 1)+' кВт LHV и около '+f(target['fuel_L_h'], 1)+' л дизеля/ч.</p><p>Эти требования превышают нынешний размерный кандидат горелки на 120 кВт LHV. При допущении нагрева воздуха на 25 К требуется '+f(target['air_m3_s'], 2)+' м³/с. Бюджет вентилятора при такой скорости выходит за область модели и не используется для предсказания потребления.</p>'
    return {'ENGINE_ROWS': engines, 'HEAT_ROWS': heat_rows, 'AIR_ROWS': air_rows,
            'SIZING_FORMULAS': formulas, 'SIZING_SUMMARY': '<p>Компактная звезда: '+f(r['geometry']['swept_L'], 3)+' л; '+f(r['shaft_kW'])+' кВт / '+f(r['shaft_hp'])+' л.с. на валу. После принятых вспомогательных потребителей: '+f(r['net_kW'])+' кВт, до трансмиссии. Пар '+f(r['mass_kg_h'], 1)+' кг/ч; кривошипы '+f(r['crank_rpm'], 0)+' об/мин.</p>',
            'TARGET_40': target_text, 'LIMITATIONS': ''.join('<li>'+escape(s)+'</li>' for s in data['limitations'])}
