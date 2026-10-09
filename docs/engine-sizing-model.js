import {displacement} from './radial-engine-model.js?v=7f88549d47ae';
export const sizingDefaults=Object.freeze({heat_kW:50,eta_is:.5,eta_mech:.9,eta_electric:.85,
 cutoff:.3,filling_factor:.85,ambient_C:20,air_rise_K:25,air_area_m2:.05525,air_rho:1.18,air_cp:1005,
 fan_efficiency:.55,pump_efficiency:.55,static_air_Pa:250,air_loss_coefficient:1,
 receiver_bar_abs:2,crank_study_limit_rpm:2600,hp_W:735.49875});
export const sizingCandidates=Object.freeze([
 {id:'original-two',name:'Прежние два цилиндра',count:2,bore:100,stroke:120,rod:24,output_ratio:1,
  size_mm:[545,385,500],size_basis:'Габарит текущего native GLB; сервисные и горячие зазоры отдельно',fit_status:'Внутри проектного резерва; реальные внутренние размеры кузова не подтверждены'},
 {id:'large-seven',name:'Прежняя звезда Ø100 × 120',count:7,bore:100,stroke:120,rod:24,output_ratio:2,
  size_mm:[1492,1448,329],size_basis:'Габарит опубликованной сборки с коллекторами и граничными патрубками',fit_status:'Не входит в резерв 600 × 500 × 500 мм'},
 {id:'compact-seven',name:'Компактная звезда Ø32 × 36',count:7,bore:32,stroke:36,rod:7.68,output_ratio:2,
  core_scale:.3,core_radius_bound_mm:Math.hypot(685,24)*.3,core_height_bound_mm:165*.3,
  budget_mm:[480,460,420],size_mm:[511.0469207763672,490.10508728027344,419.6000061035156],size_basis:'Габарит новой компактной 3D-сборки с трубками, коллекторами, изоляцией и угловой передачей; стойки до пола отдельно',fit_status:'Поверхности не пересекают предоставленный кузов и статическую подвеску; реальная посадка, динамические и горячие зазоры не подтверждены'}
]);
const finitePositive=x=>Number.isFinite(x)&&x>0;
function lmtd(a,b){if(a<=0||b<=0)return null;return Math.abs(a-b)<1e-8?(a+b)/2:(a-b)/Math.log(a/b);}
export function sizeEngine(data,candidate,options={}){
 const k={...sizingDefaults,filling_factor:data.filling_factor??sizingDefaults.filling_factor,...options},s=data.steam,t=data.cycle,source=data.diesel;
 if(!finitePositive(k.heat_kW)||k.heat_kW>1000||![k.eta_is,k.eta_mech,k.eta_electric,k.fan_efficiency,k.pump_efficiency,k.cutoff,k.filling_factor].every(x=>finitePositive(x)&&x<=1)||!finitePositive(k.air_area_m2)||!finitePositive(k.air_rise_K)||k.air_rise_K>60||!finitePositive(k.crank_study_limit_rpm)||!Number.isFinite(k.static_air_Pa)||k.static_air_Pa<0||!Number.isFinite(k.air_loss_coefficient)||k.air_loss_coefficient<0)throw new RangeError('Invalid sizing assumptions');
 const geometry=displacement(candidate.count,{...candidate,cutoff:k.cutoff,density:s.density_kg_m3});
 const pumpSpecific=(t.p_in_Pa-k.receiver_bar_abs*1e5)/(t.rho_feed_kg_m3*k.pump_efficiency);
 const heatPerKg=t.h_in_J_kg-t.h_feed_J_kg-pumpSpecific;
 if(pumpSpecific<0||heatPerKg<=0)throw new RangeError('Invalid pump or heat balance');
 const massFlow=k.heat_kW*1000/heatPerKg,indicated=massFlow*t.dh_is_J_kg*k.eta_is,
 shaft=indicated*k.eta_mech,pump=massFlow*pumpSpecific,
 hExhaust=t.h_in_J_kg-t.dh_is_J_kg*k.eta_is,
 mainHeat=massFlow*(hExhaust-t.h_liquid_J_kg),subHeat=massFlow*(t.h_liquid_J_kg-t.h_feed_J_kg),reject=mainHeat+subHeat;
 const air=reject/(k.air_rho*k.air_cp*k.air_rise_K),airSpeed=air/k.air_area_m2,
 pressure=k.static_air_Pa+k.air_loss_coefficient*k.air_rho*airSpeed**2/2,
 fan=pressure*air/k.fan_efficiency;
 const input=k.heat_kW/source.efficiency,lhv=source.LHV_MJ_kg,
 fuelKgH=input*3.6/lhv,fuelLH=fuelKgH/source.density_kg_L;
 const f=source.flue,gasMass=input*1000/(lhv*1e6)*(1+f.stoich_air*f.excess_air),
 gasRho=101325/(f.gas_R_J_kgK*(f.wall_C+273.15)),gasD=f.inside_mm/1000,gasArea=Math.PI*gasD**2/4,
 gasSpeed=gasMass/(gasRho*gasArea),gasDrop=(f.friction_factor*data.flue_length_m/gasD+2.6)*gasRho*gasSpeed**2/2,
 gasFan=gasDrop*gasMass/gasRho/.4;
 const electric=pump+fan+source.aux_W+25+gasFan,auxShaft=electric/k.eta_electric,net=shaft-auxShaft;
 const rpm=massFlow/s.density_kg_m3/(geometry.admitted_L/1000*k.filling_factor)*60,outputRpm=rpm/candidate.output_ratio;
 const mainLMTD=lmtd(t.condensing_C-k.ambient_C,t.condensing_C-k.ambient_C-k.air_rise_K),subLMTD=lmtd(t.condensing_C-k.ambient_C-k.air_rise_K,60-k.ambient_C);
 const reserve=[600,500,500],dims=candidate.size_mm??candidate.budget_mm;
 return {candidate_id:candidate.id,geometry,assumptions:k,heat_kW:k.heat_kW,mass_kg_h:massFlow*3600,
 indicated_kW:indicated/1000,shaft_kW:shaft/1000,shaft_hp:shaft/k.hp_W,
 net_kW:airSpeed<=60?net/1000:null,net_hp:airSpeed<=60?net/k.hp_W:null,electric_kW:airSpeed<=60?electric/1000:null,aux_shaft_kW:airSpeed<=60?auxShaft/1000:null,air_budget_applicable:airSpeed<=60,
 pump_kW:pump/1000,fan_kW:airSpeed<=60?fan/1000:null,flue_fan_kW:gasFan/1000,
 reject_kW:reject/1000,main_reject_kW:mainHeat/1000,subcool_kW:subHeat/1000,
 air_m3_s:air,air_m_s:airSpeed,air_Pa:pressure,air_out_C:k.ambient_C+k.air_rise_K,
 UA_main_estimate_W_K:mainLMTD?mainHeat/mainLMTD:null,UA_subcool_estimate_W_K:subLMTD?subHeat/subLMTD:null,
 crank_rpm:rpm,output_rpm:outputRpm,torque_output_Nm:shaft/(outputRpm*2*Math.PI/60),mean_piston_m_s:2*candidate.stroke/1000*rpm/60,
 fuel_input_kW:input,fuel_kg_h:fuelKgH,fuel_L_h:fuelLH,
 engine_speed_study_ok:rpm<=k.crank_study_limit_rpm,source_power_ok:input<=source.max_input_kW,
 fits_reserve_box:dims.every((x,i)=>x<=reserve[i]),has_current_mesh_bounds:['original-two','compact-seven'].includes(candidate.id),
 energy_residual_W:k.heat_kW*1000+pump-indicated-reject,
 effective_thermal_efficiency:shaft/(k.heat_kW*1000),ideal_rankine_efficiency:t.dh_is_J_kg/heatPerKg};
}
export function heatForPower(data,power_hp=40,options={}){
 const k={...sizingDefaults,...options},t=data.cycle,wp=(t.p_in_Pa-k.receiver_bar_abs*1e5)/(t.rho_feed_kg_m3*k.pump_efficiency);
 if(!finitePositive(power_hp)||!finitePositive(k.eta_is)||k.eta_is>1||!finitePositive(k.eta_mech)||k.eta_mech>1)throw new RangeError('Invalid target');
 return power_hp*k.hp_W/(t.dh_is_J_kg*k.eta_is*k.eta_mech)*(t.h_in_J_kg-t.h_feed_J_kg-wp)/1000;
}
