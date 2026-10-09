// Concept geometry only. Bearing fits, gear strength and lubrication are not rated.
import {engineGeometry as K,cylinderCycle} from './double-acting-cycle.js';
export const crankLayout=Object.freeze({journalRadius:18,pinRadius:10,pinHalfWidth:14,
 cheekInner:14,cheekOuter:26,cheekRadius:20,rodHalfWidth:12,bigEyeOuter:22,bigEyeInner:11,
 smallEyeOuter:13,smallEyeInner:6.5,guideOffsetX:36,guideWidthX:8,shoeOuterX:31.5,
 guideMinZ:130,guideMaxZ:283,gearX:105,gearWidth:12,module:2,teeth:28,pressureAngle:20*Math.PI/180,
 backlashAngle:.003,journalIntervals:[[85,174],[226,389],[441,550]]});
export function mechanismPose(cylinder,angle){
 const cycle=cylinderCycle(angle+cylinder*K.phaseOffset),x=K.cylinderX[cylinder],a=cycle.angle_rad;
 return {cycle,pin:[x,K.cylinderY+K.crankRadius*Math.sin(a),K.crankZ+K.crankRadius*Math.cos(a)],crosshead:[x,K.cylinderY,cycle.pistonZ_mm-K.pistonRod],crankRotation:-a,outputRotation:angle};
}
// Polygonal approximation of standard involute flanks; root transitions are simplified.
export function gearOutline(){
 const {module:m,teeth:z,pressureAngle:alpha,backlashAngle}=crankLayout,r=m*z/2,base=r*Math.cos(alpha),tip=r+m,root=r-1.25*m,invAlpha=Math.tan(alpha)-alpha,pitch=2*Math.PI/z;
 const halfAt=radius=>{const t=Math.sqrt(Math.max(0,(radius/base)**2-1));return Math.PI/(2*z)+invAlpha-(t-Math.atan(t))-backlashAngle;};
 const p=[],point=(radius,angle)=>p.push([radius*Math.cos(angle),radius*Math.sin(angle)]);
 for(let tooth=0;tooth<z;tooth++){
  const center=tooth*pitch;point(root,center-halfAt(base));
  for(let i=0;i<=7;i++){const radius=base+(tip-base)*i/7;point(radius,center-halfAt(radius));}
  for(let i=1;i<=3;i++)point(tip,center-halfAt(tip)+2*halfAt(tip)*i/3);
  for(let i=6;i>=0;i--){const radius=base+(tip-base)*i/7;point(radius,center+halfAt(radius));}
  point(root,center+halfAt(base));
  for(let i=1;i<=3;i++)point(root,center+halfAt(base)+(pitch-2*halfAt(base))*i/3);
 }
 return p;
}
