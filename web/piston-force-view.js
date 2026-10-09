import * as T from 'three';
import {engineGeometry as K} from './double-acting-cycle.js';
import {pistonForces} from './piston-force-model.js';
export const forceColors={A:'#ffb44b',B:'#60cfff',gravity:'#ced4df',friction:'#ff87aa',rod:'#bca0ff',guide:'#ffeb72',net:'#6ee3ab'};
const fmt=n=>Number(n).toLocaleString('ru-RU',{maximumFractionDigits:0});
export function pistonForceView(parent){
 const root=new T.Group();root.name='Силы на поршне и крейцкопфе · расчётная схема';root.userData.viewOnly=true;parent.add(root);
 const items=[];
 for(const [i,x]of K.cylinderX.entries())for(const kind of Object.keys(forceColors)){
  const color=forceColors[kind],arrow=new T.ArrowHelper(new T.Vector3(0,0,1),new T.Vector3(),1,color,1,1);arrow.name=`Сила ${kind} · цилиндр ${i+1}`;
  for(const m of [arrow.line.material,arrow.cone.material]){m.depthTest=false;m.depthWrite=false;}
  arrow.line.renderOrder=940;arrow.cone.renderOrder=940;root.add(arrow);
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=80;
  const texture=new T.CanvasTexture(canvas),sprite=new T.Sprite(new T.SpriteMaterial({map:texture,depthTest:false,depthWrite:false}));sprite.scale.set(92,14,1);sprite.renderOrder=941;root.add(sprite);
  items.push({i,x,kind,arrow,sprite,canvas,texture,previous:''});
 }
 let snapshot=null;
 return {root,snapshot:()=>snapshot,update(angle,{visible=true,labels=true,layer='pressure',scale_N=10000,...inputs}={},clippingPlanes=[],camera=null,viewportHeight=800){
  const values=K.cylinderX.map((_,i)=>pistonForces(angle+i*K.phaseOffset,inputs));root.visible=visible;
  for(const item of items){const {i,x,kind,arrow,sprite}=item,v=values[i],f=v.forces,z=v.cycle.pistonZ_mm,cross=z-K.pistonRod;
   const map={A:[0,0,f.faceA_N],B:[0,0,f.faceB_N],gravity:[0,0,f.gravity_N],friction:[0,0,f.friction_N],rod:[0,f.rod_Y_N,f.rod_Z_N],guide:[0,f.guide_Y_N,0],net:[0,0,f.net_Z_N]},vector=new T.Vector3(...map[kind]),force=vector.length(),length=force*100/scale_N;
   const shown=visible&&(layer==='all'&&kind!=='net'||layer==='pressure'&&['A','B'].includes(kind)||layer==='net'&&kind==='net')&&force>1e-6;
   arrow.visible=shown;sprite.visible=shown&&labels;
   const origin={A:[x-16,205,z+K.pistonThickness/2],B:[x+16,205,z-K.pistonThickness/2],gravity:[x+38,215,z],friction:[x-38,215,z],rod:[x,215,cross],guide:[x,250,cross],net:[x+72,215,z]}[kind];
   arrow.position.fromArray(origin);
   if(force>1e-6){vector.normalize();arrow.setDirection(vector);arrow.setLength(length,Math.min(8,length*.28),Math.min(6,length*.20));}
   arrow.userData={cylinder:i,kind,force_N:force,vector_N:map[kind],length_mm:length,scale_N,viewOnly:true};
   for(const m of [arrow.line.material,arrow.cone.material])m.clippingPlanes=clippingPlanes;
   sprite.material.clippingPlanes=clippingPlanes;
   const names={A:'A · p−p₀',B:'B · p−p₀',gravity:'mg',friction:'Трение',rod:'Шатун',guide:'Направляющие',net:'ΣF = ma'};
   const text=names[kind]+' · '+fmt(force)+' Н';
   if(text!==item.previous){item.previous=text;const ctx=item.canvas.getContext('2d');ctx.clearRect(0,0,512,80);ctx.fillStyle='#09131eef';ctx.fillRect(0,0,512,80);ctx.fillStyle=forceColors[kind];ctx.font='bold 34px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,40);item.texture.needsUpdate=true;}
   sprite.position.copy(arrow.position).addScaledVector(vector,length*.55);sprite.position.x+=kind==='A'?-42:kind==='B'?42:kind==='friction'?-46:46;
   if(camera&&sprite.visible){
    const world=sprite.getWorldPosition(new T.Vector3()).applyMatrix4(camera.matrixWorldInverse),scale=root.getWorldScale(new T.Vector3());
    const unitsPerPixel=2*Math.abs(world.z)*Math.tan(camera.fov*Math.PI/360)/Math.max(1,viewportHeight);
    sprite.scale.set(174*unitsPerPixel/scale.x,27*unitsPerPixel/scale.y,1);
   }
  }
  snapshot={visible,layer,scale_N,values,arrows:items.map(({arrow})=>({visible:arrow.visible,...arrow.userData,origin_mm:arrow.position.toArray()}))};return snapshot;
 }};
}
