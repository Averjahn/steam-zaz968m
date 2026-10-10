import * as T from 'three';
import {temperatureRGB} from './thermal-model.js';
// Native assembly geometry is animated in place; no second mechanism is overlaid.
export function fittedRadialView(api){
 let angle=0,time=0,state=null,current=null;
 return {hide(){state=null;},snapshot:()=>state,exportMechanism:()=>null,
 frame(dt,s,o={}){const m=api.models.get('ENG'),e=m?.radialEngine;if(!e){state=null;return;}if(e!==current){current=e;angle=0;time=0;const box=document.getElementById('engineMechanismOnly');box.disabled=!e.mechanismOnly;document.getElementById('engineDriveDescription').textContent=e.config.mechanism==='master-articulated'?'Один главный и шесть прицепных шатунов передают усилие одной общей шатунной шейке. Передача к коленвалу прямая,1:1; угловая пара пока только направляет выход к КПП.':'Архив: семь отдельных кривошипов и зубчатое суммирование,2:1.';}const mode=o.mode||'explain';
 if(mode==='manual')angle=(o.angleDegrees||0)*Math.PI/180;
 else if(mode==='simulation')angle=(s.crank_angle_rad||0)/e.config.outputRatio;
 else if(o.playing!==false)angle=(angle+Math.min(.1,dt)*(o.speedDegrees||60)*Math.PI/180)%(2*Math.PI);
 if(mode!=='explain'||o.playing!==false)time+=Math.min(.1,dt);
 e.mounts.visible=e.contacts.visible=document.getElementById('componentView').value!=='ENG';
 e.mechanismOnly?.(document.getElementById('engineMechanismOnly').checked&&!o.fluidOnly);e.cutaway(o.cutaway!==false||o.fluidOnly);const states=e.update(angle,time,api.camera,o.arrows!==false&&m.root.visible&&(mode!=='simulation'||s.flow>0));
 if(o.thermal)for(let i=0;i<e.cylinders.length;i++)for(const ch of ['A','B']){const p=states[i][ch],value=p.inlet?(o.thermal.inlet??s.boiler.T):p.exhaust?(o.thermal.exhaust??null):null;e.cylinders[i]['fluid'+ch].material.color.setRGB(...temperatureRGB(value,o.thermal.min,o.thermal.max),T.SRGBColorSpace);}
 e.root.traverse(n=>{if(n.isMesh&&n.name.startsWith('Пар в камере')){n.visible=(o.fluidPaths!==false||o.fluidOnly)&&o.steamRender!=='off';n.material.opacity=o.steamOpacity??.15;n.material.visible=true;}});
 state={mode,angle_deg:angle*180/Math.PI%360,radial:true,geometry:e.config,forces:null,cylinders:states.map(p=>({...p,angle_deg:p.phase*180/Math.PI%360,A:{...p.A,inletOpen:p.A.inlet,exhaustOpen:p.A.exhaust,direction:p.A.inlet?1:p.A.exhaust?-1:0},B:{...p.B,inletOpen:p.B.inlet,exhaustOpen:p.B.exhaust,direction:p.B.inlet?1:p.B.exhaust?-1:0}}))};
 }};
}
