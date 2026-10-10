// One master rod plus six articulated rods, all driving ONE crankpin.
// Pin angles/link lengths numerically fitted so each crosshead spans 127.5–172.5
// mm for a 22.5 mm throw. These are kinematic dimensions, not strength sizing.
export const sharedLinkages=Object.freeze([
 {beta:Math.PI/2,length:150},
 {beta:2.468158215516697,length:126.19710828556119},
 {beta:3.3628009239661716,length:126.3085620385239},
 {beta:4.260091509051952,length:126.061674101906},
 {beta:5.164686451715456,length:126.06167410210465},
 {beta:6.061977036803103,length:126.30856203935053},
 {beta:6.9566197452526835,length:126.19710828557872}
].map(Object.freeze));
const TAU=2*Math.PI,normalize=a=>((a%TAU)+TAU)%TAU;
export function sharedPose(index,angle,bore=40,cutoff=.3,cylinder={}){
 if(!Number.isInteger(index)||index<0||index>6||!Number.isFinite(angle)||bore<32||bore>64)throw RangeError('Invalid shared-crank geometry');
 const s=bore/40,r=22.5*s,L=150*s,R=24*s,z=61,alpha=Math.PI/2+index*TAU/7,u=[Math.cos(alpha),Math.sin(alpha)],v=[-u[1],u[0]];
 const C=[r*Math.cos(angle),r*Math.sin(angle)],dC=[-r*Math.sin(angle),r*Math.cos(angle)],h=Math.sqrt(L*L-C[0]*C[0]);
 const tilt=Math.atan2(h,-C[0])-Math.PI/2,dTilt=dC[0]/h;
 let pin=C,q,dq;
 if(index===0){q=C[1]+h;dq=dC[1]-C[0]*dC[0]/h;}
 else{
  const k=sharedLinkages[index],beta=k.beta+tilt,length=k.length*s;
  pin=[C[0]+R*Math.cos(beta),C[1]+R*Math.sin(beta)];
  const dp=[dC[0]-R*Math.sin(beta)*dTilt,dC[1]+R*Math.cos(beta)*dTilt];
  const projection=u[0]*pin[0]+u[1]*pin[1],cross=v[0]*pin[0]+v[1]*pin[1],root=Math.sqrt(length*length-cross*cross);
  q=projection+root;dq=u[0]*dp[0]+u[1]*dp[1]-cross*(v[0]*dp[0]+v[1]*dp[1])/root;
 }
 const stroke=45*s,pistonRadius=q+67.5*s,f=Math.max(0,Math.min(1,(172.5*s-q)/stroke));
 const D=cylinder.bore_mm??bore,rod=cylinder.rod_mm??9.6*s;if(!Number.isFinite(D)||D<32||D>100||!Number.isFinite(rod)||rod<=0||rod>=D)throw RangeError('Invalid cylinder section');
 const A=Math.PI*D*D/4,B=Math.PI*(D*D-rod*rod)/4;
 const chamber=(expanding,fraction,volume)=>{const phase=!expanding?'exhaust':fraction>.985?'release':fraction<cutoff?'admission':'expansion';return{phase,inlet:phase==='admission',exhaust:phase==='exhaust'||phase==='release',volume_cm3:volume};};
 const at=radius=>[u[0]*radius,u[1]*radius,z];
 return{index,alpha,phase:normalize(alpha-angle),pin:[...pin,z],crankpin:[...C,z],axis:[0,0,0],crosshead:at(q),piston:at(pistonRadius),pistonRadius,crossheadRadius:q,derivative_mm_rad:dq,masterTilt:tilt,
  A:chamber(dq<0,f,A*(244.5*s-pistonRadius-3.75*s)/1000),B:chamber(dq>=0,1-f,B*(pistonRadius-3.75*s-190.5*s)/1000)};
}
