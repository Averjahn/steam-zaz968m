// Geometric study: seven independent slider-cranks geared to one output.
// No rated engine, gear strength, pressure-vessel design or measured efficiency.
export const radialGeometry=Object.freeze({count:7,bore:100,stroke:120,rod:24,
 crank:60,link:190,pistonRod:180,pistonThickness:20,clearance:2,
 module:5,centralTeeth:56,localTeeth:28,axisRadius:210,axisZ:45,
 shellRadius:60,innerHead:508,outerHead:652,valveRadius:710,
 inletRadius:470,inletZ:180,returnRadius:445,returnZ:140,reserve:[600,500,500]});
const TAU=2*Math.PI;
export const normalize=a=>((a%TAU)+TAU)%TAU;
export function displacement(count=7,{bore=100,stroke=120,rod=24,cutoff=.3,rpm=300,density=4.299140178878613,dh=2691790.8626737575}={}){
 if(!Number.isInteger(count)||count<1||![bore,stroke,rod,cutoff,rpm,density,dh].every(Number.isFinite)||bore<=0||stroke<=0||rod<0||rod>=bore||cutoff<0||cutoff>1||rpm<0||density<=0||dh<=0)throw new RangeError('Invalid cylinder geometry or operating estimate');
 const A=Math.PI*(bore/1000)**2/4,B=Math.PI*((bore/1000)**2-(rod/1000)**2)/4;
 const swept=count*A*stroke/1000,doubleSwept=count*(A+B)*stroke/1000,admitted=doubleSwept*cutoff;
 const massFlow=admitted*rpm/60*density;
 return {count,A_m2:A,B_m2:B,one_L:A*stroke,swept_L:swept*1000,double_L:doubleSwept*1000,
 admitted_L:admitted*1000,mass_kg_h:massFlow*3600,heat_kW:massFlow*dh/1000,
 crank_rpm:rpm,output_rpm:rpm/2,double_L_per_output_turn:doubleSwept*2000};
}
export function gearPolygon(teeth){
 const m=radialGeometry.module,r=m*teeth/2,alpha=20*Math.PI/180,base=r*Math.cos(alpha),tip=r+m,root=r-1.25*m,pitch=TAU/teeth,inv=Math.tan(alpha)-alpha;
 const half=R=>{const t=Math.sqrt(Math.max(0,(R/base)**2-1));return Math.PI/(2*teeth)+inv-(t-Math.atan(t))-.002;},points=[];
 const add=(R,a)=>points.push([R*Math.cos(a),R*Math.sin(a)]);
 for(let i=0;i<teeth;i++){const a=i*pitch;add(root,a-half(base));for(let j=0;j<=6;j++){const R=base+(tip-base)*j/6;add(R,a-half(R));}for(let j=1;j<=3;j++)add(tip,a-half(tip)+2*half(tip)*j/3);for(let j=5;j>=0;j--){const R=base+(tip-base)*j/6;add(R,a+half(R));}add(root,a+half(base));for(let j=1;j<=3;j++)add(root,a+half(base)+(pitch-2*half(base))*j/3);}
 return points;
}
export function radialPose(index,outputAngle,cutoff=.3){
 const K=radialGeometry;if(!Number.isInteger(index)||index<0||index>=K.count||!Number.isFinite(outputAngle)||!Number.isFinite(cutoff)||cutoff<0||cutoff>1)throw new RangeError('Invalid phase');
 const alpha=Math.PI/2+index*TAU/K.count,phase=normalize(index*TAU/K.count-2*outputAngle),u=[Math.cos(alpha),Math.sin(alpha)],v=[-u[1],u[0]],axis=u.map(x=>x*K.axisRadius);
 const c=Math.cos(phase),s=Math.sin(phase),q=K.crank*c+Math.sqrt(K.link**2-K.crank**2*s*s),pistonRadius=K.axisRadius+q+K.pistonRod;
 const at=(radius,z=K.axisZ)=>[u[0]*radius,u[1]*radius,z];
 const pin=[axis[0]+K.crank*(u[0]*c+v[0]*s),axis[1]+K.crank*(u[1]*c+v[1]*s),K.axisZ];
 const fraction=(K.link+K.crank-q)/K.stroke;
 function chamber(expanding,f,area){const release=f>.985,phase=expanding?(release?'release':f<cutoff?'admission':'expansion'):'exhaust';return {phase,inlet:phase==='admission',exhaust:phase==='exhaust'||phase==='release',volume_cm3:area*(K.clearance+f*K.stroke)/1000};}
 const AA=Math.PI*K.bore**2/4,AB=Math.PI*(K.bore**2-K.rod**2)/4;
 // Output turns positive; local crank phase decreases. A expands when sin(phase)<0.
 const expanding=Math.sin(phase)<=0;
 return {index,alpha,phase,pin,axis:[...axis,0],crosshead:at(K.axisRadius+q),piston:at(pistonRadius),pistonRadius,
 gearAngle:3*alpha+Math.PI-Math.PI/K.localTeeth-2*outputAngle,
 pinAngle:alpha+phase,A:chamber(expanding,fraction,AA),B:chamber(!expanding,1-fraction,AB)};
}
