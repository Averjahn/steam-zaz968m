import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {engineGeometry as K,cylinderCycle} from './web/double-acting-cycle.js';
import {createChamberCloudState} from './web/steam-cloud-model.js';
const checks=[],test=(name,pass)=>{assert.ok(pass,name);checks.push({name,pass:true});};
let confined=true,finite=true,rodClear=true,minHeight=Infinity;
for(let cylinder=0;cylinder<2;cylinder++)for(const chamber of ['A','B']){
 const cloud=createChamberCloudState(cylinder,chamber);
 for(let degrees=0;degrees<360;degrees+=2){const cycle=cylinderCycle(degrees*Math.PI/180+cylinder*K.phaseOffset);cloud.update(cycle,degrees/7);const b=cloud.bounds;minHeight=Math.min(minHeight,b.high-b.low);
  for(let i=0;i<cloud.count;i++){const [x,y,z]=cloud.centers.slice(i*3,i*3+3),r=Math.hypot(x-K.cylinderX[cylinder],y-K.cylinderY);confined&&=r<=K.bore/2&&z>=b.low-1e-4&&z<=b.high+1e-4;rodClear&&=chamber==='A'||r>=K.rodDiameter/2;finite&&=[x,y,z,cloud.sizes[i],cloud.alpha[i]].every(Number.isFinite);}
 }
}
test('All tracer centers remain inside four moving chambers over a full turn',confined);
test('Rod-side particles never intersect the piston rod',rodClear);
test('All particle coordinates, sizes and opacities remain finite',finite);
test('Minimum chamber height respects the original clearance',minHeight>=K.clearance-1e-8);
const cycle=cylinderCycle(20*Math.PI/180),a=createChamberCloudState(0,'A'),b=createChamberCloudState(0,'A');
a.update(cycle,2);b.update(cycle,2);test('Identical angle and time reproduce the same cloud',Buffer.from(a.centers.buffer).equals(Buffer.from(b.centers.buffer)));
const before=a.centers.slice();a.update(cycle,2);test('A paused clock freezes every particle',before.every((v,i)=>v===a.centers[i]));
a.update(cycle,2.01);test('Playback moves the particles',before.some((v,i)=>v!==a.centers[i]));
test('Admission travels away from the upper head',a.centers[2]<before[2]);
const exhaust=cylinderCycle(200*Math.PI/180);a.update(exhaust,2);const release=a.centers.slice();a.update(exhaust,2.01);test('Exhaust reverses towards the same upper head',a.centers[2]>release[2]);
a.update(cycle,3,false);test('A cold simulation can clear all cloud opacity',a.alpha.every(v=>v===0));
test('Default quality uses a bounded 384-puff budget',createChamberCloudState(0,'A').count*4===384);
const result={status:'passed',scope:'Deterministic visual tracers and chamber confinement, not CFD, molecular dynamics or cylinder thermodynamics',checks,source_sha256:Object.fromEntries(['web/steam-cloud-model.js','web/steam-cloud.js','web/double-acting-view.js','web/assembly-systems.js','web/assembly.html','verify_steam_cloud.mjs'].map(n=>[n,createHash('sha256').update(fs.readFileSync(n)).digest('hex')]))};
fs.writeFileSync('steam-cloud-checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length}));
