"""Create preliminary orthographic SVG/DXF sheets and CAD envelopes (mm).
No pressure-containing or load-bearing fabrication geometry is provided.
"""
import json
import math
from pathlib import Path
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parent
LAY=json.loads((ROOT/'layout.json').read_text())
OUT=ROOT/'drawings'; OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial','/System/Library/Fonts/Supplemental/Arial.ttf'))

def intersects(a,b,padding=0):
    return all(a['xyz'][i]-padding < b['xyz'][i]+b['size'][i] and b['xyz'][i]-padding < a['xyz'][i]+a['size'][i] for i in range(3))

def checks():
    parts=LAY['parts']; direct=[]; service=[]
    for i,a in enumerate(parts):
        if intersects(a,LAY['excluded_solid']): direct.append([a['id'],'CAB'])
        for b in parts[i+1:]:
            if intersects(a,b): direct.append([a['id'],b['id']])
            elif intersects(a,b,100): service.append([a['id'],b['id']])
    return {'solid_intersections':direct,'clearance_under_100mm':service,
            'not_checked':['реальные стенки кузова','колесные ниши и полный ход подвески','рулевое управление','крепления','трассы с диаметром и изоляцией','тепловые зоны','демонтаж агрегатов','ударные зоны'],
            'result':'Отсутствие пересечений целевых параллелепипедов не доказывает посадку'}

def scad_obj():
    lines=['// PRELIMINARY ENVELOPES ONLY. Units mm. NOT FOR FABRICATION.', '$fn=32;']
    for p in LAY['parts']:
        c=p['color'];rgb=[int(c[i:i+2],16)/255 for i in (1,3,5)]
        lines.append(f'// {p["id"]}: {p["name"]}')
        lines.append(f'color({rgb}) translate({p["xyz"]}) cube({p["size"]});')
    # Body wireframe, plus an approximate passenger compartment outline.
    for x in [0,3765]:
        lines.append(f'color([0.6,0.6,0.6,0.3]) translate([{x},-745,240]) cube([8,1490,500]);')
    lines.append('color([0.6,0.6,0.6,0.2]) translate([0,-745,240]) cube([3765,1490,8]);')
    lines.append('color([0.6,0.6,0.6,0.12]) translate([1100,-620,330]) cube([1370,1240,970]);')
    for x in [800,2960]:
        for y in [-615,615]:
            lines.append(f'color([0.2,0.2,0.2]) translate([{x},{y},280]) rotate([90,0,0]) cylinder(r=280,h=145,center=true);')
    (ROOT/'assembly.scad').write_text('\n'.join(lines))
    verts=[];faces=[];obj=['# target envelopes only; mm','mtllib assembly.mtl'];mtl=[]
    for p in LAY['parts']:
        x,y,z=p['xyz'];a,b,c=p['size'];base=len(verts)
        vv=[(x,y,z),(x+a,y,z),(x+a,y+b,z),(x,y+b,z),(x,y,z+c),(x+a,y,z+c),(x+a,y+b,z+c),(x,y+b,z+c)]
        obj += ['o '+p['id'],'usemtl '+p['id']]+['v '+' '.join(map(str,v)) for v in vv]
        for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            obj.append('f '+' '.join(str(base+i+1) for i in f))
        verts+=vv
        rgb=[int(p['color'][i:i+2],16)/255 for i in (1,3,5)]
        mtl+=['newmtl '+p['id'],'Kd '+' '.join(map(str,rgb))]
    (ROOT/'assembly.obj').write_text('\n'.join(obj));(ROOT/'assembly.mtl').write_text('\n'.join(mtl))

def sheet():
    W,H=1600,1120; svg=[]; dxf=['0','SECTION','2','ENTITIES']
    pdf=canvas.Canvas(str(OUT/'01-layout.pdf'),pagesize=(W,H))
    def line(x1,y1,x2,y2,color='#334155',dash=False):
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.4"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
        pdf.setStrokeColor(HexColor(color));pdf.setDash([5,4] if dash else []);pdf.line(x1,H-y1,x2,H-y2)
        dxf.extend(['0','LINE','8','OUTLINE','10',str(x1),'20',str(H-y1),'11',str(x2),'21',str(H-y2)])
    def text(x,y,t,size=16,color='#0f172a'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(t)}</text>')
        pdf.setFont('Arial',size);pdf.setFillColor(HexColor(color));pdf.drawString(x,H-y,t)
    def rect(x,y,w,h,color='#334155',fill=False):
        if fill:
            svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.13"/>')
            pdf.setFillColor(HexColor('#f1f5f9'));pdf.rect(x,H-y-h,w,h,stroke=0,fill=1)
        for aa,bb in [((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))]:line(*aa,*bb,color)
    def dim(x1,y1,x2,y2,label):
        line(x1,y1,x2,y2)
        for x,y in [(x1,y1),(x2,y2)]:line(x-5,y+5,x+5,y-5)
        text((x1+x2)/2-25,(y1+y2)/2-7,label,14)
    text(45,44,'ЗАЗ-968М • ЭСКИЗ КОМПОНОВКИ B • 08.10.2026',25)
    text(45,72,'Целевые внешние габариты. Внутренние размеры кузова и посадка не подтверждены. Не для изготовления.',16,'#b91c1c')
    # Projection scale is graphical only; dimensions in the coordinate table govern.
    s=.255;ox=75;oy=145
    text(ox,oy-30,'ВИД СВЕРХУ • перед автомобиля слева',18)
    rect(ox,oy,3765*s,1490*s)
    cab=LAY['excluded_solid'];rect(ox+cab['xyz'][0]*s,oy+(cab['xyz'][1]+745)*s,cab['size'][0]*s,cab['size'][1]*s,'#94a3b8')
    for p in LAY['parts']:
        x,y,z=p['xyz'];a,b,c=p['size'];xx=ox+x*s;yy=oy+(y+745)*s
        rect(xx,yy,a*s,b*s,p['color'],True);text(xx+4,yy+20,p['id'],15,p['color'])
    for x in [800,2960]:line(ox+x*s,oy-12,ox+x*s,oy+1490*s+12,dash=True)
    dim(ox,oy+1490*s+30,ox+3765*s,oy+1490*s+30,'3765')
    dim(ox+800*s,oy-10,ox+2960*s,oy-10,'2160')
    # Side
    sy=640;text(ox,sy-26,'ВИД СБОКУ • профиль кузова условный',18)
    rect(ox,sy,3765*s,1400*s,'#94a3b8')
    for p in LAY['parts']:
        x,y,z=p['xyz'];a,b,c=p['size'];xx=ox+x*s;yy=sy+(1400-z-c)*s
        rect(xx,yy,a*s,c*s,p['color'],True);text(xx+4,yy+18,p['id'],14,p['color'])
    line(ox,sy+1400*s,ox+3765*s,sy+1400*s)
    for x in [800,2960]:
        # wheel circle svg and pdf (DXF circle uses paper-space coordinates)
        cx=ox+x*s;cy=sy+(1400-280)*s;rr=280*s
        svg.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="#475569"/>')
        pdf.setStrokeColor(HexColor('#475569'));pdf.circle(cx,H-cy,rr,stroke=1,fill=0)
        dxf.extend(['0','CIRCLE','8','WHEEL','10',str(cx),'20',str(H-cy),'40',str(rr)])
    # Coordinate table
    tx=1090;text(tx,120,'КООРДИНАТЫ / ГАБАРИТЫ, мм',18)
    for i,p in enumerate(LAY['parts']):
        yy=155+i*84;text(tx,yy,p['id']+' '+p['name'],16,p['color'])
        text(tx,yy+22,'XYZ: '+', '.join(map(str,p['xyz'])),14)
        text(tx,yy+43,'L×W×H: '+' × '.join(map(str,p['size'])),14)
    text(tx,865,'Система координат:',16);text(tx,892,'X — назад; Y — влево; Z — вверх.',14)
    text(tx,917,'Передняя ось X=800 условно.',14);text(tx,942,'Размеры агрегатов — задания поставщикам.',14)
    text(45,1050,'01 / Габаритный эскиз / Все размеры — мм / Координаты и размеры заданы в layout.json / Масштаб рисунка условный',15)
    text(45,1080,'DXF этого листа в координатах листа. Для модели 1:1 использовать 01-layout-mm.dxf, OBJ или SCAD.',14,'#b91c1c')
    (OUT/'01-layout.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif">'+''.join(svg)+'</g></svg>')
    pdf.save();dxf+=['0','ENDSEC','0','EOF'];(OUT/'01-layout-sheet.dxf').write_text('\n'.join(dxf))
    # Actual world coordinates, top view at 1:1 in millimetres, separate layer per part.
    d=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
    for p in LAY['parts']+[{'id':'BODY','xyz':[0,-745,0],'size':[3765,1490,1400]}]:
        x,y,_=p['xyz'];a,b,_=p['size']
        for aa,bb in [((x,y),(x+a,y)),((x+a,y),(x+a,y+b)),((x+a,y+b),(x,y+b)),((x,y+b),(x,y))]:
            d+=['0','LINE','8',p['id'],'10',str(aa[0]),'20',str(aa[1]),'11',str(bb[0]),'21',str(bb[1])]
    d+=['0','ENDSEC','0','EOF'];(OUT/'01-layout-mm.dxf').write_text('\n'.join(d))

if __name__=='__main__':
    scad_obj();sheet();(ROOT/'geometry-checks.json').write_text(json.dumps(checks(),ensure_ascii=False,indent=2))
    print(json.dumps(checks(),ensure_ascii=False))
