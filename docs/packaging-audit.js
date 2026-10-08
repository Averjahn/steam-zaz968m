import * as THREE from 'three';
import { computeBoundsTree } from './vendor/three-mesh-bvh/build/index.module.js';
const round=v=>Math.round(v*10)/10;
function meshes(root){const out=[];root.traverseVisible(o=>{if(o.isMesh&&o.geometry?.attributes.position)out.push(o);});return out;}
function boxGap(a,b){return Math.hypot(...['x','y','z'].map(k=>Math.max(0,a.min[k]-b.max[k],b.min[k]-a.max[k])));}
function overlap(a,b){return ['x','y','z'].map(k=>Math.min(a.max[k],b.max[k])-Math.max(a.min[k],b.min[k]));}
const yieldFrame=()=>new Promise(r=>requestAnimationFrame(r));
export async function auditPackaging(body,parts,layout={},isCurrent=()=>true){
 body.root.updateWorldMatrix(true,true);for(const p of parts)p.root.updateWorldMatrix(true,true);
 const allParts=parts,stockMeshes=parts.filter(p=>p.retainedStock).flatMap(p=>meshes(p.root)).filter(o=>o.userData.collision!==false);parts=parts.filter(p=>!p.retainedStock);
 const wallMeshes=meshes(body.root).filter(o=>o.userData.collision!==false),cap=layout.geometry_clearance_rule_mm||30;
 const result={status:'Проверка гипотетической геометрии; не подтверждение реальной посадки',units:'mm',layout:layout.name||layout.status,geometric_screen_mm:cap,removed_body_groups:layout.removed_body_groups||[],body_surface_objects:wallMeshes.length,parts:[],component_pairs:[],limitations:['Проверяются только видимые узлы. Экранный срез не удаляет геометрию.','Расстояния измерены до сетки реконструкции, её реальная точность не установлена.','30 мм — правило геометрического просмотра, не тепловой или сервисный допуск.','Штатная КПП показана грубым габаритом; её пересечение с гипотетическим полом требует реального CAD.','Конденсатор расположен снаружи намеренно. Замкнутость корпуса и полное вложение в сплошной металл алгоритм не доказывает.'],open_issues:layout.open_issues||[]};
 result.stock_surface_objects=stockMeshes.length;result.limitations.push('Подвеска — статическая гипотеза по штатной схеме. Ход, поворот колёс, осадка под новой массой и огибающие движения не рассчитаны.');
 for(const part of parts){const pm=meshes(part.root);const hits=new Set();let closest=cap,closestNode=null;
  for(const a of wallMeshes){const abox=new THREE.Box3().setFromObject(a),worldScale=new THREE.Vector3();a.getWorldScale(worldScale);const scale=Math.abs(worldScale.x);if(Math.max(Math.abs(Math.abs(worldScale.y)-scale),Math.abs(Math.abs(worldScale.z)-scale))>1e-5)throw Error('Неравномерный масштаб кузова: расстояния не рассчитаны.');
   for(const b of pm){const bBox=new THREE.Box3().setFromObject(b),lower=boxGap(abox,bBox);if(lower>closest+1e-6)continue;
    a.geometry.boundsTree ||= computeBoundsTree.call(a.geometry,{indirect:true});b.geometry.boundsTree ||= computeBoundsTree.call(b.geometry,{indirect:true});const transform=new THREE.Matrix4().copy(a.matrixWorld).invert().multiply(b.matrixWorld);
    if(abox.intersectsBox(bBox)&&a.geometry.boundsTree.intersectsGeometry(b.geometry,transform)){hits.add(a.name);closest=0;closestNode=a.name;continue;}
    if(closest>0){const hit=a.geometry.boundsTree.closestPointToGeometry(b.geometry,transform,{},null,0,(closest+1e-5)/scale);if(hit&&hit.distance*scale<closest){closest=hit.distance*scale;closestNode=a.name;}}
   }await yieldFrame();if(!isCurrent())throw Error('Геометрия изменилась. Запустите проверку заново.');
  }
  const stockHits=new Set();let stockDistance=cap,stockNearest=null;const exclusions=[];
  for(const a of stockMeshes){if(a.userData.mechanicalInterface===part.id){exclusions.push(a.name);continue;}const abox=new THREE.Box3().setFromObject(a),worldScale=new THREE.Vector3();a.getWorldScale(worldScale);const scale=Math.abs(worldScale.x);
   if(Math.max(Math.abs(Math.abs(worldScale.y)-scale),Math.abs(Math.abs(worldScale.z)-scale))>1e-5)throw Error('Неравномерный масштаб подвески: расстояния не рассчитаны.');
   for(const b of pm){const bBox=new THREE.Box3().setFromObject(b);if(boxGap(abox,bBox)>stockDistance+1e-6)continue;
    a.geometry.boundsTree ||= computeBoundsTree.call(a.geometry,{indirect:true});b.geometry.boundsTree ||= computeBoundsTree.call(b.geometry,{indirect:true});const transform=new THREE.Matrix4().copy(a.matrixWorld).invert().multiply(b.matrixWorld);
    if(abox.intersectsBox(bBox)&&a.geometry.boundsTree.intersectsGeometry(b.geometry,transform)){stockHits.add(a.name);stockDistance=0;stockNearest=a.name;continue;}
    if(stockDistance>0){const hit=a.geometry.boundsTree.closestPointToGeometry(b.geometry,transform,{},null,0,(stockDistance+1e-5)/scale);if(hit&&hit.distance*scale<stockDistance){stockDistance=hit.distance*scale;stockNearest=a.name;}}
   }await yieldFrame();if(!isCurrent())throw Error('Геометрия изменилась. Запустите проверку заново.');
  }
  const box=new THREE.Box3().setFromObject(part.root);result.parts.push({id:part.id,name:part.name,kind:part.kind,size_mm:box.getSize(new THREE.Vector3()).toArray().map(round),min_xyz_mm:box.min.toArray().map(round),body_intersections:[...hits],nearest_body_node:closestNode,clearance_mm:round(closest),clearance_is_lower_bound:closest>=cap-1e-6,intentionally_external:part.id==='CND',fixed_proxy:part.id==='GBX',stock_intersections:[...stockHits],nearest_stock_node:stockNearest,stock_clearance_mm:round(stockDistance),stock_clearance_is_lower_bound:stockDistance>=cap-1e-6,stock_mechanical_interfaces_excluded:exclusions});
 }
 for(let i=0;i<parts.length;i++)for(let j=i+1;j<parts.length;j++){const a=parts[i],b=parts[j],ba=new THREE.Box3().setFromObject(a.root),bb=new THREE.Box3().setFromObject(b.root),ov=overlap(ba,bb);const planned=(layout.planned_matings||[]).some(pair=>pair.includes(a.id)&&pair.includes(b.id));let permitted=false;
  if(planned){const burner=a.id==='BRN'?a:b,other=a.id==='BRN'?b:a;const housing=meshes(burner.root).filter(m=>m.userData.matingPart==='housing');permitted=housing.length>0&&housing.every(m=>!overlap(new THREE.Box3().setFromObject(m),new THREE.Box3().setFromObject(other.root)).every(v=>v>.1));}
  const gap=boxGap(ba,bb);if(ov.every(v=>v>.1)||gap<cap-.05||planned)result.component_pairs.push({ids:[a.id,b.id],envelope_overlap:ov.every(v=>v>.1),gap_mm:round(gap),planned_head_interface:planned&&permitted,housing_collision:planned&&!permitted});
 }
 const box=new THREE.Box3();for(const p of allParts)box.union(new THREE.Box3().setFromObject(p.root));box.union(new THREE.Box3().setFromObject(body.root));result.assembly_size_mm=box.getSize(new THREE.Vector3()).toArray().map(round);
 result.summary={stock_conflicts:result.parts.filter(p=>p.stock_intersections.length).map(p=>p.id),stock_gaps_under_screen:result.parts.filter(p=>p.stock_clearance_mm<cap&&!p.fixed_proxy).map(p=>({id:p.id,gap_mm:p.stock_clearance_mm,node:p.nearest_stock_node})),body_conflicts:result.parts.filter(p=>p.body_intersections.length).map(p=>p.id),unplanned_envelope_overlaps:result.component_pairs.filter(p=>p.envelope_overlap&&!p.planned_head_interface).map(p=>p.ids),body_gaps_under_screen:result.parts.filter(p=>p.clearance_mm<cap&&!p.fixed_proxy&&!p.intentionally_external).map(p=>({id:p.id,gap_mm:p.clearance_mm})),component_gaps_under_screen:result.component_pairs.filter(p=>!p.envelope_overlap&&!p.planned_head_interface).map(p=>({ids:p.ids,gap_mm:p.gap_mm}))};return result;
}
