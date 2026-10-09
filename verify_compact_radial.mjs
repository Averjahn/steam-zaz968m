import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {compactGeometry as K,compactPose,compactDisplacement,compactPipes,pipeSection} from './web/compact-radial-model.js';
const checks=[];
const test=(name,condition)=>{assert.ok(condition,name);checks.push({name,passed:true});};
const near=(a,b,t=1e-8)=>Math.abs(a-b)<t;
const v=compactDisplacement(),fit=JSON.parse(fs.readFileSync('compact-radial-fit.json')),meta=JSON.parse(fs.readFileSync('models/compact-radial-engine.json'));
test('Swept volume independently equals seven circular piston areas times stroke',near(v.swept_L,7*Math.PI*.032**2/4*.036*1000));
test('Double-acting swept volume subtracts seven rod areas',near(v.double_L,7*Math.PI*(2*.032**2-.00768**2)/4*.036*1000));
test('Pitch-circle centres and 2:1 reduction agree',near(K.axisRadius,K.module*(K.centralTeeth+K.localTeeth)/2)&&K.centralTeeth/K.localTeeth===K.outputRatio);
let maxLinkError=0,minA=Infinity,minB=Infinity,strokeError=0;
for(let i=0;i<7;i++){
 let lo=Infinity,hi=-Infinity;
 for(let j=0;j<=1440;j++){
  const p=compactPose(i,Math.PI*j/720);
  maxLinkError=Math.max(maxLinkError,Math.abs(Math.hypot(...p.pin.map((x,k)=>x-p.crosshead[k]))-K.link));
  lo=Math.min(lo,p.pistonRadius);hi=Math.max(hi,p.pistonRadius);
  minA=Math.min(minA,p.A.volume_cm3);minB=Math.min(minB,p.B.volume_cm3);
  assert.ok(!p.A.inlet||!p.A.exhaust);assert.ok(!p.B.inlet||!p.B.exhaust);
 }
 strokeError=Math.max(strokeError,Math.abs(hi-lo-K.stroke));
}
test('All seven slider-cranks preserve 57 mm rod length over a full output revolution',maxLinkError<1e-8);
test('All seven pistons travel 36 mm',strokeError<.001);
test('Both chambers retain the intended 0.6 mm dead clearance',near(minA,v.A_m2*1e6*.6/1000,1e-8)&&near(minB,v.B_m2*1e6*.6/1000,1e-8));
test('Seven crank phases are distinct',new Set(Array.from({length:7},(_,i)=>compactPose(i,0).phase.toFixed(8))).size===7);
test('Previous upstream steam pipe retains its full insulation envelope',near(compactPipes.boundaryIn.envelope_mm,109.2));
assert.throws(()=>pipeSection(12,8));assert.throws(()=>pipeSection(8,12,-1));checks.push({name:'Invalid pipe sections are rejected',passed:true});
test('Actual core mesh fits the 600 × 500 × 500 mm reserve',fit.bounds.inside_reserve&&fit.bounds.size_mm.every((x,i)=>x<=K.reserveMax[i]-K.reserveMin[i]));
test('Core and posts do not intersect body or static suspension meshes',fit.audit.parts.every(p=>!p.body_intersections.length&&!p.stock_intersections.length)&&!fit.audit.summary.unplanned_mesh_intersections.length);
test('Core retains a measured positive body gap',fit.audit.parts.find(p=>p.id==='COMPACT_ENGINE').clearance_mm>=40);
test('Four support-pad surfaces match nine samples each on the supplied floor',fit.contacts.length===4&&fit.contacts.every(p=>p.geometric_contact_confirmed&&p.samples.length===9&&p.max_error_mm<.01&&!p.load_bearing_confirmed));
test('Actual stored engine dimensions match sizing inputs',JSON.parse(fs.readFileSync('engine-sizing.json')).candidates.find(c=>c.id==='compact-seven').size_mm.every((x,i)=>near(x,meta.bounds.core.size_mm[i],.001)));
for(const r of meta.routes){
 assert.ok(r.spec.outside_mm>r.spec.inside_mm&&r.spec.insulation_mm>=0,r.name);
 if(r.points.length>2)assert.ok(r.bend_radius_mm>=1.5*r.spec.outside_mm,r.name+' bend radius');
 assert.ok(r.length_mm>0&&r.points.every(p=>p.length===3&&p.every(Number.isFinite)),r.name);
}
test('Seven cylinders have four independently specified flow routes each',meta.routes.filter(r=>r.index!==null).length===28&&meta.ports.length===7);
for(const p of meta.ports){
 for(const ch of ['A','B']){
  const r=meta.routes.find(r=>r.index===p.cylinder&&r.chamber===ch);
  assert.ok(r.points.at(-1).every((x,i)=>near(x,p[ch].face_mm[i])),'Chamber pipe ends at port face');
  const a=r.points.at(-2),b=r.points.at(-1),d=b.map((x,i)=>x-a[i]),L=Math.hypot(...d);
  assert.ok(near(d.reduce((s,x,i)=>s+x*p[ch].outward[i],0)/L,-1),'Terminal pipe is normal to chamber cover');
  assert.equal(r.spec.inside_mm,p[ch].bore_mm,'Pipe bore matches cover port');
 }
}
checks.push({name:'Fourteen chamber connections have matching bore, endpoint and axial direction',passed:true});
for(const p of meta.ports){
 const alpha=Math.PI/2+p.cylinder*2*Math.PI/7,u=[Math.cos(alpha),Math.sin(alpha)],w=[-u[1],u[0]];
 const rotate=q=>[q[0]*u[0]+q[1]*w[0],q[0]*u[1]+q[1]*w[1],q[2]];
 for(const [role,ch,id,end]of [['inlet',null,'in',1],['outlet',null,'out',0],['chamber','A','A',0],['chamber','B','B',0]]){
  const r=meta.routes.find(r=>r.index===p.cylinder&&r.role===role&&r.chamber===ch),port=p.valve_ports.find(x=>x.id===id),face=rotate(port.anchor_mm),normal=rotate(port.outward);
  const q=end?r.points.at(-1):r.points[0],a=end?r.points.at(-2):r.points[0],b=end?r.points.at(-1):r.points[1],d=b.map((x,i)=>x-a[i]),L=Math.hypot(...d);
  assert.ok(q.every((x,i)=>near(x,face[i])),'Valve pipe endpoint');assert.ok(near(d.reduce((s,x,i)=>s+x*normal[i],0)/L,end?-1:1),'Valve pipe axial direction');assert.equal(r.spec.inside_mm,port.bore_mm);
 }
}
checks.push({name:'All 28 valve interfaces match bore, face and through-hole axis',passed:true});

const assets=['models/compact-radial-engine.glb','models/compact-radial-in-body.glb'];
for(const file of assets){const b=fs.readFileSync(file);assert.equal(b.toString('ascii',0,4),'glTF');assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);assert.ok(b.length<100e6);}
checks.push({name:'Both exports are complete glTF 2 binary files below 100 MB',passed:true});
for(const [file,sha]of Object.entries(fit.provenance.source_sha256))assert.equal(createHash('sha256').update(fs.readFileSync(file)).digest('hex'),sha,file+' audit provenance');
checks.push({name:'Body audit belongs to the current source and reference meshes',passed:true});
const files=['web/compact-radial-model.js','web/compact-radial-geometry.js','web/compact-radial.js','compact-radial-fit.json','models/compact-radial-engine.json',...assets];
fs.writeFileSync('compact-radial-checks.json',JSON.stringify({status:'passed',scope:'Concept geometry, exact slider-crank kinematics, chamber volumes, nominal body/static suspension screening and floor contact; not manufacture, pressure ratings, self-interference, strength or vehicle feasibility',checks,source_sha256:Object.fromEntries(files.map(file=>[file,createHash('sha256').update(fs.readFileSync(file)).digest('hex')]))},null,2)+'\n');
console.log(JSON.stringify({status:'passed',checks:checks.length,volume_L:v.swept_L,double_L:v.double_L,bounds_mm:fit.bounds.size_mm,max_link_error_mm:maxLinkError}));
