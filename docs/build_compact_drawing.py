"""Dimensioned concept layout from the measured compact mesh metadata."""
import json
import math
from pathlib import Path
from html import escape
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.lib.colors import toColor as HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

root = Path(__file__).resolve().parent
meta = json.loads((root / 'models/compact-radial-engine.json').read_text())
b = meta['bounds']['core']
origin = meta['origin_mm']
size = b['size_mm']
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1260 891"><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="none" stroke="#172c35"/></marker></defs><rect width="1260" height="891" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#172c35;font-size:16px} .title{font-size:27px;font-weight:bold} .note{font-size:14px}.dim{stroke:#172c35;stroke-width:1;fill:none;marker-start:url(#arrow);marker-end:url(#arrow)}.thin{stroke:#899a9f;stroke-width:1;fill:none}</style><rect x="20" y="20" width="1220" height="851" fill="none" stroke="#172c35"/><text x="45" y="65" class="title">ЗАЗ-968М: компактная семицилиндровая паровая звезда</text><text x="45" y="93">Габаритная схема · Ø32 × 36 мм · двойное действие · все размеры в миллиметрах</text>''']

def text(x, y, value, cls=''):
    parts.append(f'<text x="{x}" y="{y}" class="{cls}">{escape(value)}</text>')

def line(a, z, color='#172c35', width=2, dash=''):
    parts.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{z[0]}" y2="{z[1]}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>')

def dimension(a, z, label, x, y):
    parts.append(f'<path d="M{a[0]},{a[1]} L{z[0]},{z[1]}" class="dim"/>')
    text(x, y, label)

cx, cy = 355, 432
def top(p):
    return cx + p[0], cy - p[1]

xmin, ymin, zmin = [x-o for x,o in zip(b['min_mm'], origin)]
xmax, ymax, zmax = [x-o for x,o in zip(b['max_mm'], origin)]
parts.append(f'<rect x="{cx+xmin}" y="{cy-ymax}" width="{size[0]}" height="{size[1]}" fill="none" stroke="#6c7b83" stroke-dasharray="7 5"/>')
parts.append(f'<rect x="{cx-230}" y="{cy-195}" width="460" height="390" fill="#eef1f2" stroke="#465c66"/>')
for radius, color in [(104, '#368bad'), (132, '#cd7b36')]:
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" stroke="{color}" stroke-width="10" fill="none"/>')
for i in range(7):
    a = math.pi/2+i*2*math.pi/7
    u=(math.cos(a), math.sin(a))
    def at(r, t=0): return [u[0]*r-u[1]*t,u[1]*r+u[0]*t,61]
    A, B = top(at(152.4)), top(at(195.6))
    line(A,B,'#dcd3c0',71)
    line(A,B,'#6f858d',40)
    line(top(at(63)),top(at(156)),'#bc9159',3)
    parts.append(f'<circle cx="{top(at(63))[0]}" cy="{top(at(63))[1]}" r="21" fill="none" stroke="#465c66"/>')
    tx, ty=top(at(212))
    text(tx-4,ty+5,str(i+1))
for r in meta['routes']:
    if r['index'] not in [None,0]: continue
    coords=' '.join(f'{top(p)[0]},{top(p)[1]}' for p in r['points'])
    color='#368bad' if r['role'] in ['return','outlet'] else '#cd7b36'
    parts.append(f'<polyline points="{coords}" stroke="{color}" stroke-width="2" fill="none" stroke-dasharray="4 3"/>')
dimension((cx+xmin,155),(cx+xmax,155),f'{size[0]:.1f}'.replace('.',','),cx-20,145)
dimension((65,cy-ymax),(65,cy-ymin),f'{size[1]:.1f}'.replace('.',','),32,cy)
text(100,720,'Вид сверху: X вдоль автомобиля, Y поперёк')
text(100,743,'Трасса B огибает коллекторы и входит под штоком.', 'note')

sx, sy = 930, 540
def side(x,z): return sx+.8*x,sy-.8*z
parts.append(f'<rect x="{sx+.8*xmin}" y="{sy-.8*zmax}" width="{.8*size[0]}" height="{.8*size[2]}" fill="#fafbfc" stroke="#6c7b83" stroke-dasharray="7 5"/>')
line(side(-230,-51),side(230,-51),'#465c66',6)
for x,y,z in meta['floor_anchors']:
    x-=origin[0];z-=origin[2]
    line(side(x,z+7),side(x,-51),'#465c66',5)
    line(side(x-6,z),side(x+6,z),'#465c66',4)
line(side(-144,245),side(144,245),'#cd7b36',30)
line(side(-128,170),side(128,170),'#368bad',50)
line(side(-196,61),side(196,61),'#6f858d',40)
line(side(0,-90),side(0,30),'#bc9159',8)
line(side(-230,-90),side(-12,-90),'#bc9159',8)
dimension((1190,sy-.8*zmax),(1190,sy-.8*zmin),f'{size[2]:.1f}'.replace('.',','),1167,sy-105)
text(695,720,'Вид сбоку: ось выходного вала Z = 400')
text(695,743,'Стойки до пола не входят в габарит ядра.', 'note')
line((40,775),(1220,775),'#172c35',1)
text(45,800,'Начало двигателя в кузове: X=3210; Y=0; Z=490. Резерв: 600 × 500 × 500.', 'note')
text(45,822,'Объём: 7πD²S/4 = 0,203 л. Обе стороны: 7π(2D²−dшт²)S/4 = 0,394 л за оборот кривошипов.', 'note')
text(45,844,'Концепт, не изготовительный чертёж. Трассы здесь по осям; реальные гибы, изоляция и поверхности — в GLB.', 'note')
text(1045,865,'09.10.2026 · лист 10', 'note')
parts.append('</svg>')
svg=''.join(parts)
dest=root/'drawings/10-compact-radial.svg'
dest.write_text(svg)
# Export the same simple SVG primitives as vector PDF without a Cairo runtime.
pdfmetrics.registerFont(TTFont('CompactArial','/System/Library/Fonts/Supplemental/Arial.ttf'))
scale = 420/1260*72/25.4
pdf = canvas.Canvas(str(dest.with_suffix('.pdf')),pagesize=(1260*scale,891*scale))
pdf.scale(scale,scale)
for el in ET.fromstring(svg):
    tag=el.tag.split('}')[-1];a=el.attrib
    if tag in ['defs','style']:continue
    stroke=a.get('stroke','none');fill=a.get('fill','none')
    if tag=='path' and a.get('class')=='dim':stroke='#172c35'
    if stroke!='none':pdf.setStrokeColor(HexColor(stroke))
    if fill!='none':pdf.setFillColor(HexColor(fill))
    pdf.setLineWidth(float(a.get('stroke-width',1)))
    pdf.setDash([float(x) for x in a.get('stroke-dasharray','').split()] or [])
    if tag=='rect':pdf.rect(float(a.get('x',0)),891-float(a.get('y',0))-float(a['height']),float(a['width']),float(a['height']),stroke=int(stroke!='none'),fill=int(fill!='none'))
    elif tag=='circle':pdf.circle(float(a['cx']),891-float(a['cy']),float(a['r']),stroke=int(stroke!='none'),fill=int(fill!='none'))
    elif tag=='line':pdf.line(float(a['x1']),891-float(a['y1']),float(a['x2']),891-float(a['y2']))
    elif tag=='polyline':
        points=[list(map(float,x.split(','))) for x in a['points'].split()];path=pdf.beginPath();path.moveTo(points[0][0],891-points[0][1])
        for x,y in points[1:]:path.lineTo(x,891-y)
        pdf.drawPath(path,stroke=1,fill=0)
    elif tag=='path':
        pts=a['d'].replace('M','').replace('L','').split();coords=[list(map(float,x.split(','))) for x in pts]
        pdf.line(coords[0][0],891-coords[0][1],coords[1][0],891-coords[1][1])
        for n,other in [(coords[0],coords[1]),(coords[1],coords[0])]:
            dx,dy=other[0]-n[0],other[1]-n[1];length=math.hypot(dx,dy);dx/=length;dy/=length
            for sign in [-1,1]:pdf.line(n[0],891-n[1],n[0]+6*dx+sign*3*dy,891-(n[1]+6*dy-sign*3*dx))
    elif tag=='text':
        pdf.setFillColor(HexColor('#172c35'));pdf.setFont('CompactArial',27 if a.get('class')=='title' else 14 if a.get('class')=='note' else 16)
        pdf.drawString(float(a['x']),891-float(a['y']),el.text or '')
pdf.save()
print('Created compact radial dimensioned SVG/PDF concept sheet')
