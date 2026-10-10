import {distributionState} from './engine-distribution-model.js';
const fmt=x=>x.toLocaleString('ru-RU',{maximumFractionDigits:1});
let previous='',last=0;
function diagram(){return `<svg style="display:block;width:100%;height:auto" viewBox="0 0 900 430" role="img" aria-label="Четыре клапана: P к A, A к T, P к B, B к T"><style>
.dist-pipe{fill:none;stroke:#778997;stroke-width:8;stroke-linejoin:round}.dist-pipe[data-open="true"]{stroke:#ffe3b0;stroke-dasharray:13 9;animation:dist-flow .8s linear infinite}.dist-pipe[data-open="true"][data-kind="exhaust"]{stroke:#a5d0e6}.dist-gate{fill:#df746a;stroke:#243640;stroke-width:3}.dist-gate[data-open="true"]{fill:#83d294}text{fill:currentColor;font-size:17px}.dist-caption{font-size:15px}@keyframes dist-flow{to{stroke-dashoffset:-44}}@media(prefers-reduced-motion:reduce){.dist-pipe{animation:none!important}}
</style><text x="450" y="27" text-anchor="middle">P · свежий пар от генератора</text>
<path class="dist-pipe" d="M450 38V72H210 M450 72H690"/>
<path class="dist-pipe" data-edge="PA" data-kind="inlet" d="M210 72V220H300"/><path class="dist-pipe" data-edge="PB" data-kind="inlet" d="M690 72V220H600"/>
<path class="dist-pipe" data-edge="AT" data-kind="exhaust" d="M300 220H210V365H450V385"/><path class="dist-pipe" data-edge="BT" data-kind="exhaust" d="M600 220H690V365H450V385"/>
<rect x="300" y="170" width="300" height="100" rx="12" fill="none" stroke="currentColor" stroke-width="3"/>
<rect x="300" y="175" width="145" height="90" fill="#ffe3b0" opacity=".2" data-fluid="A"/><rect x="455" y="175" width="145" height="90" fill="#a5d0e6" opacity=".2" data-fluid="B"/>
<path data-rod="" d="M455 220H635" stroke="#bca281" stroke-width="12"/><rect data-piston="" x="445" y="173" width="10" height="94" fill="#d9a275"/>
<text x="335" y="155">A · без штока</text><text x="485" y="155">B · со штоком</text>
${[['PA',210,125,'P→A · впуск A',100],['PB',690,125,'P→B · впуск B',705],['AT',210,310,'A→T · выпуск A',100],['BT',690,310,'B→T · выпуск B',705]].map(([id,x,y,label,tx])=>`<circle class="dist-gate" data-gate="${id}" cx="${x}" cy="${y}" r="13"/><text class="dist-caption" x="${tx}" y="${y-22}" text-anchor="${tx===100?'middle':'start'}">${label}</text>`).join('')}
<text x="450" y="415" text-anchor="middle">T · выпуск к конденсатору → вода возвращается в генератор</text></svg>`;}
export function updateDistributionUI(engine,states,time,playing){
 const host=document.getElementById('engineDistributionDiagram');if(!host)return;
 if(!host.firstElementChild){host.innerHTML=diagram();const dialog=document.getElementById('engineDistributionDialog'),live=document.getElementById('engineDistributionLive');document.getElementById('engineDistributionEnlarge').addEventListener('click',()=>{document.getElementById('engineDistributionDialogSlot').append(live);dialog.showModal();});document.getElementById('engineDistributionClose').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>document.getElementById('engineDistributionCanvas').append(live));}
 const selector=document.getElementById('engineCylinderInspect'),index=Math.max(0,Number(selector.value)),pose=states[index],state=distributionState(pose);
 const key=engine.config.bore+':'+index+':'+state.valves.map(v=>Number(v.open)).join('')+':'+playing;
 host.querySelectorAll('.dist-pipe').forEach(n=>n.style.animationPlayState=playing?'running':'paused');
 const min=pose.A.cylinder_volume_cm3/(Math.PI*engine.config.bore**2/4/1000),fraction=Math.min(1,Math.max(0,(min-engine.config.clearance)/engine.config.stroke)),x=310+270*fraction;
 host.querySelector('[data-piston]').setAttribute('x',x-5);host.querySelector('[data-rod]').setAttribute('d',`M${x} 220H635`);
 for(const [ch,start,width]of [['A',300,x-305],['B',x+5,595-x]]){const n=host.querySelector(`[data-fluid="${ch}"]`);n.setAttribute('x',start);n.setAttribute('width',Math.max(0,width));n.setAttribute('fill',pose[ch].exhaust?'#a5d0e6':'#ffe3b0');}
 if(previous!==key){previous=key;for(const v of state.valves){host.querySelector(`[data-edge="${v.id}"]`).dataset.open=String(v.open);host.querySelector(`[data-gate="${v.id}"]`).dataset.open=String(v.open);}
  document.getElementById('engineValveStates').textContent=`Цилиндр ${index+1}: `+state.valves.map(v=>`${v.id} ${v.open?'открыт':'закрыт'}`).join(' · ')+`. ${state.valid?'Прямого прохода P→T нет.':'ОШИБКА: подача сообщается с выпуском.'}`;
 }
 if(time-last>.15||previous!==key){last=time;const lines=['A','B'].map(ch=>{const c=pose[ch],r=engine.routes.find(r=>r.index===index&&r.chamber===ch);return `${ch}: π × ${r.spec.inside_mm}² × ${fmt(r.length_mm)} / 4000 = ${fmt(c.connection_volume_cm3)} см³ в трубке; цилиндр ${fmt(c.cylinder_volume_cm3)} + трубка ${fmt(c.connection_volume_cm3)} = ≥${fmt(c.volume_cm3)} см³`;});
  document.getElementById('engineConnectionVolumes').textContent=lines.join('; ')+'. Это соединённый объём до клапана; внутренние полости арматуры ещё не учтены.';
 }
}
