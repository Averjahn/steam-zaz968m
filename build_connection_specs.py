"""Named, oriented concept ports; CAD-derived Cat axes are kept distinct from hypotheses."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent
ports={}
def port(id,anchor,face,od,bore,kind='weld-neck',basis='Проектный патрубок; изделие и прочность не подтверждены',thread=None):
 d=[face[i]-anchor[i] for i in range(3)];L=math.sqrt(sum(x*x for x in d));ports[id]=dict(id=id,owner=id.split('.')[0],anchor_mm=anchor,face_mm=face,outward=[x/L for x in d],od_mm=od,bore_mm=bore,kind=kind,basis=basis,thread=thread)
port('STM.steam',[2620,335,1180],[2630,335,1180],48,40)
port('STM.feed',[2530,300,750],[2530,260,750],20,14)
port('STM.relief',[2595,310,1180],[2595,270,1180],28,20)
port('STM.flueOutlet',[2520,460,1050],[2660,460,1050],82,80,'duct')
port('ENG.inlet',[3110,-120,715],[3110,-170,715],48,40)
port('ENG.exhaustR',[3330,-120,705],[3330,-155,705],80,70)
# A second front valve outlet replaces the previous unattached rear-cylinder endpoint.
port('ENG.exhaustL',[3110,-120,625],[3110,-160,625],80,70)
port('CND.inletR',[3330,-410,765],[3330,-365,765],80,70)
port('CND.inletL',[3430,410,765],[3430,365,765],80,70)
port('CND.drain',[3500,-490,600],[3540,-490,600],24,18)
port('CND.drainL',[3450,410,600],[3450,365,600],24,18)
port('CND.pumpIn',[3500,-440,600],[3540,-440,600],24,18)
port('CND.returnPumpOut',[3590,-440,600],[3625,-440,600],24,18)
port('WTR.out',[850,-170,700],[885,-170,700],20,14)
port('RCV.makeup',[870,70,700],[905,70,700],20,14)
port('RCV.return',[870,260,780],[905,260,780],24,18)
port('RCV.out',[800,480,675],[800,520,675],26,20)
# STEP native axes: X-width, Y-height, Z-length; CAD origin min=(-127,-34,-20).
# Side fluid bores: X=+66, inlet(Y=0,Z=49.5), outlet(Y=72,Z=22).
# Not the oil cap at (20,112.2,119). Drawing specifies 1/2 NPT inlet and 3/8 NPT discharge.
for name,a in [('inletConcept',[2179.5,-167,504]),('outletConcept',[2152,-167,576])]:
 port('PMP.'+name,a,[a[0],-117,a[2]],26 if name=='inletConcept' else 20,20 if name=='inletConcept' else 14,'thread-adapter','Ось бокового отверстия из заводского STEP; размер резьбы из паспорта. Геометрия переходника проектная.', '1/2 NPT(M) → ID20' if name=='inletConcept' else '3/8 NPT(M) → ID14')
port('SEP.inlet',[2340,-520,890],[2340,-520,935],28,20)
port('BODY.flushRearExhaust',[3729,-250,700],[3725,-250,700],82,80,'duct','Проектное выпускное окно и его крепление; кузов ещё требует обмера.')
port('FUE.out',[2190,180,540],[2190,140,540],12,8)
port('BRN.fuelConcept',[2470,-292,720],[2470,-327,720],12,8)
points={
'PIPE_STEAM':[[2630,335,1180],[2780,335,1180],[2780,-300,850],[2910,-300,715],[3110,-300,715],[3110,-170,715]],
'PIPE_EXHAUST_R':[[3330,-155,705],[3330,-200,705],[3330,-320,765],[3330,-365,765]],
'PIPE_EXHAUST_L':[[3110,-160,625],[3110,-310,625],[3670,-310,520],[3670,190,520],[3430,190,765],[3430,365,765]],
'PIPE_RETURN':[[3625,-440,600],[3700,-440,600],[3700,-600,550],[3100,-600,550],[3030,-600,760],[2650,-600,760],[2550,-665,760],[1100,-665,760],[1010,-460,760],[1010,260,780],[905,260,780]],
'PIPE_BALANCE':[[3450,365,600],[3450,285,600],[3450,285,400],[3650,285,400],[3650,-490,400],[3650,-490,600],[3540,-490,600]],
'PIPE_MAKEUP':[[885,-170,700],[980,-170,700],[980,70,700],[905,70,700]],
'PIPE_SUCTION':[[800,520,675],[800,620,675],[1020,620,675],[1020,340,930],[925,340,930],[925,190,930],[925,190,840],[1130,190,840],[1130,625,420],[1970,625,420],[1970,-50,420],[1970,-50,504],[2179.5,-50,504],[2179.5,-117,504]],
'PIPE_FEED':[[2152,-117,576],[2152,-60,576],[2710,-60,576],[2710,100,750],[2530,100,750],[2530,260,750]],
'PIPE_FUEL':[[2190,140,540],[2190,60,540],[2055,60,540],[2055,-400,540],[2055,-400,720],[2470,-400,720],[2470,-327,720]],
'PIPE_FLUE':[[2660,460,1050],[3000,460,1050],[3000,-250,950],[3450,-250,950],[3600,-250,700],[3725,-250,700]],
'PIPE_RELIEF':[[2595,270,1180],[2595,100,1180],[2455,100,1180],[2455,-520,1180],[2340,-520,1035],[2340,-520,935]]}
# Source-specific fuel and flue fittings. No fuel hose for solid fuel / electrical heat.
ports['PMP.inletConcept'].update(entry_od_mm=21.34,entry_bore_mm=16)
ports['PMP.outletConcept'].update(entry_od_mm=17.15,entry_bore_mm=12)
variants={}
for sid in ['diesel','wood','pellets','lpg','electric']:
 v={'ports':{k:dict(p) for k,p in ports.items()},'route_points':{k:p for k,p in points.items()}}
 if sid in ['wood','pellets']:
  for key in ['STM.flueOutlet','BODY.flushRearExhaust']:v['ports'][key]={**v['ports'][key],'od_mm':102,'bore_mm':100}
 if sid=='lpg':
  v['ports']['FUE.out']={**ports['FUE.out'],'anchor_mm':[2490,345,540],'face_mm':[2505,345,540],'outward':[1,0,0]}
  v['ports']['BRN.fuelConcept']={**ports['BRN.fuelConcept'],'anchor_mm':[2475,-300,705],'face_mm':[2475,-335,705],'outward':[0,-1,0]}
  v['route_points']['PIPE_FUEL']=[[2505,345,540],[2750,345,540],[2750,345,740],[2750,-400,740],[2475,-400,705],[2475,-335,705]]
 if sid in ['wood','pellets','electric']:
  for key in ['FUE.out','BRN.fuelConcept']:v['ports'].pop(key)
  v['route_points'].pop('PIPE_FUEL')
 if sid=='electric':
  for key in ['STM.flueOutlet','BODY.flushRearExhaust']:v['ports'].pop(key)
  v['route_points'].pop('PIPE_FLUE')
 variants[sid]=v
out=dict(units='mm',status='Geometric concept joints, not leak/pressure certification',ports=ports,route_points=points,variants=variants,inline_components=[{'id':'BOOST.filter','start_mm':[925,295,930],'end_mm':[925,245,930],'bore_mm':20,'od_mm':48},{'id':'BOOST.pump','start_mm':[990,190,840],'end_mm':[1075,190,840],'bore_mm':20,'od_mm':48}],sources=[{'title':'Cat Pumps dimensional drawing, page 4','url':'https://www.catpumps.com/sites/default/files/2025-09/5CP2120W_L.pdf'},{'title':'Cat Pumps factory STEP','url':'https://www.catpumps.com/sites/default/files/2026-07/5CP2120W_0.STEP'}],limitations=['Геометрическое совпадение не подтверждает герметичность и прочность.','Резьба NPT — условный графический профиль, не модель для изготовления; детали и уплотнения надо выбрать по давлению/температуре.','Все патрубки, кроме осей боковых отверстий Cat, — проектные; требуются чертежи реальных агрегатов.'])
(ROOT/'connection-specs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(ROOT/'web/connection-data.js').write_text('// Generated by build_connection_specs.py; project port hypotheses, mm.\nexport const connectionSpecs='+json.dumps(out,ensure_ascii=False,separators=(',',':'))+';\n')
print('Named ports:',len(ports))
