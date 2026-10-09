import {engineGeometry as K,cylinderCycle} from './double-acting-cycle.js?v=02f171f7ae23';

// Local force estimate, not an indicator diagram or a replacement power model.
export const forceDefaults=Object.freeze({inlet_bar:10,exhaust_bar:1,ambient_bar:1,
 rpm:300,mass_kg:3,friction_N:80,polytropic:1.2,alpha_rad_s2:0});
export function pistonKinematics(angle,rpm,alpha=0){
 const r=K.crankRadius/1000,l=K.connectingRod/1000,s=Math.sin(angle),c=Math.cos(angle),q=Math.sqrt(l*l-r*r*s*s);
 const dz=-r*s-r*r*s*c/q;
 const ddz=-r*c-r*r*(c*c-s*s)/q-r**4*s*s*c*c/q**3;
 const omega=rpm*2*Math.PI/60;
 return {r_m:r,l_m:l,q_m:q,dz_m_rad:dz,ddz_m_rad2:ddz,omega_rad_s:omega,
  velocity_m_s:dz*omega,acceleration_m_s2:ddz*omega*omega+dz*alpha};
}
export function chamberPressure(cycle,ch,options){
 const o={...forceDefaults,...options},v=cycle[ch],area=Math.PI*(K.bore/1000)**2/4-(ch==='B'?Math.PI*(K.rodDiameter/1000)**2/4:0);
 const volume=v.volume_cm3*1e-6,cutVolume=area*(K.clearance+.30*2*K.crankRadius)/1000;
 const closeAngle=(ch==='A'?2*Math.PI:Math.PI)-12*Math.PI/180;
 const closeVolume=cylinderCycle(closeAngle)[ch].volume_cm3*1e-6;
 let pressure=o.exhaust_bar*1e5,reference=volume,referencePressure=pressure;
 if(o.equalized)return {pressure_Pa:pressure,volume_m3:volume,reference_m3:volume,reference_Pa:pressure,law:'equalized'};
 if(v.phase==='admission'){pressure=o.inlet_bar*1e5;referencePressure=pressure;}
 if(v.phase==='expansion'){reference=cutVolume;referencePressure=o.inlet_bar*1e5;pressure=referencePressure*(reference/volume)**o.polytropic;}
 if(v.phase==='compression'){reference=closeVolume;referencePressure=o.exhaust_bar*1e5;pressure=referencePressure*(reference/volume)**o.polytropic;}
 return {pressure_Pa:pressure,volume_m3:volume,reference_m3:reference,reference_Pa:referencePressure,law:v.phase};
}
export function pistonForces(angle,options={}){
 const o={...forceDefaults,...options};
 for(const key of ['inlet_bar','exhaust_bar','ambient_bar','rpm','mass_kg','friction_N','polytropic','alpha_rad_s2'])if(!Number.isFinite(o[key]))throw Error('Non-finite force input: '+key);
 if(o.inlet_bar<=0||o.exhaust_bar<=0||o.ambient_bar<=0||o.rpm<0||o.mass_kg<=0||o.friction_N<0||o.polytropic<=0)throw Error('Invalid force inputs');
 const cycle=cylinderCycle(angle),motion=pistonKinematics(cycle.angle_rad,o.rpm,o.alpha_rad_s2);
 const areaA=Math.PI*(K.bore/1000)**2/4,areaRod=Math.PI*(K.rodDiameter/1000)**2/4,areaB=areaA-areaRod;
 const A=chamberPressure(cycle,'A',o),B=chamberPressure(cycle,'B',o),ambient=o.ambient_bar*1e5;
 // Gauge face forces also account for ambient pressure on the exposed rod end.
 const faceA=-(A.pressure_Pa-ambient)*areaA,faceB=(B.pressure_Pa-ambient)*areaB;
 const gravity=-o.mass_kg*9.81,friction=Math.abs(motion.velocity_m_s)>1e-10?-Math.sign(motion.velocity_m_s)*o.friction_N:0;
 const inertia=o.mass_kg*motion.acceleration_m_s2,gas=faceA+faceB,drive=gas+gravity+friction-inertia;
 const rodZ=-drive,rodY=-rodZ*motion.r_m*Math.sin(cycle.angle_rad)/motion.q_m,guideY=-rodY;
 return {cycle,inputs:o,motion,areas:{A_m2:areaA,B_m2:areaB,rod_m2:areaRod},pressures:{A,B},
  forces:{faceA_N:faceA,faceB_N:faceB,gas_N:gas,gravity_N:gravity,friction_N:friction,
   rod_Z_N:rodZ,rod_Y_N:rodY,guide_Y_N:guideY,rod_magnitude_N:Math.hypot(rodZ,rodY),
   net_Z_N:gas+gravity+friction+rodZ,ma_N:inertia,transmitted_N:drive},
  // Work conjugate torque for increasing displayed theta; actual crank rotation is -theta.
  torque_theta_Nm:drive*motion.dz_m_rad,
  residual_Z_N:gas+gravity+friction+rodZ-inertia,residual_Y_N:rodY+guideY};
}
