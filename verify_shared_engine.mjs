import assert from 'node:assert/strict';
import fs from 'node:fs';
import {sharedPose,sharedLinkages} from './web/shared-radial-model.js';
const checks=[],test=(name,ok)=>{assert.ok(ok,name);checks.push({name,passed:true});};
let minTorque=Infinity,maxLengthError=0,maxDerivativeError=0;
const minima=Array(7).fill(Infinity),maxima=Array(7).fill(-Infinity),duty=Array.from({length:7},()=>[0,0]);
for(let j=0;j<14400;j++){
 const angle=j*2*Math.PI/14400;let torque=0;
 for(let i=0;i<7;i++){
  const p=sharedPose(i,angle),q=sharedPose(i,angle+1e-5),b=sharedPose(i,angle-1e-5);
  minima[i]=Math.min(minima[i],p.crossheadRadius);maxima[i]=Math.max(maxima[i],p.crossheadRadius);
  maxLengthError=Math.max(maxLengthError,Math.abs(Math.hypot(p.crosshead[0]-p.pin[0],p.crosshead[1]-p.pin[1])-sharedLinkages[i].length));
  maxDerivativeError=Math.max(maxDerivativeError,Math.abs(p.derivative_mm_rad-(q.crossheadRadius-b.crossheadRadius)/2e-5));
  testFinite(p);
  if(p.A.inlet)duty[i][0]++;if(p.B.inlet)duty[i][1]++;
  const AA=Math.PI*.04**2/4,AB=Math.PI*(.04**2-.0096**2)/4;
  const pressure=(ch,area)=>ch.inlet?1e6:ch.phase==='expansion'?Math.max(1.2e5,1e6*((.00075+.3*.045)*area/(ch.volume_cm3/1e6))**1.15):1.2e5;
  // Virtual work: an inward A pressure or outward B pressure produces torque.
  const radialForce=(pressure(p.B,AB)-1.2e5)*AB-(pressure(p.A,AA)-1.2e5)*AA;
  torque+=radialForce*p.derivative_mm_rad/1000;
 }
 minTorque=Math.min(minTorque,torque);
}
function testFinite(p){assert.ok(Object.values(p.A).every(v=>typeof v!=='number'||Number.isFinite(v)));assert.ok(p.A.volume_cm3>0&&p.B.volume_cm3>0);assert.ok(!(p.A.inlet&&p.B.inlet));assert.ok(!(p.A.inlet&&p.A.exhaust)&&!(p.B.inlet&&p.B.exhaust));}
for(let i=0;i<7;i++)test('Cylinder '+(i+1)+' has full 45 mm stroke and the retained piston envelope',Math.abs(minima[i]-127.5)<2e-5&&Math.abs(maxima[i]-172.5)<2e-5);
test('All seven rigid rod lengths remain constant through a turn',maxLengthError<1e-10);
test('Analytical velocities agree with independent finite differences',maxDerivativeError<1e-7);
test('Actual double-acting phasing produces positive combined quasi-static torque',minTorque>0);
test('A whole output turn returns the shared mechanism to its starting pose',sharedLinkages.every((_,i)=>Math.hypot(...sharedPose(i,0).crosshead.map((v,j)=>v-sharedPose(i,2*Math.PI).crosshead[j]))<1e-8));
test('All force paths use the same crankpin centre',sharedLinkages.every((_,i)=>Math.hypot(...sharedPose(i,1).crankpin.map((v,j)=>v-sharedPose(0,1).crankpin[j]))<1e-10));
const result={status:'passed',checks,dimensions:{bore_mm:40,stroke_mm:45,master_length_mm:150,slave_linkages:sharedLinkages.slice(1),articulation_radius_mm:24,crank_radius_mm:22.5,output_ratio:1},minima_mm:minima,maxima_mm:maxima,max_length_error_mm:maxLengthError,max_derivative_error_mm_rad:maxDerivativeError,illustrative_min_torque_Nm:minTorque,torque_assumptions:'10 bar admission, 1.2 bar exhaust, polytropic expansion n=1.15, no inertia/friction/strength; not rated torque',duty:duty.map(x=>x.map(v=>v/14400)),pose_zero:sharedLinkages.map((_,i)=>sharedPose(i,0))};
fs.writeFileSync('shared-engine-kinematics.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length,minTorque,maxLengthError,maxDerivativeError}));
