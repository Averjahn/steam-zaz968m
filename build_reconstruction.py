"""Photo-guided PARAMETRIC reconstruction, not a measured/photogrammetric scan.
GLB: metres, glTF Y-up. OBJ: millimetres, Z-up. Run with Python stdlib.
All engineering dimensions/quality labels are in models/zaz-968m-reconstruction.json.
"""
from pathlib import Path
import json, math, struct, hashlib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'models'
PARAM = OUT / 'zaz-968m-reconstruction.json'
D = json.loads(PARAM.read_text())
P = D['parameters_mm']
L, W, H = (P[k]['value'] for k in ['length', 'width', 'height'])
XF = P['front_axle_x']['value']; XR = XF + P['wheelbase']['value']
R = P['tyre_radius']['value']; ARCH = P['arch_radius']['value']
FLOOR = P['cabin_floor_z']['value']; BULK = P['rear_bulkhead_x']['value']
meshes = []
colors = {'paint': [0.16,0.49,0.67,1], 'inner': [.54,.67,.72,1],
          'glass': [.17,.3,.38,.35], 'rubber': [.045,.055,.065,1],
          'chrome': [.6,.65,.67,1], 'seat': [.31,.24,.19,1],
          'lamp': [.87,.9,.78,1], 'red': [.62,.05,.025,1], 'orange': [1,.37,.03,1]}

def mesh(name, color='paint', group='exterior', collision=True):
    m={'name':name,'color':color,'group':group,'collision':collision,'v':[],'f':[]};meshes.append(m);return m

def quad(m, a,b,c,d):
    i=len(m['v']);m['v'] += [a,b,c,d];m['f'] += [(i,i+1,i+2),(i,i+2,i+3)]

def box(m, low, size):
    x,y,z=low; a,b,c=size
    v=[(x,y,z),(x+a,y,z),(x+a,y+b,z),(x,y+b,z),(x,y,z+c),(x+a,y,z+c),(x+a,y+b,z+c),(x,y+b,z+c)]
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:quad(m,*(v[i] for i in f))

def tube_y(m,x,y,z, radius,width, n=48, inner=0):
    # Axial cylinder/ring; wheels have separate static visual meshes, no sweep claims.
    for i in range(n):
        a=2*math.pi*i/n;b=2*math.pi*(i+1)/n
        def p(t,yy,r):return (x+r*math.cos(t),yy,z+r*math.sin(t))
        quad(m,p(a,y,radius),p(b,y,radius),p(b,y+width,radius),p(a,y+width,radius))
        for yy in [y,y+width]:quad(m,p(a,yy,inner),p(b,yy,inner),p(b,yy,radius),p(a,yy,radius))
        if inner:quad(m,p(a,y,inner),p(b,y,inner),p(b,y+width,inner),p(a,y+width,inner))

def beam(m, a,b, width=15):
    # A thin prism following a side silhouette. Display thickness is not metal gauge.
    dx,dz=b[0]-a[0],b[2]-a[2];l=math.hypot(dx,dz)
    u=(-dz/l*width/2,0,dx/l*width/2) if l else (0,0,width/2)
    quad(m,tuple(a[i]+u[i] for i in range(3)),tuple(b[i]+u[i] for i in range(3)),tuple(b[i]-u[i] for i in range(3)),tuple(a[i]-u[i] for i in range(3)))

def halfwidth(x,z=780):
    # Mirrored transverse shape is a hypothesis; no measured internal transverse slices.
    taper = 1-0.1*max(0,1-min(x-80,L-80-x)/260)
    return W/2*taper - max(0,780-z)*.045

# Body side panels, cutouts follow static wheel arches, not suspension swept volumes.
for s,name in [(-1,'Правая'),(1,'Левая')]:
    m=mesh(name+' боковина и арки')
    stations=sorted(set([80,L-80,1030,2020,3020]+[80+(L-160)*i/150 for i in range(151)]+[c-ARCH for c in [XF,XR]]+[c+ARCH for c in [XF,XR]]))
    def lower(x):
        return max([260]+[R+math.sqrt(max(0,ARCH*ARCH-(x-c)**2)) for c in [XF,XR] if abs(x-c)<ARCH])
    for a,b in zip(stations,stations[1:]):
        za,zb=lower(a),lower(b)
        for t,u in [(0,.18),(.18,.9),(.9,1)]:
            def p(x,zmin,k):
                z=zmin+(820-zmin)*k
                return (x,s*halfwidth(x,z),z)
            quad(m,p(a,za,t),p(b,zb,t),p(b,zb,u),p(a,za,u))
    sill=mesh(name+' порог','inner','interior')
    box(sill,(1040, s*650-45,250),(1430,90,65))

# Front and rear skins. Hood and lid are separately removable meshes.
for start,end,name in [(80,1040,'Передний капот'),(3020,L-80,'Крышка моторного отсека')]:
    m=mesh(name,group='covers')
    for i in range(24):
        a=start+(end-start)*i/24;b=start+(end-start)*(i+1)/24
        for j in range(24):
            t=-1+2*j/24;u=-1+2*(j+1)/24
            def p(x,v):return (x,v*halfwidth(x),835+25*(1-v*v)+(15*(x-start)/(end-start) if start==80 else -15*(x-start)/(end-start)))
            quad(m,p(a,t),p(b,t),p(b,u),p(a,u))
for x,name in [(80,'Передняя панель'),(L-80,'Задняя панель')]:
    m=mesh(name)
    for j in range(20):
        a=-1+2*j/20;b=-1+2*(j+1)/20
        quad(m,(x,a*halfwidth(x,350),350),(x,b*halfwidth(x,350),350),(x,b*halfwidth(x),835+25*(1-b*b)),(x,a*halfwidth(x),835+25*(1-a*a)))
trim=mesh('Бамперы, ручки, молдинги','chrome','trim',False)
for x in [0,L-80]:box(trim,(x,-705,405),(80,1410,65))
for s in [-1,1]:
    box(trim,(1980,s*738-4,865),(95,8,16))
    for a,b in [(90,1040),(1040,2020),(2020,3670)]:beam(trim,(a,s*744,795),(b,s*744,795),6)
    # Door seam and M's flush rear-side ventilation slots.
    for a,b in [((1040,s*744,795),(1040,s*726,390)),((1040,s*726,390),(2020,s*726,320)),((2020,s*726,320),(2020,s*744,795))]:beam(trim,a,b,3)
    for x in range(3070,3480,34):box(trim,(x,s*737-2,585),(7,4,85))

# Roof with a crowned transverse section.
roof=mesh('Крыша',group='covers')
for i in range(32):
    a=1370+(2640-1370)*i/32;b=1370+(2640-1370)*(i+1)/32
    for j in range(24):
        t=-1+2*j/24;u=-1+2*(j+1)/24
        def rp(x,v):return (x,v*605,H-40*v*v-18*((x-2005)/635)**2)
        quad(roof,rp(a,t),rp(b,t),rp(b,u),rp(a,u))
# Side window frames, A/B/C pillars, separate glass.
for s,name in [(-1,'Правая'),(1,'Левая')]:
    pillars=mesh(name+' стойки и оконные рамки')
    path=[(1040,0,865),(1420,0,1345),(2550,0,1345),(2910,0,865),(1040,0,865)]
    def sidep(p):
        x,_,z=p;return(x,s*(720-(z-865)*.23),z)
    for a,b in zip(path,path[1:]):beam(pillars,sidep(a),sidep(b),48 if a[0]!=b[0] else 45)
    beam(pillars,sidep((2020,0,865)),sidep((2020,0,1345)),45)
    glass=mesh(name+' боковое стекло','glass','glass')
    for points in [[(1110,0,900),(1430,0,1305),(1985,0,1305),(1985,0,900)],[(2060,0,900),(2515,0,1305),(2830,0,900),(2060,0,900)]]:
        if points[0]==points[-1]: # Rear window is a quadrilateral, not a repeated vertex.
            points=[(2060,0,900),(2060,0,1305),(2515,0,1305),(2830,0,900)]
        quad(glass,*(sidep(p) for p in points))
for name,lowx,highx in [('Лобовое стекло',1040,1370),('Заднее стекло',3020,2640)]:
    g=mesh(name,'glass','glass')
    quad(g,(lowx,-690,865),(lowx,690,865),(highx,595,1340),(highx,-595,1340))
    frame=mesh(name+' рамка')
    pts=[(lowx,-720,850),(lowx,720,850),(highx,620,1350),(highx,-620,1350)]
    for a,b in zip(pts,pts[1:]+pts[:1]):beam(frame,a,b,35)
# Flat floor patches and anatomical divisions inferred from cutaway photos.
m=mesh('Пол салона','inner','interior')
quad(m,(1100,-630,FLOOR),(2390,-630,FLOOR),(2390,630,FLOOR),(1100,630,FLOOR))
m=mesh('Центральный тоннель — условный','inner','interior')
box(m,(1120,-75,FLOOR),(1280,150,100))
m=mesh('Передняя перегородка и наклонный пол','inner','interior')
quad(m,(1000,-620,430),(1100,-620,FLOOR),(1100,620,FLOOR),(1000,620,430))
quad(m,(1000,-620,430),(1000,620,430),(1040,680,850),(1040,-680,850))
m=mesh('Подъём пола под задним сиденьем','inner','interior')
quad(m,(2390,-630,FLOOR),(2390,630,FLOOR),(2460,630,480),(2460,-630,480))
quad(m,(2460,-630,480),(BULK,-630,480),(BULK,630,480),(2460,630,480))
m=mesh('Задняя перегородка и полка','inner','interior')
quad(m,(BULK,-620,480),(BULK,620,480),(BULK+100,660,850),(BULK+100,-660,850))
quad(m,(BULK+100,-660,850),(BULK+100,660,850),(3020,690,865),(3020,-690,865))
m=mesh('Дно переднего отсека — гипотеза','inner','interior')
quad(m,(140,-430,390),(990,-430,390),(990,430,390),(140,430,390))
# Wheel-house surfaces are separate so questionable boundaries can be inspected/hidden.
for x,track,label in [(XF,P['front_track']['value'],'Передняя'),(XR,P['rear_track']['value'],'Задняя')]:
    for s,name in [(-1,'правая'),(1,'левая')]:
        m=mesh(label+' '+name+' внутренняя колёсная ниша','inner','interior')
        yin=s*P['wheelhouse_inner_y']['value'];yout=s*700
        for i in range(48):
            a=math.pi*i/48;b=math.pi*(i+1)/48
            def p(t,y):return(x+ARCH*math.cos(t),y,R+ARCH*math.sin(t))
            quad(m,p(a,yin),p(b,yin),p(b,yout),p(a,yout))
            quad(m,(x+ARCH*math.cos(a),yin,260),(x+ARCH*math.cos(b),yin,260),p(b,yin),p(a,yin))
# Rear bay has no invented full-width bottom tray: the stock engine hangs below it.
m=mesh('Боковые полки моторного отсека — гипотеза','inner','interior')
for s in [-1,1]:
    y1,y2=sorted([s*540,s*705]);quad(m,(3100,y1,410),(3670,y1,410),(3670,y2,410),(3100,y2,410))
# Seats are coarse envelopes, not upholstery measurements. They can be removed.
m=mesh('Передние сиденья — приблизительные','seat','seats')
for y in [-540,90]:
    box(m,(1570,y,FLOOR+105),(480,450,120));box(m,(1970,y,FLOOR+225),(100,450,500))
m=mesh('Заднее сиденье — приблизительное','seat','rear-seat')
box(m,(2400,-585,490),(390,1170,125));box(m,(2700,-585,610),(130,1170,470))
# Wheels: references only. Radii/tyre width are assumed, tracks are documented.
rubber=mesh('Колёса — неподвижный визуальный ориентир','rubber','wheels',False)
rims=mesh('Диски — условная форма','chrome','wheels',False)
for x,t in [(XF,P['front_track']['value']),(XR,P['rear_track']['value'])]:
    for s in [-1,1]:
        y=s*t/2;tube_y(rubber,x,y-77.5,R,R,155,inner=180)
        tube_y(rims,x,y-79,R,180,158);tube_y(rims,x,y-82,R,90,164)
# Headlamps are oriented along X.
lamps=mesh('Фары и фонари — внешний референс','lamp','trim',False)
for y in [-510,510]:
    for i in range(48):
        a=2*math.pi*i/48;b=2*math.pi*(i+1)/48
        quad(lamps,(78,y,660),(78,y+100*math.cos(a),660+100*math.sin(a)),(78,y+100*math.cos(b),660+100*math.sin(b)),(78,y,660))
    box(lamps,(78,y-95,490),(4,190,60))
red=mesh('Задние фонари','red','trim',False)
for y in [-625,375]:box(red,(L-77,y,580),(4,250,155))

# glTF positions converted from project Z-up mm into standards-compliant Y-up metres.
binary=bytearray();views=[];accessors=[];gmeshes=[];nodes=[]
def buffer(values,fmt,typ,component,count,minimum=None,maximum=None,target=34962):
    while len(binary)%4:binary.append(0)
    start=len(binary);binary.extend(struct.pack('<'+fmt*len(values),*values))
    vi=len(views);views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
    ac={'bufferView':vi,'componentType':component,'count':count,'type':typ}
    if minimum is not None:ac['min']=minimum;ac['max']=maximum
    ai=len(accessors);accessors.append(ac);return ai
materials=[];matindex={}
for name,c in colors.items():
    matindex[name]=len(materials);materials.append({'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':c,'metallicFactor':.05 if name not in ['chrome'] else .65,'roughnessFactor':.65},'alphaMode':'BLEND' if c[3]<1 else 'OPAQUE'})
for m in meshes:
    # Face-split normals make the mesh portable and avoid relying on viewer inference.
    vv=[];nn=[]
    for f in m['f']:
        pts=[m['v'][i] for i in f]
        a,b,c=pts;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(i*i for i in n))
        if length<1e-8:continue
        n=[i/length for i in n]
        for x,y,z in pts:vv.extend([x/1000,z/1000,-y/1000]);nn.extend([n[0],n[2],-n[1]])
    if not vv:continue
    mi=len(gmeshes);lo=[min(vv[i::3]) for i in range(3)];hi=[max(vv[i::3]) for i in range(3)]
    pa=buffer(vv,'f','VEC3',5126,len(vv)//3,lo,hi);na=buffer(nn,'f','VEC3',5126,len(nn)//3)
    gmeshes.append({'name':m['name'],'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'material':matindex[m['color']]}]})
    nodes.append({'name':m['name'],'mesh':mi,'extras':{'bodyGroup':m['group'],'collision':m['collision'],'geometryQuality':'photo-guided hypothesis; dimensional accuracy unknown'}})
asset={'asset':{'version':'2.0','generator':'Steam ZAZ photo-guided parametric reconstruction v1','copyright':'Photo-derived reconstruction CC BY-SA 3.0; attribution in zaz-968m-reconstruction.json'},'scene':0,'scenes':[{'name':'ZAZ-968M approximate body — not measured CAD','nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':gmeshes,'materials':materials,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,'extras':{'units':'metres','upAxis':'Y','projectAxes':'X rearward, Y left, Z up after rotate X +90deg','accuracy':'unknown; not a scan','engineeringUse':'preliminary layout screening only'}}
js=json.dumps(asset,ensure_ascii=False,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary.extend(b'\x00'*((-len(binary))%4))
glb=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
(OUT/'zaz-968m-reconstructed.glb').write_bytes(glb)
# OBJ preserves names/group separation, Z-up and actual project-coordinate origin.
obj=['# Approximate ZAZ-968M. Units mm; X rearward, Y left, Z up. NOT a scan.','# CC BY-SA 3.0; see zaz-968m-reconstruction.json','mtllib zaz-968m-reconstructed.mtl'];offset=1
for m in meshes:
    obj+=['o '+m['name'].replace(' ','_'),'usemtl '+m['color']]
    obj+=['v '+' '.join(f'{v:.4f}' for v in p) for p in m['v']]
    obj+=['f '+' '.join(str(i+offset) for i in f) for f in m['f']];offset+=len(m['v'])
(OUT/'zaz-968m-reconstructed.obj').write_text('\n'.join(obj)+'\n')
(OUT/'zaz-968m-reconstructed.mtl').write_text('\n'.join('newmtl '+n+'\nKd '+' '.join(map(str,c[:3]))+'\nd '+str(c[3]) for n,c in colors.items())+'\n')
allv=[p for m in meshes for p in m['v']];lo=[min(v[i] for v in allv) for i in range(3)];hi=[max(v[i] for v in allv) for i in range(3)]
checks={'status':'Checks of generated geometry, not validation of real vehicle dimensions','bounds_min_mm':lo,'bounds_max_mm':hi,'size_mm':[hi[i]-lo[i] for i in range(3)],'wheel_centres_x_mm':[XF,XR],'wheelbase_mm':XR-XF,'meshes':len(nodes),'triangles':sum(accessors[g['primitives'][0]['attributes']['POSITION']]['count']//3 for g in gmeshes),'glb_bytes':len(glb),'sha256':hashlib.sha256(glb).hexdigest(),'all_vertices_finite':all(math.isfinite(v) for p in allv for v in p)}
# Crown top falls between sample stations; construction bounds should be within 1 mm.
assert checks['all_vertices_finite'] and abs(hi[0]-L)<.01 and abs(hi[1]-lo[1]-W)<1 and abs(hi[2]-H)<1
assert lo[2]==0 and XR-XF==2160
(OUT/'reconstruction-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(checks,ensure_ascii=False,indent=2))

# Native vector side profile for source comparison; no raster generation.
from html import escape
polygons=[]
for m in meshes:
    if m['group'] not in ['exterior','covers','wheels','trim']:continue
    # The visible side is Y<0. Front/rear/roof surfaces project to edges or shallow areas.
    color=colors[m['color']];fill='#'+''.join(f'{int(v*255):02x}' for v in color[:3])
    for f in m['f']:
        pts=[m['v'][i] for i in f]
        if sum(v[1] for v in pts)/3>0:continue
        area=(pts[1][0]-pts[0][0])*(pts[2][2]-pts[0][2])-(pts[2][0]-pts[0][0])*(pts[1][2]-pts[0][2])
        if abs(area)<.1:continue
        polygons.append((sum(v[1] for v in pts)/3, '<polygon points="'+' '.join(f'{v[0]:.1f},{H-v[2]:.1f}' for v in pts)+'" fill="'+fill+'"/>'))
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="-120 -150 4005 1700"><title>Приближённая реконструкция ЗАЗ-968М, вид сбоку</title><rect x="-120" y="-150" width="4005" height="1700" fill="#eef3f4"/>'
svg+=''.join(s for _,s in sorted(polygons,key=lambda v:-v[0]))
# Transparent glass projection is shown after the shell, with explicit frame space.
for points in [[(1110,900),(1430,1305),(1985,1305),(1985,900)],[(2060,900),(2060,1305),(2515,1305),(2830,900)]]:
 svg+='<polygon points="'+' '.join(f'{x},{H-z}' for x,z in points)+'" fill="#486576" opacity=".7"/>'
svg+='<path d="M675 1460H2835 M675 1440V1480 M2835 1440V1480" stroke="#2e5262" stroke-width="6"/><text x="1755" y="1530" text-anchor="middle" font-family="sans-serif" font-size="55">База 2160 мм · передний свес ≈675 мм по фото</text><text x="0" y="-65" font-family="sans-serif" font-size="52">Реконструкция · наружные размеры заданы, внутренние не измерены</text></svg>'
(OUT/'zaz-968m-profile.svg').write_text(svg)

# Unmodified reference photo with a separate vector annotation layer.
reg=D['photo_registration'];pts=reg['manually_picked_points_px'];f=pts['front_wheel_center'];r=pts['rear_wheel_center']
annotation='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1187 735"><title>Ручная разметка бокового фото. Масштаб по базе; не фотограмметрия.</title><image href="side2.jpg" width="1187" height="735"/>'
for q in [f,r]:annotation+=f'<circle cx="{q[0]}" cy="{q[1]}" r="10" fill="none" stroke="#ffff00" stroke-width="4"/><path d="M{q[0]-15} {q[1]}h30 M{q[0]} {q[1]-15}v30" stroke="#ffff00" stroke-width="2"/>'
annotation+=f'<path d="M{f[0]} {f[1]}V575H{r[0]}V{r[1]}" fill="none" stroke="#ffff00" stroke-width="3"/><rect x="300" y="550" width="420" height="45" fill="#14212b" opacity=".85"/><text x="510" y="580" text-anchor="middle" fill="white" font-family="sans-serif" font-size="25">2160 мм по документации</text><rect x="25" y="675" width="1137" height="45" fill="#14212b" opacity=".85"/><text x="45" y="705" fill="white" font-family="sans-serif" font-size="20">Фото PaPaKo · CC BY-SA 3.0 · разметка проекта, перспектива не устранена</text></svg>'
(OUT/'references/side-registration.svg').write_text(annotation)
