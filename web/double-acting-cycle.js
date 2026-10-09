// Illustrative valve timing, not a measured indicator diagram or power model.
export const engineGeometry=Object.freeze({cylinderX:[200,415],cylinderY:250,crankZ:89,outputZ:145,
 crankRadius:60,connectingRod:110,pistonRod:173,crossheadBridgeZ:17,bore:100,rodDiameter:24,pistonThickness:20,
 bottomFace:300,topFace:444,clearance:2,phaseOffset:Math.PI/2});
export function cylinderCycle(angle,{cutoff=.30,releaseDegrees=12}={}){
 const k=engineGeometry,a=((angle%(2*Math.PI))+2*Math.PI)%(2*Math.PI),r=k.crankRadius,l=k.connectingRod;
 const z=k.crankZ+r*Math.cos(a)+Math.sqrt(l*l-r*r*Math.sin(a)**2)+k.pistonRod;
 const down=a<Math.PI,release=releaseDegrees*Math.PI/180;
 const progress=down?(k.crankZ+l+k.pistonRod+r-z)/(2*r):(z-(k.crankZ+l+k.pistonRod-r))/(2*r);
 const active=progress<cutoff?'admission':a%(Math.PI)>Math.PI-release?'release':'expansion';
 const returning=a%(Math.PI)>Math.PI-release?'compression':'exhaust';
 const phaseA=down?active:returning,phaseB=down?returning:active;
 const chamber=(phase,height,area)=>({phase,height_mm:height,volume_cm3:area*height/1000,
  inletOpen:phase==='admission',exhaustOpen:phase==='exhaust'||phase==='release',
  direction:phase==='admission'?1:phase==='exhaust'||phase==='release'?-1:0});
 const area=Math.PI*k.bore**2/4,rodArea=Math.PI*k.rodDiameter**2/4;
 return {angle_rad:a,angle_deg:a*180/Math.PI,pistonZ_mm:z,down,progress,
  A:chamber(phaseA,k.topFace-z-k.pistonThickness/2,area),
  B:chamber(phaseB,z-k.pistonThickness/2-k.bottomFace,area-rodArea)};
}
export const phaseNames={admission:'Впуск',expansion:'Отсечка · расширение',exhaust:'Выпуск',release:'Опережение выпуска',compression:'Сжатие остатка'};
