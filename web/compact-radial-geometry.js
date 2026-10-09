import * as T from 'three';
import {compactGeometry as K,compactPipes as P,compactPose,compactGearPolygon} from './compact-radial-model.js';
import {pipeCurve} from './pipe-path.js';
import {hollowTube,hollowBox} from './pipe-joints.js';
import {pipeArrows} from './pipe-arrows.js';
const V=p=>new T.Vector3(...p),Z=new T.Vector3(0,0,1),TAU=2*Math.PI;
const mat=(color,metal=.7)=>new T.MeshStandardMaterial({color,metalness:metal,roughness:.4,side:T.DoubleSide});
export function createCompactRadial(){
 const root=new T.Group();root.name='Компактная звезда · 7 × Ø32 / ход36 · миллиметры';
 const core=new T.Group();core.name='Двигатель, коллекторы, изоляция и угловая передача';root.add(core);
 const mounts=new T.Group();mounts.name='Стойки до пола предоставленного кузова';root.add(mounts);
 const contacts=new T.Group();contacts.name='Контактные площадки на полу';root.add(contacts);
 const steel=mat('#a4b4bd'),dark=mat('#374953'),brass=mat('#c8a165'),copper=mat('#c88749'),insulation=mat('#d4ccb5',.05),orange=mat('#e0a36d');
 const skins=[],cylinders=[],routes=[],portRecords=[];
 function mesh(g,name,geo,m){const o=new T.Mesh(geo,m.clone());o.name=name;g.add(o);return o;}
 function bar(g,name,a,b,r,m=steel){const d=V(b).sub(V(a)),o=mesh(g,name,new T.CylinderGeometry(r,r,d.length(),20),m);o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return o;}
 function box(g,name,center,size,m=dark){const o=mesh(g,name,new T.BoxGeometry(...size),m);o.position.fromArray(center);return o;}
 function beam(g,name,a,b,w=7,h=5,m=dark){const d=V(b).sub(V(a)),o=mesh(g,name,new T.BoxGeometry(d.length(),w,h),m);o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.rotation.z=Math.atan2(d.y,d.x);return o;}
 function plate(g,name,at,normal,inner,outer,depth,m=steel,holes=[]){const sh=new T.Shape();sh.absarc(0,0,outer,0,TAU,false);if(inner>0){const h=new T.Path();h.absarc(0,0,inner,0,TAU,true);sh.holes.push(h);}for(const [x,y,r]of holes){const h=new T.Path();h.absarc(x,y,r,0,TAU,true);sh.holes.push(h);}const o=mesh(g,name,new T.ExtrudeGeometry(sh,{depth,bevelEnabled:false,curveSegments:32}),m);o.position.fromArray(at);o.quaternion.setFromUnitVectors(Z,V(normal));return o;}
 function skin(o){o.userData.compactSkin=true;skins.push(o);return o;}
 // Cylinder wall unwrapped into a plane, with a true side opening, then tessellated
 // in angular coordinate and mapped back to the circular wall.
 function wall(g,name,r,z0,z1,m,port=null){
  if(!port){const geo=new T.CylinderGeometry(r,r,z1-z0,96,1,true);geo.rotateX(Math.PI/2);geo.translate(0,0,(z0+z1)/2);return mesh(g,name,geo,m);}
  const sh=new T.Shape();sh.moveTo(0,z0);sh.lineTo(TAU*r,z0);sh.lineTo(TAU*r,z1);sh.lineTo(0,z1);sh.closePath();
  if(port){const h=new T.Path(),points=[];for(let i=0;i<=64;i++){const a=TAU*i/64;points.push([r*(port.angle+Math.asin(port.radius*Math.cos(a)/r)),port.z+port.radius*Math.sin(a)]);}h.moveTo(...points[0]);for(const p of points.slice(1))h.lineTo(...p);h.closePath();sh.holes.push(h);}
  const flat=new T.ShapeGeometry(sh,32),pos=flat.attributes.position,index=flat.index,out=[],normals=[];
  const pushTri=(a,b,c)=>{const stack=[[a,b,c]];while(stack.length){const q=stack.pop(),edges=[[0,1,2],[1,2,0],[2,0,1]],e=edges.reduce((best,e)=>Math.abs(q[e[0]][0]-q[e[1]][0])>Math.abs(q[best[0]][0]-q[best[1]][0])?e:best,edges[0]);if(Math.abs(q[e[0]][0]-q[e[1]][0])>r*.12){const mid=q[e[0]].map((x,i)=>(x+q[e[1]][i])/2);stack.push([q[e[0]],mid,q[e[2]]],[mid,q[e[1]],q[e[2]]]);continue;}for(const p of q){const a=p[0]/r;out.push(r*Math.cos(a),r*Math.sin(a),p[1]);normals.push(Math.cos(a),Math.sin(a),0);}}};
  for(let i=0;i<index.count;i+=3)pushTri(...[0,1,2].map(j=>{const k=index.getX(i+j);return [pos.getX(k),pos.getY(k)];}));flat.dispose();const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(out,3));geo.setAttribute('normal',new T.Float32BufferAttribute(normals,3));return mesh(g,name,geo,m);
 }
 function plenum(name,R,width,height,z,coat,supply,sideAngle,sideBore){
  const g=new T.Group();g.name=name;core.add(g);const inside=R-width/2,outside=R+width/2,bottom=z-height/2,top=z+height/2,t=K.headerWall;
  for(const r of [inside,inside+t,outside-t,outside])wall(g,name+' · стенка3 мм',r,bottom,top,steel,r>=outside-t?{angle:sideAngle,radius:sideBore/2,z}:null);
  const ports=Array.from({length:7},(_,i)=>{const a=Math.PI/2+i*TAU/7;return [R*Math.cos(a),R*Math.sin(a),supply?4:6];});
  plate(g,name+' · нижняя крышка',[0,0,bottom], [0,0,1],inside,outside,t,steel,supply?[]:ports);
  plate(g,name+' · верхняя крышка',[0,0,top-t], [0,0,1],inside,outside,t,steel,supply?ports:[]);
  skin(wall(g,name+' · изоляция '+coat+' мм',outside+coat,bottom-coat,top+coat,insulation,{angle:sideAngle,radius:(supply?28.5:36),z}));
  skin(wall(g,name+' · внутренний пояс изоляции',inside-coat,bottom-coat,top+coat,insulation));
  const skinPorts=ports.map(p=>[p[0],p[1],supply?P.supply.envelope_mm/2:P.exhaust.envelope_mm/2]);
  skin(plate(g,name+' · изоляция крышки',[0,0,bottom-coat],[0,0,1],inside-coat,outside+coat,coat,insulation,supply?[]:skinPorts));
  skin(plate(g,name+' · изоляция крышки',[0,0,top],[0,0,1],inside-coat,outside+coat,coat,insulation,supply?skinPorts:[]));
  return {g,top,bottom,inside,outside};
 }
 const supply=plenum('Верхний кольцевой пленум свежего пара',132,24,30,245,15,true,Math.PI,20);
 const ret=plenum('Кольцевой пленум выпуска',104,48,50,170,12.5,false,3*Math.PI/2,40);
 class Span extends T.Curve{constructor(curve,a,b){super();Object.assign(this,{curve,a,b});}getPoint(t,target){return this.curve.getPointAt(this.a+(this.b-this.a)*t,target);}getTangent(t,target){return this.curve.getTangentAt(this.a+(this.b-this.a)*t,target);}}
 function tube(name,points,spec,R,role,index=null,chamber=null,bareEnd=12){
  const g=new T.Group();g.name=name;core.add(g);const curve=pipeCurve({points,geometry_valid:true,bend_radius_mm:R}),L=curve.getLength(),segments=Math.max(20,Math.ceil(L/4));
  mesh(g,name+' · наружная стенка',new T.TubeGeometry(curve,segments,spec.outside_mm/2,12,false),steel);mesh(g,name+' · проход Ø'+spec.inside_mm,new T.TubeGeometry(curve,segments,spec.inside_mm/2,12,false),steel);
  for(const end of [0,1])plate(g,name+' · торец',curve.getPointAt(end).toArray(),curve.getTangentAt(end).toArray(),spec.inside_mm/2,spec.outside_mm/2,.05,steel);
  if(spec.insulation_mm&&L>bareEnd+12){const span=new Span(curve,12/L,(L-bareEnd)/L);skin(mesh(g,name+' · изоляция '+spec.insulation_mm,new T.TubeGeometry(span,segments,spec.envelope_mm/2-spec.jacket_mm,12,false),insulation));skin(mesh(g,name+' · защитная оболочка',new T.TubeGeometry(span,segments,spec.envelope_mm/2,12,false),steel));}
  const arrows=pipeArrows(curve,{id:name,fluid:role==='outlet'||role==='return'?'exhaust':'steam'});arrows.group.userData.viewOnly=true;g.add(arrows.group);
  const rec={name,points,spec,bend_radius_mm:R,curve,length_mm:L,role,index,chamber,arrows,bare_end_mm:bareEnd};routes.push(rec);return rec;
 }
 // Boundary reducer preserves the upstream Ø109.2 insulated envelope.
 hollowTube(core,'Впуск · переход ID40→20',[-244,0,245],[-218,0,245],26,20,{entry_od_mm:48,entry_bore_mm:40});
 tube('Граничный впуск ID40 / OD48',[[-260,0,245],[-244,0,245]],P.boundaryIn,60,'supply',null,null,0);
 // Short boundary has a full-size insulation sleeve, rather than no insulation.
 hollowTube(core,'Изоляция границы впуска · полный Ø109,2',[-260,0,245],[-244,0,245],109.2,48,{color:'#d4ccb5'}).userData.compactSkin=true;skins.push(core.children.at(-1));
 tube('Ввод в пленум ID20',[[-218,0,245],[-144,0,245]],{...P.supply,inside_mm:20,outside_mm:26,wall_mm:3,insulation_mm:15,envelope_mm:57},40,'supply');
 tube('Граничный выпуск ID40 / OD46',[[0,-128,170],[0,-230,170]],P.boundaryOut,70,'return');
 const central=new T.Group();core.add(central);
 function gear(g,name,n,p){const sh=new T.Shape(compactGearPolygon(n).map(p=>new T.Vector2(...p))),h=new T.Path();h.absarc(0,0,5,0,TAU,true);sh.holes.push(h);const o=mesh(g,name,new T.ExtrudeGeometry(sh,{depth:6,bevelEnabled:false}),steel);o.position.fromArray(p);o.position.z-=3;return o;}
 const centralGear=gear(central,'Центральная шестерня · m1,5 · 56 зубьев',56,[0,0,0]);
 bar(core,'Вертикальный выходной вал · до угловой передачи',[0,0,-78],[0,0,30],5,dark);
 plate(core,'Подшипник общего вала',[0,0,-28],[0,0,1],5.15,14,12,brass);
 plate(core,'Кольцо силовой рамы с проходами семи валов',[0,0,-30],[0,0,1],53,72,8,dark,Array.from({length:7},(_,i)=>{const a=Math.PI/2+i*TAU/7;return [63*Math.cos(a),63*Math.sin(a),5.3];}));
 const trayShape=new T.Shape([[-230,-195],[230,-195],[230,195],[-230,195]].map(p=>new T.Vector2(...p))),trayHole=new T.Path([[-50,-45],[-50,45],[50,45],[50,-45]].map(p=>new T.Vector2(...p)));trayShape.holes.push(trayHole);
 const tray=mesh(core,'Опорный поддон460×390 с окном под вал',new T.ExtrudeGeometry(trayShape,{depth:6,bevelEnabled:false}),dark);tray.position.z=K.trayZ-K.origin[2];
 for(const x of [-165,165])for(const y of [-135,135]){bar(core,'Опора двигателя на поддон',[x,y,-45],[x,y,-30],8,brass);beam(core,'Балка под радиальной рамой',[x,y,-30],[0,y,-30],18,6,dark);}
 // Two bevel pitch cones meet at a common apex; neither shaft crosses the other.
 function bevel(name,axis){const g=new T.Group();g.name=name;g.position.z=-90;g.quaternion.setFromUnitVectors(Z,V(axis));core.add(g);const positions=[];for(let i=0;i<24;i++)for(let j=0;j<4;j++){const a=TAU*(i+j/4)/24,radial=(j===1||j===2)?1.04:.9;for(const z of [12,23])positions.push([z*radial*Math.cos(a),z*radial*Math.sin(a),z]);}const tris=[];for(let i=0;i<96;i++){const j=(i+1)%96;for(const k of [2*i,2*j,2*i+1,2*j,2*j+1,2*i+1])tris.push(...positions[k]);}const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(tris,3));geo.computeVertexNormals();mesh(g,name+' · схематические зубья',geo,steel).userData.tightBounds=true;plate(g,'Ступица конусной шестерни',[0,0,18],[0,0,1],5.1,12,5,brass);return g;}
 const bevelVertical=bevel('Вертикальная коническая шестерня1:1',[0,0,1]),bevelHorizontal=bevel('Горизонтальная коническая шестерня1:1',[-1,0,0]);
 bar(core,'Горизонтальный вал к КПП',[-12,0,-90],[-230,0,-90],5,dark);
 for(const x of [-38,-185])plate(core,'Опора горизонтального вала',[x,0,-90],[1,0,0],5.2,14,12,brass);
 const housing=hollowBox.bind(null,core,'Корпус угловой передачи',[-40,-35,-120],[80,70,60],dark,[{anchor_mm:[0,0,-60],outward:[0,0,1],bore_mm:12},{anchor_mm:[-40,0,-90],outward:[-1,0,0],bore_mm:12}]);housing();for(const o of core.children.filter(o=>o.name.includes('Корпус угловой')))skin(o);
 for(const x of [-65,65])for(const y of [-30,30]){beam(core,'Консоль корпуса угловой передачи',[Math.sign(x)*35,y,-60],[x,y,-60],8,5,steel);bar(core,'Подвес корпуса к поддону',[x,y,-60],[x,y,K.trayZ-K.origin[2]],3,steel);}
 for(const x of [-185,-38])bar(core,'Опора подшипника выхода к поддону',[x,0,-76],[x,0,K.trayZ-K.origin[2]],4,dark);
 plate(core,'Выходная соединительная муфта · ось КПП пока условная',[-230,0,-90],[1,0,0],5.2,22,10,brass);
 for(let i=0;i<7;i++){
  const p=compactPose(i,0),alpha=p.alpha,u=[Math.cos(alpha),Math.sin(alpha)],v=[-u[1],u[0]],at=(r,z=61,t=0)=>[u[0]*r+v[0]*t,u[1]*r+v[1]*t,z],g=new T.Group();g.name='Цилиндр '+(i+1)+' · двойное действие';g.userData.cylinder=i;core.add(g);
  const localGear=gear(g,'Шестерня28 зубьев',28,[...p.axis.slice(0,2),0]);bar(g,'Коренной вал кривошипа',at(63,-25),at(63,43),5,dark);plate(g,'Подшипник кривошипа',at(63,-25),[0,0,1],5.1,11,12,brass);
  const crank=new T.Group();crank.position.fromArray(at(63,43));g.add(crank);beam(crank,'Щека кривошипа r18',[0,0,0],[18,0,0],9,5,orange);bar(crank,'Смещённая шейка',[18,0,5],[18,0,26],3,brass);
  const rod=beam(g,'Шатун57 мм',p.pin,p.crosshead,6,4),big=plate(g,'Большая головка',p.pin,[0,0,1],3.1,7,4,dark),small=plate(g,'Малая головка',p.crosshead,[0,0,1],2.1,4.5,4,dark);
  const crosshead=box(g,'Крейцкопф',p.crosshead,[10.5,40,8],steel);crosshead.rotation.z=alpha;for(const y of [-20.25,20.25])box(crosshead,'Башмак направляющей',[0,y,0],[10.5,.5,7],brass);
  for(const t of [-22,22])beam(g,'Направляющая крейцкопфа',at(94,58,t),at(145,58,t),3,12,dark);
  beam(g,'Радиальная балка',at(69,-26),at(207,-26),16,8,dark);
  for(const r of [158,190]){beam(g,'Лапа цилиндра',at(r,-16,-24),at(r,-16,24),9,12,steel);for(const t of [-20,20])bar(g,'Стойка до цилиндра',at(r,-10,t),at(r,61,t),3,brass);}
  const barrel=skin(plate(g,'Гильза ID32 / OD40',at(152.4),[...u,0],16,20,43.2,steel));
  const jacket=skin(plate(g,'Изоляция цилиндра15 мм',at(152.4),[...u,0],20,35,43.2,insulation));skin(plate(g,'Защитный кожух цилиндра0,5 мм',at(152.4),[...u,0],35,35.5,43.2,steel));
  const inv=new T.Quaternion().setFromUnitVectors(Z,V([...u,0])).invert(),offB=V([0,0,-12]).applyQuaternion(inv),offA=V([-v[0]*10,-v[1]*10,0]).applyQuaternion(inv);
  plate(g,'Штоковая крышка B · проход штока и отдельный порт',at(150.4),[...u,0],3.94,24,2,steel,[[offB.x,offB.y,4]]);
  plate(g,'Наружная крышка A · отдельный порт',at(195.6),[...u,0],0,24,2,steel,[[offA.x,offA.y,4]]);
  const piston=bar(g,'ПоршеньØ32',at(p.pistonRadius-3),at(p.pistonRadius+3),15.85,orange),pistonRod=bar(g,'ШтокØ7,68',p.crosshead,p.piston,3.84,brass);
  const fluidMat=mat('#fff1d6',0);fluidMat.transparent=true;fluidMat.opacity=.15;fluidMat.depthWrite=false;
  const fluidA=bar(g,'Пар в камере A',at(p.pistonRadius+3),at(195.6),15.8,fluidMat),fluidB=plate(g,'Пар в камере B',at(152.4),[...u,0],3.9,15.8,39,fluidMat);
  const valve=new T.Group();valve.name='Распределитель '+(i+1)+' · проходы A/B';valve.rotation.z=alpha;g.add(valve);
  const vp=[{id:'A',anchor_mm:[196,-10,190],outward:[1,0,0],bore_mm:8},{id:'B',anchor_mm:[176,14,205],outward:[0,0,1],bore_mm:8},{id:'in',anchor_mm:[176,-14,205],outward:[0,0,1],bore_mm:8},{id:'out',anchor_mm:[176,0,165],outward:[0,0,-1],bore_mm:12}];
  hollowBox(valve,'Коробка парораспределения · не выбранный клапан',[156,-25,165],[40,50,40],dark,vp);for(const o of valve.children)skin(o);
  tube('Подача '+(i+1),[at(132,260),at(132,278),at(176,278,-14),at(176,205,-14)],P.supply,18,'inlet',i);
  tube('Выпуск '+(i+1),[at(176,165),at(176,120),at(104,120),at(104,145)],P.exhaust,24,'outlet',i);
  tube('Камера '+(i+1)+'A',[at(196,190,-10),at(230,190,-10),at(230,61,-10),at(197.6,61,-10)],P.chamber,18,'chamber',i,'A',24);
  tube('Камера '+(i+1)+'B',[at(176,205,14),at(176,278,14),at(230,278,14),at(230,278,60),at(230,100,60),at(110,100,60),at(110,49,60),at(110,49),at(150.4,49)],P.chamber,18,'chamber',i,'B',80);
  portRecords.push({cylinder:i,A:{face_mm:at(197.6,61,-10),outward:[...u,0],bore_mm:8},B:{face_mm:at(150.4,49),outward:[-u[0],-u[1],0],bore_mm:8},valve_ports:vp});
  cylinders.push({g,at,piston,pistonRod,rod,big,small,crank,localGear,crosshead,fluidA,fluidB,barrel,jacket});
 }
 const anchorData=[[3000,-177,286.5353667979263],[3000,177,286.5350932618857],[3420,-177,366.4795014104693],[3420,177,366.4795014104296]];
 // Plane113 is sloped: a flat pad and a cylinder starting at centre height cut
 // into its high side. These wedges follow the actual local plane at all corners.
 const floorSlopes=[[.0132322107,-.6028257649],[.0132321559,.6028269496],[.0741366940,-.0000000951],[.0741366940,.0000000951]];
 for(const [index,[x,y,z]]of anchorData.entries()){
  const [sx,sy]=floorSlopes[index],q=[x-K.origin[0],y-K.origin[1],z-K.origin[2]],corners=[[-6,-6],[6,-6],[6,6],[-6,6]],base=corners.map(([dx,dy])=>[q[0]+dx,q[1]+dy,q[2]+sx*dx+sy*dy]),top=Math.max(...base.map(p=>p[2]))+3;
  const points=[...base,...corners.map(([dx,dy])=>[q[0]+dx,q[1]+dy,top])],faces=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7],geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(faces.flatMap(i=>points[i]),3));geo.computeVertexNormals();const pad=mesh(contacts,'Клиновая площадка12×12 · контакт с Plane113',geo,steel);pad.userData.floorContact={anchor_mm:[x,y,z],slopes:[sx,sy],pad_half_mm:6,top_world_mm:top+K.origin[2],load_bearing_confirmed:false};
  bar(mounts,'Стойка от клиновой площадки до поддона',[q[0],q[1],top],[q[0],q[1],K.trayZ-K.origin[2]],6,dark);plate(core,'Крепление стойки к поддону',[q[0],q[1],K.trayZ-K.origin[2]],[0,0,1],3.2,12,6,brass);
 }
 function setBar(o,a,b){const d=V(b).sub(V(a));o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.scale.y=d.length()/o.geometry.parameters.height;o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());}
 function update(angle,flowTime,camera,arrowsVisible=true){centralGear.rotation.z=angle;bevelVertical.rotation.z=angle;bevelHorizontal.rotation.z=-angle;const states=cylinders.map((c,i)=>{
  const p=compactPose(i,angle);c.localGear.rotation.z=p.gearAngle;c.crank.rotation.z=p.pinAngle;c.crosshead.position.fromArray(p.crosshead);const d=V(p.crosshead).sub(V(p.pin));c.rod.position.copy(V(p.pin).add(V(p.crosshead)).multiplyScalar(.5));c.rod.scale.x=d.length()/c.rod.geometry.parameters.width;c.rod.rotation.z=Math.atan2(d.y,d.x);c.big.position.fromArray(p.pin);c.big.position.z-=2;c.small.position.fromArray(p.crosshead);c.small.position.z-=2;
  setBar(c.piston,c.at(p.pistonRadius-3),c.at(p.pistonRadius+3));setBar(c.pistonRod,p.crosshead,p.piston);setBar(c.fluidA,c.at(p.pistonRadius+3),c.at(195.6));c.fluidB.scale.z=(p.pistonRadius-3-152.4)/39;
  c.fluidA.material.color.set(p.A.exhaust?'#9ac9e4':'#ffe3b0');c.fluidB.material.color.set(p.B.exhaust?'#9ac9e4':'#ffe3b0');return p;
 });
  if(camera)for(const r of routes){const p=r.index===null?null:states[r.index],ch=r.chamber?p[r.chamber]:null,active=ch?ch.inlet||ch.exhaust:r.role==='inlet'?p.A.inlet||p.B.inlet:r.role==='outlet'?p.A.exhaust||p.B.exhaust:true;r.arrows.update({camera,radius:r.spec.outside_mm/2,phase:flowTime*.45,visible:arrowsVisible&&active,direction:ch?.exhaust?-1:1,color:ch?.exhaust||['return','outlet'].includes(r.role)?'#a5d0e6':'#ffe3b0',clippingPlanes:[]});}
  return states;
 }
 function cutaway(on){for(const o of skins){o.material.transparent=on;o.material.opacity=on?.14:1;o.material.depthWrite=!on;}}
 cutaway(true);update(0,0);
 root.userData={id:'COMPACT_ENGINE',units:'mm/Z-up',geometry:'Seven double-acting cylinders D32 S36; port and shell geometry, conceptual distributor and bevel gearing',not_manufacturing_cad:true};
 return {root,core,mounts,contacts,cylinders,routes,portRecords,anchorData,update,cutaway};
}
