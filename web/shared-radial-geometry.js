import * as T from 'three';
import {compactGeometry as BASE,compactPipes as P} from './compact-radial-model.js';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';
import {sharedPose,sharedLinkages} from './shared-radial-model.js';
import {pipeCurve} from './pipe-path.js';
import {hollowTube,hollowBox} from './pipe-joints.js';
import {pipeArrows} from './pipe-arrows.js';
const V=p=>new T.Vector3(...p),Z=new T.Vector3(0,0,1),TAU=2*Math.PI;
const mat=(color,metal=.7)=>new T.MeshStandardMaterial({color,metalness:metal,roughness:.4,side:T.DoubleSide});
// Only the mechanical dimensions change. Pipe bores, insulation and header sections stay full size.
export function createSharedRadial({bore_mm=40,origin_mm=null,floorAnchors=null,floorSlopes=null,skipSupports=false}={}){
 const s=bore_mm/32;if(!(s>=1&&s<=2))throw Error('Study range: bore 32–64 mm');
 const K={...BASE,outputZ:-45,bore:bore_mm,stroke:36*s,rod:7.68*s,crank:18*s,link:57*s,pistonRod:54*s,pistonThickness:6*s,clearance:.6*s,axisRadius:63*s,module:1.5*s,innerHead:152.4*s,outerHead:195.6*s,shellRadius:20*s,origin:origin_mm||[2980+230*s,0,490]};
 K.outputRatio=1;K.mechanism='master-articulated';K.link=120*s;K.articulationRadius=19.2*s;K.axisRadius=0;K.centralTeeth=0;K.localTeeth=0;
 const outputReach=K.origin[0]-2980;
 const compactPose=(i,a)=>sharedPose(i,a,bore_mm);
 const root=new T.Group();root.name=`Звезда под кузов · 7 × Ø${K.bore} / ход ${K.stroke} · миллиметры`;
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
 function connectingRod(g,name,a,b,main=false){
  const length=V(a).distanceTo(V(b)),R0=(main?5:6)*jointScale,R1=5*jointScale,sh=new T.Shape();
  sh.moveTo(0,-R0);sh.lineTo(length,-R1);sh.absarc(length,0,R1,-Math.PI/2,Math.PI/2,false);sh.lineTo(0,R0);sh.absarc(0,0,R0,Math.PI/2,3*Math.PI/2,false);
  for(const [x,r]of (main?[[length,2.2*jointScale]]:[[0,3.2*jointScale],[length,2.2*jointScale]])){const h=new T.Path();h.absarc(x,0,r,0,TAU,true);sh.holes.push(h);}
  const geo=new T.ExtrudeGeometry(sh,{depth:4,bevelEnabled:false,curveSegments:24});geo.translate(-length/2,0,-2);const o=mesh(g,name,geo,orange);o.userData.rodLength=length;o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.rotation.z=Math.atan2(b[1]-a[1],b[0]-a[0]);return o;
 }
 function forkCrosshead(g,p,alpha){
  const w=10.5*s,h=40*s,geos=[];
  for(const z of [-4,2.5]){const sh=new T.Shape([[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]].map(q=>new T.Vector2(...q))),hole=new T.Path();hole.absarc(0,0,2.2*jointScale,0,TAU,true);sh.holes.push(hole);const geo=new T.ExtrudeGeometry(sh,{depth:1.5,bevelEnabled:false});geo.translate(0,0,z);geos.push(geo);}
  for(const y of [-h*.35,h*.35]){const geo=new T.BoxGeometry(w,h*.2,5);geo.translate(0,y,0);geos.push(geo);}
  const tail=new T.BoxGeometry(w/2-5.4*jointScale,h,5);tail.translate((w/2+5.4*jointScale)/2,0,0);geos.push(tail);
  const simple=geos.map(geo=>{const o=geo.index?geo.toNonIndexed():geo;for(const key of Object.keys(o.attributes))if(!['position','normal'].includes(key))o.deleteAttribute(key);return o;});
  const o=mesh(g,'Крейцкопф · вилка с зазором под шатун',mergeGeometries(simple,false),steel);o.position.fromArray(p);o.rotation.z=alpha;
  bar(o,'Палец крейцкопфа в отверстиях шатуна и вилки',[0,0,-5],[0,0,5],2*jointScale,brass);return o;
 }
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
 const commonCrank=new T.Group();commonCrank.name='Единый кривошип общего коленвала';commonCrank.position.z=43;core.add(commonCrank);
 beam(commonCrank,'Одна щека коленвала',[0,0,0],[K.crank,0,0],12*s,5,orange);
 bar(commonCrank,'Одна общая шатунная шейка',[K.crank,0,5],[K.crank,0,30],6*s,brass);
 const masterFork=new T.Group();masterFork.name='Вильчатая головка главного шатуна и шесть шарниров';core.add(masterFork);
 const jointScale=bore_mm/40,holes=sharedLinkages.slice(1).map(k=>[24*jointScale*Math.cos(k.beta),24*jointScale*Math.sin(k.beta),3.5*jointScale]);
 for(const z of [53,66])plate(masterFork,'Щека вилки главного шатуна',[0,0,z],[0,0,1],6.15*s,25.6*s,3,orange,holes);
 hollowTube(masterFork,'Подшипник общей шатунной шейки',[0,0,53],[0,0,69],19.2*s,12.3*s,{color:'#c8a165'});
 for(const k of sharedLinkages.slice(1)){const xy=[24*jointScale*Math.cos(k.beta),24*jointScale*Math.sin(k.beta)];bar(masterFork,'Палец прицепного шатуна',[...xy,53],[...xy,69],3*jointScale,brass);}
 beam(masterFork,'Перемычка главного шатуна',[0,27*jointScale,61],[0,32*jointScale,61],12*jointScale,16,orange);
 bar(core,'Вертикальный выходной вал · до угловой передачи',[0,0,-33],[0,0,43],5*s,dark);
 plate(core,'Подшипник общего вала',[0,0,-28],[0,0,1],5.15*s,14*s,12,brass);
 plate(core,'Кольцо силовой рамы · без семи промежуточных валов',[0,0,-30],[0,0,1],53*s,72*s,8,dark);
 plate(core,'Верхний коренной подшипник общего коленвала',[0,0,25],[0,0,1],5.15*s,14*s,12,brass);
 const trayShape=new T.Shape([[-230,-180],[230,-180],[230,180],[-230,180]].map(p=>new T.Vector2(...p))),trayHole=new T.Path([[-50,-45],[-50,45],[50,45],[50,-45]].map(p=>new T.Vector2(...p)));trayShape.holes.push(trayHole);
 const tray=mesh(core,'Опорный поддон460×360 с окном под вал',new T.ExtrudeGeometry(trayShape,{depth:6*s,bevelEnabled:false}),dark);tray.position.z=K.trayZ-K.origin[2];
 for(const x of [-165,165])for(const y of [-135,135]){bar(core,'Опора двигателя на поддон',[x,y,-45],[x,y,-30],8,brass);beam(core,'Балка под радиальной рамой',[x,y,-30],[0,y,-30],18,6,dark);}
 // Two bevel pitch cones meet at a common apex; neither shaft crosses the other.
 function bevel(name,axis){const g=new T.Group();g.name=name;g.position.z=-45;g.quaternion.setFromUnitVectors(Z,V(axis));core.add(g);const positions=[];for(let i=0;i<24;i++)for(let j=0;j<4;j++){const a=TAU*(i+j/4)/24,radial=(j===1||j===2)?1.04:.9;for(const z of [12,23])positions.push([z*radial*Math.cos(a),z*radial*Math.sin(a),z]);}const tris=[];for(let i=0;i<96;i++){const j=(i+1)%96;for(const k of [2*i,2*j,2*i+1,2*j,2*j+1,2*i+1])tris.push(...positions[k]);}const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(tris,3));geo.computeVertexNormals();mesh(g,name+' · схематические зубья',geo,steel).userData.tightBounds=true;plate(g,'Ступица конусной шестерни',[0,0,18],[0,0,1],5.1*s,12*s,5,brass);return g;}
 const bevelVertical=bevel('Вертикальная коническая шестерня1:1',[0,0,1]),bevelHorizontal=bevel('Горизонтальная коническая шестерня1:1',[-1,0,0]);
 bar(core,'Горизонтальный вал к КПП',[-12,0,-45],[-outputReach,0,-45],5*s,dark);
 for(const x of [-38,-185])plate(core,'Опора горизонтального вала',[x,0,-45],[1,0,0],5.2*s,14*s,12,brass);
 const housing=hollowBox.bind(null,core,'Корпус угловой передачи',[-40,-35,-75],[80,70,60],dark,[{anchor_mm:[0,0,-15],outward:[0,0,1],bore_mm:2*5*s+2},{anchor_mm:[-40,0,-45],outward:[-1,0,0],bore_mm:2*5*s+2}]);housing();for(const o of core.children.filter(o=>o.name.includes('Корпус угловой')))skin(o);
 for(const x of [-65,65])for(const y of [-30,30]){beam(core,'Консоль корпуса угловой передачи',[Math.sign(x)*35,y,-15],[x,y,-15],8,5,steel);bar(core,'Подвес корпуса к поддону',[x,y,-15],[x,y,K.trayZ-K.origin[2]],3,steel);}
 for(const x of [-185,-38])bar(core,'Опора подшипника выхода к поддону',[x,0,-31],[x,0,K.trayZ-K.origin[2]],4,dark);
 plate(core,'Выходная соединительная муфта · ось КПП пока условная',[-outputReach,0,-45],[1,0,0],5.2*s,22,10,brass);
 for(let i=0;i<7;i++){
  const p=compactPose(i,0),alpha=p.alpha,u=[Math.cos(alpha),Math.sin(alpha)],v=[-u[1],u[0]],at=(r,z=61,t=0)=>[u[0]*r+v[0]*t,u[1]*r+v[1]*t,z],mechanical=(r,z=61,t=0)=>at(r*s,z,t*s),g=new T.Group();g.name='Цилиндр '+(i+1)+' · двойное действие';g.userData.cylinder=i;core.add(g);
  const rodStart=i===0?V(p.crankpin).add(V(p.crosshead).sub(V(p.crankpin)).normalize().multiplyScalar(28*jointScale)).toArray():p.pin;
  const rod=connectingRod(g,i===0?'Главный шатун':'Прицепной шатун '+i,rodStart,p.crosshead,i===0),big=null,small=null;
  const crosshead=forkCrosshead(g,p.crosshead,alpha);for(const y of [-20.25*s,20.25*s])box(crosshead,'Башмак направляющей',[0,y,0],[10.5*s,.5*s,7],brass);
  for(const t of [-22,22])beam(g,'Направляющая крейцкопфа',mechanical(94,58,t),mechanical(145,58,t),3,12,dark);
  beam(g,'Радиальная балка',mechanical(69,-26),mechanical(207,-26),16,8,dark);
  for(const r of [158,190]){beam(g,'Лапа цилиндра',mechanical(r,-16,-24),mechanical(r,-16,24),9,12,steel);for(const t of [-20,20])bar(g,'Стойка до цилиндра',mechanical(r,-10,t),mechanical(r,61,t),3,brass);}
  const barrel=skin(plate(g,'Гильза ID32 / OD40',mechanical(152.4),[...u,0],16*s,20*s,43.2*s,steel));
  const jacket=skin(plate(g,'Изоляция цилиндра15 мм',mechanical(152.4),[...u,0],20*s,20*s+15,43.2*s,insulation));skin(plate(g,'Защитный кожух цилиндра0,5 мм',mechanical(152.4),[...u,0],20*s+15,20*s+15.5,43.2*s,steel));
  const inv=new T.Quaternion().setFromUnitVectors(Z,V([...u,0])).invert(),offB=V([0,0,-12]).applyQuaternion(inv),offA=V([-v[0]*10*s,-v[1]*10*s,0]).applyQuaternion(inv);
  plate(g,'Штоковая крышка B · проход штока и отдельный порт',mechanical(150.4),[...u,0],3.94*s,24*s,2*s,steel,[[offB.x,offB.y,4]]);
  plate(g,'Наружная крышка A · отдельный порт',mechanical(195.6),[...u,0],0,24*s,2*s,steel,[[offA.x,offA.y,4]]);
  const piston=bar(g,'ПоршеньØ32',at(p.pistonRadius-3*s),at(p.pistonRadius+3*s),16*s-.15,orange),pistonRod=bar(g,'ШтокØ7,68',p.crosshead.map((x,j)=>x+(j<2?u[j]*5.25*s:0)),p.piston,3.84*s,brass);
  const fluidMat=mat('#fff1d6',0);fluidMat.transparent=true;fluidMat.opacity=.15;fluidMat.depthWrite=false;
  const fluidA=bar(g,'Пар в камере A',at(p.pistonRadius+3*s),mechanical(195.6),16*s-.2,fluidMat),fluidB=plate(g,'Пар в камере B',mechanical(152.4),[...u,0],3.9*s,16*s-.2,39*s,fluidMat);
  const valve=new T.Group();valve.name='Распределитель '+(i+1)+' · проходы A/B';valve.rotation.z=alpha;g.add(valve);
  const valveR=176*s,loopR=195.6*s+34;
  const vp=[{id:'A',anchor_mm:[valveR+20,-10,190],outward:[1,0,0],bore_mm:8},{id:'B',anchor_mm:[valveR,14,205],outward:[0,0,1],bore_mm:8},{id:'in',anchor_mm:[valveR,-14,205],outward:[0,0,1],bore_mm:8},{id:'out',anchor_mm:[valveR,0,165],outward:[0,0,-1],bore_mm:12}];
  hollowBox(valve,'Коробка парораспределения · не выбранный клапан',[valveR-20,-25,165],[40,50,40],dark,vp);for(const o of valve.children)skin(o);
  tube('Подача '+(i+1),[at(132,260),at(132,278),at(valveR,278,-14),at(valveR,205,-14)],P.supply,18,'inlet',i);
  tube('Выпуск '+(i+1),[at(valveR,165),at(valveR,120),at(104,120),at(104,145)],P.exhaust,24,'outlet',i);
  tube('Камера '+(i+1)+'A',[at(valveR+20,190,-10),at(loopR,190,-10),at(loopR,61,-10*s),mechanical(197.6,61,-10)],P.chamber,18,'chamber',i,'A',24);
  tube('Камера '+(i+1)+'B',[at(valveR,205,14),at(valveR,278,14),at(loopR,278,14),at(loopR,278,60*s),at(loopR,100,60*s),mechanical(110,100,60),mechanical(110,49,60),mechanical(110,49),mechanical(150.4,49)],P.chamber,18,'chamber',i,'B',80);
  portRecords.push({cylinder:i,A:{face_mm:mechanical(197.6,61,-10),outward:[...u,0],bore_mm:8},B:{face_mm:mechanical(150.4,49),outward:[-u[0],-u[1],0],bore_mm:8},valve_ports:vp});
  cylinders.push({g,at,mechanical,piston,pistonRod,rod,big,small,crosshead,fluidA,fluidB,barrel,jacket});
 }
 const defaultAnchors=[[3000,-177,286.5353667979263],[3000,177,286.5350932618857],[3420,-177,366.4795014104693],[3420,177,366.4795014104296]];
 // Plane113 is sloped: a flat pad and a cylinder starting at centre height cut
 // into its high side. These wedges follow the actual local plane at all corners.
 const defaultSlopes=[[.0132322107,-.6028257649],[.0132321559,.6028269496],[.0741366940,-.0000000951],[.0741366940,.0000000951]];
 const anchorData=floorAnchors||defaultAnchors.map(p=>[p[0]+K.origin[0]-3210,p[1],p[2]]),slopes=floorSlopes||defaultSlopes;
 if(!skipSupports)for(const [index,[x,y,z]]of anchorData.entries()){
  const [sx,sy]=slopes[index],q=[x-K.origin[0],y-K.origin[1],z-K.origin[2]],corners=[[-6,-6],[6,-6],[6,6],[-6,6]],base=corners.map(([dx,dy])=>[q[0]+dx,q[1]+dy,q[2]+sx*dx+sy*dy]),top=Math.max(...base.map(p=>p[2]))+3;
  const points=[...base,...corners.map(([dx,dy])=>[q[0]+dx,q[1]+dy,top])],faces=[0,2,1,0,3,2,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7],geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(faces.flatMap(i=>points[i]),3));geo.computeVertexNormals();const pad=mesh(contacts,'Клиновая площадка12×12 · контакт с Plane113',geo,steel);pad.userData.floorContact={anchor_mm:[x,y,z],slopes:[sx,sy],pad_half_mm:6,top_world_mm:top+K.origin[2],load_bearing_confirmed:false};
  bar(mounts,'Стойка от клиновой площадки до поддона',[q[0],q[1],top],[q[0],q[1],K.trayZ-K.origin[2]],6,dark);plate(core,'Крепление стойки к поддону',[q[0],q[1],K.trayZ-K.origin[2]],[0,0,1],3.2,12,6,brass);
 }
 function setBar(o,a,b){const d=V(b).sub(V(a));o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.scale.y=d.length()/o.geometry.parameters.height;o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());}
 function update(angle,flowTime,camera,arrowsVisible=true){commonCrank.rotation.z=angle;const main=compactPose(0,angle);masterFork.position.set(main.crankpin[0],main.crankpin[1],0);masterFork.rotation.z=main.masterTilt;bevelVertical.rotation.z=angle;bevelHorizontal.rotation.z=-angle;const states=cylinders.map((c,i)=>{
  const p=compactPose(i,angle);c.crosshead.position.fromArray(p.crosshead);const rodStart=i===0?V(p.crankpin).add(V(p.crosshead).sub(V(p.crankpin)).normalize().multiplyScalar(28*jointScale)).toArray():p.pin;const d=V(p.crosshead).sub(V(rodStart));c.rod.position.copy(V(rodStart).add(V(p.crosshead)).multiplyScalar(.5));c.rod.scale.x=d.length()/c.rod.userData.rodLength;c.rod.rotation.z=Math.atan2(d.y,d.x);if(c.big){c.big.position.fromArray(p.pin);c.big.position.z-=2;}
  setBar(c.piston,c.at(p.pistonRadius-3*s),c.at(p.pistonRadius+3*s));setBar(c.pistonRod,c.at(p.crossheadRadius+5.25*s),p.piston);setBar(c.fluidA,c.at(p.pistonRadius+3*s),c.mechanical(195.6));c.fluidB.scale.z=(p.pistonRadius-3*s-152.4*s)/(39*s);
  c.fluidA.material.color.set(p.A.exhaust?'#9ac9e4':'#ffe3b0');c.fluidB.material.color.set(p.B.exhaust?'#9ac9e4':'#ffe3b0');return p;
 });
  if(camera)for(const r of routes){const p=r.index===null?null:states[r.index],ch=r.chamber?p[r.chamber]:null,active=ch?ch.inlet||ch.exhaust:r.role==='inlet'?p.A.inlet||p.B.inlet:r.role==='outlet'?p.A.exhaust||p.B.exhaust:true;r.arrows.update({camera,radius:r.spec.outside_mm/2,phase:flowTime*.45,visible:arrowsVisible&&active,direction:ch?.exhaust?-1:1,color:ch?.exhaust||['return','outlet'].includes(r.role)?'#a5d0e6':'#ffe3b0',clippingPlanes:[]});}
  return states;
 }
 function mechanismOnly(on){for(const g of core.children)if(/пленум|Подача |Выпуск |Камера |Граничный|Ввод в пленум|Впуск ·|Изоляция границы/.test(g.name))g.visible=!on;for(const c of cylinders){for(const g of c.g.children)if(g.name.startsWith('Распределитель'))g.visible=!on;} }
 function cutaway(on){for(const o of skins){o.material.transparent=on;o.material.opacity=on?.14:1;o.material.depthWrite=!on;}}
 root.traverse(o=>{o.name=o.name.replace('m1,5', 'm'+K.module).replace('ID32 / OD40',`ID${K.bore} / OD${40*s}`).replace('ПоршеньØ32',`ПоршеньØ${K.bore}`).replace('ШтокØ7,68',`ШтокØ${K.rod}`).replace('Шатун57 мм',`Шатун${K.link} мм`).replace('r18',`r${K.crank}`);if(o.name.startsWith('Пар в камере'))o.userData.collision=false;});
 cutaway(true);update(0,0);
 root.userData={id:'FITTED_ENGINE',mechanism:'master-articulated',units:'mm/Z-up',geometry:`Seven double-acting cylinders D${K.bore} S${K.stroke}; one master and six articulated rods on one crankpin; conceptual distributor and one bevel pair`,not_manufacturing_cad:true};
 return {root,core,mounts,contacts,cylinders,routes,portRecords,anchorData,update,cutaway,config:K,pose:compactPose,commonCrank,masterFork,mechanismOnly};
}
