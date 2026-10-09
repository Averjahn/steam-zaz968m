// Calendar exposure model, SI except explicitly named mm, MPa, hours and rpm.
// It does not integrate the vehicle motion or extrapolate liquid-water tables below 0 C.
export const agingDefaults=Object.freeze({days:730,distance_km_day:50,speed_km_h:50,starts_day:1,warmup_min_start:15,corrosion_mm_year:.1,restraint:.1,E_GPa:200,alpha_per_K:12e-6,climate:'seasonal',winter:'filled',protected_C:5,protection_UA_W_K:5});
export function ambientTemperature(day,climate='seasonal'){
 if(climate==='hot')return 35;if(climate==='cold')return -25;
 if(climate!=='seasonal')throw Error('Неизвестный климат');
 return 5+30*Math.cos(2*Math.PI*day/365);
}
export function hoopStressMPa(inside_mm,outside_mm,pressure_bar_g){
 if(![inside_mm,outside_mm,pressure_bar_g].every(Number.isFinite)||inside_mm<=0||outside_mm<inside_mm||pressure_bar_g<0)throw Error('Некорректные размеры или давление');
 if(outside_mm===inside_mm)return null;
 const a=inside_mm/2,b=outside_mm/2;
 return .1*pressure_bar_g*(a*a+b*b)/(b*b-a*a);
}
export function validateCurve(curve,part){
 if(!curve||curve.component_id!==part.id||typeof curve.reference!=='string'||!curve.reference.trim()||typeof curve.material!=='string'||!curve.material.trim()||curve.stress_ratio_R!==0||!Array.isArray(curve.temperature_range_C)||curve.temperature_range_C.length!==2||!curve.temperature_range_C.every(Number.isFinite)||curve.temperature_range_C[0]>part.hot_C||curve.temperature_range_C[1]<part.hot_C||!Array.isArray(curve.points)||curve.points.length<2)throw Error('Нужна кривая выбранной детали: материал, источник, R=0, диапазон температуры и минимум две точки.');
 const p=curve.points;
 if(!p.every(x=>Number.isFinite(x.stress_amplitude_MPa)&&x.stress_amplitude_MPa>0&&Number.isFinite(x.cycles)&&x.cycles>0)||p.some((x,i)=>i&&(x.stress_amplitude_MPa<=p[i-1].stress_amplitude_MPa||x.cycles>=p[i-1].cycles)))throw Error('Точки должны идти по возрастанию амплитуды и убыванию числа циклов.');
 return curve;
}
export function fatigueLife(curve,amplitude){
 const p=curve.points;if(amplitude<p[0].stress_amplitude_MPa||amplitude>p.at(-1).stress_amplitude_MPa)return null;
 for(let i=1;i<p.length;i++)if(amplitude<=p[i].stress_amplitude_MPa){const a=p[i-1],b=p[i],f=Math.log(amplitude/a.stress_amplitude_MPa)/Math.log(b.stress_amplitude_MPa/a.stress_amplitude_MPa);return Math.exp(Math.log(a.cycles)+f*Math.log(b.cycles/a.cycles));}
 return null;
}
export function runAging(data,options={},curve=null){
 const k={...agingDefaults,...options},rpm=data.crank_rpm;
 const bounds={days:[1,3650],distance_km_day:[1,500],speed_km_h:[1,150],starts_day:[1,20],warmup_min_start:[0,180],corrosion_mm_year:[0,5],restraint:[0,1],E_GPa:[1,400],alpha_per_K:[1e-7,1e-4],protected_C:[1,40],protection_UA_W_K:[0,1000]};
 for(const [key,[min,max]] of Object.entries(bounds))if(!Number.isFinite(k[key])||k[key]<min||k[key]>max)throw Error('Некорректное значение '+key);
 if(!Number.isInteger(k.days)||!Number.isInteger(k.starts_day)||!['filled','drained','heated'].includes(k.winter)||!Number.isFinite(rpm)||rpm<=0)throw Error('Некорректный режим');
 const driving=k.distance_km_day/k.speed_km_h,hot=driving+k.warmup_min_start*k.starts_day/60;
 if(hot>=24)throw Error('Поездка и прогрев должны занимать меньше суток.');
 if(curve){const part=data.parts.find(p=>p.id===curve.component_id);if(!part||part.pressure_bar_g===null)throw Error('Для этой детали нет модели давления.');validateCurve(curve,part);}
 const history=[],damage={};for(const p of data.parts)damage[p.id]={sum:0,covered:true};
 let freezeDays=0,energy=0;
 for(let day=1;day<=k.days;day++){
  const ambient=ambientTemperature(day-1,k.climate),cold=k.winter==='heated'?Math.max(k.protected_C,ambient):ambient;
  const exposure=ambient<0;if(exposure)freezeDays++;
  const heat_kWh=k.winter==='heated'?k.protection_UA_W_K*Math.max(0,k.protected_C-ambient)*(24-hot)/1000:0;energy+=heat_kWh;
  const loss=k.corrosion_mm_year*day/365;
  const parts=data.parts.map(p=>{
   const initial=(p.outside_mm-p.inside_mm)/2,wall=Math.max(0,initial-loss),outside=p.inside_mm+2*wall;
   const stress=p.pressure_bar_g===null?null:hoopStressMPa(p.inside_mm,outside,p.pressure_bar_g);
   const hot_C=Math.max(p.hot_C,cold),delta=hot_C-cold,expansion=p.length_m===null?null:k.alpha_per_K*p.length_m*1000*delta;
   // Uniaxial elastic restraint estimate, NOT hoop stress, yield or a local weld analysis.
   const thermal=k.restraint*k.E_GPa*1000*k.alpha_per_K*delta;
   if(curve&&curve.component_id===p.id){const N=stress===null?null:fatigueLife(curve,stress/2);if(N===null)damage[p.id].covered=false;else damage[p.id].sum+=k.starts_day/N;}
   return {id:p.id,metal_hot_C:hot_C,initial_wall_mm:initial,wall_mm:wall,loss_mm:Math.min(loss,initial),through_wall:wall===0,hoop_MPa:stress,thermal_axial_range_MPa:thermal,free_expansion_mm:expansion,delta_K:delta,pressure_start_damage:curve?.component_id===p.id&&damage[p.id].covered?damage[p.id].sum:null,thermal_fatigue_damage:null,creep_damage:null,allowable_pressure_bar:null,certified_life:null};
  });
  history.push({day,ambient_C:ambient,metal_cold_C:cold,km:day*k.distance_km_day,planned_driving_h:day*driving,planned_hot_h:day*hot,starts:day*k.starts_day,crank_cycles_per_cylinder:day*driving*60*rpm,output_turns:day*driving*60*rpm/data.output_ratio,piston_strokes_per_cylinder:2*day*driving*60*rpm,frost_exposure_days:freezeDays,unprotected_water_days:k.winter==='filled'?freezeDays:0,protection_kWh:energy,parts});
 }
 return {status:'conditional_exposure_study',mission_feasibility:'unverified',water_phase_simulated:false,calendar_year_days:365,assumptions:k,crank_rpm:rpm,output_ratio:data.output_ratio,curve,history,summary:history.at(-1),system_life:null};
}
