import {Vector3,MathUtils} from 'three';

// OrbitControls moves the eye around a target. Here the eye stays fixed and
// the target follows the viewing direction instead. Coordinates are Z-up.
export function attachCameraLook({camera,controls,element,button,status,rotationSelect}){
 let locked=false,yaw=0,pitch=0,orbitDistance=1,pinchDistance=0;
 const eye=new Vector3(),direction=new Vector3(),pointers=new Map();
 const limit=MathUtils.degToRad(89.5);
 element.tabIndex=0;
 element.setAttribute('aria-label','3D-модель автомобиля');

 function sync(){
  button.setAttribute('aria-pressed',String(locked));
  button.textContent=locked?'Снять фиксацию':'Зафиксировать камеру';
  element.classList.toggle('camera-look-locked',locked);
  rotationSelect.disabled=locked;
  status.textContent=locked
   ?'Камера зафиксирована · перетаскивание или клавиши ← ↑ ↓ → — взгляд; колесо или два пальца — угол обзора. Выбор вида или переход к детали снимает фиксацию.'
   :'Свободная камера · вращение вокруг модели, сдвиг и приближение.';
 }
 function aim(){
  direction.set(Math.cos(pitch)*Math.cos(yaw),Math.cos(pitch)*Math.sin(yaw),Math.sin(pitch));
  controls.target.copy(eye).addScaledVector(direction,orbitDistance);
  camera.lookAt(controls.target);
 }
 function rotate(dx,dy){
  const radiansPerPixel=MathUtils.degToRad(camera.fov)/Math.max(1,element.clientHeight);
  yaw-=dx*radiansPerPixel;
  pitch=MathUtils.clamp(pitch-dy*radiansPerPixel,-limit,limit);
  aim();
 }
 function zoom(factor){camera.fov=MathUtils.clamp(camera.fov*factor,15,100);camera.updateProjectionMatrix();}
 function releasePointers(){
  for(const id of pointers.keys())if(element.hasPointerCapture(id))element.releasePointerCapture(id);
  pointers.clear();pinchDistance=0;
 }
 function setLocked(value){
  if(locked===value)return;
  releasePointers();
  if(value){
   // Clear pending damping, then restore the exact eye/pose captured at click.
   eye.copy(camera.position);const quaternion=camera.quaternion.clone(),target=controls.target.clone(),damping=controls.enableDamping;
   controls.enableDamping=false;controls.update();controls.enableDamping=damping;
   camera.position.copy(eye);camera.quaternion.copy(quaternion);controls.target.copy(target);
   orbitDistance=Math.max(1,eye.distanceTo(target));
   camera.getWorldDirection(direction);yaw=Math.atan2(direction.y,direction.x);pitch=Math.asin(MathUtils.clamp(direction.z,-1,1));
   controls.enabled=false;
  }else{
   // Continue orbiting around the point now being viewed, without a jump.
   camera.getWorldDirection(direction);controls.target.copy(camera.position).addScaledVector(direction,orbitDistance);
   controls.enabled=true;controls.update();
  }
  locked=value;sync();
 }
 const pairDistance=()=>{const [a,b]=[...pointers.values()];return a&&b?Math.hypot(a.x-b.x,a.y-b.y):0;};
 element.addEventListener('pointerdown',e=>{
  if(!locked||e.button!==0)return;
  e.preventDefault();element.focus({preventScroll:true});
  pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});element.setPointerCapture(e.pointerId);pinchDistance=pairDistance();
 });
 element.addEventListener('pointermove',e=>{
  if(!locked||!pointers.has(e.pointerId))return;
  const before=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(pointers.size===1)rotate(e.clientX-before.x,e.clientY-before.y);
  else{const distance=pairDistance();if(distance>0&&pinchDistance>0)zoom(pinchDistance/distance);pinchDistance=distance;}
 });
 const end=e=>{pointers.delete(e.pointerId);pinchDistance=pairDistance();};
 for(const name of ['pointerup','pointercancel','lostpointercapture'])element.addEventListener(name,end);
 element.addEventListener('wheel',e=>{if(!locked)return;e.preventDefault();const pixels=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?element.clientHeight:1);zoom(Math.exp(MathUtils.clamp(pixels,-1000,1000)*.001));},{passive:false});
 element.addEventListener('contextmenu',e=>{if(locked)e.preventDefault();});
 element.addEventListener('keydown',e=>{
  if(!locked)return;
  const steps={ArrowLeft:[-24,0],ArrowRight:[24,0],ArrowUp:[0,-24],ArrowDown:[0,24]};
  if(steps[e.key]){e.preventDefault();rotate(...steps[e.key]);}
 });
 button.addEventListener('click',()=>setLocked(!locked));sync();
 return {get locked(){return locked;},setLocked,releaseForNavigation:()=>setLocked(false),update(){if(!locked)controls.update();}};
}
