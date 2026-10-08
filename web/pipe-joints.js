import * as T from 'three';
import {connectionSpecs} from './connection-data.js';
import {pipeCurve} from './pipe-path.js';
const V=p=>new T.Vector3(...p);
const material=(color='#aeb7bb')=>new T.MeshStandardMaterial({color,metalness:.65,roughness:.37,side:T.DoubleSide});
export function hollowTube(g,name,a,b,od,bore,options={}){
 const A=V(a),B=V(b),L=A.distanceTo(B),profile=[new T.Vector2((options.entry_bore_mm||bore)/2,-L/2),new T.Vector2((options.entry_od_mm||od)/2,-L/2),new T.Vector2(od/2,L/2),new T.Vector2(bore/2,L/2),new T.Vector2((options.entry_bore_mm||bore)/2,-L/2)];
 const mesh=new T.Mesh(new T.LatheGeometry(profile,32),material(options.color));mesh.name=name;mesh.position.copy(A).add(B).multiplyScalar(.5);mesh.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),B.sub(A).normalize());mesh.userData={semantic:true,connectionHardware:true,bore_mm:bore,...options};g.add(mesh);return mesh;
}
function seal(g,name,face,axis,outer,bore){return hollowTube(g,name,V(face).addScaledVector(V(axis),-.6).toArray(),V(face).addScaledVector(V(axis),.6).toArray(),outer,bore,{color:'#2c3937',seal:true});}
export function jointHalf(g,p,face,sign=1){
 const n=V(p.outward),q=V(face),OD=p.od_mm+Math.max(14,p.od_mm*.22),bore=p.bore_mm;
 hollowTube(g,(sign>0?'Ответная муфта трубы · ':'Муфта патрубка · ')+p.id,q.clone().addScaledVector(n,sign*.6).toArray(),q.clone().addScaledVector(n,sign*10).toArray(),OD,bore,{portId:p.id,kind:p.kind});
 if(sign<0)seal(g,'Уплотнение · материал не выбран · '+p.id,face,p.outward,OD-2,bore);
 const side=new T.Vector3(Math.abs(n.z)<.9?0:1,0,Math.abs(n.z)<.9?1:0).cross(n).normalize(),up=new T.Vector3().crossVectors(n,side);
 // Bolts stay outside the bore; dimensions are illustrative, not a selected flange.
 if(p.kind==='weld-neck')for(let i=0;i<4;i++){
  const c=q.clone().addScaledVector(side,Math.cos(i*Math.PI/2)*(OD/2-4)).addScaledVector(up,Math.sin(i*Math.PI/2)*(OD/2-4));
  const o=new T.Mesh(new T.CylinderGeometry(2.6,2.6,20,6),material('#48525b'));o.position.copy(c);o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),n);o.name='Крепёж разъёма · условный · '+p.id;o.userData={semantic:true,connectionHardware:true,portId:p.id};g.add(o);
 }
}
export function equipmentPorts(g,xyz,id,sourceId='diesel'){
 const offset=V(xyz),ports=Object.values(connectionSpecs.variants[sourceId].ports).filter(p=>p.owner===id);
 for(const p of ports){if(p.kind==='duct'&&id==='BODY')continue;const a=V(p.anchor_mm).sub(offset),b=V(p.face_mm).sub(offset);hollowTube(g,'Полый патрубок · '+p.id,a.toArray(),b.toArray(),p.od_mm,p.bore_mm,{portId:p.id,thread:p.thread,entry_od_mm:p.entry_od_mm,entry_bore_mm:p.entry_bore_mm});jointHalf(g,p,b.toArray(),-1);}
 g.userData.ports=ports;return g;
}
// Pressure walls with actual through-holes. Coordinates of the port anchor locate
// its opening; an inclined nozzle gets the elliptical intersection of its bore.
export function hollowBox(g,name,pos,size,keyMaterial,ports=[],customPolygon=null){
 const [L,B,H]=size,origin=V(pos),t=4,polygon=customPolygon||[[0,0],[L,0],[L,B],[0,B]];
 const add=(shape,center,u,v,n,depth=t)=>{const o=new T.Mesh(new T.ExtrudeGeometry(shape,{depth,bevelEnabled:false,curveSegments:24}),keyMaterial.clone());o.name=name+' · полая стенка';o.position.copy(center).addScaledVector(n,-depth);o.quaternion.setFromRotationMatrix(new T.Matrix4().makeBasis(u,v,n));o.userData.semantic=true;g.add(o);};
 function hole(shape,p,center,u,v,n){const anchor=V(p.anchor_mm),axis=V(p.outward),delta=anchor.sub(center),dot=axis.dot(n);if(Math.abs(delta.dot(n))>.05||Math.abs(dot)<.01)return;const a=delta.dot(u),b=delta.dot(v),r=(p.entry_bore_mm||p.bore_mm)/2,proj=new T.Vector2(axis.dot(u),axis.dot(v));if(!new T.Box2().setFromPoints(shape.getPoints()).containsPoint(new T.Vector2(a,b)))return;const h=new T.Path();h.absellipse(a,b,r/Math.abs(dot),r,0,2*Math.PI,false,Math.atan2(proj.y,proj.x));shape.holes.push(h);}
 for(let i=0;i<polygon.length;i++){const a=polygon[i],b=polygon[(i+1)%polygon.length],u=V([b[0]-a[0],b[1]-a[1],0]).normalize(),v=V([0,0,1]),n=new T.Vector3().crossVectors(u,v),len=Math.hypot(b[0]-a[0],b[1]-a[1]),center=origin.clone().add(V([(a[0]+b[0])/2,(a[1]+b[1])/2,H/2]));const sh=new T.Shape([new T.Vector2(-len/2,-H/2),new T.Vector2(len/2,-H/2),new T.Vector2(len/2,H/2),new T.Vector2(-len/2,H/2)]);for(const p of ports)hole(sh,p,center,u,v,n);add(sh,center,u,v,n);}
 for(const z of [0,H]){const n=V([0,0,z?1:-1]),u=V([1,0,0]),v=V([0,z?1:-1,0]),center=origin.clone().add(V([L/2,B/2,z])),sh=new T.Shape(polygon.map(p=>new T.Vector2(p[0]-L/2,(p[1]-B/2)*(z?1:-1))));for(const p of ports)hole(sh,p,center,u,v,n);add(sh,center,u,v,n);}
}
export function localPorts(id,xyz,sourceId='diesel') {return Object.values(connectionSpecs.variants[sourceId].ports).filter(p=>p.owner===id).map(p=>({...p,anchor_mm:p.anchor_mm.map((v,i)=>v-xyz[i])}));}
class Span extends T.Curve {constructor(curve,start,end){super();Object.assign(this,{curve,start,end,length:curve.getLength()});}getPoint(t,target=new T.Vector3()){return this.curve.getPointAt((this.start+t*(this.end-this.start))/this.length,target);}getPointAt(t,target){return this.getPoint(t,target);}getTangent(t,target){return this.curve.getTangentAt((this.start+t*(this.end-this.start))/this.length,target);}getTangentAt(t,target){return this.getTangent(t,target);}getLength(){return this.end-this.start;}}
function station(curve,p){let sum=0;const target=V(p);for(const c of curve.curves){const L=c.getLength();if(c.isLineCurve3){const d=c.v2.clone().sub(c.v1),f=T.MathUtils.clamp(target.clone().sub(c.v1).dot(d)/d.lengthSq(),0,1);if(c.getPoint(f).distanceTo(target)<.001)return sum+f*L;}sum+=L;}throw Error('Inline fitting is not on a straight pipe span: '+p);}
export function physicalPipeSpans(spec,insulated=false){const curve=pipeCurve(spec),L=curve.getLength(),ends=insulated?spec.exposed_end_mm||0:0,intervals=(spec.inline_components||[]).map(p=>[station(curve,p.start_mm),station(curve,p.end_mm)]).sort((a,b)=>a[0]-b[0]);let start=ends;const spans=[];for(const [a,b]of intervals){if(a>start)spans.push(new Span(curve,start,a));start=b;}if(L-ends>start)spans.push(new Span(curve,start,L-ends));return spans;}
export function jointMetrics(route){return (route.end_ports||[]).map((p,i)=>{const points=route.points,q=points[i?points.length-1:0],delta=i?V(points.at(-1)).sub(V(points.at(-2))):V(points[1]).sub(V(points[0])),expected=V(p.outward).multiplyScalar(i?-1:1);return {port:p.id,gap_mm:V(q).distanceTo(V(p.face_mm)),axis_error_deg:T.MathUtils.radToDeg(Math.acos(T.MathUtils.clamp(delta.normalize().dot(expected),-1,1))),pipe_bore_mm:route.inside_id_mm,port_bore_mm:p.bore_mm,geometry_ok:V(q).distanceTo(V(p.face_mm))<.001&&delta.dot(expected)>.99999&&route.inside_id_mm===p.bore_mm,pressure_verified:false};});}
