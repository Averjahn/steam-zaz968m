import assert from 'node:assert/strict';
import fs from 'node:fs';
import {engineGeometry as k,cylinderCycle} from './web/double-acting-cycle.js';
const checks=[];const test=(name,condition)=>{assert.ok(condition,name);checks.push({name,pass:true});};
let min=Infinity,max=-Infinity,valid=true,volumeValid=true,rodRigid=true,roles=new Set();
for(let d=0;d<360;d+=.2){const c=cylinderCycle(d*Math.PI/180);min=Math.min(min,c.pistonZ_mm);max=Math.max(max,c.pistonZ_mm);
 for(const ch of [c.A,c.B]){valid&&=!(ch.inletOpen&&ch.exhaustOpen);volumeValid&&=ch.height_mm>=k.clearance-1e-8&&ch.volume_cm3>0;roles.add(ch.phase);}
 const pinY=250+k.crankRadius*Math.sin(c.angle_rad),pinZ=k.crankZ+k.crankRadius*Math.cos(c.angle_rad),crosshead=c.pistonZ_mm-k.pistonRod;
 rodRigid&&=Math.abs(Math.hypot(pinY-250,pinZ-crosshead)-k.connectingRod)<1e-8;
}
test('A chamber cannot admit and exhaust simultaneously',valid);
test('Piston completes a 120 mm stroke',Math.abs(max-min-120)<1e-7);
test('Piston stays within the head clearances',volumeValid);
test('Connecting rod has constant length through the whole revolution',rodRigid);
test('All five explanatory valve phases occur',roles.size===5);
const down=cylinderCycle(20*Math.PI/180),up=cylinderCycle(200*Math.PI/180);
test('Downstroke admits above the piston and exhausts below',down.A.inletOpen&&down.B.exhaustOpen);
test('Upstroke admits below the piston and exhausts above',up.B.inletOpen&&up.A.exhaustOpen);
test('Same head line reverses between the two strokes',down.A.direction===1&&up.A.direction===-1);
test('Cutoff closes admission while expansion continues',cylinderCycle(100*Math.PI/180).A.phase==='expansion'&&cylinderCycle(100*Math.PI/180).A.direction===0);
test('Rod-side volume accounts for the 24 mm rod',Math.abs(down.B.volume_cm3/down.B.height_mm/(down.A.volume_cm3/down.A.height_mm)-(1-24**2/100**2))<1e-10);
test('Full turns preserve the cycle state',Math.abs(cylinderCycle(-340*Math.PI/180).pistonZ_mm-down.pistonZ_mm)<1e-7);
const result={status:'passed',scope:'Illustrative rigid-body kinematics and valve sequencing, not measured valve capacity or cylinder thermodynamics',geometry:k,checks};
fs.writeFileSync('double-acting-checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,checks:checks.length}));
