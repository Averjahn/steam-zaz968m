"""Internal concept feasibility: existing B thermodynamics, illustrative geometry.
No pressure vessel/fabrication design or certified mounting ratings are produced.
Run with PYTHONPATH=.deps for CoolProp and ReportLab.
"""
from pathlib import Path
import json, math
from html import escape
from CoolProp.CoolProp import PropsSI
ROOT=Path(__file__).resolve().parent
layout=json.loads((ROOT/'layout-internal.json').read_text())
source=json.loads((ROOT/'results.json').read_text())
b=next(s for s in source['scenarios'] if s['case']['id']=='B');r=b['rated'];cycle=source['inputs']['cycle']
f=lambda n: f'{n:,.2f}'.replace(',','\u202f').replace('.',',')
rows=[]
def calc(name,formula,sub,value,unit,note):
 rows.append(dict(name=name,formula=formula,substitution=sub,value=value,unit=unit,note=note))
q=r['condenser_kW'];air=q/(cycle['cooling_air_density_kg_m3']*cycle['air_heat_capacity_kJ_kgK']*cycle['air_temperature_rise_K'])
calc('Требуемый объём воздуха B','V̇ = Q / (ρ · cₚ · ΔT)',f'{f(q)} / (1,18 × 1,005 × 25)',air,'м³/с','Исходные ρ, ΔT и теплоёмкость — допущения старого расчёта. Это необходимый тепловой баланс воздуха, не паспорт конденсатора.')
face=2*.5*.085
calc('Фронтальная площадь двух внутренних блоков','A = 2 · L · H','2 × 0,500 × 0,085',face,'м²','Площадь двух текущих оребрённых секций высотой 85 мм; коллекторы не считаются рёбрами. Не площадь поверхности теплообмена и не свободная площадь штатных отверстий.')
freeface=.65*face
calc('Свободная площадь условного фронта','Aсв = φ · A',f'0,65 × {f(face)}',freeface,'м²','φ=0,65 — геометрическая гипотеза; требуется измерение реального блока.')
duct=2*.49*.17*.65
calc('Свободное сечение условных воздуховодов','Aкан = 2 · L · H · φ','2 × 0,490 × 0,170 × 0,65',duct,'м²','Геометрическая гипотеза канала. Его выход через штатные отверстия не измерен.')
a=min(freeface,duct);u=air/a
calc('Скорость воздуха в меньшем условном сечении','u = V̇ / min(Aсв, Aкан)',f'{f(air)} / {a:.5f}',u,'м/с','Получается чрезмерная скорость для компактной автомобильной системы. Четыре нарисованных вентилятора эту производительность не подтверждают.')
dynamic=.5*1.18*u*u
calc('Масштаб динамического давления воздуха','pдин = ρ · u² / 2',f'1,18 × {f(u)}² / 2',dynamic,'Па','Динамическое давление не равно потере давления вентилятора. Старые 250 Па требуют отдельной проверки каналов и кривых вентиляторов.')
calc('Требуемая эффективная поверхность по прежним допущениям','Aтепл = Q · 1000 / (U · ΔTlm)',f'{f(q)} × 1000 / (40 × 40)',q*1000/(40*40),'м²','U=40 Вт/(м²·К), ΔTlm=40 К — допущения. Видимые рёбра декоративные; необходимы паспорт теплообменника и расчёт оребрения.')
limits=[]
for v in [5,10,15]:
 heat=1.18*1.005*25*a*v
 calc(f'Воздушный предел при {v} м/с','Qвозд = ρ · cₚ · ΔT · Aкан · u',f'1,18 × 1,005 × 25 × {a:.5f} × {v}',heat,'кВт','Верхняя оценка по нагреву воздуха при принятых сечениях. Не теплоотдача реального блока и не мощность двигателя.')
 limits.append(dict(air_velocity_m_s=v,air_enthalpy_upper_kW=heat,fraction_of_B=heat/q))
m=r['steam_kg_h']/3600
rhoout=PropsSI('D','P',b['case'].get('exhaust_pressure_bar_abs',cycle['exhaust_pressure_bar_abs'])*1e5,'T',r['exhaust_temperature_C']+273.15,'Water')
for name,d,rho,mdot in [('Скорость свежего пара · условный ID 40 мм',.04,r['inlet_density_kg_m3'],m),('Скорость выпуска · две ветви ID 70 мм',.07,rhoout,m/2),('Скорость воды перед Cat · условный ID 20 мм',.02,r['feed_density_kg_m3'],m)]:
 val=4*mdot/(rho*math.pi*d*d)
 calc(name,'u = 4 · ṁ / (ρ · π · dвн²)',f'4 × {mdot:.6f} / ({rho:.6f} × π × {d:.3f}²)',val,'м/с','Проверка масштаба трассы. Стенка, допустимые скорости, потери, двухфазное течение, расширение и материал требуют расчёта. Плотности воды/пара — CoolProp, состояние B.')
feed=m/r['feed_density_kg_m3']*60000
calc('Объём подачи воды B','V̇воды = ṁ / ρ · 60 000',f'{m:.6f} / {r["feed_density_kg_m3"]:.6f} × 60 000',feed,'л/мин','Максимальный системный расход для рекомендации бака здесь условно принят равным номиналу B; если режим выше, бак должен быть больше.')
calc('Рекомендуемый объём питательного бака · нижняя граница','Vбак ≥ 6 · V̇max',f'6 × {f(feed)}',6*feed,'л','Cat TB002: бак с перегородками, 6–10 максимальных минутных расходов. Не заменяет условия подпора горячей воды.')
calc('Рекомендуемый объём питательного бака · верхняя граница','Vбак ≥ 10 · V̇max',f'10 × {f(feed)}',10*feed,'л','Из того же первичного источника Cat TB002.')
for p in layout['parts']:
 if p['id'] not in ['WTR','RCV','FUE']:continue
 x,y,z=p['size'];v=x*y*z/1e6
 if p.get('notch'):v-=math.prod(p['notch']['size'])/1e6
 calc(p['name']+' · наружный объём','Vгаб = (L · B · H − Vвырезов) / 10⁶',(f'({x} × {y} × {z} − '+ ' × '.join(map(str,p['notch']['size']))+') / 1 000 000' if p.get('notch') else f'{x} × {y} × {z} / 1 000 000'),v,'л','Внешние размеры; это не вместимость бака. Не вычтены стенки, перегородки, арматура.')
 calc(p['name']+' · верхняя оценка полезного объёма','Vпол ≤ k · Vгаб',f'0,8 × {f(v)}',.8*v,'л','k=0,8 — допущение, не паспорт. Ни масса жидкости, ни запас хода прежнего B не подтверждены этим габаритом.')
calc('Пример нагрузки на одну из четырёх опор генератора','F = m · g · kдин / N','90 × 9,81 × 3 / 4',90*9.81*3/4,'Н','Иллюстрация только: 90 кг — прежнее допущение, kдин=3 условный, нагрузки неравномерны. Не подбор болтов, сечения или прочности кузова.')
meta=dict(status='Внутренний компоновочный кандидат, готовность к изготовлению и эксплуатации не подтверждена',all_equipment_inside_required=True,scenario_reference='B; results.json, unchanged thermodynamic assumptions',coolprop_version=__import__('CoolProp').__version__,formula_rows=rows,air_limits=limits,conclusion=f'Номинал B на 18 кВт привода с 358 кВт отвода тепла не подтверждён двумя нарисованными внутренними блоками. Их сечения требуют около {f(u)} м/с при прежнем подъёме температуры воздуха 25 К. Требуются иной реальный цикл/компоненты/компоновка, без наружных блоков согласно требованию.',sources=[dict(title='Cat Pumps 5CP2120W · заводской CAD и паспорт',url='https://www.catpumps.com/products/pumps/5cp-plunger-pump-high-temp-5cp2120w3000'),dict(title='Cat Pumps TB002 · горячий вход, подпор и ёмкость бака',url='https://www.catpumps.com/sites/default/files/2025-12/TB002_B.pdf'),dict(title='CoolProp · уравнение состояния воды IAPWS-95',url='https://coolprop.org/fluid_properties/fluids/Water.html')],limitations=layout['open_issues'])
(ROOT/'internal-feasibility.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
# Accessible source HTML; site builder supplies common navigation.
formulas=''.join('<article class="formula-card"><h3>'+escape(x['name'])+'</h3><p><strong>'+escape(x['formula'])+'</strong></p><p>'+escape(x['substitution'])+' = <strong>'+f(x['value'])+' '+escape(x['unit'])+'</strong></p><p class="fine-print">'+escape(x['note'])+'</p></article>' for x in rows)
audit=json.loads((ROOT/'internal-fit-audit.json').read_text()) if (ROOT/'internal-fit-audit.json').exists() else None
conflicts='Проверка поверхностей выполняется; итог ещё не записан.'
if audit:
 hit=[p for p in audit['parts'] if p['body_intersections']]
 conflicts='<div class="scroll"><table><thead><tr><th>Узел</th><th>Пересечения с игровым кузовом</th></tr></thead><tbody>'+''.join('<tr><td>'+escape(p['id']+' · '+p['name'])+'</td><td>'+escape(', '.join(p['body_intersections']).replace('_',' '))+'</td></tr>' for p in hit)+'</tbody></table></div><p>За пределами внешнего прямоугольного габарита: '+escape(', '.join(audit.get('equipment_outside_body_aabb',[])) or 'нет')+'. Это не доказательство нахождения во внутренней полости.</p>'
if audit:
 pairs=audit['summary']['unplanned_mesh_intersections']
 conflicts+='<h3>Незапланированные пересечения агрегатов и трасс</h3><p>'+escape('; '.join(' ↔ '.join(x) for x in pairs) or 'Не найдены показанными поверхностями')+'</p><p>Список относится к текущему дизельному кандидату; после изменения источника нужен новый аудит. Контакты опор с полом и условные порты показаны отдельно в полном аудите. Трубы не проходят сквозь перегородки автоматически: нужны реальные отверстия, защищённые проходы и свободные коридоры.</p>'
page='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>@@TITLE@@</title><link rel="icon" href="favicon.svg"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="calculations.css"></head><body>@@HEADER@@<main id="main" class="page-main internal-page"><span class="eyebrow">ВНУТРИ КУЗОВА / ПРОЕКТНАЯ СБОРКА</span><h1>Паровая установка без наружных блоков.</h1><p>Это цель новой компоновки. <a href="heat.html">Новые варианты дизеля, дров, пеллет, LPG и электричества с замкнутым водяным циклом →</a> В вашем кузове yatloo показаны двигатель, генератор, два боковых конденсатора, заводской насос Cat, привод насоса, подпор, трубопроводы, арматура, рамы, виброопоры и условные защитные перегородки.</p><p>Два места: генератор с горелкой заменяют задний ряд, двигатель и конденсаторы занимают задний отсек, водяные баки — передний, питательный насос с мотором — под горелкой за сиденьями. Штатная подвеска сохранена. Под капотами остаются исходные пол и ниши; наружного конденсатора на крыше больше нет.</p><div class="status-note"><p>Модель показывает предполагаемое расположение и принцип крепления. Реальный двигатель, генератор, конденсаторы, моторы и арматура ещё не выбраны. '''+escape(meta['conclusion'])+'''</p></div><p><a class="button" href="assembly.html">Открыть детальную сборку →</a> <a class="button secondary" href="models/steam-internal-assembly.glb" download>Скачать полную сборку GLB ↓</a></p><div class="reference-photos"><figure><img src="models/internal-rear.png" alt="Паровая машина, боковые конденсаторы и опоры в заднем отсеке"><figcaption>Задний отсек: подробные формы — проектные, кузов — из вашего файла.</figcaption></figure><figure><img src="models/internal-boiler.png" alt="Змеевик, камера и горелка вместо заднего сиденья"><figcaption>За сиденьями: змеевик, камера, горелка и трубопроводы. Скрытие кожуха — режим осмотра.</figcaption></figure></div><h2>Как смотреть</h2><p>Кнопки «Под задней крышкой», «Под передним капотом» и «Генератор за сиденьями» приближают соответствующий отсек. Слои «Трубопроводы» и «Рамы и перегородки» включаются отдельно. Уберите кожух генератора, чтобы увидеть змеевик. Срезы позволяют проверить положение в нескольких плоскостях.</p><p>Серебристые наружные кожухи закрывают рассчитанную изоляцию горячих трасс; отключите их, чтобы увидеть бежевую изоляцию, а затем металл трубы. Фиолетовый — управление, золотистая трубка — топливо. <a href="piping.html">Диаметры, радиусы и формулы трубопроводов →</a> Полный дымовой маршрут показан к заднему выпуску; кузовное окно, дымосос и защитный сброс требуют подтверждения. Условные скорости, потери и тепловой экран рассчитаны по B; арматура, компенсаторы и крепления должны быть подобраны по реальному режиму.</p><h2>Реальные размеры и форма по фотографиям</h2><p>Насос Cat имеет заводскую геометрию, а компактный корпус G10 показан по размерному ориентиру каталога A305/D262/E261/F108 мм (глубина 369 мм). Для них масштаб зафиксирован. Двигатель, генератор, конденсаторы, баки, моторы и арматура ещё не выбраны: их форма — проектная, а не восстановленная с подтверждённой точностью по фотографиям реальных изделий. Фото без опорных размеров нельзя использовать как доказательство масштаба.</p><p><a href="https://www.riello.com/international/files/catalogo-pdf/riello_products_catalogue_international-markets_process_burners_eng.pdf">Riello: профиль, размерный чертёж и обслуживание →</a></p><h2>Крепления</h2><p>Показаны продольные балки, поперечины, площадки, виброопоры, болты лап двигателя, стяжки баков и защитные перегородки. Это принцип сборки с передачей нагрузок на проверенные силовые точки кузова. Таких обмеренных точек пока нет: болты и сечения условные. Площадки и стойки доведены до треугольников исходного пола по лучам: опоры не висят отдельно от кузова. Эти контакты с игровой поверхностью не подтверждают силовые точки реального автомобиля. Модели нельзя использовать как размеры для сверления или изготовления котла.</p><h2>Проверка геометрии</h2>'''+conflicts+'''<p>Проверка сеток не доказывает отсутствие полного вложения в металл. Для раздельных конденсаторов и трасс перекрытие их больших габаритных коробов отделено от пересечений реальных показанных треугольников. Планируемые стыки выделены отдельно. Резервные габариты двигателя и КПП всё равно нужно проверять.</p><p><a href="internal-fit-audit.json">Полный аудит текущей сборки →</a> · <a href="layout-internal.json">Координаты и допущения →</a></p><h2>Формула → подстановка → результат</h2><p>Ниже сохранена проверка исторического большого сценария B. Актуальные пять источников, меньший режим и расход: <a href="heat.html">сравнение тепла</a>. Ни нарисованные детали, ни их масса не объявлены паспортными характеристиками; расчёт нового запаса хода и нагрузок на оси требует подбора оборудования. Округление только в отображении, вычисления выполнены с полной точностью.</p><div class="formula-grid">'''+formulas+'''</div><h2>Чертёж и материалы</h2><p><a href="drawings/07-internal-assembly.pdf">Компоновочный лист PDF ↓</a> · <a href="drawings/07-internal-assembly.svg">Три проекции SVG ↓</a> · <a href="internal-feasibility.json">Расчёты JSON ↓</a> · <a href="models/internal-routes.json">Трассы и конечные точки JSON ↓</a></p><h2>Что остаётся решить</h2><ul>'''+''.join('<li>'+escape(x)+'</li>' for x in layout['open_issues'])+'''</ul><h2>Первичные источники</h2><ul>'''+''.join('<li><a href="'+escape(x['url'],quote=True)+'">'+escape(x['title'])+'</a></li>' for x in meta['sources'])+'''</ul></main>@@FOOTER@@</body></html>'''
(ROOT/'web/internal.html').write_text(page)
# Native SVG and PDF conceptual layout projections. Dimensions are reserves, not metal drawings.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1000" viewBox="0 0 1400 1000"><rect width="1400" height="1000" fill="#0b1117"/><g font-family="Arial,sans-serif" fill="#edf2f4"><text x="35" y="38" font-size="24">ЗАЗ-968М · внутренняя проектная сборка</text><text x="35" y="65" font-size="14">Все размеры в мм. Резервные габариты и трассы; не чертёж для изготовления.</text>']
for title,axes,ox,oy,scale in [('Сверху · X/Y',(0,1),40,110,.24),('Сбоку · X/Z',(0,2),40,490,.24),('Сзади · Y/Z',(1,2),1020,490,.22)]:
 svg.append(f'<text x="{ox}" y="{oy-14}" font-size="17">{title}</text>')
 for p in layout['parts']:
  pos=p['xyz'][:];size=p['size'][:]
  if p['id']=='BRN':size=[476,684,474]
  if axes==(0,1):x=ox+pos[0]*scale;y=oy+(pos[1]+745)*scale;w=size[0]*scale;h=size[1]*scale
  elif axes==(0,2):x=ox+pos[0]*scale;y=oy+(1420-pos[2]-size[2])*scale;w=size[0]*scale;h=size[2]*scale
  else:x=ox+(pos[1]+745)*scale;y=oy+(1420-pos[2]-size[2])*scale;w=size[1]*scale;h=size[2]*scale
  svg.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{p["color"]}" fill-opacity=".16" stroke="{p["color"]}"/><text x="{x+3:.2f}" y="{y+15:.2f}" font-size="11">{p["id"]}</text>')
 svg.append(f'<rect x="{ox}" y="{oy}" width="{(3640.73135 if axes[0]==0 else 1493.93612)*scale}" height="{(1493.93612 if axes[1]==1 else 1420.00599)*scale}" fill="none" stroke="#65727f" stroke-dasharray="6 4"/>')
svg.extend(['<text x="35" y="880" font-size="15">CND: два боковых блока, центральная часть свободна для ENG. Задний ряд сидений удаляется.</text>','<text x="35" y="905" font-size="15">Точные панели кузова — в GLB. Короб CND на этом листе охватывает оба блока; это не сплошной агрегат.</text>','<text x="35" y="930" font-size="15">Проверьте пересечения по internal-fit-audit.json. Теплоотвод 358 кВт не подтверждён.</text>','<text x="35" y="955" font-size="15">Площадки, болты, трубки и стенки не рассчитаны для изготовления. Для монтажа нужны обмеры и выбор изделий.</text>','</g></svg>'])
(ROOT/'drawings/07-internal-assembly.svg').write_text('\n'.join(svg))
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
font='/System/Library/Fonts/Supplemental/Arial.ttf'
pdfmetrics.registerFont(TTFont('InternalArial',font));c=canvas.Canvas(str(ROOT/'drawings/07-internal-assembly.pdf'),pagesize=(1400,1000));c.setTitle('ЗАЗ-968М: внутренняя компоновка, проектный лист');c.setFont('InternalArial',20);c.drawString(35,960,'ЗАЗ-968М · внутренняя сборка · проектный лист')
c.setFont('InternalArial',12);c.drawString(35,934,'Миллиметры. Масштаб кузова по базе 2160 мм; игровые поверхности не заменяют обмеры.')
for title,axes,ox,oy,scale in [('Сверху · X/Y',(0,1),40,880,.24),('Сбоку · X/Z',(0,2),40,490,.24),('Сзади · Y/Z',(1,2),1020,490,.22)]:
 c.setFillColorRGB(0,0,0);c.setFont('InternalArial',14);c.drawString(ox,oy+14,title)
 for p in layout['parts']:
  a=p['xyz'];d=[476,684,474] if p['id']=='BRN' else p['size'];color=p['color'];rgb=tuple(int(color[i:i+2],16)/255 for i in [1,3,5]);c.setStrokeColorRGB(*rgb)
  if axes==(0,1):x=ox+a[0]*scale;y=oy-(a[1]+745+d[1])*scale;w=d[0]*scale;h=d[1]*scale
  elif axes==(0,2):x=ox+a[0]*scale;y=oy-(1420-a[2])*scale;w=d[0]*scale;h=d[2]*scale
  else:x=ox+(a[1]+745)*scale;y=oy-(1420-a[2])*scale;w=d[1]*scale;h=d[2]*scale
  c.rect(x,y,w,h);c.setFont('InternalArial',10);c.drawString(x+3,y+h-13,p['id'])
 c.setStrokeColorRGB(.5,.5,.5);c.rect(ox,oy-(1493.93612 if axes[1]==1 else 1420.00599)*scale,(3640.73135 if axes[0]==0 else 1493.93612)*scale,(1493.93612 if axes[1]==1 else 1420.00599)*scale)
c.setFont('InternalArial',12)
for i,t in enumerate(['CND: два боковых блока; охватывающий короб не означает сплошного объёма между ними.','Крепления показаны как принцип: сечения, болты, силовые точки и тепловые перегородки не рассчитаны.','Номинал B требует около 358 кВт теплоотвода; паспортной внутренней системы для него пока нет.','Текущие пересечения и трассы см. internal-fit-audit.json и models/internal-routes.json.','Это компоновочный лист, не чертёж для изготовления котла или монтажа оборудования.']):c.drawString(35,145-i*24,t)
c.showPage()
anchors=layout['mount_register']['anchors']
for start in range(0,len(anchors),28):
 c.setFont('InternalArial',19);c.drawString(35,950,'Контакты опор с игровым полом · не координаты для сверления')
 c.setFont('InternalArial',11);c.drawString(35,923,'Миллиметры; Z контакта получена по исходной треугольной поверхности. Реальная силовая точка не подтверждена.')
 c.drawString(35,893,'ID');c.drawString(280,893,'X');c.drawString(410,893,'Y');c.drawString(540,893,'Z пола');c.drawString(680,893,'Z поддона');c.drawString(820,893,'Исходная панель')
 for i,a in enumerate(anchors[start:start+28]):
  y=863-i*27;c.drawString(35,y,a['id'])
  for x,v in zip([280,410,540,680],a['foot_xyz']+[a['tray_z']]):c.drawString(x,y,f(v))
  c.drawString(820,y,str(a.get('floor_node',a.get('body_node','см. JSON'))))
 c.showPage()
c.save()
print(json.dumps({'air_m3_s':air,'duct_area_m2':duct,'velocity_m_s':u,'formula_rows':len(rows),'exhaust_density_kg_m3':rhoout},ensure_ascii=False))
