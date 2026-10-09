import {radialPose,gearPolygon,displacement} from './radial-engine-model.js?v=7f88549d47ae';
export const compactGeometry=Object.freeze({count:7,bore:32,stroke:36,rod:7.68,crank:18,link:57,pistonRod:54,pistonThickness:6,clearance:.6,axisRadius:63,axisZ:61,module:1.5,centralTeeth:56,localTeeth:28,innerHead:152.4,outerHead:195.6,shellRadius:20,cylinderInsulation:15,valveRadius:176,valveZ:185,inletRadius:132,inletZ:245,inletWidth:24,inletHeight:30,returnRadius:104,returnZ:170,returnWidth:48,returnHeight:50,headerWall:3,origin:[3210,0,490],reserveMin:[2910,-250,300],reserveMax:[3510,250,800],trayZ:439,outputZ:-90,outputRatio:2});
export function compactPose(index,angle,cutoff=.3){
 const k=compactGeometry,p=radialPose(index,angle,cutoff),map=a=>[a[0]*.3,a[1]*.3,k.axisZ],R=p.pistonRadius*.3;
 const AA=Math.PI*k.bore**2/4,AB=Math.PI*(k.bore**2-k.rod**2)/4;
 return {...p,pin:map(p.pin),axis:[p.axis[0]*.3,p.axis[1]*.3,0],crosshead:map(p.crosshead),piston:map(p.piston),pistonRadius:R,A:{...p.A,volume_cm3:AA*(k.outerHead-R-k.pistonThickness/2)/1000},B:{...p.B,volume_cm3:AB*(R-k.pistonThickness/2-k.innerHead)/1000}};
}
export const compactGearPolygon=teeth=>gearPolygon(teeth).map(p=>p.map(x=>x*.3));
export const compactDisplacement=()=>displacement(7,{bore:32,stroke:36,rod:7.68});
export function pipeSection(id_mm,od_mm,insulation_mm=0,jacket_mm=.5){if(![id_mm,od_mm,insulation_mm,jacket_mm].every(Number.isFinite)||id_mm<=0||od_mm<=id_mm||insulation_mm<0||jacket_mm<0)throw Error('Invalid pipe section');return {inside_mm:id_mm,outside_mm:od_mm,wall_mm:(od_mm-id_mm)/2,insulation_mm,jacket_mm,envelope_mm:od_mm+2*insulation_mm+2*jacket_mm,area_m2:Math.PI*(id_mm/1000)**2/4};}
export const compactPipes=Object.freeze({chamber:pipeSection(8,12,7),supply:pipeSection(8,12,7),exhaust:pipeSection(12,16,10),boundaryIn:pipeSection(40,48,30,.6),boundaryOut:pipeSection(40,46,12.5)});
