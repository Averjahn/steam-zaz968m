"""Locate concept support feet on the supplied game's actual floor triangles.
Coordinates are graphical contact points, NOT verified load bearing points of a car.
"""
from pathlib import Path
import json,struct,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent;b=(ROOT/'models/zaz-968m-yatloo.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);data=b[28+n:]
def arr(ai):
 a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];typ={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];dim={'VEC3':3,'SCALAR':1}[a['type']];return np.frombuffer(data,dtype=typ,count=a['count']*dim,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,dim)
tris={}
for o in g['nodes']:
 if 'mesh' not in o or not any(x in o['name'] for x in ['Plane136','Plane113','Plane158']):continue
 p=g['meshes'][o['mesh']]['primitives'][0];v=arr(p['attributes']['POSITION']);v=np.column_stack([v[:,0],-v[:,2],v[:,1]])*1000
 t=v[arr(p['indices']).reshape(-1).reshape(-1,3)] if 'indices' in p else v.reshape(-1,3,3);tris[o['name']]=t
l=json.loads((ROOT/'layout-internal.json').read_text());plates=[];anchors=[]
# Thin trays at the actual lower bounding datum, with vertical legs to source floor.
# Four legs per tray; rail/decorative beams are added independently in the viewer.
for id,pos,size in [
 ('ENG',[2980,-195,439],[460,390,6]),
 ('STM',[2120,75,644],[480,440,6]),
 ('BRN',[2140,-400,644],[440,430,6]),
 ('CND-R',[3000,-515,559],[500,105,6]),('CND-L',[3000,410,559],[500,105,6]),
 ('PMP',[2100,-370,464],[280,274,6]),('MOTOR',[2080,-570,449],[280,165,6]),
 ('WTR',[400,-430,629],[450,400,6]),('RCV',[250,10,629],[620,400,6]),
 ('FUE',[2050,180,469],[450,330,6]),('ELE',[2050,0,354],[100,120,6]),
 ('SEP',[2280,-580,644],[120,120,6]),('BOOST',[880,160,810],[100,60,6]),('BOOST-FILTER',[895,310,824],[60,60,6])]:
 plates.append(dict(id=id,xyz=pos,size=size))
 for x in [pos[0]+(50 if id=='RCV' else 20),pos[0]+(250 if id=='FUE' else size[0]-20)]:
  for y in [pos[1]+18,pos[1]+size[1]-18]:
   hits=[]
   for name,t in tris.items():
    a=t[:,0];u=t[:,1]-a;v=t[:,2]-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0];ok=np.abs(den)>1e-6;safe=np.where(ok,den,1);du=((x-a[:,0])*v[:,1]-(y-a[:,1])*v[:,0])/safe;dv=(u[:,0]*(y-a[:,1])-u[:,1]*(x-a[:,0]))/safe;k=ok&(du>=-1e-5)&(dv>=-1e-5)&(du+dv<=1.00001)
    hits.extend((float(z),name) for z in (a[:,2]+du*u[:,2]+dv*v[:,2])[k] if z<pos[2]-2)
   if not hits:raise RuntimeError(f'No supporting floor below {id} at {x},{y}')
   z,name=max(hits);anchors.append(dict(id=id,foot_xyz=[x,y,z],tray_z=pos[2],body_node=name,leg_length_mm=pos[2]-z,confirmed_load_bearing=False))
meta=dict(status='Graphical support contact with supplied game triangles; strength/real-car dimensions unverified',body_sha256=hashlib.sha256(b).hexdigest(),units='mm',plates=plates,anchors=anchors,limitations=['Площадки касаются поверхностей игрового кузова, а не подтверждённых усиленных зон реального автомобиля.','Плоская площадка на наклонном полу — условная; нужны фасонные опоры по обмерам.','Сечения, материал, крепёж, усталость, вибрации и аварийные нагрузки не рассчитаны.','Случайные пересечения стоек и панелей остаются в аудите; контакт опоры с полом не исключает их автоматически.'])
(ROOT/'models/internal-mounts.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');l['mount_register']=meta
(ROOT/'layout-internal.json').write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'trays':len(plates),'contact_points':len(anchors),'min_leg_mm':min(a['leg_length_mm'] for a in anchors)},ensure_ascii=False))
