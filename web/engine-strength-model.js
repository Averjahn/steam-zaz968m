// Preliminary rigid kinematics and beam/shaft screening. NOT a fatigue or FEA model.
import {sharedPose} from './shared-radial-model.js';
const PI=Math.PI,TAU=2*PI,cross=(a,b)=>a[0]*b[1]-a[1]*b[0],dot=(a,b)=>a[0]*b[0]+a[1]*b[1];
export const strengthDefaults=Object.freeze({stroke_mm:45,rod_mm:9.6,pressure_bar_abs:10,back_bar_abs:1.2,ambient_bar_abs:1,structural_pressure_bar_abs:15,overspeed_rpm:2600,steel_density:7850,E_MPa:210000,yield_MPa:550,allowable_MPa:110,load_factor:1.5,extra_reciprocating_kg:.35,polytropic_n:1.15,cutoff:.3});
export function sectionChecks(F,T,dimensions,k=strengthDefaults){
 const d=dimensions,allow=k.allowable_MPa;
 const shaftM=F*d.shaft_overhang_mm,shaftB=32*shaftM/(PI*d.shaft_mm**3),shaftT=16*T*1000/(PI*d.shaft_mm**3),shaftVM=Math.hypot(shaftB,Math.sqrt(3)*shaftT);
 const pinM=F*d.pin_span_mm/4,pinB=32*pinM/(PI*d.crankpin_mm**3),pinShear=F/(2*PI*d.crankpin_mm**2/4),pinVM=Math.hypot(pinB,Math.sqrt(3)*pinShear);
 return {shaft_bending_MPa:shaftB,shaft_torsion_MPa:shaftT,shaft_vm_MPa:shaftVM,shaft_room_yield_margin:k.yield_MPa/shaftVM,shaft_screen_ok:shaftVM<=allow,
  crankpin_vm_MPa:pinVM,crankpin_room_yield_margin:k.yield_MPa/pinVM,crankpin_screen_ok:pinVM<=allow,crankpin_bearing_MPa:F/(d.crankpin_mm*d.bearing_length_mm),
  shaft_deflection_mm:F*d.shaft_overhang_mm**3/(3*k.E_MPa*PI*d.shaft_mm**4/64),
  topology:'Shaft: equivalent overhung load. Crankpin: proposed double-supported pin; current single cheek is checked separately as cantilever.'};
}
export function smallJointChecks(F,d,t,width,length,k=strengthDefaults){
 const shear=F/(2*PI*d*d/4),bend=32*(F*(t+6)/4)/(PI*d**3),vm=Math.hypot(bend,Math.sqrt(3)*shear),netArea=(width-d-.4)*t;
 const rodStress=netArea>0?2.5*F/netArea:Infinity, I=width*t**3/12,euler=PI**2*k.E_MPa*I/length**2;
 return {pin_vm_MPa:vm,net_section_with_assumed_Kt_MPa:rodStress,bearing_MPa:F/(d*t),euler_load_N:euler,buckling_margin:euler/F,pin_screen_ok:vm<=k.allowable_MPa,net_screen_ok:rodStress<=k.allowable_MPa,buckling_screen_ok:euler/F>=3};
}
// F[i] is the radial force delivered by crosshead i to its linkage.
// Articulated rods are two-force members; the master rod has seven joints.
export function mechanismLoads(poses,F){
 const forces=[],main=poses[0],C=main.crankpin,S=main.crosshead,r=[S[0]-C[0],S[1]-C[1]],u0=[Math.cos(main.alpha),Math.sin(main.alpha)],v0=[-u0[1],u0[0]];
 let moment=0,x=0,y=0;
 for(let i=1;i<7;i++){const p=poses[i],dx=p.crosshead[0]-p.pin[0],dy=p.crosshead[1]-p.pin[1],L=Math.hypot(dx,dy),w=[dx/L,dy/L],u=[Math.cos(p.alpha),Math.sin(p.alpha)],N=F[i]/dot(w,u),f=w.map(q=>q*N);forces[i]=N;x+=f[0];y+=f[1];moment+=cross([p.pin[0]-C[0],p.pin[1]-C[1]],f);}
 const tangent=-(moment+cross(r,u0)*F[0])/cross(r,v0),f0=[F[0]*u0[0]+tangent*v0[0],F[0]*u0[1]+tangent*v0[1]];forces[0]=Math.hypot(...f0);x+=f0[0];y+=f0[1];
 return {reaction_N:Math.hypot(x,y),reaction_xy_N:[-x,-y],torque_Nm:cross(C,[x,y])/1000,joint_max_N:Math.max(...forces.map(Math.abs)),slave_max_N:Math.max(...forces.slice(1).map(Math.abs)),master_tangent_N:tangent,master_joint_N:forces[0],moment_residual_Nmm:moment+cross(r,f0)};
}
export function strengthStudy(bore,rpm,kInput={}){
 const k={...strengthDefaults,...kInput};if(!Number.isFinite(bore)||bore<32||bore>100||!Number.isFinite(rpm)||rpm<=0||rpm>6000)throw RangeError('Invalid strength study');
 const area=PI*bore**2/4,annular=PI*(bore**2-k.rod_mm**2)/4,omega=rpm*TAU/60;
 // Steel piston + piston rod + explicit allowance for crosshead and lumped rod mass.
 const mass=k.steel_density*(area*7.5+PI*k.rod_mm**2/4*67.5)*1e-9+k.extra_reciprocating_kg;
 const peak={reaction_N:0,torque_Nm:0,joint_max_N:0,slave_max_N:0,master_joint_N:0,acceleration_m_s2:0,virtual_work_error_Nm:0,moment_residual_Nmm:0};
 const bound={reaction_N:0,torque_Nm:0,joint_max_N:0,slave_max_N:0,master_joint_N:0};const step=TAU/720,eps=1e-4;
 for(let j=0;j<720;j++){
  const a=j*step,poses=Array.from({length:7},(_,i)=>sharedPose(i,a,40,k.cutoff,{bore_mm:bore,rod_mm:k.rod_mm}));
  const accelerations=poses.map((p,i)=>(sharedPose(i,a+eps).derivative_mm_rad-sharedPose(i,a-eps).derivative_mm_rad)/(2*eps)/1000*omega**2);
  peak.acceleration_m_s2=Math.max(peak.acceleration_m_s2,...accelerations.map(Math.abs));
  const chamberPressure=(p,side)=>{const c=p[side];if(c.exhaust)return k.back_bar_abs;if(c.inlet)return k.pressure_bar_abs;const A=side==='A'?area:annular,Vcut=A*(.75+k.cutoff*k.stroke_mm)/1000;return Math.max(k.back_bar_abs,k.pressure_bar_abs*(Vcut/c.volume_cm3)**k.polytropic_n);};
  const F=poses.map((p,i)=>((chamberPressure(p,'B')-k.ambient_bar_abs)*annular-(chamberPressure(p,'A')-k.ambient_bar_abs)*area)*.1-mass*accelerations[i]);
  const actual=mechanismLoads(poses,F);for(const key of ['reaction_N','torque_Nm','joint_max_N','slave_max_N','master_joint_N'])peak[key]=Math.max(peak[key],Math.abs(actual[key]));
  peak.virtual_work_error_Nm=Math.max(peak.virtual_work_error_Nm,Math.abs(actual.torque_Nm-F.reduce((s,f,i)=>s+f*poses[i].derivative_mm_rad/1000,0)));peak.moment_residual_Nmm=Math.max(peak.moment_residual_Nmm,Math.abs(actual.moment_residual_Nmm));
  // All 128 corners of independent chamber force intervals. No valve phasing benefit assumed.
  if(j%4===0)for(let bits=0;bits<128;bits++){
   const forces=poses.map((_,i)=>(bits&(1<<i)?annular:-area)*(k.structural_pressure_bar_abs-k.ambient_bar_abs)*.1-mass*accelerations[i]),r=mechanismLoads(poses,forces);
   for(const key of Object.keys(bound))bound[key]=Math.max(bound[key],Math.abs(r[key]));
  }
 }
 const current={shaft_mm:12.5,shaft_overhang_mm:36,crankpin_mm:15,pin_span_mm:25,bearing_length_mm:16};
 const proposed={shaft_mm:45,shaft_overhang_mm:15,crankpin_mm:40,pin_span_mm:32,bearing_length_mm:24};
 const F=bound.reaction_N*k.load_factor,T=bound.torque_Nm*k.load_factor,jointF=bound.joint_max_N*k.load_factor,slaveF=bound.slave_max_N*k.load_factor;
 const baseline=sectionChecks(F,T,current,k),larger=sectionChecks(F,T,proposed,k);
 baseline.actual_cantilever_crankpin_vm_MPa=Math.hypot(32*(F*18)/(PI*15**3),Math.sqrt(3)*4*F/(3*PI*15**2/4));baseline.actual_cantilever_crankpin_screen_ok=baseline.actual_cantilever_crankpin_vm_MPa<=k.allowable_MPa;
 const currentSmall=smallJointChecks(jointF,4,4,10,150,k),currentSlave=smallJointChecks(slaveF,6,4,12,126.31,k);
 const proposedSmall=smallJointChecks(jointF,16,12,36,150,k),proposedSlave=smallJointChecks(slaveF,16,12,36,126.31,k);
 const wall=5,ri=bore/2,ro=ri+wall,pGauge=(k.structural_pressure_bar_abs-k.ambient_bar_abs)*.1;
 const hoop=pGauge*(ro*ro+ri*ri)/(ro*ro-ri*ri),axial=pGauge*ri*ri/(ro*ro-ri*ri),wallVM=Math.sqrt(((hoop-axial)**2+(axial+pGauge)**2+(-pGauge-hoop)**2)/2);
 // Conservative strip through a solid circular head, supported at its rim. Port/bolt/gland holes NOT included.
 const headScreen=3*pGauge*(bore/2)**2/2.5**2,headRequired=bore/2*Math.sqrt(3*pGauge/k.allowable_MPa);
 const pinSpeed=PI*.04*rpm/60,PV=larger.crankpin_bearing_MPa*pinSpeed;
 const pistonRod={current_mm:9.6,proposed_mm:14,current_assumed_Kt_stress_MPa:2*jointF/(PI*9.6**2/4),proposed_assumed_Kt_stress_MPa:2*jointF/(PI*14**2/4),proposed_euler_N:PI**2*k.E_MPa*(PI*14**4/64)/67.5**2,notch_factor_assumed:2};
 const crankWeb={current_width_mm:15,current_thickness_mm:5,current_assumed_Kt_stress_MPa:2*(T*1000/(5*15**2/6)+F/(5*15)),proposed_width_mm:80,proposed_thickness_mm:25,proposed_assumed_Kt_stress_MPa:2*(T*1000/(25*80**2/6)+F/(25*80)),model:'Conservative sum of axial and bending section stress, assumed Kt2; two-cheek 3D geometry and fillets require FEA'};
 const currentForkNet=2*3*4.5,proposedForkNet=2*12*10.8;
 const masterFork={current_cheek_mm:3,current_outer_diameter_mm:64,current_articulation_radius_mm:24,current_ligament_mm:4.5,current_assumed_Kt_stress_MPa:2.5*slaveF/currentForkNet,proposed_cheek_mm:12,proposed_outer_diameter_mm:120,proposed_articulation_radius_mm:40,proposed_ligament_mm:10.8,proposed_assumed_Kt_stress_MPa:2.5*slaveF/proposedForkNet,FEA_required:true};
 return {bore_mm:bore,stroke_mm:45,rod_mm:k.rod_mm,rpm,mass_reciprocating_each_kg:mass,assumptions:k,working_force_A_N:((k.pressure_bar_abs-k.ambient_bar_abs)*area-(k.back_bar_abs-k.ambient_bar_abs)*annular)*.1,working_force_B_N:((k.pressure_bar_abs-k.ambient_bar_abs)*annular-(k.back_bar_abs-k.ambient_bar_abs)*area)*.1,peak,independent_force_bound:bound,design_loads:{crankpin_N:F,torque_Nm:T,joint_N:jointF,slave_joint_N:slaveF},piston_rod:pistonRod,crank_web:crankWeb,master_fork:masterFork,current_dimensions:current,current:baseline,current_small_joint:currentSmall,current_slave_joint:currentSlave,proposed_dimensions:proposed,proposed:larger,proposed_small_joint:proposedSmall,proposed_slave_joint:proposedSlave,cylinder:{wall_mm:wall,wall_hoop_MPa:hoop,wall_vm_MPa:wallVM,head_current_mm:2.5,head_solid_strip_MPa:headScreen,head_solid_minimum_mm:headRequired,head_proposal_mm:8,port_and_bolt_analysis_missing:true},bearing:{speed_upper_m_s:pinSpeed,pv_upper_MPa_m_s:PV,oil_system_not_designed:true},all_strength_confirmed:false};
}
