"""Dimensioned conceptual projections from the chosen native mesh and its routes."""
import json,math
from pathlib import Path
from html import escape
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import toColor as Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parent
d=json.loads((root/'fitted-engine-study.json').read_text());meta=json.loads((root/'models/fitted-radial-engine.json').read_text());b=meta['bounds'];origin=meta['origin'];s=40/32
p=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1260 891"><rect width="1260" height="891" fill="white"/><rect x="20" y="20" width="1220" height="851" fill="none" stroke="#172c35"/><style>text{font-family:Arial,sans-serif;fill:#172c35;font-size:16px}.title{font-size:27px;font-weight:bold}.note{font-size:14px}</style>']
def text(x,y,t,cls=''):p.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(t)}</text>')
def line(a,b,c='#172c35',w=2,dash=''):p.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{c}" stroke-width="{w}" stroke-dasharray="{dash}"/>')
def circle(x,y,r,c='#6d8894',w=2):p.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{c}" stroke-width="{w}"/>')
def dim(a,b,label):
 line(a,b,'#172c35',1)
 for point,other in [(a,b),(b,a)]:
  dx,dy=other[0]-point[0],other[1]-point[1];L=math.hypot(dx,dy);dx/=L;dy/=L
  for sign in [-1,1]:line(point,(point[0]+7*dx+sign*3*dy,point[1]+7*dy-sign*3*dx),'#172c35',1)
 text((a[0]+b[0])/2+8,(a[1]+b[1])/2-8,label)
text(45,65,'ЗАЗ-968М: семицилиндровая паровая звезда по свободному месту','title')
text(45,95,'Ø40 × ход45 мм · шток9,6 мм · двойное действие · размерная схема, все размеры в мм')
top=lambda x,y:(355+.7*x,390-.7*y)
side=lambda x,z:(935+.65*x,565-.65*(z+75))
text(170,140,'ВИД СВЕРХУ · трубы по осям');text(805,140,'ВИД СБОКУ · проектные уровни')
for R,z,c in [(132,245,'#ce813e'),(104,170,'#3c93b6')]:circle(*top(0,0),R*.7,c,10);line(side(-R,z),side(R,z),c,16)
for i in range(7):
 a=math.pi/2+i*2*math.pi/7;u=(math.cos(a),math.sin(a));v=(-u[1],u[0]);pt=lambda r,t=0:top(r*u[0]+t*v[0],r*u[1]+t*v[1]);line(pt(152.4*s),pt(195.6*s),'#8fa3ab',50*s*.7);line(pt(152.4*s),pt(195.6*s),'#cad3d6',40*s*.7);circle(*pt(63*s),21*s*.7);line(pt(63*s),pt(152.4*s),'#b98947',3);text(*pt(212*s),str(i+1))
for r in meta['routes']:
 pts=[top(x,y) for x,y,z in r['points']];color='#529db5' if 'Выпуск' in r['name'] or 'выпуск' in r['name'] else '#ce813e';p.append('<polyline points="'+' '.join(f'{x},{y}'for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="2"/>')
line(top(-287.5,0),top(0,0),'#ab874b',5)
line(side(-287.5,-45),side(0,-45),'#ab874b',7);line(side(0,-45),side(0,30),'#ab874b',7)
line(side(-230,-51),side(230,-51),'#556970',6)
line(side(-245,61),side(245,61),'#97a8b0',45)
for x,z in [(3057.5,274.453033),(3477.5,370.74236)]:line(side(x-origin[0],z-origin[2]),side(x-origin[0],-51),'#556970',4)
localmin=[b['min_mm'][i]-origin[i] for i in range(3)];localmax=[b['max_mm'][i]-origin[i]for i in range(3)]
dim(top(localmin[0],-350),top(localmax[0],-350),'589,2');dim(top(350,localmin[1]),top(350,localmax[1]),'588,8');dim(side(390,localmin[2]),side(390,localmax[2]),'374,6')
text(680,205,'Полная геометрия без стоек: 589,2 × 588,8 × 374,6')
text(680,236,'Плоскость цилиндров: Z=551; общий выход к КПП: Z=445')
text(680,267,'Верхний пленум свежего пара: Z=735; выпуск: Z=660')
text(680,298,'Шестерни: 56 / 28 зубьев; модуль1,875; 2:1')
text(45,745,'Начало двигателя в кузове: X=3267,5; Y=0; Z=490. Поддон460×360; опоры по сетке пола.','note')
text(45,769,'V = 7πD²S/4 = 0,396 л; V обеих сторон = 7π(2D²−d²)S/4 = 0,769 л за оборот кривошипов.','note')
text(45,793,'При50 кВт тепла в паре:1323 об/мин кривошипов;661 об/мин общего вала;3,35 кВт до вспомогательных нагрузок.','note')
text(45,817,'Зазор двигателя до игровой сетки кузова18 мм. Реальная посадка, тепло и прочность не подтверждены.','note')
text(45,841,'НЕ ИЗГОТОВИТЕЛЬНЫЙ ЧЕРТЁЖ. Полная установка имеет нерешённые пересечения; гибы и поверхности — в GLB.','note')
text(1050,864,'10.10.2026 · лист11','note');p.append('</svg>');svg=''.join(p);dest=root/'drawings/11-fitted-radial.svg';dest.write_text(svg)
pdfmetrics.registerFont(TTFont('FittedArial','/System/Library/Fonts/Supplemental/Arial.ttf'));scale=420/1260*72/25.4;pdf=canvas.Canvas(str(dest.with_suffix('.pdf')),pagesize=(1260*scale,891*scale));pdf.scale(scale,scale)
for e in ET.fromstring(svg):
 tag=e.tag.split('}')[-1];a=e.attrib;stroke=a.get('stroke','none');fill=a.get('fill','none');pdf.setLineWidth(float(a.get('stroke-width',1)));pdf.setDash([float(v)for v in a.get('stroke-dasharray','').split()]or[])
 if stroke!='none':pdf.setStrokeColor(Color(stroke))
 if fill!='none':pdf.setFillColor(Color(fill))
 if tag=='rect':pdf.rect(float(a.get('x',0)),891-float(a.get('y',0))-float(a['height']),float(a['width']),float(a['height']),stroke=int(stroke!='none'),fill=int(fill!='none'))
 elif tag=='line':pdf.line(float(a['x1']),891-float(a['y1']),float(a['x2']),891-float(a['y2']))
 elif tag=='circle':pdf.circle(float(a['cx']),891-float(a['cy']),float(a['r']),stroke=1,fill=0)
 elif tag=='polyline':
  points=[list(map(float,v.split(',')))for v in a['points'].split()];q=pdf.beginPath();q.moveTo(points[0][0],891-points[0][1])
  for x,y in points[1:]:q.lineTo(x,891-y)
  pdf.drawPath(q,stroke=1,fill=0)
 elif tag=='text':pdf.setFillColor(Color('#172c35'));pdf.setFont('FittedArial',27 if a.get('class')=='title' else 14 if a.get('class')=='note' else 16);pdf.drawString(float(a['x']),891-float(a['y']),e.text or '')
pdf.save();print('Built dimensioned concept sheet11 SVG/PDF')
