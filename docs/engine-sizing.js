import {sizeEngine} from './engine-sizing-model.js?v=c80f30c2fdf3';
const $=id=>document.getElementById(id),fmt=(n,p=2)=>n===null?'вне модели':n.toLocaleString('ru-RU',{maximumFractionDigits:p,minimumFractionDigits:p});
let data,last;
const card=(name,formula,sub,result)=>`<article class="formula-card"><h3>${name}</h3><p class="formula">${formula}</p><p>${sub}</p><strong>${result}</strong></article>`;
function update(){
 if(!data)return;try{const heat=$('sizingHeat').valueAsNumber,eta=$('sizingEfficiency').valueAsNumber,rise=$('sizingAirRise').valueAsNumber;if(heat<1||heat>150||eta<.1||eta>1||rise<10||rise>60)throw Error('Задайте тепло 1–150 кВт, КПД 0,1–1 и нагрев воздуха 10–60 К.');
 const c=data.candidates.find(c=>c.id===$('sizingEngine').value),v=sizeEngine(data.input,c,{heat_kW:heat,eta_is:eta,air_rise_K:rise});last=v;
 $('sizingSummary').textContent=`${c.name}: ${fmt(v.geometry.swept_L,3)} л. На валу до потребителей: ${fmt(v.shaft_kW)} кВт / ${fmt(v.shaft_hp)} л.с. Баланс после вспомогательных: ${fmt(v.net_kW)} кВт, до автомобильной трансмиссии. Пар ${fmt(v.mass_kg_h,1)} кг/ч; кривошипы ${fmt(v.crank_rpm,0)} об/мин, выход ${fmt(v.output_rpm,0)} об/мин.`;
 $('sizingWarnings').textContent=[!v.engine_speed_study_ok?'Обороты превышают исследовательский предел 2600 об/мин.':'',!v.source_power_ok?'Превышена максимальная мощность размерного кандидата горелки.':'',!v.air_budget_applicable?'Скорость воздуха превышает область данного бюджета вентилятора: потребление и полезная мощность не оценены.':'',v.net_kW!==null&&v.net_kW<=0?'Вспомогательные потребители превышают мощность вала: стационарный режим с ними не поддерживается.':'',c.id==='compact-seven'?'Компактная сборка построена и проверена в игровой сетке кузова. Реальная посадка, прочность и КПД не подтверждены.':c.fit_status].filter(Boolean).join(' ');
 const t=data.input.cycle,k=v.assumptions,d=v.geometry,dh=(t.h_in_J_kg-t.h_feed_J_kg)/1000,wp=(t.p_in_Pa-2e5)/(t.rho_feed_kg_m3*k.pump_efficiency)/1000;
 $('sizingFormulas').innerHTML=[
 card('Геометрический рабочий объём','V = NπD²S / 4',`${c.count} × π × (${fmt(c.bore/1000,3)} м)² × ${fmt(c.stroke/1000,3)} м / 4 × 1000`,fmt(d.swept_L,3)+' л'),
 card('Обе стороны за цикл поршня','Vдв = N [πD²/4 + π(D² − d²)/4] S',`${c.count} × [π × ${fmt(c.bore/1000,4)}² / 4 + π × (${fmt(c.bore/1000,4)}² − ${fmt(c.rod/1000,4)}²) / 4] × ${fmt(c.stroke/1000,3)} × 1000`,fmt(d.double_L,3)+' л/цикл'),
 card('Расход пара по теплу','ṁ = Q̇ / (hвх − hпит − wнас)',`${fmt(heat,1)} / (${fmt(dh,3)} − ${fmt(wp,3)}) × 3600`,fmt(v.mass_kg_h,1)+' кг/ч'),
 card('Мощность на валу','Pвал = ṁ × Δhиз × ηis × ηмех',`${fmt(v.mass_kg_h/3600,6)} × 400,354 × ${fmt(eta)} × 0,90`,fmt(v.shaft_kW)+' кВт / '+fmt(v.shaft_hp)+' л.с.'),
 card('Обороты по объёмной подаче','nкр = 60ṁ / (ρпар ε ηv Vдв)',`60 × ${fmt(v.mass_kg_h/3600,6)} / (4,29914 × 0,30 × 0,85 × ${fmt(d.double_L/1000,7)})`,fmt(v.crank_rpm,0)+' об/мин'),
 card('Обороты выхода и момент','nвых = nкр / i; Mвых = Pвал / (2πnвых/60)',`${fmt(v.crank_rpm,1)} / ${c.output_ratio}; ${fmt(v.shaft_kW*1000,1)} / (2π × ${fmt(v.output_rpm,1)} / 60)`,fmt(v.output_rpm,0)+' об/мин · '+fmt(v.torque_output_Nm,1)+' Н·м'),
 card('Средняя скорость поршня','cп = 2Snкр / 60',`2 × ${fmt(c.stroke/1000,3)} × ${fmt(v.crank_rpm,1)} / 60`,fmt(v.mean_piston_m_s)+' м/с · не паспортный предел'),
 card('Замыкание водяного теплового баланса','Q̇воды = Q̇ген + Pнас − Pинд',`${fmt(heat)} + ${fmt(v.pump_kW,3)} − ${fmt(v.indicated_kW,3)}`,fmt(v.reject_kW)+' кВт, включая '+fmt(v.subcool_kW)+' кВт доохлаждения'),
 card('Поток воздуха','V̇возд = Q̇воды / (ρвозд cp ΔT)',`${fmt(v.reject_kW*1000,1)} / (1,18 × 1005 × ${fmt(rise,0)})`,fmt(v.air_m3_s,3)+' м³/с · '+fmt(v.air_m_s)+' м/с'),
 card('Бюджет вентилятора','Pвент = [250 + Kρu²/2] V̇ / ηвент',`[250 + 1 × 1,18 × ${fmt(v.air_m_s)}² / 2] × ${fmt(v.air_m3_s,3)} / 0,55 / 1000`,fmt(v.fan_kW)+' кВт электричества · заданный бюджет потерь'),
 card('После вспомогательных потребителей','Pост = Pвал − ΣPэл / ηген',`${fmt(v.shaft_kW,3)} − ${fmt(v.electric_kW,3)} / 0,85`,fmt(v.net_kW)+' кВт · до трансмиссии'),
 card('Расход дизеля','B = (Q̇/ηкотла) × 3,6 / (LHV ρтопл)',`(${fmt(heat)} / 0,85) × 3,6 / (42,6 × 0,835)`,fmt(v.fuel_L_h)+' л/ч')].join('');
 $('sizingExport').disabled=false;
 }catch(e){last=null;$('sizingWarnings').textContent=e.message;$('sizingExport').disabled=true;}
}
for(const id of ['sizingEngine','sizingHeat','sizingEfficiency','sizingAirRise'])$(id).addEventListener('input',update);
$('sizingExport').onclick=()=>{if(!last)return;const url=URL.createObjectURL(new Blob([JSON.stringify({status:data.status,inputs:data.input,result:last,limitations:data.limitations},null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='engine-sizing-current.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);};
fetch('engine-sizing.json?v=23e468c4a381').then(r=>{if(!r.ok)throw Error('Не удалось загрузить исходные данные');return r.json();}).then(x=>{data=x;update();}).catch(e=>{$('sizingWarnings').textContent=e.message;$('sizingExport').disabled=true;});
