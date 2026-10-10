import * as T from 'three';
import {distributionState} from './engine-distribution-model.js?v=79cc68aec8c0';
import {pipeArrows} from './pipe-arrows.js?v=dd3bd35c3fcf';
// The diameter of this functional overlay is symbolic. It is intentionally
// excluded from collision/pressure/volume calculations. GLB retains it with
// explicit schematic metadata; it must not be treated as pressure-manifold CAD.
// A real, sized four-valve manifold and its drive still need engineering.
export function distributorDiagram(group,R,studyOutlet){
 const diagram=new T.Group();diagram.name='Функциональная схема · четыре клапана, НЕ размерный коллектор';diagram.userData.viewOnly=true;diagram.userData.distributionSchematic=true;group.add(diagram);
 const channels=[],gates=[];
 const P=[[R,-14,205],[R,-14,199],[R-8,-14,199]],A=[R+12,-10,185],B=[R-8,14,185];
 function path(name,points,color,gate=null){
  const curve=new T.CurvePath();for(let i=1;i<points.length;i++)curve.add(new T.LineCurve3(new T.Vector3(...points[i-1]),new T.Vector3(...points[i])));
  const mesh=new T.Mesh(new T.TubeGeometry(curve,Math.max(8,points.length*5),1.8,8,false),new T.MeshBasicMaterial({color,transparent:true,opacity:.8,depthWrite:false}));mesh.name=name+' · условный проход';diagram.add(mesh);
  const arrows=pipeArrows(curve,{id:name,fluid:color==='#a5d0e6'?'exhaust':'steam'});diagram.add(arrows.group);channels.push({gate,mesh,arrows});return curve;
 }
 path('P · свежий пар',P,'#ffe3b0');
 path('Верхний канал P',[[R-8,-14,199],[R+12,-14,199],[R+12,-10,199]],'#ffe3b0','PA');
 path('Ответвление P к B',[[R-8,-14,199],[R-8,14,199]],'#ffe3b0','PB');
 const outlet=studyOutlet?[[R-20,0,185],[R-14,0,185],[R-14,0,173],[R,0,173]]:[[R,0,173],[R,0,165]];
 // Orient every exhaust channel toward T, including the side outlet variant.
 path('T · отработавший пар',studyOutlet?outlet.toReversed():outlet,'#a5d0e6');
 for(const [id,from,to]of [['AT',[R+12,-10,173],[R,0,173]],['BT',[R-8,14,173],[R,0,173]]])path('Нижний канал '+id,[from,[from[0],0,173],to],'#a5d0e6',id);
 for(const [ch,node]of [['A',A],['B',B]]){
  path('P→'+ch,[[node[0],node[1],199],node],'#ffe3b0','P'+ch);
  path(ch+'→T',[node,[node[0],node[1],173]],'#a5d0e6',ch+'T');
  path('Порт '+ch,ch==='A'?[A,[R+12,-10,190],[R+20,-10,190]]:[B,[R,14,185],[R,14,205]],'#c8a165',ch);
  for(const [id,z]of [['P'+ch,193],[ch+'T',179]]){
   const disc=new T.Mesh(new T.CylinderGeometry(3.4,3.4,1.2,16),new T.MeshBasicMaterial({color:'#eb7064'}));disc.rotation.x=Math.PI/2;disc.position.set(node[0],node[1],z);disc.name=id+' · запорный орган (условная схема)';diagram.add(disc);gates.push({id,disc,z,x:node[0],y:node[1],side:ch==='A'?1:-1});
  }
 }
 function update(pose,time,camera,visible){const state=distributionState(pose),byId=Object.fromEntries(state.valves.map(v=>[v.id,v.open]));
  for(const {id,disc,z,x,y,side}of gates){const open=byId[id];disc.position.set(x,y+(open?7*side:0),z);disc.material.color.set(open?'#90d69d':'#eb7064');disc.userData.open=open;}
  if(camera)for(const c of channels){const chamber=c.gate==='A'||c.gate==='B'?pose[c.gate]:null,active=chamber?chamber.inlet||chamber.exhaust:c.gate?byId[c.gate]:state.valves.some(v=>v.open&&v.kind===(c.mesh.name.startsWith('P')?'inlet':'exhaust'));
   c.arrows.update({camera,radius:2,phase:time*.45,visible:visible&&active,direction:chamber?.exhaust?-1:1,color:chamber?.exhaust||c.mesh.name.startsWith('T')||c.mesh.name.startsWith('Нижний')||c.gate?.endsWith('T')?'#a5d0e6':'#ffe3b0',clippingPlanes:[]});
  }return state;
 }
 return {group:diagram,gates,channels,update};
}
