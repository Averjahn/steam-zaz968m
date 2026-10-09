const $=id=>document.getElementById(id);
const f=(n,d=2)=>Number(n).toLocaleString('ru-RU',{maximumFractionDigits:d});
const fields={inlet_bar:['engineForceInlet',.01,50],exhaust_bar:['engineForceExhaust',.01,50],ambient_bar:['engineForceAmbient',.01,5],rpm:['engineForceRPM',0,2600],mass_kg:['engineForceMass',.05,30],friction_N:['engineForceFriction',0,2000],polytropic:['engineForceExponent',1,1.4],scale_N:['engineForceScale',1000,100000]};
const defaults={inlet_bar:10,exhaust_bar:1,ambient_bar:1,rpm:300,mass_kg:3,friction_N:80,polytropic:1.2,scale_N:10000};
export function forceSettings(mode,s){
 const o={visible:$('engineShowForces').checked,labels:$('engineForceLabels').checked,layer:$('engineForceLayer').value};
 for(const [key,[id,min,max]]of Object.entries(fields)){const input=$(id),raw=input.valueAsNumber;o[key]=Number.isFinite(raw)?Math.max(min,Math.min(max,raw)):defaults[key];}
 if(mode==='simulation'){o.rpm=Math.max(0,s.rpm||0);o.inlet_bar=Math.max(.00001,s.boiler.p/1e5);o.exhaust_bar=Math.max(.00001,s.condenser.p/1e5);o.equalized=!(s.flow>1e-9)&&o.rpm===0;}
 return o;
}
function formula(parent,law,substitution){const row=document.createElement('div');row.className='force-formula';const code=document.createElement('code'),p=document.createElement('p');code.textContent=law;p.textContent=substitution;row.append(code,p);parent.append(row);}
export function forceUI(snapshot,mode){
 if(!snapshot)return;
 for(const id of ['engineForceInlet','engineForceExhaust','engineForceRPM'])$(id).disabled=mode==='simulation';
 const hud=$('engineForceHud');hud.hidden=!snapshot.visible||!$('showMechanism').checked;
 hud.textContent='Силы · цилиндр 1: A '+f(snapshot.values[0].forces.faceA_N,0)+' Н · B '+f(snapshot.values[0].forces.faceB_N,0)+' Н · ΣFz '+f(snapshot.values[0].forces.net_Z_N,0)+' Н';
 if(!$('engineForcePanel').open)return;
 const selected=Number($('engineForceCylinder').value),v=snapshot.values[selected],{inputs:o,motion:m,forces:F,pressures:P,areas:A}=v;
 $('engineForceSource').textContent=(mode==='simulation'?'Границы и обороты взяты из текущей симуляции. ':'Давления и рабочие обороты заданы ниже; это независимый пример. ')+
  'p входа '+f(o.inlet_bar)+' бар abs; p выпуска '+f(o.exhaust_bar)+' бар abs; n = '+f(o.rpm,0)+' об/мин. '+
  (o.equalized?'При остановке без расхода принято выравнивание обеих камер с выпуском; запертый пар не отслеживается. ':'Давление каждой камеры оценено по её фазе. ')+
  'Рабочая частота для сил отличается от скорости замедленного показа. Угловое ускорение принято равным нулю.';
 $('engineForceLegend').textContent='Одинаковый линейный масштаб всех стрелок: 100 мм модели = '+f(snapshot.scale_N,0)+' Н. Нулевая сила скрыта; небольшие силы могут быть едва видны. A — оранжевый; B — голубой; вес — серый; трение — розовый; шатун — фиолетовый; направляющие — жёлтый; сумма — зелёный.';
 const tables=$('engineForceTables');tables.replaceChildren();
 for(const [i,c]of snapshot.values.entries()){
  const card=document.createElement('article'),title=document.createElement('h4'),dl=document.createElement('dl');card.className='force-card';title.textContent='Цилиндр '+(i+1)+' · '+f(c.cycle.angle_deg,0)+'°';card.append(title,dl);
  const rows=[['Камера A / B',f(c.pressures.A.pressure_Pa/1e5)+' / '+f(c.pressures.B.pressure_Pa/1e5)+' бар abs'],['A · по p − p₀',f(c.forces.faceA_N,0)+' Н'],['B · по p − p₀',f(c.forces.faceB_N,0)+' Н'],['Вес сборки',f(c.forces.gravity_N,0)+' Н'],['Трение',f(c.forces.friction_N,0)+' Н'],['Шатун · по Z',f(c.forces.rod_Z_N,0)+' Н'],['Шатун · по Y',f(c.forces.rod_Y_N,0)+' Н'],['Направляющие · по Y',f(c.forces.guide_Y_N,0)+' Н'],['ΣF по Z = ma',f(c.forces.net_Z_N,0)+' Н'],['Ускорение по Z',f(c.motion.acceleration_m_s2)+' м/с²'],['Скорость по Z',f(c.motion.velocity_m_s,3)+' м/с']];
  for(const [name,value]of rows){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=name;dd.textContent=value;dl.append(dt,dd);}tables.append(card);
 }
 const formulas=$('engineForceFormulas');formulas.replaceChildren();
 if(!$('engineForceCalculation').open)return;
 formula(formulas,'Aₐ = πD²/4; Aᵦ = π(D² − d²)/4','D = 0,100 м; d = 0,024 м → Aₐ = '+f(A.A_m2,6)+' м²; Aᵦ = '+f(A.B_m2,6)+' м².');
 for(const ch of ['A','B']){const p=P[ch];
  if(['expansion','compression'].includes(p.law))formula(formulas,ch+': pVᵏ = const → p = pᵣ(Vᵣ/V)ᵏ',f(p.reference_Pa,0)+' × ('+f(p.reference_m3,8)+' / '+f(p.volume_m3,8)+')^'+f(o.polytropic)+' = '+f(p.pressure_Pa,0)+' Па = '+f(p.pressure_Pa/1e5)+' бар abs.');
  else formula(formulas,ch+': p ≈ p впуска или выпуска',ch+' → '+f(p.pressure_Pa,0)+' Па; '+({admission:'клапан впуска открыт',release:'клапан выпуска открыт',exhaust:'клапан выпуска открыт',equalized:'принято выравнивание с выпуском'}[p.law]||p.law)+'. Перепад на клапане не рассчитывается.');
 }
 formula(formulas,'Fₐ = −(pₐ − p₀)Aₐ; Fᵦ = +(pᵦ − p₀)Aᵦ','−('+f(P.A.pressure_Pa,0)+' − '+f(o.ambient_bar*1e5,0)+') × '+f(A.A_m2,6)+' = '+f(F.faceA_N,0)+' Н; ('+f(P.B.pressure_Pa,0)+' − '+f(o.ambient_bar*1e5,0)+') × '+f(A.B_m2,6)+' = '+f(F.faceB_N,0)+' Н.');
 formula(formulas,'F давления = −pₐAₐ + pᵦAᵦ + p₀A штока = Fₐ + Fᵦ',f(F.faceA_N,0)+' + ('+f(F.faceB_N,0)+') = '+f(F.gas_N,0)+' Н. Атмосферное давление на наружный конец штока учтено.');
 formula(formulas,'ω = 2πn/60; q = √(L² − r²sin²θ)', '2π × '+f(o.rpm,0)+' / 60 = '+f(m.omega_rad_s,3)+' рад/с; r = 0,060 м; L = 0,110 м; θ = '+f(v.cycle.angle_deg)+'° → q = '+f(m.q_m,6)+' м.');
 formula(formulas,"z′ = −r sinθ − r²sinθ cosθ/q; v = z′ω",'z′ = '+f(m.dz_m_rad,6)+' м/рад; v = '+f(m.dz_m_rad,6)+' × '+f(m.omega_rad_s,3)+' = '+f(m.velocity_m_s,3)+' м/с.');
 formula(formulas,"z″ = −r cosθ − r²(cos²θ − sin²θ)/q − r⁴sin²θ cos²θ/q³; a = z″ω² + z′α",'z″ = '+f(m.ddz_m_rad2,6)+' м/рад²; α = 0 → a = '+f(m.ddz_m_rad2,6)+' × '+f(m.omega_rad_s,3)+'² = '+f(m.acceleration_m_s2)+' м/с².');
 formula(formulas,'F веса = −mg; F трения = −F₀ sign(v)', '−'+f(o.mass_kg)+' × 9,81 = '+f(F.gravity_N,1)+' Н; −'+f(o.friction_N,0)+' × sign('+f(m.velocity_m_s,3)+') = '+f(F.friction_N,0)+' Н. При v = 0 принято F трения = 0; трение покоя не определено.');
 formula(formulas,'ΣFz = Fₐ + Fᵦ + F веса + F трения + F шатуна,z = ma',f(F.faceA_N,0)+' + ('+f(F.faceB_N,0)+') + ('+f(F.gravity_N,1)+') + ('+f(F.friction_N,0)+') + ('+f(F.rod_Z_N,0)+') ≈ '+f(o.mass_kg)+' × '+f(m.acceleration_m_s2)+' = '+f(F.ma_N,0)+' Н.');
 formula(formulas,'F шатуна,y = −F шатуна,z · r sinθ/q; R направляющих,y = −F шатуна,y', '−('+f(F.rod_Z_N,0)+') × 0,060 × sin('+f(v.cycle.angle_deg)+'°) / '+f(m.q_m,6)+' = '+f(F.rod_Y_N,0)+' Н; R = '+f(F.guide_Y_N,0)+' Н. Боковая сила действует на крейцкопф.');
}
