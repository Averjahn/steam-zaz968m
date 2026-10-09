import * as T from 'three';
import {pipeArrows} from './pipe-arrows.js';
import {engineGeometry as K,cylinderCycle} from './double-acting-cycle.js';
import {temperatureRGB} from './thermal-model.js';
import {chamberSteam} from './steam-cloud.js';
import {rodMechanism} from './crank-mechanism.js';
const fresh='#fff0be',spent='#b8d2dc',closed='#71828d';
const mat=(color,opacity=1)=>new T.MeshBasicMaterial({color,transparent:opacity<1,opacity,depthWrite:opacity===1});
export function doubleActingView(api){
 const root=new T.Group();root.name='Double-acting cycle overlay (view only)';root.userData.viewOnly=true;api.scene.add(root);
 let bound=null,lines=[],shells=[],moving=[],wheels=[],cranks=[],gears=[],lastState=null,demoAngle=0,steamClock=0;
 const cylinders=[];
 function mesh(g,name,geometry,color,opacity=1){const o=new T.Mesh(geometry,mat(color,opacity));o.explanationBaseColor=o.material.color.clone();o.name=name;g.add(o);return o;}
 function label(g,p){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=96;const texture=new T.CanvasTexture(canvas),m=new T.SpriteMaterial({map:texture,transparent:true,depthTest:false,depthWrite:false}),s=new T.Sprite(m);s.position.fromArray(p);s.scale.set(170,32,1);s.renderOrder=920;g.add(s);let previous='';return {sprite:s,write(text,color){if(text===previous)return;previous=text;const c=canvas.getContext('2d');c.clearRect(0,0,512,96);c.fillStyle='#0b1827';c.fillRect(0,0,512,96);c.strokeStyle=color;c.lineWidth=5;c.strokeRect(3,3,506,90);c.fillStyle=color;c.font='bold 38px sans-serif';c.textAlign='center';c.textBaseline='middle';c.fillText(text,256,48);texture.needsUpdate=true;}};}
 for(const [i,x]of K.cylinderX.entries()){
  const g=new T.Group();root.add(g);
  const piston=mesh(g,'Движущийся поршень '+(i+1),new T.CylinderGeometry(49,49,K.pistonThickness,32),'#e9e8dc');piston.rotation.x=Math.PI/2;
  const rod=mesh(g,'Шток '+(i+1),new T.CylinderGeometry(K.rodDiameter/2,K.rodDiameter/2,1,20),'#d2b484');
  rod.rotation.x=Math.PI/2;
  const linkage=rodMechanism(g,i,key=>mat(key==='brass'?'#d2b484':'#a5bac2'));
  const volumes={};
  for(const ch of ['A','B']){const fluid=mesh(g,'Объём камеры '+(i+1)+ch,new T.CylinderGeometry(48,48,1,24),fresh,.035);fluid.rotation.x=Math.PI/2;fluid.renderOrder=910;const tag=label(g,[x+(i?96:-96),250,ch==='A'?460:285]);const steam=chamberSteam(g,i,ch,{count:innerWidth<=600?48:96});volumes[ch]={fluid,tag,steam};}
  const gates=[];for(const ch of ['A','B'])for(const circuit of ['inlet','exhaust']){const z=ch==='A'?451:293,gate=mesh(g,'Клапан '+(i+1)+ch+' · '+circuit,new T.SphereGeometry(8,12,8),closed);gate.position.set(x+(i?36:-36),circuit==='inlet'?140:168,z);gate.userData={chamber:ch,circuit,cylinder:i};gate.renderOrder=915;gate.material.depthTest=false;gates.push(gate);}
  cylinders.push({i,x,g,piston,rod,linkage,volumes,gates});
 }
 function bind(model){
  restore();
  for(const line of lines){for(const item of [line.arrows.group,line.fluid])item.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});root.remove(line.arrows.group,line.fluid);}lines=[];shells=[];moving=[];wheels=[];cranks=[];gears=[];bound=model;
  model?.root.traverse(o=>{
   if(o.userData.doubleActingShell)shells.push({node:o,materials:[].concat(o.material).map(material=>({material,opacity:material.opacity,transparent:material.transparent,depthWrite:material.depthWrite}))});
   if(o.userData.doubleActingStaticMoving)moving.push(o);
   if(o.userData.doubleActingWheel)wheels.push(o);
   if(Number.isInteger(o.userData.doubleActingCrank))cranks.push(o);
   if(o.userData.doubleActingGear)gears.push(o);
   for(const p of o.doubleActingPaths||[]){const arrows=pipeArrows(p.curve,{id:p.id,fluid:p.role==='exhaust'||p.role==='vent'?'exhaust':'steam'}),fluid=mesh(root,'Среда · '+p.id,new T.TubeGeometry(p.curve,Math.max(8,Math.ceil(p.curve.getLength()/12)),p.bore,10,false),fresh,.45);fluid.renderOrder=900;fluid.material.depthTest=false;root.add(arrows.group);lines.push({...p,arrows,fluid});}
  });
 }
 function restore(){for(const o of moving)o.visible=true;for(const wheel of wheels)wheel.rotation.x=0;for(const crank of cranks)crank.rotation.x=-crank.userData.doubleActingCrank*K.phaseOffset;for(const gear of gears)gear.rotation.x=gear.userData.phase;for(const entry of shells)for(const m of entry.materials){m.material.opacity=m.opacity;m.material.transparent=m.transparent;m.material.depthWrite=m.depthWrite;}}
 return {hide(){root.visible=false;restore();},snapshot:()=>lastState,exportMechanism(){
  if(!root.visible||!cylinders.some(c=>c.piston.visible))return null;
  const result=new T.Group();result.name='Поршни, штоки и крейцкопфы · текущая поза';result.userData={angle_deg:lastState?.angle_deg};
  for(const c of cylinders)for(const node of [c.piston,c.rod,c.linkage.group])result.add(node.clone(true));
  return result;
 },frame(dt,s,{mode='explain',angleDegrees=0,playing=true,speedDegrees=60,cutaway=true,labels=true,mechanism=true,clock=0,arrows=true,fluidPaths=true,fluidOnly=false,thermal=null,steamRender='cloud',steamOpacity=.75}={}){
  const model=api.models.get('ENG');if(model!==bound)bind(model);
  root.visible=mechanism&&!!model?.root.visible;
  if(!root.visible){restore();return;}
  for(const o of moving)o.visible=false;
  for(const entry of shells)for(const m of entry.materials){m.material.opacity=cutaway?.08:m.opacity;m.material.transparent=cutaway||m.transparent;m.material.depthWrite=cutaway?false:m.depthWrite;}
  model.root.updateWorldMatrix(true,false);root.matrixAutoUpdate=false;root.matrix.copy(model.root.matrixWorld);
  if(mode==='explain'&&playing){demoAngle+=Math.min(dt,.1)*speedDegrees*Math.PI/180;steamClock+=Math.min(dt,.1);}
  const angle=mode==='manual'?angleDegrees*Math.PI/180:mode==='simulation'?(s.crank_angle_rad||0):demoAngle;
  // One monotonic marker clock; phase changes never teleport the crank angle.
  const phase=mode==='simulation'?(s.crank_angle_rad||0)/(2*Math.PI):mode==='manual'?0:demoAngle/(2*Math.PI);
  const states=cylinders.map(c=>cylinderCycle(angle+c.i*K.phaseOffset));for(const wheel of wheels)wheel.rotation.x=angle;
  for(const crank of cranks)crank.rotation.x=-states[crank.userData.doubleActingCrank].angle_rad;
  for(const gear of gears)gear.rotation.x=gear.userData.sign*angle+gear.userData.phase;
  const steamTime=mode==='manual'?angleDegrees/60:mode==='simulation'?(s.time||0):steamClock;
  const steamPresent=mode!=='simulation'||s.flow>1e-9;
  const planes=api.clipPlanes('ENG');root.traverse(o=>{if(o.material)for(const m of [].concat(o.material))m.clippingPlanes=planes;});
  const temperatureColor=value=>new T.Color().setRGB(...temperatureRGB(value,thermal?.min,thermal?.max),T.SRGBColorSpace);
  for(const c of cylinders){const state=states[c.i];
   c.piston.position.set(c.x,250,state.pistonZ_mm);c.linkage.pose(state);c.linkage.group.visible=!fluidOnly;
   for(const o of [c.piston,c.rod,...c.linkage.objects,...c.gates]){o.visible=!fluidOnly;o.material.color.copy(thermal?temperatureColor(s.engine_C):o.explanationBaseColor);}
   const rodLength=K.pistonRod-K.crossheadBridgeZ;c.rod.position.set(c.x,250,state.pistonZ_mm-rodLength/2);c.rod.scale.y=rodLength;
   for(const ch of ['A','B']){const v=c.volumes[ch],value=state[ch],color=value.direction>0?fresh:value.direction<0?spent:closed;
    const chamberColor=thermal?temperatureColor(value.direction>0?thermal.inlet:value.direction<0?thermal.exhaust:null):value.direction<0?'#cddfe9':'#f4f4ee';
    v.fluid.visible=fluidPaths&&steamPresent&&steamRender!=='off';v.fluid.position.set(c.x,250,ch==='A'?K.topFace-value.height_mm/2:K.bottomFace+value.height_mm/2);v.fluid.scale.y=Math.max(.01,value.height_mm);v.fluid.material.color.set(chamberColor);
    v.steam.update(state,steamTime,{visible:fluidPaths,present:steamPresent,render:steamRender,opacity:steamOpacity,color:chamberColor,clippingPlanes:planes});
    v.tag.sprite.visible=labels;v.tag.write((c.i+1)+ch+' · '+({admission:'Впуск',expansion:'Закрыта',exhaust:'Выпуск',release:'Сброс',compression:'Сжатие'}[value.phase]),color);
   }
   for(const gate of c.gates){const v=state[gate.userData.chamber],open=gate.userData.circuit==='inlet'?v.inletOpen:v.exhaustOpen;gate.scale.setScalar(open?1.4:.8);gate.material.color.set(thermal?temperatureColor(s.engine_C):open?(gate.userData.circuit==='inlet'?fresh:spent):closed);gate.userData.open=open;}
  }
  for(const line of lines){const state=line.cylinder===null?null:states[line.cylinder],value=state?.[line.chamber];
   let direction=1,active=true,color=fresh;
   if(line.role==='chamber'){direction=value.direction||1;active=value.direction!==0;color=value.direction>0?fresh:spent;}
   else if(line.role==='admission')active=value.inletOpen;
   else if(line.role==='vent'){active=value.exhaustOpen;color=spent;}
   else if(line.role==='exhaust'){active=state.A.exhaustOpen||state.B.exhaustOpen;color=spent;}
   else if(line.role==='steam'&&state)active=state.A.inletOpen||state.B.inletOpen;
   else if(line.role==='steam')active=states[1].A.inletOpen||states[1].B.inletOpen;
   if(mode==='simulation'&&!(s.flow>0))active=false;
   if(thermal)color=temperatureColor(line.role==='exhaust'||line.role==='vent'||line.role==='chamber'&&value.direction<0?thermal.exhaust:line.role==='chamber'&&!value.direction?null:thermal.inlet);
   line.fluid.visible=fluidPaths;line.fluid.material.color.set(thermal?color:line.role==='chamber'&&!value.direction?closed:color);
   line.arrows.update({camera:api.camera,radius:line.radius,phase,visible:arrows&&active,clippingPlanes:planes,direction,color});
  }
  lastState={mode,angle_deg:states[0].angle_deg,cylinders:states,steam:{render:steamRender,time:steamTime,present:steamPresent,clouds:cylinders.flatMap(c=>Object.entries(c.volumes).map(([ch,v])=>({cylinder:c.i,chamber:ch,visible:v.steam.mesh.visible,count:v.steam.state.count,bounds:v.steam.state.bounds})))},lines:lines.map(l=>({id:l.id,role:l.role,cylinder:l.cylinder,chamber:l.chamber,active:l.arrows.group.visible,direction:l.arrows.markers[0]?.marker.userData.direction,fraction:l.arrows.markers[0]?.marker.userData.routeFraction}))};
 }};
}
