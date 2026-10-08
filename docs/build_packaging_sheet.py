"""Revised layout drawing: envelopes and placement, not fabrication drawings."""
from pathlib import Path
from html import escape
import json,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent
layout=json.loads((ROOT/'layout-revised.json').read_text())
parts=[*layout['parts'],{'id':'PMP','name':'Cat Pumps 5CP2120W','xyz':layout['pump_xyz'],'size':[259.25,254,146.2],'color':'#0891b2'}]
def size(p):
 v=p['size'];r=p.get('rotation_deg',[0,0,0]);x,y,z=[math.radians(t) for t in r]
 # XYZ Euler, matching Three.js Group.rotation.
 cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 m=[[cy*cz,-cy*sz,sy],[sx*sy*cz+cx*sz,-sx*sy*sz+cx*cz,-sx*cy],[-cx*sy*cz+sx*sz,cx*sy*sz+sx*cz,cx*cy]]
 return [round(sum(abs(m[i][j])*v[j] for j in range(3)),2) for i in range(3)]
pdfmetrics.registerFont(TTFont('Arial','/System/Library/Fonts/Supplemental/Arial.ttf'))
W,H=1600,1120;pdf=canvas.Canvas(str(ROOT/'drawings/06-revised-layout.pdf'),pagesize=(W,H));pdf.setFillColor(HexColor('#ffffff'));pdf.rect(0,0,W,H,stroke=0,fill=1);svg=[]
def text(x,y,t,sz=16,color='#153145'):
 svg.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{sz}" fill="{color}">{escape(t)}</text>');pdf.setFillColor(HexColor(color));pdf.setFont('Arial',sz);pdf.drawString(x,H-y,t)
def line(x,y,x2,y2,color='#778c99',dash=False):
 svg.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{color}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>');pdf.setStrokeColor(HexColor(color));pdf.setDash([5,4] if dash else []);pdf.line(x,H-y,x2,H-y2)
def rect(x,y,w,h,color,fill=False,r=0):
 svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="'+(color if fill else 'none')+f'" fill-opacity=".12" stroke="{color}"/>');pdf.setStrokeColor(HexColor(color));pdf.setFillColor(HexColor(color));pdf.setFillAlpha(.12 if fill else 1);pdf.roundRect(x,H-y-h,w,h,r,stroke=1,fill=int(fill));pdf.setFillAlpha(1)
text(45,45,'06 · ЗАЗ-968М · ПЕРЕРАБОТАННАЯ КОМПОНОВКА · 08.10.2026',25)
text(45,74,'Целевые габариты без уменьшения техники. Заднее сиденье удаляется. Внутренние размеры не измерены.',16,'#b45309')
text(45,100,'Не для изготовления. Изменения массы, теплоизоляция, крепления, сервисные зазоры и дорожный допуск не рассчитаны.',15,'#b45309')
s=.255;ox=80;oy=175
text(ox,oy-25,'ВИД СВЕРХУ · перед слева · размеры в мм',18)
rect(ox,oy,3765*s,1490*s,'#58788a',r=25)
rect(ox+1040*s,oy+(745-630)*s,(2780-1040)*s,1260*s,'#9aabb4',r=12)
for p in parts:
 x,y,z=p['xyz'];a,b,c=size(p);rect(ox+x*s,oy+(y+745)*s,a*s,b*s,p['color'],True);text(ox+x*s+3,oy+(y+745)*s+18,p['id'],14,p['color'])
for x in [675,2835]:line(ox+x*s,oy-8,ox+x*s,oy+1490*s+8,dash=True)
line(ox+675*s,oy-8,ox+2835*s,oy-8);text(ox+1650*s,oy-16,'2160',14)
text(ox,oy+1490*s+27,'X осей 675 / 2835 — оценка реконструкции по фото; в старом расчёте 800 / 2960.',14)
base=1020
text(ox,600,'ВИД СБОКУ · разные высоты показывают разнесение агрегатов',18)
# Reference outline only; actual reconstructed surfaces are inspected in the 3D viewer.
points=[(80,350),(80,830),(1040,865),(1420,1340),(2550,1340),(2910,865),(3685,830),(3685,350)]
for a,b in zip(points,points[1:]+points[:1]):line(ox+a[0]*s,base-a[1]*s,ox+b[0]*s,base-b[1]*s)
for x in [675,2835]:
 svg.append(f'<circle cx="{ox+x*s}" cy="{base-280*s}" r="{280*s}" fill="none" stroke="#7b8e99"/>');pdf.circle(ox+x*s,H-(base-280*s),280*s,stroke=1,fill=0)
for p in parts:
 x,y,z=p['xyz'];a,b,c=size(p);rect(ox+x*s,base-(z+c)*s,a*s,c*s,p['color'],True);text(ox+x*s+3,base-(z+c)*s+18,p['id'],14,p['color'])
line(ox,base,ox+3765*s,base);text(ox+1460*s,base+25,'3765 · высота сборки с конденсатором 1610',14)
x=1090;y=155
text(x,y,'ПРИНЯТЫЕ ГАБАРИТЫ / XYZ',18)
for i,p in enumerate(parts):
 yy=y+40+i*56;a,b,c=size(p);text(x,yy,p['id']+' · '+p['name'],14,p['color']);text(x,yy+21,'×'.join(f'{v:g}' for v in [a,b,c])+' · XYZ '+','.join(f'{v:g}' for v in p['xyz']),13)
for i,t in enumerate(['BRN ↔ STM: головка входит в камеру.','Это проектное сопряжение, камера не выбрана.','GBX: грубый короб конфликтует с условным полом.','Нужны реальный CAD КПП и обмер пола.','Приёмник 17,6 л не обеспечивает 57–95 л','из рекомендации TB002 для номинального B.','Конденсатор снаружи; 358 кВт не подтверждены.','Мотор насоса, арматура и трубные трассы','требуют дополнительного объёма.']):text(x,780+i*25,t,13,'#a34d13')
text(45,1095,'Источник координат: layout-revised.json. Проверка сетки: packaging-audit.json. Все зазоры предварительные.',14)
pdf.save();(ROOT/'drawings/06-revised-layout.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120"><rect width="1600" height="1120" fill="white"/>'+''.join(svg)+'</svg>')
print('Built drawings/06-revised-layout.pdf and .svg')
