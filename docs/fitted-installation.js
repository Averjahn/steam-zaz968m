import * as T from 'three';
import {connectionSpecs} from './connection-data.js?v=f9e176aa78c5';
import {pipeRoutes} from './pipe-data.js?v=140c14a4b388';
import {pipeCurve} from './pipe-path.js?v=0b785b2d508c';
import {hollowBox,hollowTube} from './pipe-joints.js?v=783013dea290';
export function fittedOrigin(bore){return [2980+230*bore/32,0,490];}
const port=(id,owner,p,n,bore,od)=>({id,owner,anchor_mm:p,face_mm:p,outward:n,bore_mm:bore,od_mm:od,kind:'concept-weld-neck',basis:'Проектный интерфейс; прочность и герметичность не подтверждены'});
export function fittedRoutes(origin){
 const [x]=origin,ep=x-260,h=port('EXHAUST_HEADER.in','EXHAUST_HEADER',[x,-305,660],[0,1,0],40,46);
 const replacements={
 PIPE_STEAM:{points:[[2630,335,1180],[ep-180,335,1180],[ep-180,335,940],[ep-180,-300,940],[ep-180,-300,735],[ep-180,0,735],[ep,0,735]],end_ports:[pipeRoutes.find(r=>r.id==='PIPE_STEAM').end_ports[0],port('ENG.inlet','ENG',[ep,0,735],[-1,0,0],40,48)]},
 PIPE_EXHAUST_R:{points:[[x+55,-335,660],[3430,-335,660],[3600,-335,520],[3600,-80,520],[3600,-80,850],[3330,-80,850],[3330,-200,850],[3330,-285,765],[3330,-315,765]],end_ports:[port('EXHAUST_HEADER.right','EXHAUST_HEADER',[x+55,-335,660],[1,0,0],40,46),port('CND.reducerR','CND',[3330,-315,765],[0,1,0],40,46)],od:46,inside_id_mm:40,wall_mm:3,insulation_mm:12.5,jacket_mm:.5,outer_envelope_mm:72,bend_radius_mm:70},
 PIPE_EXHAUST_L:{points:[[x-55,-335,660],[2960,-335,660],[2960,-335,850],[2960,200,850],[3350,200,850],[3350,285,765],[3350,315,765]],end_ports:[port('EXHAUST_HEADER.left','EXHAUST_HEADER',[x-55,-335,660],[-1,0,0],40,46),port('CND.reducerL','CND',[3350,315,765],[0,-1,0],40,46)],od:46,inside_id_mm:40,wall_mm:3,insulation_mm:12.5,jacket_mm:.5,outer_envelope_mm:72,bend_radius_mm:70}};
 const all=pipeRoutes.map(r=>{if(!replacements[r.id])return r;const n={...r,...replacements[r.id],inline_components:[],exposed_end_mm:12,connected:true};n.ends=n.end_ports.map(p=>p.id);const cuts=n.points.map(()=>0);for(let i=1;i<n.points.length-1;i++){const u=new T.Vector3(...n.points[i]).sub(new T.Vector3(...n.points[i-1])).normalize(),v=new T.Vector3(...n.points[i+1]).sub(new T.Vector3(...n.points[i])).normalize();cuts[i]=n.bend_radius_mm*Math.tan(Math.acos(T.MathUtils.clamp(u.dot(v),-1,1))/2);}n.bend_violations=[];for(let i=1;i<n.points.length;i++)if(cuts[i]+cuts[i-1]>new T.Vector3(...n.points[i]).distanceTo(new T.Vector3(...n.points[i-1]))+.001)n.bend_violations.push('Слишком короткий участок '+i);n.geometry_valid=n.bend_violations.length===0;if(!n.geometry_valid)throw Error(n.id+': '+n.bend_violations.join(', '));n.centerline_length_m=pipeCurve(n).getLength()/1000;return n;});
 all.push({...all.find(r=>r.id==='PIPE_EXHAUST_R'),id:'PIPE_EXHAUST_COMMON',name:'Общий выпуск семицилиндровой звезды',points:[[x,-230,660],[x,-305,660]],end_ports:[port('ENG.exhaust','ENG',[x,-230,660],[0,-1,0],40,46),h],ends:['ENG.exhaust','EXHAUST_HEADER.in'],inline_components:[],geometry_valid:true,centerline_length_m:.075,bends:[],bend_violations:[]});
 return all;
}
export function fittedCondenserPorts(){return Object.values(connectionSpecs.variants.diesel.ports).filter(p=>p.owner==='CND').map(p=>p.id==='CND.inletL'?{...p,anchor_mm:[3350,...p.anchor_mm.slice(1)],face_mm:[3350,...p.face_mm.slice(1)]}:p);}
export function fittedInterfaces(origin){
 const [x]=origin,g=new T.Group();g.name='Разделение выпуска и переходы к двум конденсаторам';
 const ports=[port('in','EXHAUST_HEADER',[x,-305,660],[0,1,0],40,46),port('right','EXHAUST_HEADER',[x+55,-335,660],[1,0,0],40,46),port('left','EXHAUST_HEADER',[x-55,-335,660],[-1,0,0],40,46)];
 const m=new T.MeshStandardMaterial({color:'#a6b5c0',metalness:.7,roughness:.4,side:T.DoubleSide});
 hollowBox(g,'Полый делитель выпуска · стенка4 мм',[x-55,-365,630],[110,60,60],m,ports);
 for(const [side,px,py,sign]of [['R',3330,-315,-1],['L',3350,315,1]])hollowTube(g,'Переход к конденсатору '+side+' · ID40→70',[px,py,765],[px,py+50*sign,765],80,70,{entry_od_mm:46,entry_bore_mm:40});
 return {id:'EXHAUST_HEADER',name:'Делитель выпуска · два конденсатора',content:g,xyz:[0,0,0],connections:['ENG.exhaust','PIPE_EXHAUST_R','PIPE_EXHAUST_L','CND.inletR','CND.inletL'],source:'Проектный делитель 110×60×60; два перехода ID40→70. Теплоизоляция, нагрузка и давление требуют проверки.'};
}
