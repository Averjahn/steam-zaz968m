"""Readable conditional pipe calculation, dimensional sections and routed concept drawing."""
from pathlib import Path
import json,math
from html import escape as e
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent
meta=json.loads((ROOT/'pipe-engineering.json').read_text());routes=meta['routes']
def f(v,places=2):return f'{v:,.{places}f}'.replace(',','\u202f').replace('.',',')
def card(title,formula,sub,value,unit):return '<article class="formula-card"><h3>'+e(title)+'</h3><p><strong>'+e(formula)+'</strong></p><p>'+e(sub)+' = <strong>'+f(value)+' '+e(unit)+'</strong></p></article>'
head='''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>@@TITLE@@</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="calculations.css"></head><body>@@HEADER@@<main class="page-main internal-page" id="main"><span class="eyebrow">ДИАМЕТР / ИЗОЛЯЦИЯ / ИЗГИБЫ</span><h1>Трубы в масштабе кузова.</h1><p>Все 13 трасс имеют заданный наружный габарит и круговые отводы. Трубопровод свежего пара: ID 40 мм, OD 48 мм, аэрогель 30 мм, кожух 0,6 мм; полный диаметр 109,2 мм. Его радиус изгиба 90 мм — по оси трубы. Изменены вершины трасс, размеры труб и изоляции сохранены в модели и при экспорте.</p><p><a class="button" href="assembly.html">Посмотреть трубы в 3D →</a> <a class="button secondary" href="drawings/08-pipe-routing.pdf">Чертёж трасс PDF ↓</a></p><div class="status-note"><p>Расчётная гипотеза: сценарий B, наружный воздух 40 °C, целевая поверхность 55 °C, суммарный коэффициент внешней теплоотдачи h=8 Вт/(м²·К). Это проверка установившегося цилиндрического участка. При h=5 поверхность горячее; мосты в креплениях, клапанах и фланцах не рассчитаны. 55 °C — выбранная цель, а не подтверждение безопасности касания. Кожухи, арматура и реальная температура под капотом требуют проверки.</p><p>Реальный выпуск, отверстия и опоры труб ещё не согласованы с обмеренным кузовом. Изоляция дымового канала даёт Ø283,2 мм; между проектным двигателем и боковым конденсатором всего около 215 мм. Такая трасса не проходит через этот зазор. Общая посадка и теплоотвод B остаются нерешёнными; пересечения не скрыты.</p></div><h2>Разрез трубы</h2><p>В 3D выключите «Кожухи труб», чтобы увидеть изоляцию; выключите «Изоляция труб», чтобы увидеть металл. Независимые слои имеют реальные расчётные толщины. Срезы в окне сборки обрезают поверхности; размерный поперечный разрез ниже показывает слои явно.</p><div class="reference-photos">'''
for id in ['PIPE_STEAM','PIPE_FLUE']:
 s=next(x for x in routes if x['id']==id);out=s['outer_envelope_mm'];scale=220/out
 circles=''.join(f'<circle cx="145" cy="145" r="{d/2*scale:.3f}" fill="{color}"/>' for d,color in [(out,'#9caeb6'),(out-2*s['jacket_mm'],'#d2c9b1'),(s['od'],'#526770'),(s['inside_id_mm'],'#0b1117')])
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 290" role="img" aria-label="{e(s["name"])}">{circles}<g fill="#edf2f4" font-family="Arial" font-size="16"><text x="280" y="70">ID {s["inside_id_mm"]} мм</text><text x="280" y="104">OD {s["od"]} мм</text><text x="280" y="138">Изоляция {s["insulation_mm"]} мм</text><text x="280" y="172">Кожух {f(s["jacket_mm"],1)} мм</text><text x="280" y="206">Итог Ø{f(out,1)} мм</text></g></svg>'
 (ROOT/'drawings'/f'08-section-{id.lower()}.svg').write_text(svg)
 head+=f'<figure>{svg}<figcaption>{e(s["name"])}. Масштаб каждого сечения свой.</figcaption></figure>'
head+='</div><h2>Таблица трасс · мм, м, °C</h2><div class="scroll"><table><thead><tr><th>Трасса</th><th>ID / OD</th><th>Изоляция</th><th>Полный Ø</th><th>R оси</th><th>Длина</th><th>Поверхность</th></tr></thead><tbody>'
for s in routes:head+=f'<tr><td><a href="#{s["id"]}">{e(s["id"])}</a></td><td>{s["inside_id_mm"] or "—"} / {s["od"]}</td><td>{s["insulation_mm"]}</td><td>{f(s["outer_envelope_mm"],1)}</td><td>{s["bend_radius_mm"]}</td><td>{f(s["centerline_length_m"])}</td><td>{f(s["thermal"]["surface_C"]) if s.get("thermal") else "не рассчитывается"}</td></tr>'
head+='</tbody></table></div><h2>Как выполнен расчёт</h2><p>Плотность и вязкость воды и пара рассчитаны CoolProp по заданным P и T. Сечение потока берётся по ID. Потери Дарси—Вейсбаха используют приближение Хааланда для коэффициента трения, шероховатость 0,045 мм, K=0,2 на отвод и суммарное K=1 для прочей арматуры — допущения, требующие данных выбранных изделий. Возврат конденсата рассчитан как однофазная вода: вскипание, разделение фаз, ловушки и противодавление должны быть проверены отдельно. Высота воды учитывается отдельно от трения; давление генератора в этот результат не включено.</p><p>Для изоляции λ интерполируется по таблице производителя при средней температуре (Tст+Tпов)/2. Ниже нижнего значения таблицы берётся его λ. Теплопроводность тонкого кожуха, внутренняя теплоотдача и сопротивление металла здесь пренебрежимо малы относительно изоляции; температуры стенки приняты равными температурам среды. Дымовая стенка 350 °C — неподтверждённая гипотеза, расход дымовых газов неизвестен. Его ID 160 мм показан как резерв и не объявлен аэродинамически рассчитанным.</p><p>Отводы построены по окружности, без уменьшения радиуса. Критерий R ≥ max(1,5 OD; Rнаруж+15 мм) — выбранное геометрическое допущение, не паспорт гибки. Проверено, что касательные соседних отводов помещаются на прямых участках. Крепления трубы и компенсация расширения требуют отдельной разработки; хомуты показывают габарит, но не подтверждают силовую опору.</p>'
for s in routes:
 c=[];OD=s['od'];delta=s['insulation_mm'];J=s['jacket_mm'];D=s['outer_envelope_mm'];L=s['centerline_length_m']
 c.append(card('Полный наружный диаметр','Dнаруж = OD + 2δ + 2tкож',f'{OD} + 2 × {delta} + 2 × {f(J)}',D,'мм'))
 c.append(card('Радиус изгиба по оси','R = округление вверх max(1,5 OD; Dнаруж/2 + 15; Rзад)',f'max(1,5 × {OD}; {f(D)} / 2 + 15; {90 if s['id']=='PIPE_STEAM' else 30 if s['fluid']=='wire' else 0})',s['bend_radius_mm'],'мм'))
 bends=s['bends'];trim=sum(x['tangent_mm'] for x in bends);sumlen=sum(math.dist(a,b) for a,b in zip(s['points'],s['points'][1:]));arc=sum(math.radians(x['angle_deg'])*s['bend_radius_mm'] for x in bends)
 c.append(card('Длина оси с круговыми отводами','L = (Σlпрям − 2ΣR tan(θ/2) + ΣRθ) / 1000',f'({f(sumlen)} − 2 × {f(trim)} + {f(arc)}) / 1000',L,'м'))
 if s.get('hydraulics'):
  h=s['hydraulics'];d=s['inside_id_mm']/1000;flow=h['mass_kg_s'];rho=h['density_kg_m3'];u=h['speed_m_s'];Re=h['Re'];mu=h['viscosity_Pa_s'];fr=h['Darcy_f'];K=h['K_sum'];pressure=h['pressure_Pa']
  c.append(card('Объёмный расход','V̇ = ṁ / ρ × 60 000',f'{flow:.6f} / {rho:.6f} × 60 000',flow/rho*60000,'л/мин'))
  c.append(card('Скорость потока','u = 4ṁ / (ρπd²)',f'4 × {flow:.6f} / ({rho:.6f} × π × {d:.3f}²)',u,'м/с'))
  c.append(card('Число Рейнольдса','Re = ρud / μ',f'{rho:.6f} × {u:.6f} × {d:.3f} / {mu:.8f}',Re,''))
  c.append(card('Коэффициент трения Дарси','fD = [−1,8 log₁₀((ε/(3,7d))^1,11 + 6,9/Re)]^−2',f'[−1,8 log₁₀((0,000045/(3,7 × {d:.3f}))^1,11 + 6,9/{Re:.2f})]^−2',fr,''))
  c.append(card('Условные местные сопротивления','ΣK = Nотв × Kотв + Kпроч',f'{len(bends)} × 0,2 + 1',K,''))
  c.append(card('Трение и местные потери','Δp = (fD L/d + ΣK)ρu²/2',f'({fr:.6f} × {L:.6f}/{d:.3f} + {K:.2f}) × {rho:.6f} × {u:.6f}²/2',h['friction_minor_Pa'],'Па'))
  if s['fluid']=='water':c.append(card('Гидростатический перепад','Δpвыс = ρg(z₂−z₁)',f'{rho:.6f} × 9,81 × ({s["points"][-1][2]} − {s["points"][0][2]})/1000',h['static_head_Pa'],'Па'))
  if s['id']=='PIPE_RELIEF':c.append('<p class="status-note">Диаметр сброса не выбран по норме или паспорту клапана. Расход B подставлен только для иллюстрации: скорость более 100 м/с. Эта линия не является рассчитанным устройством защиты.</p>')
 if s.get('thermal'):
  t=s['thermal'];r1=OD/2000;r2=r1+delta/1000;rc=t['R_cond_mK_W'];rs=t['R_external_mK_W'];r3=t['external_jacket_radius_m'];tw=s['wall_temperature_C'];k=t['lambda_W_mK'];q=t['heat_W_m']
  c.append(card('Тепловое сопротивление изоляции на метр','Rиз = ln(r₂/r₁)/(2πλ)',f'ln({r2:.4f}/{r1:.4f})/(2π × {k:.6f})',rc,'м·К/Вт'))
  c.append(card('Внешнее сопротивление на метр','Rнар = 1/(2πr₃h), r₃ = r₂ + tкож',f'1/(2π × {r3:.4f} × 8)',rs,'м·К/Вт'))
  c.append(card('Теплопотери цилиндрического участка','q′ = (Tст − Tвозд)/(Rиз + Rнар)',f'({tw:.4f} − 40)/({rc:.6f} + {rs:.6f})',q,'Вт/м'))
  c.append(card('Температура наружной поверхности','Tпов = Tвозд + q′Rнар',f'40 + {q:.6f} × {rs:.6f}',t['surface_C'],'°C'))
  c.append(card('Теплопотери всей трассы без мостов','Q = q′L',f'{q:.6f} × {L:.6f}',q*L,'Вт'))
  c.append('<p>При h=5 / 8 / 15 Вт/(м²·К) наружная температура: '+ ' / '.join(f(x['surface_C'])+' °C' for x in t['h_sensitivity'])+'. При тех же исходных данных ProRox PS 960 требует толщины '+str(t['stone_wool_comparison']['thickness_mm'])+' мм вместо '+str(delta)+' мм аэрогеля. Это тепловое сравнение, не смета и не подтверждённая цена материала.</p>')
 head+=f'<details id="{s["id"]}"'+(' open' if s['id'] in ['PIPE_STEAM','PIPE_FLUE'] else '')+f'><summary>{e(s["id"]+" · "+s["name"])}</summary><div class="formula-grid">'+''.join(c)+'</div><p>Вершины оси в мм: '+e(' → '.join('('+', '.join(map(str,p))+')' for p in s['points']))+'.</p><p>Углы и касательные отводов: '+e('; '.join(f'θ={f(x["angle_deg"])}°, R={x["radius_mm"]} мм, t={f(x["tangent_mm"])} мм' for x in bends))+'</p></details>'
head+='<h2>Материалы для проверки</h2><p><a href="pipe-engineering.json">Все данные расчёта JSON ↓</a> · <a href="models/internal-routes.json">Трассы экспортированной сборки ↓</a> · <a href="internal.html">Компоновка и нерешённые пересечения →</a></p><h2>Первичные источники</h2><ul>'+''.join('<li><a href="'+e(x['url'],quote=True)+'">'+e(x['title'])+'</a></li>' for x in meta['sources'])+'</ul></main>@@FOOTER@@</body></html>'
(ROOT/'web/piping.html').write_text(head)
def curved_points(spec):
 pts=spec['points'];out=[pts[0]];R=spec['bend_radius_mm']
 def add(a,b):return [x+y for x,y in zip(a,b)]
 def mul(a,b):return [x*b for x in a]
 def sub(a,b):return [x-y for x,y in zip(a,b)]
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
 def normal(a):return mul(a,1/math.sqrt(dot(a,a)))
 for i in range(1,len(pts)-1):
  u=normal(sub(pts[i],pts[i-1]));v=normal(sub(pts[i+1],pts[i]));theta=math.acos(max(-1,min(1,dot(u,v))))
  if theta<1e-7:continue
  t=R*math.tan(theta/2);a=add(pts[i],mul(u,-t));axis=normal(cross(u,v));center=add(a,mul(cross(axis,u),R));radial=normal(sub(a,center));out.append(a)
  for j in range(1,41):
   angle=theta*j/40;rot=add(add(mul(radial,math.cos(angle)),mul(cross(axis,radial),math.sin(angle))),mul(axis,dot(axis,radial)*(1-math.cos(angle))))
   out.append(add(center,mul(rot,R)))
 out.append(pts[-1]);return out
# Concept top/side projection + dimension/thermal tables; uses the same declared vertices.
pdfmetrics.registerFont(TTFont('PipesArial','/System/Library/Fonts/Supplemental/Arial.ttf'))
c=canvas.Canvas(str(ROOT/'drawings/08-pipe-routing.pdf'),pagesize=(1190,842));c.setTitle('Steam ZAZ · insulated pipe routing candidate')
def text(x,y,s,size=12):c.setFont('PipesArial',size);c.drawString(x,y,s)
text(30,805,'ЗАЗ-968М · трубопроводы, изоляция и радиусы · концепт',22)
text(30,779,'мм, X назад / Y влево / Z вверх. Проекции осей с круговыми отводами; точная геометрия и полные оболочки в GLB.',12)
colors={'steam':(.83,.54,.33),'exhaust':(.4,.6,.7),'flue':(.45,.45,.45),'water':(.1,.65,.7),'fuel':(.75,.6,.25),'wire':(.55,.45,.75)}
for name,axes,ox,oy in [('Сверху X/Y',(0,1),35,717),('Сбоку X/Z',(0,2),35,356)]:
 scale=.245;text(ox,oy+15,name,15);c.setStrokeColorRGB(.65,.65,.65);c.rect(ox,oy-1494*scale,3641*scale,1494*scale)
 for s in routes:
  c.setStrokeColorRGB(*colors[s['fluid']]);c.setLineWidth(max(.8,s['outer_envelope_mm']*scale));p=c.beginPath()
  for i,a in enumerate(curved_points(s)):
   x=ox+a[0]*scale;y=oy-(a[1]+747 if axes==(0,1) else 1420-a[2])*scale
   (p.moveTo if i==0 else p.lineTo)(x,y)
  c.drawPath(p);c.setLineWidth(1)
text(949,704,'Цвет / среда',14)
for i,(name,key) in enumerate([('Пар','steam'),('Выпуск','exhaust'),('Вода','water'),('Топливо','fuel'),('Дым','flue'),('Проводка','wire')]):c.setFillColorRGB(*colors[key]);text(949,672-i*26,name);c.setFillColorRGB(0,0,0)
text(30,26,'Габариты с изоляцией намеренно не уменьшены. Посадка, вырезы, конечный выпуск и опоры не подтверждены.',11)
c.showPage();text(30,805,'Размеры всех трасс и результаты условного расчёта B',20)
headers=['Трасса','ID / OD','Изоляция','Итог Ø','R оси','L, м','u, м/с','Δp, Па','Tпов, °C'];xs=[30,205,300,405,500,595,680,780,930]
for x,h in zip(xs,headers):text(x,763,h,12)
for i,s in enumerate(routes):
 h=s.get('hydraulics');t=s.get('thermal');vals=[s['id'],str(s['inside_id_mm'] or '—')+' / '+str(s['od']),str(s['insulation_mm']),f(s['outer_envelope_mm'],1),str(s['bend_radius_mm']),f(s['centerline_length_m']),f(h['speed_m_s']) if h else '—',f(h['friction_minor_Pa']) if h else '—',f(t['surface_C']) if t else '—']
 for x,v in zip(xs,vals):text(x,731-i*31,v,11)
notes=['h=8 Вт/(м²·К), воздух 40 °C, цель поверхности 55 °C; λ(T) из документов производителей.', 'R — проектный геометрический минимум, не паспорт реального отвода. Кожух 0,6 мм на сторону.', 'Расход B: 551,74 кг/ч. Выпуск разделён на две равные ветви. Вода: однофазная гипотеза.', 'Δp — трение + условные местные потери; гидростатика, парогенератор и двухфазность требуют отдельного учёта.', 'Сброс не выбран по защитному клапану: строка показывает только расход B через условный диаметр.', 'Дым: Tст=350 °C — допущение. ID 160 мм не проверен по расходу газов; полный Ø283,2 мм.', 'Проход около 215 мм между двигателем и конденсатором меньше Ø дымового канала.', 'Геометрические пересечения, требуемые отверстия, силовые опоры и нагрев арматуры остаются нерешёнными.', 'Это схема компоновки. Не использовать для изготовления котла, подбора предохранительного клапана или сверления.']
for i,v in enumerate(notes):text(30,275-i*24,v,11)
c.showPage();c.save()
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1190" height="842" viewBox="0 0 1190 842"><rect width="1190" height="842" fill="#0b1117"/><g fill="#edf3f6" font-family="Arial"><text x="30" y="36" font-size="23">ЗАЗ-968М · изолированные трассы и круговые отводы</text><text x="30" y="62" font-size="13">Концепт, мм. Диаметр включает изоляцию и кожух. Пересечения дымового канала остаются нерешёнными.</text>']
for title,axes,ox,oy in [('Сверху X/Y',(0,1),35,105),('Сбоку X/Z',(0,2),35,490)]:
 scale=.21;svg.append(f'<text x="{ox}" y="{oy-12}" font-size="17">{title}</text><rect x="{ox}" y="{oy}" width="{3641*scale}" height="{1494*scale}" fill="none" stroke="#65727f"/>')
 for j,s in enumerate(routes):
  rgb=colors[s['fluid']];color='#'+''.join(f'{round(v*255):02x}' for v in rgb);points=' '.join(f'{ox+a[0]*scale:.3f},{oy+(a[1]+747 if axes==(0,1) else 1420-a[2])*scale:.3f}' for a in curved_points(s));svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{s["outer_envelope_mm"]*scale:.3f}" stroke-linejoin="round"/>')
  if axes==(0,1):svg.append(f'<text x="845" y="{105+j*23}" fill="{color}" font-size="12">{s["id"]}: Ø{f(s["outer_envelope_mm"],1)} / R{s["bend_radius_mm"]}</text>')
svg.append('</g></svg>');(ROOT/'drawings/08-pipe-routing.svg').write_text(''.join(svg))

print(json.dumps({'routes':len(routes),'formula_cards':head.count('class="formula-card"')}))
