import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFExporter} from 'three/addons/exporters/GLTFExporter.js';
import {radialGeometry as K,radialPose,displacement,gearPolygon} from './radial-engine-model.js?v=7f88549d47ae';
import {pipeCurve} from './pipe-path.js?v=0b785b2d508c';
import {pipeArrows} from './pipe-arrows.js?v=dd3bd35c3fcf';
const $=id=>document.getElementById(id),fmt=(x,n=2)=>x.toLocaleString('ru-RU',{maximumFractionDigits:n,minimumFractionDigits:n});
const scene=new T.Scene();scene.background=new T.Color('#0b1117');
const camera=new T.PerspectiveCamera(40,1,1,10000);camera.up.set(0,0,1);
const renderer=new T.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
$('radialViewport').append(renderer.domElement);$('radialFallback').hidden=true;
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.rotateSpeed=-1;
scene.add(new T.HemisphereLight(0xddeaff,0x334155,2));for(const p of [[500,-500,1500],[-700,800,900]]){const light=new T.DirectionalLight(0xffffff,2);light.position.set(...p);scene.add(light);}
const root=new T.Group();root.name='Семицилиндровая паровая звезда · проектная геометрия в мм';scene.add(root);
const material=(color,opacity=1)=>new T.MeshStandardMaterial({color,roughness:.45,metalness:.55,transparent:opacity<1,opacity,depthWrite:opacity===1});
const steel=material('#869aa8'),dark=material('#334956'),brass=material('#d0ab65'),orange=material('#f79445'),steam=material('#fff2d4',.15),exhaust=material('#a9cbea',.15);
const V=a=>new T.Vector3(...a),zaxis=new T.Vector3(0,0,1);
function mesh(parent,name,geometry,mat){const o=new T.Mesh(geometry,mat);o.name=name;parent.add(o);return o;}
function bar(parent,name,a,b,r,mat=steel){const d=V(b).sub(V(a)),o=mesh(parent,name,new T.CylinderGeometry(r,r,d.length(),16),mat);o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());return o;}
function beam(parent,name,a,b,width=20,height=10,mat=dark){const d=V(b).sub(V(a)),o=mesh(parent,name,new T.BoxGeometry(d.length(),width,height),mat);o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.rotation.z=Math.atan2(d.y,d.x);return o;}
function ring(parent,name,point,normal,inner,outer,depth,mat=steel,holes=[]){const shape=new T.Shape();shape.absarc(0,0,outer,0,Math.PI*2,false);const h=new T.Path();h.absarc(0,0,inner,0,Math.PI*2,true);shape.holes.push(h);for(const [x,y,r]of holes){const port=new T.Path();port.absarc(x,y,r,0,Math.PI*2,true);shape.holes.push(port);}const o=mesh(parent,name,new T.ExtrudeGeometry(shape,{depth,bevelEnabled:false,curveSegments:36}),mat);o.position.copy(V(point));o.quaternion.setFromUnitVectors(zaxis,V(normal));return o;}
function gear(parent,name,teeth,x=0,y=0){const shape=new T.Shape(gearPolygon(teeth).map(p=>new T.Vector2(...p))),hole=new T.Path();hole.absarc(0,0,18,0,Math.PI*2,true);shape.holes.push(hole);const o=mesh(parent,name,new T.ExtrudeGeometry(shape,{depth:12,bevelEnabled:false}),steel);o.position.set(x,y,-6);return o;}
function label(parent,text,point){const c=document.createElement('canvas');c.width=256;c.height=96;const ctx=c.getContext('2d');ctx.fillStyle='#132330e8';ctx.fillRect(0,0,256,96);ctx.font='bold 48px sans-serif';ctx.fillStyle='#ffffff';ctx.textAlign='center';ctx.fillText(text,128,66);const sprite=new T.Sprite(new T.SpriteMaterial({map:new T.CanvasTexture(c),depthTest:false}));sprite.position.copy(V(point));sprite.scale.set(90,34,1);sprite.userData.viewOnly=true;parent.add(sprite);return sprite;}
const central=gear(root,'Центральная шестерня · 56 зубьев',56);
bar(root,'Выходной вал · ось Z',[0,0,-40],[0,0,125],17,dark);ring(root,'Выходная муфта',[0,0,90],[0,0,1],17,36,22,brass);
ring(root,'Коренная опора выхода',[0,0,-30],[0,0,1],17.5,40,20,brass);for(let i=0;i<4;i++){const a=i*Math.PI/2;beam(root,'Перемычка опоры выхода',[35*Math.cos(a),35*Math.sin(a),-24],[80*Math.cos(a),80*Math.sin(a),-24],22,12,dark);}
ring(root,'Несущая центральная рама',[0,0,-30],[0,0,1],55,235,12,dark);
const manifoldSteam=mesh(root,'Верхний коллектор свежего пара',new T.TorusGeometry(K.inletRadius,9,12,144),brass);manifoldSteam.position.z=K.inletZ;
const manifoldReturn=mesh(root,'Общий выпуск к конденсатору',new T.TorusGeometry(K.returnRadius,12,12,144),steel);manifoldReturn.position.z=K.returnZ;
const cylinders=[],routes=[];
function addPipe(parent,name,points,role='chamber',chamber=null,index=null,fluid='steam',radius=6){
 const curve=pipeCurve({points,geometry_valid:true,bend_radius_mm:8});
 const tube=mesh(parent,name,new T.TubeGeometry(curve,Math.max(12,Math.ceil(curve.getLength()/12)),radius,12,false),fluid==='steam'?brass:steel);
 const arrows=pipeArrows(curve,{id:name,fluid});parent.add(arrows.group);
 const rec={tube,arrows,role,chamber,index,radius,parent,curve};routes.push(rec);return rec;
}
// Supply/return are explicit boundaries to the rest of the closed water circuit.
addPipe(root,'От перегревателя → общий впуск',[[0,0,280],[0,0,210],[470,0,210],[470,0,180]],'supply',null,null,'steam',9);
addPipe(root,'Общий выпуск → конденсатор',[[-445,0,140],[-750,0,140]],'return',null,null,'exhaust',12);
for(let i=0;i<K.count;i++){
 const pose=radialPose(i,0),a=pose.alpha,u=[Math.cos(a),Math.sin(a)],v=[-u[1],u[0]],g=new T.Group();g.name='Цилиндр '+(i+1)+' · двойное действие';g.userData.index=i;root.add(g);
 const at=(r,z=K.axisZ,t=0)=>[u[0]*r+v[0]*t,u[1]*r+v[1]*t,z];
 const localGear=gear(g,'Шестерня цилиндра '+(i+1)+' · 28 зубьев',28,...pose.axis.slice(0,2));
 bar(g,'Коренной вал кривошипа',at(210,-28),at(210,30),15,dark);ring(g,'Коренная опора на раме',at(210,-26),[0,0,1],15.5,32,12,brass);
 const crank=new T.Group();crank.name='Кривошип · r60';crank.position.set(...at(210,25));g.add(crank);
 beam(crank,'Щека кривошипа',[0,0,0],[60,0,0],25,8,orange);bar(crank,'Эксцентричная шейка',[60,0,4],[60,0,25],10,brass);
 const rod=beam(g,'Шатун · межосевое 190 мм',pose.pin,pose.crosshead,22,10);
 const eyeBig=ring(g,'Головка шатуна',pose.pin,[0,0,1],10.5,20,10,dark),eyeSmall=ring(g,'Поршневой палец',pose.crosshead,[0,0,1],6.5,15,10,dark);
 const crosshead=mesh(g,'Крейцкопф',new T.BoxGeometry(35,35,25),steel);crosshead.rotation.z=a;bar(crosshead,'Палец крейцкопфа',[0,0,-13],[0,0,13],6,brass);
 for(const t of [-24,24])beam(g,'Направляющая крейцкопфа',at(315,32,t),at(480,32,t),9,35,dark);
 beam(g,'Опора цилиндра на радиальную раму',at(225,-25),at(685,-25),48,12,dark);
 for(const r of [520,645]){beam(g,'Лапа цилиндра',at(r,-12,-70),at(r,-12,70),28,20,steel);for(const t of [-55,55])bar(g,'Болт крепления лапы',at(r,-20,t),at(r,2,t),5,brass);}
 const bodyMaterial=material('#b9d2e2',.18);
 const shell=ring(g,'Гильза · внутренний Ø100 мм',at(508),[...u,0],50,60,144,bodyMaterial);
 const normal=[...u,0],inverse=new T.Quaternion().setFromUnitVectors(zaxis,V(normal)).invert(),offB=V([v[0]*35,v[1]*35,0]).applyQuaternion(inverse),offA=V([v[0]*-12,v[1]*-12,0]).applyQuaternion(inverse);
 ring(g,'Штоковая крышка B с отдельным паровым портом',at(506),normal,12.3,67,2,steel,[[offB.x,offB.y,4.5]]);
 const capShape=new T.Shape();capShape.absarc(0,0,67,0,Math.PI*2,false);const capHole=new T.Path();capHole.absarc(offA.x,offA.y,4.5,0,Math.PI*2,true);capShape.holes.push(capHole);const cap=mesh(g,'Наружная крышка A с паровым портом',new T.ExtrudeGeometry(capShape,{depth:8,bevelEnabled:false,curveSegments:36}),steel);cap.position.copy(V(at(652)));cap.quaternion.setFromUnitVectors(zaxis,V(normal));
 const piston=bar(g,'Поршень Ø100 мм',at(pose.pistonRadius-10),at(pose.pistonRadius+10),49.5,orange);
 const pistonRod=bar(g,'Шток Ø24 мм',pose.crosshead,pose.piston,12,brass);
 const A=bar(g,'Пар в камере A',at(641),at(650),49.4,steam.clone()),B=ring(g,'Пар в камере B · кольцевой объём',at(508),[...u,0],12.3,49.4,119,exhaust.clone());
 const valve=mesh(g,'Распределительный клапан · принципиальная коробка',new T.BoxGeometry(50,48,60),dark);valve.position.set(...at(710,140));valve.rotation.z=a;
 const inlet=addPipe(g,'Впуск цилиндра '+(i+1),[at(470,180),at(710,180),at(710,170)],'inlet',null,i);
 const outlet=addPipe(g,'Выпуск цилиндра '+(i+1),[at(710,110),at(710,92),at(755,92),at(755,215),at(445,215),at(445,140)],'outlet',null,i,'exhaust');
 // Separate chamber pipes; flow direction reverses at the distributing valve.
 const pipeA=addPipe(g,'Камера '+(i+1)+'A',[at(685,145,-12),at(675,145,-12),at(675,45,-12),at(660,45,-12)],'chamber','A',i);
 const pipeB=addPipe(g,'Камера '+(i+1)+'B',[at(685,125,12),at(490,125,12),at(490,45,12),at(490,45,35),at(506,45,35)],'chamber','B',i);
 // Ports terminate in the separate end covers so the piston never switches their chamber.
 ring(g,'Соединение трубы камеры A',at(660,45,-12),normal,4.5,10,3,steel);ring(g,'Соединение трубы камеры B',at(506,45,35),u.map(x=>-x).concat(0),4.5,10,3,steel);
 label(g,String(i+1),at(640,235));
 cylinders.push({g,shell,bodyMaterial,localGear,crank,rod,eyeBig,eyeSmall,crosshead,piston,pistonRod,A,B,u,at,inlet,outlet,pipeA,pipeB});
}
const reserve=new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(...K.reserve)),new T.LineBasicMaterial({color:0xb7ef74,depthTest:false,transparent:true,opacity:.8}));reserve.position.z=210;reserve.name='Прежний проектный резерв 600×500×500';reserve.userData.viewOnly=true;scene.add(reserve);
for(let i=0;i<7;i++){const o=document.createElement('option');o.value=i;o.textContent='Цилиндр '+(i+1);$('radialCylinder').append(o);}
let outputAngle=0,flowTime=0,playing=true,last=performance.now(),lastUI=0,states=[],count=7,cutoff=.3,selected=0;
function setBar(o,a,b){const d=V(b).sub(V(a));o.position.copy(V(a).add(V(b)).multiplyScalar(.5));const height=o.geometry.parameters.height;o.scale.y=d.length()/height;o.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),d.normalize());}
function setBeam(o,a,b){const d=V(b).sub(V(a));o.position.copy(V(a).add(V(b)).multiplyScalar(.5));o.scale.x=d.length()/o.geometry.parameters.width;o.rotation.z=Math.atan2(d.y,d.x);}
function renderPose(){
 central.rotation.z=outputAngle;states=cylinders.map((c,i)=>radialPose(i,outputAngle,cutoff));
 cylinders.forEach((c,i)=>{const p=states[i];c.g.visible=i<count;c.localGear.rotation.z=p.gearAngle;c.crank.rotation.z=p.pinAngle;c.crosshead.position.copy(V(p.crosshead));setBeam(c.rod,p.pin,p.crosshead);c.eyeBig.position.set(...p.pin);c.eyeBig.position.z-=5;c.eyeSmall.position.set(...p.crosshead);c.eyeSmall.position.z-=5;
 setBar(c.piston,c.at(p.pistonRadius-10),c.at(p.pistonRadius+10));setBar(c.pistonRod,p.crosshead,p.piston);
 setBar(c.A,c.at(p.pistonRadius+10),c.at(652));c.B.scale.z=(p.pistonRadius-10-508)/119;
 c.A.material.color.set(p.A.inlet?'#fff1d2':p.A.exhaust?'#8bbfdf':'#d5ae7e');c.B.material.color.set(p.B.inlet?'#fff1d2':p.B.exhaust?'#8bbfdf':'#d5ae7e');
 });
 for(const route of routes){const p=route.index===null?null:states[route.index],ch=route.chamber?p[route.chamber]:null,active=route.role==='inlet'?(p.A.inlet||p.B.inlet):route.role==='outlet'?(p.A.exhaust||p.B.exhaust):ch?(ch.inlet||ch.exhaust):true;
 route.arrows.update({camera,radius:route.radius,phase:flowTime*.35,visible:active&&(route.index===null||route.index<count),direction:ch?.exhaust?-1:1,color:ch?.exhaust?'#a9cbea':route.role==='return'||route.role==='outlet'?'#a9cbea':'#fff2d4'});
 }
 reserve.visible=$('radialReserve').checked;
}
$('radialCutaway').onchange=()=>{for(const c of cylinders){c.bodyMaterial.opacity=$('radialCutaway').checked?.18:1;c.bodyMaterial.transparent=$('radialCutaway').checked;c.bodyMaterial.depthWrite=!$('radialCutaway').checked;c.bodyMaterial.needsUpdate=true;}renderPose();};$('radialReserve').onchange=renderPose;
const phaseName={admission:'впуск',expansion:'закрытое расширение',release:'открытие выпуска',exhaust:'выпуск'};
function status(){const p=states[selected];$('radialStatus').textContent=`Вал ${fmt(outputAngle*180/Math.PI%360,1)}° · цилиндр ${selected+1}, кривошип ${fmt(p.phase*180/Math.PI,1)}° · A: ${phaseName[p.A.phase]}, ${fmt(p.A.volume_cm3,0)} см³ · B: ${phaseName[p.B.phase]}, ${fmt(p.B.volume_cm3,0)} см³`;$('radialAngle').value=String((outputAngle*180/Math.PI%360+360)%360);}
function home(top=false){controls.target.set(0,0,70);camera.position.set(...(top?[0,0,2400]:[1400,-1700,1700]));controls.update();}
home();new ResizeObserver(()=>{const w=$('radialViewport').clientWidth,h=$('radialViewport').clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}).observe($('radialViewport'));
function select(i){selected=i;$('radialCylinder').value=String(i);status();}
$('radialPlay').onclick=()=>{playing=!playing;$('radialPlay').textContent=playing?'Пауза':'Воспроизвести';$('radialPlay').setAttribute('aria-pressed',String(playing));};
$('radialAngle').oninput=()=>{playing=false;$('radialPlay').textContent='Воспроизвести';$('radialPlay').setAttribute('aria-pressed','false');outputAngle=Number($('radialAngle').value)*Math.PI/180;renderPose();status();};
$('radialTop').onclick=()=>home(true);$('radialIso').onclick=()=>home(false);$('radialCylinder').onchange=()=>select(Number($('radialCylinder').value));
const ray=new T.Raycaster();renderer.domElement.ondblclick=e=>{const rect=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new T.Vector2(2*(e.clientX-rect.left)/rect.width-1,1-2*(e.clientY-rect.top)/rect.height),camera);for(const hit of ray.intersectObject(root,true)){let o=hit.object;while(o&&o.userData.index===undefined)o=o.parent;if(o&&o.userData.index<count){select(o.userData.index);break;}}};
const card=(title,formula,substitution,result)=>`<article class="radial-formula"><h3>${title}</h3><p class="expression">${formula}</p><p class="expression">${substitution}</p><strong>${result}</strong></article>`;
let specs=null;
function calculate(){
 const rpm=$('radialRpm').valueAsNumber,c=$('radialCutoff').valueAsNumber;if(!Number.isFinite(rpm)||rpm<0||rpm>1000||!Number.isFinite(c)||c<.05||c>1){$('radialSupply').textContent='Задайте обороты 0–1000 об/мин и отсечку 0,05–1.';return;}
 cutoff=c;const d=displacement(count,{rpm,cutoff:c,density:specs?.steam.density_kg_m3??4.299140178878613}),old=displacement(2,{rpm,cutoff:c});
 $('radialCalculations').innerHTML=[card('Один цилиндр','V₁ = πD²S / 4','π × (0,100 м)² × 0,120 м / 4',fmt(d.one_L,3)+' л'),card('Геометрический рабочий объём','V = NπD²S / 4',`${count} × π × 0,100² × 0,120 / 4 × 1000`,fmt(d.swept_L)+' л · прежний: '+fmt(old.swept_L)+' л'),card('Обе стороны за цикл поршня','Vдв = N [πD²/4 + π(D² − d²)/4] S',`${count} × [π × 0,100² / 4 + π × (0,100² − 0,024²) / 4] × 0,120 × 1000`,fmt(d.double_L)+' л/цикл'),card('Свежий пар: оценка объёма впуска','Vвп = εVдв',`${fmt(c)} × ${fmt(d.double_L,5)}`,fmt(d.admitted_L,3)+' л/цикл при входных p, T'),card('Передача и объём за оборот выхода','nвых = nкр × zмал / zцентр; Vвых = Vдв × zцентр / zмал',`${fmt(rpm,0)} × 28 / 56; ${fmt(d.double_L,5)} × 56 / 28`,fmt(d.output_rpm,0)+' об/мин · '+fmt(d.double_L_per_output_turn)+' л/оборот выхода'),card('Расход пара: гипотеза заполнения','ṁ = ρ × Vвп × nкр / 60',`4,29914 × ${fmt(d.admitted_L/1000,6)} × ${fmt(rpm,0)} / 60 × 3600`,fmt(d.mass_kg_h,1)+' кг/ч'),card('Полезное тепло генератора','Q̇ = ṁ × (hвх − hпит)',`${fmt(d.mass_kg_h/3600,5)} × (2943,122 − 251,332)`,fmt(d.heat_kW,1)+' кВт → вода/пар')].join('');
 const limitedRpm=d.heat_kW>0?rpm*50/d.heat_kW:0;
 $('radialSupply').textContent=`При ${fmt(rpm,0)} об/мин кривошипов и отсечке ${fmt(c*100,0)}% оценка: ${fmt(d.mass_kg_h,1)} кг/ч пара и ${fmt(d.heat_kW,1)} кВт тепла в воде/паре. Прежняя сравнительная подача 50 кВт покрывает такую идеализированную потребность примерно до ${fmt(limitedRpm,0)} об/мин кривошипов при той же отсечке. Это предел по подаче, а не предсказание рабочих оборотов или мощности автомобиля.`;
}
$('radialRpm').oninput=calculate;$('radialCutoff').oninput=calculate;
$('radialVariant').onchange=()=>{count=Number($('radialVariant').value);[...$('radialCylinder').options].forEach((o,i)=>o.hidden=i>=count);if(selected>=count)select(0);calculate();renderPose();showFit();};
function showFit(){root.updateMatrixWorld(true);const box=new T.Box3();root.traverse(o=>{if(o.isMesh&&o.visible&&o.ancestorsVisible!==false){let p=o.parent;while(p&&p.visible)p=p.parent;if(p===null){o.geometry.computeBoundingBox();box.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));}}});const size=box.getSize(new T.Vector3());$('radialFit').textContent=`Текущий видимый габарит с коллекторами и граничными патрубками: ${fmt(size.x,0)} × ${fmt(size.y,0)} × ${fmt(size.z,0)} мм; резерв двигателя — 600 × 500 × 500 мм. Вариант ${count===7?'семи':'двух'} цилиндров с этой радиальной передачей превышает резерв в горизонтальной плоскости. Масштабирование до размера рамки изменило бы выбранные цилиндры и ход, поэтому модель не уменьшена.`;}
let fallbackFull=false;const viewer=$('radialViewer');
function syncFullscreen(){const active=document.fullscreenElement===viewer||fallbackFull;viewer.classList.toggle('radial-expanded',fallbackFull);document.body.classList.toggle('radial-fullscreen',fallbackFull);$('radialFullscreen').textContent=active?'Выйти из полного экрана':'На весь экран';$('radialFullscreen').setAttribute('aria-pressed',String(active));}
$('radialFullscreen').onclick=async()=>{if(fallbackFull){fallbackFull=false;}else if(document.fullscreenElement===viewer)await document.exitFullscreen();else{try{await viewer.requestFullscreen();}catch{fallbackFull=true;}}syncFullscreen();};document.addEventListener('fullscreenchange',syncFullscreen);document.addEventListener('keydown',e=>{if(e.key==='Escape'&&fallbackFull){fallbackFull=false;syncFullscreen();}});
$('radialExport').onclick=async()=>{const button=$('radialExport');button.disabled=true;try{const copy=root.clone(true),excluded=[];copy.traverse(o=>{if(o.userData.viewOnly||o.isSprite)excluded.push(o);});excluded.forEach(o=>o.removeFromParent());const data=await new GLTFExporter().parseAsync(copy,{binary:true,onlyVisible:true}),a=document.createElement('a'),url=URL.createObjectURL(new Blob([data],{type:'model/gltf-binary'}));a.href=url;a.download=`radial-steam-${count}-cylinders-mm.glb`;a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);}catch(e){$('radialStatus').textContent='Не удалось экспортировать: '+e.message;}finally{button.disabled=false;}};
fetch('radial-engine-spec.json?v=e995c0495d20').then(r=>{if(!r.ok)throw Error('Missing study parameters');return r.json();}).then(s=>{specs=s;calculate();}).catch(e=>{$('radialSupply').textContent=e.message;});
$('radialKinematics').innerHTML=[card('Равномерные оси и фазы','αᵢ = 90° + i × 360°/7; ψᵢ = i × 360°/7 − 2θ', 'i = 0…6; θ — угол выходного вала','51,43° между цилиндрами'),card('Точное положение крейцкопфа','q = r cos ψ + √(L² − r² sin² ψ)','q = 60 cos ψ + √(190² − 60² sin² ψ) мм','q = 130…250 мм → ход 120 мм'),card('Положение поршня от центра звезды','Rп = Rосей + q + Lштока','Rп = 210 + q + 180 мм','Rп = 520…640 мм'),card('Межосевое расстояние шестерён','a = m (zцентр + zмал) / 2','5 × (56 + 28) / 2','210 мм')].join('');
calculate();renderPose();showFit();status();
function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,.05);last=now;if(playing){outputAngle=(outputAngle+dt*Math.PI/15)%(Math.PI*2);flowTime+=dt;}controls.update();renderPose();if(now-lastUI>200){status();lastUI=now;}renderer.render(scene,camera);}
requestAnimationFrame(animate);
