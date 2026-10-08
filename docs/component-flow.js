import * as T from 'three';
// Additional overlays follow the actual constructor curves and hollow nozzle meshes.
// Properties outside userData are runtime-only and never enter manufacturing exports.
export function componentFlowPaths(models){
 const paths=[],ends=new Map();
 for(const m of models.values())for(const [i,p]of (m.routeSpec?.end_ports||[]).entries())ends.set(p.id,{physicsId:m.id,fluid:m.routeSpec.fluid,reverse:i===1});
 for(const m of models.values())m.root.traverse(node=>{
  for(const path of node.flowPaths||[])paths.push({...path,id:m.id+'.'+path.id,owner:m.id,target:node});
  if(node.geometry?.type!=='LatheGeometry'&&!(node.geometry?.type==='CylinderGeometry'&&/Газовая рампа|Вентиль баллона/.test(node.name)))return;
  let config;
  if(node.name.startsWith('Полый патрубок'))config=ends.get(node.userData.portId)|| (node.userData.portId==='CND.pumpIn'?{physicsId:'PIPE_RETURN',fluid:'water'}:null);
  else if(node.userData.inlineComponent)config={physicsId:'PIPE_SUCTION',fluid:'water'};
  else if(node.name.startsWith('Конденсатный насос'))config={physicsId:'PIPE_RETURN',fluid:'water'};
  else if(/Головка|Патрубок горячих газов|Сопряжение источника с камерой/.test(node.name))config={physicsId:'PIPE_FLUE',fluid:'flue'};
  else if(/Газовая рампа|Вентиль баллона/.test(node.name))config={physicsId:'PIPE_FUEL',fluid:'fuel'};
  else if(node.name.startsWith('Проходной корпус дымососа'))config={physicsId:'PIPE_FLUE',fluid:'flue'};
  if(!config)return;
  const parameters=node.geometry.parameters,profile=parameters.points||[new T.Vector2(parameters.radiusBottom,-parameters.height/2),new T.Vector2(parameters.radiusTop,parameters.height/2)],a=Math.min(...profile.map(p=>p.y)),b=Math.max(...profile.map(p=>p.y));
  const start=new T.Vector3(0,config.reverse?b:a,0),end=new T.Vector3(0,config.reverse?a:b,0);
  const ra=Math.max(...profile.filter(p=>p.y===a).map(p=>p.x)),rb=Math.max(...profile.filter(p=>p.y===b).map(p=>p.x)),insulator=node.name.startsWith('Сопряжение источника')?node.parent.children.find(o=>o.name==='Изоляция рукава · 25 мм'):null;
  const radiusAt=d=>insulator?.visible?Math.max(...insulator.geometry.parameters.points.map(p=>p.x)):ra+(rb-ra)*(config.reverse?1-d/(b-a):d/(b-a));
  paths.push({...config,radiusAt,id:'LOCAL.'+m.id+'.'+(node.userData.portId||node.name),owner:m.id,target:node,curve:new T.LineCurve3(start,end),radius:Math.max(...profile.map(p=>p.x))});
 });
 return paths;
}
export function objectVisible(node){for(let o=node;o;o=o.parent)if(!o.visible)return false;return true;}
