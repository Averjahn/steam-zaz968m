import * as T from 'three';
import {hollowTube} from './pipe-joints.js?v=783013dea290';
import {engineGeometry as K} from './double-acting-cycle.js?v=02f171f7ae23';
const V=p=>new T.Vector3(...p);
// Concept passages in the existing engine envelope. Diameters are visualization
// assumptions; no new valve capacity or rated-pressure claim is made here.
export function addDoubleActingPipes(engine){
 const group=new T.Group();group.name='Double-acting: распределение и две обратимые линии на цилиндр';
 engine.add(group);group.doubleActingPaths=[];
 function path(id,points,role,cylinder=null,chamber=null,od=32,bore=24){
  // Polyline with rounded corners; preserve endpoints and avoid curve overshoot.
  const curve=new T.CurvePath();let start=V(points[0]);
  for(let i=1;i<points.length-1;i++){const a=V(points[i-1]),b=V(points[i]),d=V(points[i+1]),trim=Math.min(26,a.distanceTo(b)*.3,b.distanceTo(d)*.3),before=b.clone().add(a.sub(b).normalize().multiplyScalar(trim)),after=b.clone().add(d.sub(b).normalize().multiplyScalar(trim));curve.add(new T.LineCurve3(start,before));curve.add(new T.QuadraticBezierCurve3(before,b,after));start=after;}
  curve.add(new T.LineCurve3(start,V(points.at(-1))));
  const metal=new T.MeshStandardMaterial({color:role==='steam'?'#bcb5a1':role==='exhaust'?'#738a94':'#aabcc4',metalness:.7,roughness:.32,side:T.DoubleSide});
  for(const [r,name]of [[od/2,'стенка'],[bore/2,'проход']]){const m=new T.Mesh(new T.TubeGeometry(curve,Math.max(12,Math.ceil(curve.getLength()/9)),r,12,false),metal.clone());m.name=id+' · '+name;m.userData={semantic:true,doubleActingPipe:true,role,cylinder,chamber,od_mm:od,bore_mm:bore};group.add(m);}
  const item={id,curve,role,cylinder,chamber,radius:od/2,bore:bore/2,points};group.doubleActingPaths.push(item);return item;
 }
 // Existing external ports stay at their registered locations. Fresh-steam
 // header distributes ENG.inlet; each chest returns to its existing exhaust.
 // T-off from the registered inlet rises above the exhaust nozzle; it does
 // not run through ENG.exhaustR at [420,130,405]. Top OD stays inside Z=500.
 path('DA.common-steam',[[200,111,415],[200,111,480],[415,111,480],[415,154,480],[415,154,465]],'steam',null,null,40,32);
 for(const [i,x]of K.cylinderX.entries()){
  const side=i===0?-1:1,nodeX=x+side*36,edgeX=x+side*45,bendX=x+side*110,headX=x+side*91;
  path('DA.'+i+'.feed',i===0?[[x,130,415],[x-18,140,415]]:[[x,154,465],[x-18,140,465],[x-18,140,415]],'steam',i);
  const exhaust=i===0?[200,130,325]:[420,130,405];
  path('DA.'+i+'.exhaust',[[x+18,168,340],exhaust],'exhaust',i);
  for(const [ch,z,face]of [['A',451,K.topFace],['B',293,K.bottomFace]]){
   path('DA.'+i+'.'+ch+'.steam',[[x-18,140,415],[x-18,140,z],[nodeX,140,z],[nodeX,154,z]],'admission',i,ch,20,14);
   path('DA.'+i+'.'+ch+'.exhaust',[[nodeX,154,z],[nodeX,168,z],[x+18,168,z],[x+18,168,340]],'vent',i,ch,20,14);
   path('DA.'+i+'.'+ch+'.branch',[[nodeX,154,z],[edgeX,154,z],[bendX,154,z],[bendX,250,z],[headX,250,z]],'chamber',i,ch);
   // Nozzle ends terminate on the cylinder head rather than in empty space.
   hollowTube(group,'Штуцер камеры '+(i+1)+ch,[headX+side*10,250,z],[headX-side*8,250,z],38,24,{doubleActingPipe:true,chamber:ch,cylinder:i});
   const headCurve=new T.CurvePath();headCurve.add(new T.LineCurve3(V([headX,250,z]),V([x+side*35,250,z])));headCurve.add(new T.LineCurve3(V([x+side*35,250,z]),V([x+side*35,250,face])));
   const bore=new T.Mesh(new T.TubeGeometry(headCurve,16,12,12,false),new T.MeshBasicMaterial({color:'#b9d6d8',transparent:true,opacity:.16,depthTest:false,depthWrite:false}));
   bore.name='Показанный в разрезе канал крышки '+(i+1)+ch;bore.userData={semantic:true,doubleActingHeadPassage:true};group.add(bore);
  }
 }
 return group;
}
