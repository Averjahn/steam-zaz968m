import * as T from 'three';
import {engineGeometry as K} from './double-acting-cycle.js';
import {crankLayout as C,gearOutline} from './crank-mechanism-model.js';
const V=p=>new T.Vector3(...p),Y=new T.Vector3(0,1,0);
const planeToYZ=new T.Matrix4().makeBasis(V([0,1,0]),V([0,0,1]),V([1,0,0]));
function tools(parent,material){
 const mesh=(name,geometry,key='steel',position=[0,0,0])=>{const o=new T.Mesh(geometry,material(key));o.name=name;o.position.fromArray(position);o.userData.semantic=true;parent.add(o);return o;};
 const box=(name,center,size,key='steel')=>mesh(name,new T.BoxGeometry(...size),key,center);
 const cylinder=(name,a,b,r,key='steel')=>{const p=V(a),q=V(b),o=mesh(name,new T.CylinderGeometry(r,r,p.distanceTo(q),24),key,p.clone().add(q).multiplyScalar(.5).toArray());o.quaternion.setFromUnitVectors(Y,q.sub(p).normalize());return o;};
 const ring=(name,center,outer,inner,width,key='brass')=>{const s=new T.Shape();s.absarc(0,0,outer,0,2*Math.PI,false);const h=new T.Path();h.absarc(0,0,inner,0,2*Math.PI,true);s.holes.push(h);const g=new T.ExtrudeGeometry(s,{depth:width,bevelEnabled:false,curveSegments:24});g.applyMatrix4(planeToYZ);g.translate(-width/2,0,0);return mesh(name,g,key,center);};
 return {mesh,box,cylinder,ring};
}
export function addCrankshaft(parent,material){
 const t=tools(parent,material),cranks=[],gears=[];
 for(const [a,b]of C.journalIntervals)t.cylinder('Коренная шейка · отдельный участок',[a,K.cylinderY,K.crankZ],[b,K.cylinderY,K.crankZ],C.journalRadius);
 for(const [i,x]of K.cylinderX.entries()){
  const g=new T.Group();g.name='Колено '+(i+1)+' · две щеки и шатунная шейка';g.position.set(x,K.cylinderY,K.crankZ);g.userData={doubleActingCrank:i};parent.add(g);const q=tools(g,material);
  const shape=new T.Shape(),r=C.cheekRadius;shape.moveTo(-r,0);shape.lineTo(-r,K.crankRadius);shape.absarc(0,K.crankRadius,r,Math.PI,0,true);shape.lineTo(r,0);shape.absarc(0,0,r,0,-Math.PI,true);shape.closePath();
  for(const start of [-C.cheekOuter,C.cheekInner]){const geometry=new T.ExtrudeGeometry(shape,{depth:C.cheekOuter-C.cheekInner,bevelEnabled:false,curveSegments:16});geometry.applyMatrix4(planeToYZ);q.mesh('Щека коленвала',geometry,'steel',[start,0,0]);}
  q.cylinder('Шатунная шейка · смещена на 60 мм',[-C.pinHalfWidth,0,K.crankRadius],[C.pinHalfWidth,0,K.crankRadius],C.pinRadius,'brass');
  g.rotation.x=-i*K.phaseOffset;cranks.push(g);
 }
 // The raised output axis stays coaxial with the displayed gearbox at Z=445 mm.
 t.cylinder('Выходной вал к КПП',[25,K.cylinderY,K.outputZ],[130,K.cylinderY,K.outputZ],C.journalRadius);
 for(const [which,z,sign,phase]of [['input',K.crankZ,-1,0],['output',K.outputZ,1,Math.PI/C.teeth]]){
  const g=new T.Group();g.name='Передаточная шестерня 1:1 · '+which;g.position.set(C.gearX,K.cylinderY,z);g.userData={doubleActingGear:true,sign,phase};parent.add(g);
  const outline=gearOutline(),shape=new T.Shape(outline.map(V2=>new T.Vector2(...V2))),hole=new T.Path();hole.absarc(0,0,C.journalRadius,0,2*Math.PI,true);shape.holes.push(hole);
  const geometry=new T.ExtrudeGeometry(shape,{depth:C.gearWidth,bevelEnabled:false,curveSegments:24});geometry.applyMatrix4(planeToYZ);geometry.translate(-C.gearWidth/2,0,0);tools(g,material).mesh('Эвольвентные зубья · m2 / z28, модель',geometry,'brass');g.rotation.x=phase;gears.push(g);
 }
 return {cranks,gears};
}
export function addMechanismFrame(parent,material){
 const t=tools(parent,material);
 for(const x of K.cylinderX){
  for(const side of [-1,1]){const railX=x+side*C.guideOffsetX;
   t.box('Направляющая крейцкопфа',[railX,K.cylinderY,(C.guideMinZ+C.guideMaxZ)/2],[C.guideWidthX,48,C.guideMaxZ-C.guideMinZ],'dark');
   for(const dy of [-40,40])t.box('Стойка направляющей',[railX,K.cylinderY+dy,65],[8,8,124],'steel');
   t.box('Поперечина направляющей',[railX,K.cylinderY,126],[8,88,8],'steel');
  }
 }
 for(const x of [145,335,480]){
  t.ring('Коренной подшипник · модель',[x,K.cylinderY,K.crankZ],30,19,16);
  t.box('Опора коренного подшипника',[x,K.cylinderY,31],[16,60,56],'dark');
 }
 t.ring('Подшипник выходного вала',[77,K.cylinderY,K.outputZ],30,19,10);
 t.box('Опора выходного подшипника',[77,K.cylinderY,58],[10,60,110],'dark');
}
export function rodMechanism(parent,cylinder,material){
 const g=new T.Group();g.name='Шатун и крейцкопф '+(cylinder+1);parent.add(g);const t=tools(g,material);
 const big=t.ring('Большая головка шатуна',[0,0,0],C.bigEyeOuter,C.bigEyeInner,2*C.rodHalfWidth);
 const small=t.ring('Малая головка шатуна',[0,0,0],C.smallEyeOuter,C.smallEyeInner,18);
 const beam=t.cylinder('Тело шатуна · между головками',[0,0,0],[0,1,0],7);
 const crosshead=new T.Group();crosshead.name='Крейцкопф в направляющих';g.add(crosshead);const q=tools(crosshead,material);
 q.cylinder('Палец крейцкопфа',[-25,0,0],[25,0,0],6,'brass');
 for(const side of [-1,1]){
  q.box('Вилка крейцкопфа',[side*20,0,4],[8,32,26]);
  q.box('Ползун крейцкопфа',[side*28,0,4],[7,44,18],'brass');
 }
 q.box('Перемычка крепления штока',[0,0,K.crossheadBridgeZ],[63,32,8]);
 const objects=[];g.traverse(o=>{if(o.isMesh){o.explanationBaseColor=o.material.color.clone();objects.push(o);}});
 return {group:g,objects,pose(cycle){const x=K.cylinderX[cylinder],a=cycle.angle_rad,pin=V([x,K.cylinderY+K.crankRadius*Math.sin(a),K.crankZ+K.crankRadius*Math.cos(a)]),end=V([x,K.cylinderY,cycle.pistonZ_mm-K.pistonRod]),d=end.clone().sub(pin).normalize(),start=pin.clone().addScaledVector(d,20),finish=end.clone().addScaledVector(d,-12);
  big.position.copy(pin);small.position.copy(end);crosshead.position.copy(end);beam.position.copy(start).add(finish).multiplyScalar(.5);beam.scale.y=start.distanceTo(finish);beam.quaternion.setFromUnitVectors(Y,d);
  return {pin:pin.toArray(),crosshead:end.toArray()};
 }};
}
