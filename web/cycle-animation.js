import * as T from 'three';
import {doubleActingView} from './double-acting-view.js';
import {temperatureRGB} from './thermal-model.js';
const material=(color,opacity=1)=>new T.MeshBasicMaterial({color,transparent:opacity<1,opacity,depthTest:false,depthWrite:false});
export function cycleAnimation(api){const group=new T.Group();group.name='Cycle explanation and kinematic animation (view only)';api.scene.add(group);const engine=doubleActingView(api),cond=new T.Group(),boil=new T.Group();group.add(cond,boil);
 const drops=[];for(const y of [55,965])for(let j=0;j<8;j++){const o=new T.Mesh(new T.SphereGeometry(7,10,8),material('#d6d9dc'));cond.add(o);drops.push({o,y,j});}
 const bubbles=[];for(let j=0;j<10;j++){const o=new T.Mesh(new T.SphereGeometry(6,10,8),material('#f2f3ed',.65));boil.add(o);bubbles.push(o);}
 return {hide(){group.visible=false;engine.hide();},engineState:()=>engine.snapshot(),engineExport:()=>engine.exportMechanism(),frame(dt,s,{demo=false,mechanism=true,clock=0,...engineOptions}={}){engine.frame(dt,s,{mechanism,clock,...engineOptions});group.visible=demo||s.flow>0;cond.visible=!!api.models.get('CND')?.root.visible&&(demo||s.flow>0);boil.visible=!!api.models.get('STM')?.root.visible&&(demo||s.boiler.T>99);for(const [g,id]of [[cond,'CND'],[boil,'STM']]){const root=api.models.get(id)?.root;if(root){g.matrixAutoUpdate=false;g.matrix.copy(root.matrix);}g.traverse(o=>{if(o.material)o.material.clippingPlanes=api.clipPlanes(id);});}
 clock=demo?clock:s.time;
 for(const d of drops){const t=(clock*.23+d.j/8)%1;d.o.position.set(430+25*Math.sin(t*8*Math.PI),d.y,220-t*185);if(engineOptions.thermal)d.o.material.color.setRGB(...temperatureRGB(s.condenser.T,engineOptions.thermal.min,engineOptions.thermal.max),T.SRGBColorSpace);else d.o.material.color.set(t<.35?'#d6d9dc':'#a9d4cc');d.o.scale.setScalar(t<.35?1.4:.8);}
 bubbles.forEach((o,j)=>{const t=(clock*.32+j/10)%1;o.position.set(250+70*Math.sin(j*2.4+t*2),250+70*Math.cos(j*2.4+t*2),95+t*450);o.scale.setScalar(.6+t);if(engineOptions.thermal)o.material.color.setRGB(...temperatureRGB(s.boiler.T,engineOptions.thermal.min,engineOptions.thermal.max),T.SRGBColorSpace);else o.material.color.set('#f2f3ed');});
 }};
}
