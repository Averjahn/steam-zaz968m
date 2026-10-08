"""Stock ZAZ-968M topology from 1991 album / parts catalog, dimensions hypothetical.
Static assembly only. GLB metres Y-up; OBJ mm Z-up, same origin as body.
"""
from pathlib import Path
import json, math, struct, hashlib
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'models'
P=json.loads((OUT/'zaz-968m-reconstruction.json').read_text())['parameters_mm']
XF=P['front_axle_x']['value'];XR=XF+P['wheelbase']['value'];Z=P['tyre_radius']['value']
colors={'steel':[.34,.42,.47,1],'spring':[.87,.48,.13,1],'rubber':[.09,.11,.12,1],'rod':[.72,.78,.81,1],'torsion':[.58,.61,.22,1]}
meshes=[]
def mesh(name,color='steel',group='front',**extra):
 m={'name':name,'color':color,'group':group,'v':[],'f':[],**extra};meshes.append(m);return m
def quad(m,a,b,c,d):
 i=len(m['v']);m['v'] += [a,b,c,d];m['f'] += [(i,i+1,i+2),(i,i+2,i+3)]
def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
 l=math.sqrt(sum(v*v for v in a));return tuple(v/l for v in a)
def basis(a,b):
 w=unit(sub(b,a));u=unit(cross(w,(0,0,1) if abs(w[2])<.9 else (1,0,0)));return u,cross(w,u)
def cylinder(m,a,b,r,n=24,inner=0):
 u,v=basis(a,b)
 def p(t,end,rad):return tuple(end[i]+rad*(u[i]*math.cos(t)+v[i]*math.sin(t)) for i in range(3))
 for j in range(n):
  t=2*math.pi*j/n;s=2*math.pi*(j+1)/n
  quad(m,p(t,a,r),p(s,a,r),p(s,b,r),p(t,b,r))
  for end in [a,b]:quad(m,p(t,end,inner),p(s,end,inner),p(s,end,r),p(t,end,r))
  if inner:quad(m,p(t,a,inner),p(s,a,inner),p(s,b,inner),p(t,b,inner))
def spring(m,a,b,r,wire,turns=8):
 u,v=basis(a,b);points=[]
 for j in range(turns*48+1):
  t=j/(turns*48);angle=t*turns*2*math.pi
  points.append(tuple(a[i]*(1-t)+b[i]*t+r*(u[i]*math.cos(angle)+v[i]*math.sin(angle)) for i in range(3)))
 # Each short wire segment is capped; visual helix has no invented spring rate.
 for a,b in zip(points,points[1:]):cylinder(m,a,b,wire,n=8)
def box(m,low,size):
 x,y,z=low;dx,dy,dz=size;v=[(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z),(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)]
 for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad(m,*(v[i] for i in f))
def shock(label,a,b,group,r):
 mid=tuple(a[i]*.34+b[i]*.66 for i in range(3));cylinder(mesh(label+' · амортизатор','steel',group),a,mid,24)
 cylinder(mesh(label+' · шток','rod',group),mid,b,9)
 sa=tuple(a[i]*.86+b[i]*.14 for i in range(3));sb=tuple(a[i]*.15+b[i]*.85 for i in range(3))
 m=mesh(label+' · пружина','spring',group);spring(m,sa,sb,r,6)
 for q in [sa,sb]:cylinder(m,(q[0],q[1],q[2]-4),(q[0],q[1],q[2]+4),r+10,inner=24)
 cylinder(mesh(label+' · верхняя опора','rubber',group),(b[0],b[1],b[2]-7),(b[0],b[1],b[2]+7),30)
# Two transverse tubes ahead of wheel centres, each houses a plate torsion.
for z,title in [(240,'нижняя'),(385,'верхняя')]:
 x=XF-190
 cylinder(mesh('Передняя ось · '+title+' труба'),(x,-475,z),(x,475,z),32,inner=24)
 torsion=mesh('Торсион · '+title+' пакет пяти пластин','torsion',collision=False)
 for i in range(5):box(torsion,(x-12,-460,z-10+i*4),(24,920,3.5))
for s,name in [(-1,'правая'),(1,'левая')]:
 y=s*P['front_track']['value']/2
 mounts=mesh('Передние кронштейны · '+name)
 for z in [240,385]:box(mounts,(XF-223,s*330-22,z-44),(66,44,88))
 for z,jz,title in [(240,Z-65,'нижний'),(385,Z+65,'верхний')]:
  arm=mesh('Передний '+title+' рычаг · '+name)
  # Bent forged longitudinal arms, not MacPherson struts.
  cylinder(arm,(XF-190,s*475,z),(XF-105,s*540,z),25)
  cylinder(arm,(XF-105,s*540,z),(XF,s*540,jz),22)
  cylinder(mesh('Передний шарнир · '+title+' '+name,'rubber'),(XF,s*515,jz),(XF,s*555,jz),29)
 knuckle=mesh('Поворотный кулак · '+name);cylinder(knuckle,(XF,s*553,Z-65),(XF-12,s*548,Z+65),24)
 cylinder(knuckle,(XF,s*548,Z),(XF,y,Z),24)
 cylinder(mesh('Передний барабан / ступица · '+name),(XF,y-s*60,Z),(XF,y-s*35,Z),107)
 shock('Передняя '+name,(XF-12,s*548,Z+65),(XF-30,s*500,810),'front',48)
# Stamped rear semi-trailing arms, two silent-block pivots per side.
for s,name in [(-1,'правая'),(1,'левая')]:
 y=s*P['rear_track']['value']/2
 arm=mesh('Задний сварной рычаг · '+name,group='rear')
 pivots=[(XR-430,s*290,350),(XR-320,s*545,350)]
 # Broad triangular plate with reinforcement ribs, topology visible in fig.39.
 outline=[pivots[0],pivots[1],(XR+35,s*545,280),(XR-35,s*480,280)]
 for top in [-16,16]:quad(arm,*(tuple(q[i]+(top if i==2 else 0) for i in range(3)) for q in outline))
 for a,b in zip(outline,outline[1:]+outline[:1]):
  quad(arm,(a[0],a[1],a[2]-16),(b[0],b[1],b[2]-16),(b[0],b[1],b[2]+16),(a[0],a[1],a[2]+16))
  cylinder(arm,a,b,15)
 for i,p in enumerate(pivots):
  cylinder(mesh('Задний сайлент-блок '+str(i+1)+' · '+name,'rubber','rear'),(p[0]-27,p[1],p[2]),(p[0]+27,p[1],p[2]),26)
  box(mesh('Задний кронштейн '+str(i+1)+' · '+name,group='rear'),(p[0]-40,p[1]-36,p[2]+18),(80,72,42))
 cylinder(mesh('Задний барабан / ступица · '+name,group='rear'),(XR,y-s*65,Z),(XR,y-s*32,Z),107)
 shock('Задняя '+name,(XR+45,s*520,305),(XR-20,s*500,795),'rear',62)
 # The adjacent stock drive shafts are distinct nodes, mechanical GBX interfaces.
 shaft=mesh('Полуось и кардан · '+name,'rod','drive',mechanicalInterface='GBX')
 cylinder(shaft,(XR-105,s*145,310),(XR,s*540,Z),15)
 cylinder(shaft,(XR,s*515,Z),(XR,s*556,Z),32)
 cylinder(mesh('Пыльник полуоси · '+name,'rubber','drive',mechanicalInterface='GBX'),(XR-105,s*145,310),(XR-88,s*225,304),38)
# Standard glTF exporter. All project coordinates remain absolute.
binary=bytearray();views=[];accessors=[];nodes=[];gmeshes=[]
def buf(values):
 while len(binary)%4:binary.append(0)
 start=len(binary);binary.extend(struct.pack('<'+'f'*len(values),*values));idx=len(views)
 views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':34962})
 accessor={'bufferView':idx,'componentType':5126,'count':len(values)//3,'type':'VEC3','min':[min(values[k::3]) for k in range(3)],'max':[max(values[k::3]) for k in range(3)]}
 accessors.append(accessor);return len(accessors)-1
materials=[{'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':c,'metallicFactor':.35,'roughnessFactor':.55}} for name,c in colors.items()]
for m in meshes:
 vv=[];nn=[]
 for f in m['f']:
  a,b,c=[m['v'][k] for k in f];normal=cross(sub(b,a),sub(c,a));length=math.sqrt(sum(n*n for n in normal))
  if length<1e-8:continue
  normal=tuple(n/length for n in normal)
  for x,y,z in [a,b,c]:vv += [x/1000,z/1000,-y/1000];nn += [normal[0],normal[2],-normal[1]]
 mi=len(gmeshes);pa=buf(vv);na=buf(nn)
 gmeshes.append({'name':m['name'],'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'material':list(colors).index(m['color'])}]})
 nodes.append({'name':m['name'],'mesh':mi,'extras':{'stockGroup':m['group'],'collision':m.get('collision',True),'mechanicalInterface':m.get('mechanicalInterface'),'geometryQuality':'stock topology from documentation; dimensions and mounts unmeasured'}})
asset={'asset':{'version':'2.0','generator':'Stock ZAZ-968M suspension hypothesis v1','copyright':'Project geometry CC BY-SA 3.0; documentary topology references in stock-suspension.json'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':gmeshes,'materials':materials,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,'extras':{'units':'metres','upAxis':'Y','staticOnly':True,'dimensionalAccuracy':'unknown'}}
js=json.dumps(asset,ensure_ascii=False,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
(OUT/'stock-suspension.glb').write_bytes(glb)
obj=['# Stock topology hypothesis, mm Z-up, NOT factory CAD. CC BY-SA 3.0','mtllib stock-suspension.mtl'];offset=1
for m in meshes:
 obj += ['o '+m['name'].replace(' ','_'),'usemtl '+m['color']]+['v '+' '.join(f'{v:.4f}' for v in p) for p in m['v']]+['f '+' '.join(str(i+offset) for i in f) for f in m['f']];offset+=len(m['v'])
(OUT/'stock-suspension.obj').write_text('\n'.join(obj)+'\n')
(OUT/'stock-suspension.mtl').write_text('\n'.join('newmtl '+n+'\nKd '+' '.join(map(str,c[:3])) for n,c in colors.items())+'\n')
allv=[p for m in meshes for p in m['v']];lo=[min(p[k] for p in allv) for k in range(3)];hi=[max(p[k] for p in allv) for k in range(3)]
checks={'meshes':len(nodes),'bounds_min_mm':lo,'bounds_max_mm':hi,'size_mm':[hi[k]-lo[k] for k in range(3)],'sha256':hashlib.sha256(glb).hexdigest(),'bytes':len(glb),'all_vertices_finite':all(math.isfinite(v) for p in allv for v in p),'scope':'generated geometry only; not real-car dimensional validation'}
assert checks['all_vertices_finite'] and lo[2]>0 and lo[1]>=-745 and hi[1]<=745
(OUT/'stock-suspension-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
meta={'name':'Штатная подвеска ЗАЗ-968М · статическая гипотеза','status':'Сохраняется в проекте, без переноса точек крепления для размещения агрегатов. Пригодность под новую массу ещё не рассчитана.','units':'mm; GLB metres Y-up, OBJ mm Z-up','accuracy':'Размеры деталей, точки крепления и положение под нагрузкой не измерены. Это не заводской CAD.','sources':[{'url':'https://djvu.online/file/yS7dQhMxx1lMm','title':'ЗАЗ-968М, Шейнин / Стрюк, 1991','sections':'листы 44–50: полуоси, передняя и задняя подвески, амортизаторы'},{'url':'https://www.saporoshez-968.de/968M_ersatzteilkatalog_russisch.pdf','title':'Каталог деталей ЗАЗ-968М','sections':'рис.39–43; PDF стр.52–58'}],'documented':{'wheelbase_mm':2160,'front_track_mm':1228,'rear_track_mm':1212,'front_architecture':'Две поперечные трубы, два торсиона из пяти пластин, четыре продольных рычага, поворотные кулаки, дополнительные пружины на амортизаторах.','rear_architecture':'Два штампованных сварных рычага на сайлент-блоках, пружины и телескопические амортизаторы.','front_total_wheel_travel_mm':150,'travel_note':'Альбом: общий ход при сбитом буфере. Нельзя автоматически делить на ±75 мм вокруг нашей статической позы.'},'model_assumptions':{'wheel_center_z_mm':Z,'front_axle_x_mm':XF,'rear_axle_x_mm':XR,'front_tube_x_mm':XF-190,'front_tube_centers_z_mm':[240,385],'front_tube_outer_radius_mm':32,'front_tube_span_mm':950,'front_shock_upper_xyz_mm':[XF-30,500,810],'rear_arm_pivots_right_mm':[[XR-430,-290,350],[XR-320,-545,350]],'rear_shock_upper_left_xyz_mm':[XR-20,500,795],'spring_radii_front_rear_mm':[48,62],'spring_wire_radius_mm':6,'spring_visual_turns':8,'note':'Все параметры этого блока — геометрические допущения, не паспортные размеры и не параметры жёсткости. Координаты зеркалятся по Y.'},'not_modelled':['Ход подвески, полный поворот колёс и огибающие движения','Жёсткость пружин/торсионов, осадка под новой массой, прочность креплений','Полные тормозные и рулевые механизмы, тормозные трубки и шланги'],'mechanical_interfaces':{'GBX':'Полуоси и их пыльники стыкуются с КПП. Эти узлы исключены только из проверки пересечения с габаритным прокси GBX; контакты рычагов и пружин не исключены.'},'license':'CC BY-SA 3.0 project geometry','generated_checks':checks}
(OUT/'stock-suspension.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False))
