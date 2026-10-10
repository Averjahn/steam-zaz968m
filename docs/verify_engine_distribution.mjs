import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sharedPose} from './web/shared-radial-model.js';
import {distributionState,tubeVolumeCm3} from './web/engine-distribution-model.js';
const checks=[],test=(name,f)=>{f();checks.push({name,passed:true});};
test('Every cylinder completes admission, expansion and exhaust without a P–T path',()=>{
 for(const D of [40,60,100])for(let i=0;i<7;i++){
  const seen={A:new Set(),B:new Set()};
  for(let j=0;j<3600;j++){
   const p=sharedPose(i,j*Math.PI/1800,40,.3,{bore_mm:D}),v=distributionState(p);assert.ok(v.valid);
   for(const ch of ['A','B']){seen[ch].add(p[ch].phase);assert.equal(v.valves.filter(e=>e.chamber===ch&&e.open).length,Number(p[ch].inlet)+Number(p[ch].exhaust));}
   if(p.A.inlet)assert.ok(p.B.exhaust&&!p.B.inlet);if(p.B.inlet)assert.ok(p.A.exhaust&&!p.A.inlet);
  }
  for(const ch of ['A','B'])for(const phase of ['admission','expansion','exhaust','release'])assert.ok(seen[ch].has(phase));
 }
});
test('Fault injection detects simultaneous supply and exhaust, independently on either chamber',()=>{
 for(const ch of ['A','B']){const p={A:{inlet:false,exhaust:false},B:{inlet:false,exhaust:false}};p[ch]={inlet:true,exhaust:true};const v=distributionState(p);assert.ok(v.shortCircuit&&!v.valid&&v.overlap.includes(ch));}
});
test('Closing all four valves isolates both chambers, supply and exhaust',()=>{
 const v=distributionState({A:{inlet:false,exhaust:false},B:{inlet:false,exhaust:false}});assert.ok(v.valid&&v.valves.every(e=>!e.open));
});
test('Tube volume matches a 1 metre ID8 cylinder and rejects invalid dimensions',()=>{
 assert.ok(Math.abs(tubeVolumeCm3(1000,8)-16*Math.PI)<1e-12);assert.throws(()=>tubeVolumeCm3(-1,8));
});
test('External connection volume changes clearance, not displacement or phase timing',()=>{
 for(let i=0;i<7;i++)for(let j=0;j<360;j++){
  const p=sharedPose(i,j*Math.PI/180),q=sharedPose(i,j*Math.PI/180,40,.3,{connection_volumes_cm3:{A:9,B:23}});
  for(const [ch,extra]of [['A',9],['B',23]]){assert.equal(p[ch].phase,q[ch].phase);assert.ok(Math.abs(q[ch].volume_cm3-p[ch].volume_cm3-extra)<1e-10);assert.equal(q[ch].cylinder_volume_cm3,p[ch].volume_cm3);}
 }
});
fs.writeFileSync('engine-distribution-checks.json',JSON.stringify({status:'passed',sampled_states:75600,scope:'Ideal commanded valve states; not actuator dynamics or a pressure-flow solution',checks},null,2)+'\n');
console.log(JSON.stringify({status:'passed',checks:checks.length,sampled_states:75600}));
