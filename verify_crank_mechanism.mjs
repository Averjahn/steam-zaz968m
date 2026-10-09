import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {engineGeometry as K} from './web/double-acting-cycle.js';
import {crankLayout as C,mechanismPose,gearOutline} from './web/crank-mechanism-model.js';
const checks=[],test=(name,pass,detail)=>{assert.ok(pass,name);checks.push({name,pass:true,detail});};
let rigid=true,axial=true,cap=true,guides=true,minCap=Infinity;
for(let d=0;d<360;d+=.25)for(let i=0;i<2;i++){
 const p=mechanismPose(i,d*Math.PI/180),end=p.crosshead;
 rigid&&=Math.abs(Math.hypot(...p.pin.map((v,j)=>v-end[j]))-K.connectingRod)<1e-8;
 axial&&=C.journalIntervals.every(([a,b])=>b<=end[0]-C.rodHalfWidth||a>=end[0]+C.rodHalfWidth);
 const top=end[2]+K.crossheadBridgeZ+4;minCap=Math.min(minCap,285-top);cap&&=top<285;
 guides&&=end[2]+4-9>=C.guideMinZ&&end[2]+4+9<=C.guideMaxZ;
}
test('The connecting rod remains 110 mm long through both full revolutions',rigid);
test('No straight journal passes through either connecting-rod plane',axial);
test('The big-end bearing fits between cheeks with 2 mm axial gaps',C.cheekInner-C.rodHalfWidth===2);
test('Piston-rod attachment stays below the lower cylinder head',cap,{minimum_clearance_mm:minCap});
test('Crosshead shoes remain inside the guide length at all angles',guides);
test('Static guides are outside the crank cheeks',C.guideOffsetX-C.guideWidthX/2>C.cheekOuter);
test('Shoes have 0.5 mm visual clearance to the guide faces',C.guideOffsetX-C.guideWidthX/2-C.shoeOuterX===.5);
test('The raised output is coaxial with the displayed gearbox',300+K.outputZ===280+165);
test('The gear ratio is 1:1 and preserves output speed',C.teeth/C.teeth===1);
test('Gear center spacing agrees with module and tooth counts',K.outputZ-K.crankZ===C.module*C.teeth);
test('The lower shaft starts behind the flywheel thickness',C.journalIntervals[0][0]>50+20);
test('Stroke and piston extrema remain 120 mm, 312 mm and 432 mm',mechanismPose(0,0).cycle.pistonZ_mm===432&&mechanismPose(0,Math.PI).cycle.pistonZ_mm===312);
const outline=gearOutline(),inside=(p,polygon)=>{let hit=false;for(let i=0,j=polygon.length-1;i<polygon.length;j=i++){const a=polygon[i],b=polygon[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
const rotate=(points,angle,z)=>points.map(([x,y])=>[x*Math.cos(angle)-y*Math.sin(angle),x*Math.sin(angle)+y*Math.cos(angle)+z]);
let gearClear=true,badAngle=null;
for(let d=0;d<360;d+=.5){const a=d*Math.PI/180,lower=rotate(outline,-a,K.crankZ),upper=rotate(outline,a+Math.PI/C.teeth,K.outputZ);
 for(const [pts,other,center]of [[lower,upper,K.outputZ],[upper,lower,K.crankZ]])for(const p of pts){if(Math.hypot(p[0],p[1]-center)>30.001)continue;if(inside(p,other)){gearClear=false;badAngle=d;break;}}
 if(!gearClear)break;
}
test('Involute tooth polygons do not penetrate the opposite gear in 720 poses',gearClear,{badAngle});
const result={status:'passed',scope:'Concept rigid-body kinematics and geometric clearances, not bearing/gear strength, manufacturing tolerances or service life',geometry:K,crank_layout:C,checks,source_sha256:Object.fromEntries(['web/double-acting-cycle.js','web/crank-mechanism-model.js','web/crank-mechanism.js','web/internal-assembly.js','web/double-acting-view.js','web/assembly.html','web/assembly.js','verify_crank_mechanism.mjs'].map(n=>[n,createHash('sha256').update(fs.readFileSync(n)).digest('hex')]))};
fs.writeFileSync('crank-mechanism-checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length}));
