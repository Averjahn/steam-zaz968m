"""Conceptual process/control diagrams and proposed panel, SVG and PDF."""
from pathlib import Path
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'drawings';OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial','/System/Library/Fonts/Supplemental/Arial.ttf'))

class Sheet:
    def __init__(self,name,title,w=1400,h=850):
        self.name=name;self.w=w;self.h=h;self.svg=[]
        self.pdf=canvas.Canvas(str(OUT/(name+'.pdf')),pagesize=(w,h))
        self.text(35,43,title,25)
        self.text(35,73,'Эскиз / 08.10.2026 / Не монтажная схема / Уставки и характеристики по паспорту оборудования',16,'#b91c1c')
    def text(self,x,y,t,size=16,color='#0f172a'):
        self.svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(t)}</text>')
        self.pdf.setFont('Arial',size);self.pdf.setFillColor(HexColor(color));self.pdf.drawString(x,self.h-y,t)
    def line(self,x,y,xx,yy,color='#334155',arrow=False):
        self.svg.append(f'<path d="M{x},{y} L{xx},{yy}" stroke="{color}" stroke-width="2" fill="none"/>')
        self.pdf.setStrokeColor(HexColor(color));self.pdf.setLineWidth(2);self.pdf.line(x,self.h-y,xx,self.h-yy)
        if arrow:
            import math
            a=math.atan2(yy-y,xx-x)
            for dd in [-.5,.5]:self.line(xx,yy,xx-12*math.cos(a+dd),yy-12*math.sin(a+dd),color)
    def box(self,x,y,w,h,labels,color='#334155'):
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f8fafc" stroke="{color}" stroke-width="2"/>')
        self.pdf.setFillColor(HexColor('#f8fafc'));self.pdf.setStrokeColor(HexColor(color));self.pdf.roundRect(x,self.h-y-h,w,h,8,stroke=1,fill=1)
        for i,t in enumerate(labels):self.text(x+12,y+27+i*24,t,16,color)
    def circle(self,x,y,r,color='#334155'):
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{color}" stroke-width="2"/>')
        self.pdf.setStrokeColor(HexColor(color));self.pdf.circle(x,self.h-y,r,stroke=1,fill=0)
    def save(self):
        self.text(35,self.h-30,'Параметры соединений, сечения кабелей, уставки защиты и диаметры труб требуют отдельного рабочего проекта.',15)
        (OUT/(self.name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif">'+''.join(self.svg)+'</g></svg>')
        self.pdf.save()

def flow():
    s=Sheet('02-process','02 • Пароводяной контур и механический привод')
    s.box(40,180,190,100,['Холодная вода','Подпитка / фильтр'],'#2563eb')
    s.box(300,180,220,100,['Горячий приемник','Обезмасливание','Деаэрация'],'#14b8a6')
    s.box(590,180,210,100,['Питательный насос','Обратный клапан'],'#7c3aed')
    s.box(890,180,240,110,['Парогенератор','Горелка / перегрев','P, T, проток / стенка'],'#ef4444')
    s.line(230,230,300,230,'#2563eb',True);s.line(520,230,590,230,'#14b8a6',True);s.line(800,230,890,230,'#7c3aed',True)
    s.box(890,390,240,110,['Сепаратор при нужде','Стоп-клапан / регулятор','Дренажи'],'#ef4444')
    s.line(1010,290,1010,390,'#ef4444',True)
    s.box(890,580,240,100,['Паровая машина','Смазка / дренажи','Ограничитель оборотов'],'#ea580c')
    s.line(1010,500,1010,580,'#ef4444',True)
    s.box(1190,580,175,100,['Согласование','Сцепление','КПП / колеса'])
    s.line(1130,630,1190,630,'#334155',True)
    s.box(350,580,260,110,['Конденсатор / вентиляторы','Удаление воздуха','P выпуска / T выхода'],'#0284c7')
    s.line(890,630,610,630,'#0284c7',True);s.line(410,580,410,280,'#14b8a6',True)
    s.box(1180,180,190,100,['Механический','предохранительный','клапан'],'#ef4444')
    s.line(1130,205,1180,205,'#ef4444',True)
    s.text(1160,330,'Сброс — отдельная трасса;',15);s.text(1160,355,'нет отсечного крана',15);s.text(1160,380,'между котлом и защитой.',15)
    s.box(40,390,220,110,['Топливо / фильтр','Насос / контроллер','Отсечные клапаны'],'#a16207')
    s.line(260,440,825,440,'#a16207');s.line(825,440,825,265,'#a16207');s.line(825,265,890,265,'#a16207',True)
    s.text(40,750,'Отвод продуктов сгорания — отдельный тракт. Пар, дым и горячая вода не проходят в салон.',18)
    s.save()

def control():
    s=Sheet('03-controls','03 • Управление и независимые защиты')
    s.box(40,135,330,160,['Педаль / задатчик тяги','Старт / останов','Дисплей P, T, вода, обороты','Квитирование после проверки','Кнопка аварийного останова'],'#2563eb')
    s.box(500,135,320,160,['Регулятор процесса','Подача воды и горелка','Запрос тяги к паровой машине','Вентиляторы / питание','Журнал ошибок'],'#7c3aed')
    s.box(980,135,360,160,['Исполнительные устройства','Паровой клапан fail-close','Контроллер горелки','Питательный насос','Регулятор обдува'],'#ea580c')
    s.line(370,205,500,205,'#2563eb',True);s.line(820,205,980,205,'#7c3aed',True)
    s.box(40,405,350,185,['Независимые входы защиты','Предельное давление','Предельная T стенки / пара','Проток или низкий уровень*','Пламя / давление топлива','Предельные обороты'],'#b91c1c')
    s.box(500,405,330,185,['Защитная цепь / контроллер','Останов топлива и тяги','Контроль обрыва / питания','Защелка аварии','Ручной сброс после проверки','Без автоматического рестарта'],'#b91c1c')
    s.box(980,405,360,185,['Отдельные защитные выходы','Снять разрешение горелки','Закрыть топливные клапаны','Закрыть паровой стоп-клапан','Послепродувка / охлаждение','По алгоритму изготовителя'],'#b91c1c')
    s.line(390,475,500,475,'#b91c1c',True);s.line(830,475,980,475,'#b91c1c',True)
    s.text(40,655,'* Для проточного генератора — проток и температура стенки; уровень только в емкостях, где он физически применим.',17)
    s.text(40,690,'Потеря экрана не должна отменять защиты. Механический предохранительный клапан действует независимо.',17)
    s.text(40,725,'Аварийный останов не означает резкое опорожнение котла. Остаточное тепло и давление сохраняются.',17)
    s.save()

def panel():
    s=Sheet('04-dashboard','04 • Предложение дополнительной приборной панели',1400,850)
    scale=2.5;ox=90;oy=150;w=420*scale;h=180*scale
    s.box(ox,oy,w,h,[])
    labels=['Давление','Температура пара','Обороты','Запас воды']
    for xx,lab in zip([45,135,225,315],labels):
        cx=ox+xx*scale;cy=oy+48*scale;s.circle(cx,cy,26*scale);s.text(cx-40,cy+95,lab,17)
        s.text(cx-27,cy+6,'Ø52*',17)
    s.box(ox+115*scale,oy+112*scale,140*scale,40*scale,['Статус установки / аварии'])
    for xx,col,lab in [(45,'#16a34a','СТАРТ'),(80,'#64748b','СТОП'),(330,'#ef4444','АВАРИЯ')]:
        cx=ox+xx*scale;cy=oy+133*scale;s.circle(cx,cy,12*scale,col);s.text(cx-35,cy+62,lab,17,col)
    s.line(ox,oy-30,ox+w,oy-30);s.text(ox+w/2-15,oy-40,'420',18)
    s.line(ox+w+35,oy,ox+w+35,oy+h);s.text(ox+w+45,oy+h/2,'180',18)
    s.text(90,665,'Все размеры панели — мм. Это целевой эскиз; место в штатной панели ЗАЗ не проверено.',18)
    s.text(90,702,'* Посадочный диаметр зависит от выбранного прибора. Ø52 здесь условный.',18)
    s.text(90,739,'В салон выводятся электрические сигналы. Датчики и механический манометр остаются у установки.',18)
    s.save()

def alternative():
    import json
    d=json.loads((ROOT/'layout-vw-inspired.json').read_text())
    s=Sheet('05-vw-inspired','05 • ЗАЗ: вторая архитектура по примеру MSS VW',1500,950)
    scale=.29;ox=70;oy=170
    s.text(ox,130,'Вид сбоку. Предложение для ЗАЗ; размеры исторического VW не восстановлены.',19)
    s.box(ox,oy+350,3765*scale,170,[], '#64748b')
    s.box(ox+1100*scale,oy+110,900*scale,240,[], '#f43f5e')
    s.text(ox+1200*scale,oy+170,'Два передних места',17)
    for part in d['parts']:
        x,y,z=part['xyz'];a,b,c=part['size'];xx=ox+x*scale;yy=oy+(1700-z-c)*scale
        s.box(xx,yy,a*scale,c*scale,[part['id']],part['color'])
    for x in [800,2960]:s.circle(ox+x*scale,oy+(1700-280)*scale,280*scale,'#64748b')
    s.line(ox+2020*scale,oy+110,ox+2020*scale,oy+510,'#b91c1c')
    for yy,t in [(205,'STM — генератор'),(240,'в зоне заднего сиденья'),(295,'CND — наружный'),(330,'конденсатор'),(385,'Перегородка показана'),(420,'как требование проекта;'),(455,'ее защита не рассчитана.')]:s.text(1160,yy,t,17)
    s.text(70,750,'Все внутренние координаты, размеры и высоты — допущения. Посадка в реальный кузов не подтверждена.',18)
    s.text(70,790,'Требуются новые расчеты массы, охлаждения, креплений, внешних выступов и защитного разделения салона.',18)
    s.text(70,830,'Общие внешние размеры исходного ЗАЗ не сохраняются: наружный конденсатор выходит за габарит кузова.',18)
    s.save()
    sc=['// Target alternative envelopes for ZAZ, NOT original VW geometry; mm.']
    for a in d['parts']:
        rgb=[int(a['color'][i:i+2],16)/255 for i in (1,3,5)]
        sc.append(f'color({rgb}) translate({a["xyz"]}) cube({a["size"]});')
    (ROOT/'assembly-vw-inspired.scad').write_text('\n'.join(sc))

if __name__=='__main__':flow();control();panel();alternative()
