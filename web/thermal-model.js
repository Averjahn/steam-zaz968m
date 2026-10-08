// One-dimensional, quasi-steady screening of pipe heat loss. Node temperatures
// come from the transient control-volume simulation. This side calculation is
// not fed back into its energy balance and is not a spatial CFD solution.
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const finite=Number.isFinite;
export const unknownTemperature='#78858f';
export function temperatureRGB(T,min=0,max=350){
 if(!finite(T)||!(max>min))return [120/255,133/255,143/255];
 const stops=[[.06,.30,1],[0,.76,1],[.1,.85,.42],[1,.83,.05],[1,.10,.04]],x=clamp((T-min)/(max-min),0,1)*4,i=Math.min(3,Math.floor(x)),f=x-i;
 return stops[i].map((v,j)=>v+(stops[i+1][j]-v)*f);
}
export function interpolateTable(rows,key,x){
 if(!finite(x)||x<rows[0][key]||x>rows.at(-1)[key])return null;
 let a=0,b=rows.length-1;while(b-a>1){const m=(a+b)>>1;rows[m][key]<x?a=m:b=m;}
 const f=(x-rows[a][key])/(rows[b][key]-rows[a][key]);
 return Object.fromEntries(Object.keys(rows[a]).map(k=>[k,typeof rows[a][k]==='number'?rows[a][k]+f*(rows[b][k]-rows[a][k]):rows[a][k]]));
}
export function saturationAtPressure(data,p){return interpolateTable(data.water.saturation,'p',p);}
function steamRow(data,p){
 const rows=data.water.steam;if(p<rows[0].p*1e5||p>rows.at(-1).p*1e5)return null;
 let i=0;while(i<rows.length-2&&p>rows[i+1].p*1e5)i++;
 const f=(p/1e5-rows[i].p)/(rows[i+1].p-rows[i].p);
 return rows[i].states.map((v,j)=>({h:v.h+f*(rows[i+1].states[j].h-v.h),rho:v.rho+f*(rows[i+1].states[j].rho-v.rho),superheat:data.water.superheats_C[j]}));
}
export function waterStatePH(data,p,h){
 const sat=saturationAtPressure(data,p);if(!sat||!finite(h))return null;
 if(h>=sat.hf&&h<=sat.hg){const quality=(h-sat.hf)/(sat.hg-sat.hf);return {T:sat.T,h,p,quality,phase:quality<1e-8?'liquid':quality>1-1e-8?'vapour':'two-phase',rho:1/(sat.vf+quality*(sat.vg-sat.vf))};}
 if(h<sat.hf){
  // Incompressible approximation h(T,p)≈hf(T)+vf(T)[p−psat(T)].
  const rows=data.water.saturation,at=s=>s.hf+s.vf*(p-s.p);if(h<at(rows[0]))return null;
  let a=0,b=rows.length-1;while(b-a>1){const m=(a+b)>>1;rows[m].p<p?a=m:b=m;}const end=a;
  a=0;b=end;while(b-a>1){const m=(a+b)>>1;at(rows[m])<h?a=m:b=m;}
  let lower=rows[a],upper=rows[b];if(h>at(upper)){lower=rows[end];upper=sat;}
  const f=(h-at(lower))/(at(upper)-at(lower)),T=lower.T+f*(upper.T-lower.T),vf=lower.vf+f*(upper.vf-lower.vf);
  return {T,h,p,quality:0,phase:'liquid',rho:1/vf};
 }
 const rows=steamRow(data,p);if(!rows)return null;
 // Anchor the interpolated superheat increments to the saturation enthalpy.
 const adjusted=rows.map(r=>({...r,h:sat.hg+r.h-rows[0].h})),v=interpolateTable(adjusted,'h',h);
 return v?{T:sat.T+v.superheat,h,p,quality:1,phase:'vapour',rho:v.rho}:null;
}
export function waterEnthalpyPT(data,p,T){
 const sat=saturationAtPressure(data,p);if(!sat||!finite(T))return null;
 if(T<=sat.T){const v=interpolateTable(data.water.saturation,'T',Math.max(.01,T));return v?v.hf+v.vf*(p-v.p):null;}
 const rows=steamRow(data,p);if(!rows)return null;
 const v=interpolateTable(rows,'superheat',T-sat.T);return v?sat.hg+v.h-rows[0].h:null;
}
export function insulationConductivity(material,T){
 const rows=material.temperature_C.map((t,i)=>({T:t,k:material.lambda_W_mK[i]}));
 return interpolateTable(rows,'T',clamp(T,rows[0].T,rows.at(-1).T)).k;
}
export function cylindricalHeatLoss(route,T,ambient,material,{hExternal=8,insulated=true}={}){
 if(!finite(T)||!finite(ambient)||!(route.od>0)||!(hExternal>0))return null;
 const ri=route.od/2000,ro=ri+(insulated?route.insulation_mm||0:0)/1000,rj=ro+(insulated?route.jacket_mm||0:0)/1000;
 let surface=(T+ambient)/2,k=insulationConductivity(material,(T+surface)/2),Rc=0,Rs=1/(2*Math.PI*rj*hExternal);
 for(let i=0;i<35;i++){k=insulationConductivity(material,(T+surface)/2);Rc=ro>ri?Math.log(ro/ri)/(2*Math.PI*k):0;surface=ambient+(T-ambient)*Rs/(Rc+Rs);}
 const q=(T-ambient)/(Rc+Rs);
 return {q_W_m:q,surface_C:surface,k_W_mK:k,R_cond_mK_W:Rc,R_external_mK_W:Rs,r_m:rj,hExternal};
}
export function pipeThermalProfile({data,route,inlet,massFlow,ambient,material,segments=64,hExternal=8,cp=null}){
 const length=route.centerline_length_m;if(!inlet||!finite(inlet.T)||!(length>0)||!(massFlow>1e-8))return {status:'no-flow-or-boundary',samples:[],heat_W:null,residual_W:null};
 if(!cp&&(!finite(inlet.h)||!finite(inlet.p)))return {status:'unknown-property',samples:[],heat_W:null,residual_W:null};
 let h=cp?cp*inlet.T:inlet.h,heat=0;const startH=h,dx=length/segments,samples=[];
 const stateAt=v=>cp?{T:v/cp,h:v,p:inlet.p,rho:inlet.rho,phase:'gas',quality:null}:waterStatePH(data,inlet.p,v);
 const ambientH=cp?cp*ambient:waterEnthalpyPT(data,inlet.p,ambient);
 if(!finite(ambientH))return {status:'out-of-table',samples:[],heat_W:null,residual_W:null};
 for(let i=0;i<=segments;i++){
  const state=stateAt(h);if(!state)return {status:'out-of-table',samples:[],heat_W:null,residual_W:null};
  const x=i*dx,exposed=x<(route.exposed_end_mm||0)/1000||x>length-(route.exposed_end_mm||0)/1000;
  const loss=cylindricalHeatLoss(route,state.T,ambient,material,{hExternal,insulated:!exposed});
  samples.push({fraction:i/segments,x_m:x,...state,...loss});if(i===segments)break;
  // Midpoint integration with an equilibrium bound prevents artificial cooling
  // below ambient at very low flow and preserves the local enthalpy balance.
  let half=h-loss.q_W_m*dx/(2*massFlow);half=clamp(half,Math.min(h,ambientH),Math.max(h,ambientH));
  const mid=stateAt(half);if(!mid)return {status:'out-of-table',samples:[],heat_W:null,residual_W:null};
  const midLoss=cylindricalHeatLoss(route,mid.T,ambient,material,{hExternal,insulated:!exposed});
  const next=clamp(h-midLoss.q_W_m*dx/massFlow,Math.min(h,ambientH),Math.max(h,ambientH));heat+=massFlow*(h-next);h=next;
 }
 return {status:'quasi-steady',samples,heat_W:heat,residual_W:massFlow*(startH-h)-heat,inlet_h:startH,outlet_h:h,massFlow,ambient,length_m:length};
}
export function profileAt(profile,fraction){
 const a=profile?.samples;if(!a?.length)return null;const x=clamp(fraction,0,1)*(a.length-1),i=Math.min(a.length-2,Math.floor(x)),f=x-i;
 return Object.fromEntries(Object.keys(a[i]).map(k=>[k,typeof a[i][k]==='number'?a[i][k]+f*(a[i+1][k]-a[i][k]):a[i][k]]));
}
export function componentThermalState(id,s,cfg,source){
 const result=(T,p=null,flow=null,basis='Температура контрольного объёма')=>({T,p,flow,basis});
 switch(id){
  case 'STM':return result(s.boiler.T,s.boiler.p,s.flow,'Средняя вода/металл генератора; расход пара на выходе');
  case 'ENG':return result(s.engine_C,null,s.flow,'Средняя температура металла; общий вход пара; давление камер не рассчитано');
  case 'CND':return result(s.condenser.T,s.condenser.p,s.flow,'Равновесный контрольный объём с воздухом; входной расход');
  case 'RCV':return result(s.receiver.T,2e5,s.feed,'Приёмник: подпор 2 бар abs задан; выход к Cat');
  case 'WTR':return result(20,1e5,s.makeup,'Подпитка 20 °C задана моделью; расход из бака');
  case 'PMP':return result(s.receiver.T,s.feed_pressure_bar_abs*1e5,s.feed,'Температура жидкости, не корпуса Cat');
  case 'BOOST':return result(s.condenser.T,null,s.drain,'Температура жидкости перед подъёмом давления');
  case 'FUE':return result(null,null,null,'Нагрев топлива/аккумулятора не рассчитан');
  case 'BRN':return result(null,null,null,'Температура пламени и стенок не рассчитана');
  case 'PIPE_STEAM':return result(s.outlet_C??s.boiler.T,s.boiler.p,s.flow,'Свежий пар: граничное состояние');
  case 'PIPE_FEED':return result(s.receiver.T,s.feed_pressure_bar_abs*1e5,s.feed,'Температура до нагрева в генераторе');
  case 'PIPE_SUCTION':return result(s.receiver.T,2e5,s.feed,'Температура на входе Cat');
  case 'PIPE_RETURN':return result(s.condenser.T,2e5,s.drain,'После конденсатного насоса; давление задано');
  case 'PIPE_BALANCE':return result(s.condenser.T,s.condenser.p,(s.drain||0)/2,'Водный возврат до насоса');
  case 'PIPE_MAKEUP':return result(20,2e5,s.makeup,'После подпитки; напор устройства не подобран');
  case 'PIPE_FLUE':return result(s.flue_C,null,s.flue_mass_kg_s,'Средняя температура газового узла');
  case 'PIPE_RELIEF':return result(null,null,0,'Аварийный расход и тепловое поле не рассчитаны');
  default:if(id.startsWith('PIPE_EXHAUST')){const h=s.exhaust_h_J_kg,v=finite(h)?waterStatePH({water:cfg.water},s.condenser.p,h):null;return result(v?.T??null,s.condenser.p,(s.flow||0)/2,'H₂O при противодавлении: приближение без воздуха');}
   return result(null,null,null,'Тепловая модель этого узла отсутствует');
 }
}
export function routeInlet(data,route,s,cfg,source){
 const info=componentThermalState(route.id,s,{...cfg,water:data.water},source);let h,p=info.p;
 if(route.id==='PIPE_STEAM')h=s.inlet_h_J_kg??waterEnthalpyPT(data,p,info.T);
 else if(route.id.startsWith('PIPE_EXHAUST'))h=s.exhaust_h_J_kg;
 else if(route.id==='PIPE_FEED')h=s.feed_h_J_kg??waterEnthalpyPT(data,p,info.T);
 else if(route.fluid==='water')h=waterEnthalpyPT(data,p,info.T);
 else if(route.fluid==='flue')return {...info,cp:source.flue?.cp_J_kgK||1100,rho:null};
 else return null;
 const v=finite(h)?waterStatePH(data,p,h):null;return v?{...info,...v}:null;
}
