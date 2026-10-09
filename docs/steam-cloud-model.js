// Deterministic visual tracers, in millimetres. Not molecular dynamics or CFD.
import {engineGeometry as K} from './double-acting-cycle.js?v=6b548e33f0f2';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),fract=x=>x-Math.floor(x);
export function createChamberCloudState(cylinder,chamber,count=96){
 let seed=968+(cylinder+1)*7919+(chamber==='A'?31:67);
 const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const samples=Array.from({length:count},()=>[random(),random(),random(),random()]);
 const centers=new Float32Array(count*3),sizes=new Float32Array(count),alpha=new Float32Array(count),seeds=new Float32Array(count);
 samples.forEach((s,i)=>seeds[i]=s[3]*100);
 let bounds={low:0,high:0,radius:K.bore/2,rodRadius:chamber==='B'?K.rodDiameter/2:0};
 return {count,centers,sizes,alpha,seeds,get bounds(){return bounds;},update(cycle,time,present=true){
  const state=cycle[chamber],low=chamber==='A'?cycle.pistonZ_mm+K.pistonThickness/2:K.bottomFace,high=chamber==='A'?K.topFace:cycle.pistonZ_mm-K.pistonThickness/2,height=high-low;
  bounds={low,high,radius:K.bore/2,rodRadius:chamber==='B'?K.rodDiameter/2:0};
  for(let i=0;i<count;i++){
   const [a,b,c,d]=samples[i],moving=state.direction!==0;
   const q=moving?fract(a+time*(.31+.12*d)):clamp(a+.045*Math.sin(time*.9+d*9),.005,.995);
   const angle=b*2*Math.PI+time*(.34+.18*d),r=Math.sqrt(c)*47;
   let x=r*Math.cos(angle),y=r*Math.sin(angle);
   if(state.direction>0){const mix=clamp(q*2.4,0,1);x=(cylinder===0?-35:35)*(1-mix)+x*mix;y*=mix;}
   const radial=Math.hypot(x,y),minimum=bounds.rodRadius+1.5;
   if(bounds.rodRadius&&radial<minimum){const angle=radial>1e-6?Math.atan2(y,x):b*2*Math.PI;x=minimum*Math.cos(angle);y=minimum*Math.sin(angle);}
   const fromHead=state.direction>=0,z=chamber==='A'?(fromHead?high-q*height:low+q*height):(fromHead?low+q*height:high-q*height);
   centers.set([K.cylinderX[cylinder]+x,K.cylinderY+y,clamp(z,low+.001,high-.001)],i*3);
   sizes[i]=20+24*d;
   alpha[i]=present?({admission:.14,expansion:.11,release:.09,exhaust:.085,compression:.12}[state.phase]||.1):0;
  }
  return this;
 }};
}
