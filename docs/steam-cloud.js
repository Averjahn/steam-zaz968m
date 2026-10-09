import * as T from 'three';
import {engineGeometry as K} from './double-acting-cycle.js?v=02f171f7ae23';
import {createChamberCloudState} from './steam-cloud-model.js?v=438a7703a79a';

// Four bounded clouds: instanced camera-facing puffs with procedural wisps.
// The shader clips every fragment, including billboard edges, to the chamber.
const vertexShader=`
 attribute vec3 aCenter;
 attribute float aSize;
 attribute float aAlpha;
 attribute float aSeed;
 varying vec2 vCloudUV;
 varying vec3 vChamberPosition;
 varying float vAlpha;
 varying float vSeed;
 #include <clipping_planes_pars_vertex>
 void main(){
  vec2 corner=position.xy*aSize;
  vec3 right=vec3(modelViewMatrix[0][0],modelViewMatrix[1][0],modelViewMatrix[2][0]);
  vec3 up=vec3(modelViewMatrix[0][1],modelViewMatrix[1][1],modelViewMatrix[2][1]);
  vChamberPosition=aCenter+right*corner.x/dot(right,right)+up*corner.y/dot(up,up);
  vec4 mvPosition=modelViewMatrix*vec4(aCenter,1.0);
  mvPosition.xy+=corner;
  gl_Position=projectionMatrix*mvPosition;
  vCloudUV=uv;vAlpha=aAlpha;vSeed=aSeed;
  #include <clipping_planes_vertex>
 }`;
const fragmentShader=`
 uniform vec2 uAxis;
 uniform vec2 uBounds;
 uniform float uRadius;
 uniform float uRodRadius;
 uniform vec3 uColor;
 uniform float uTime;
 uniform float uOpacity;
 uniform float uTracer;
 varying vec2 vCloudUV;
 varying vec3 vChamberPosition;
 varying float vAlpha;
 varying float vSeed;
 #include <clipping_planes_pars_fragment>
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
 void main(){
  #include <clipping_planes_fragment>
  float radius=length(vChamberPosition.xy-uAxis);
  if(radius>uRadius||radius<uRodRadius||vChamberPosition.z<uBounds.x||vChamberPosition.z>uBounds.y)discard;
  vec2 p=vCloudUV*2.0-1.0;
  float shape=1.0-smoothstep(.12,1.0,dot(p,p));
  vec2 flow=p*2.1+vec2(vSeed,-uTime*.22);
  float cloud=.55*noise(flow)+.3*noise(flow*2.03+7.1)+.15*noise(flow*4.07-uTime*.12);
  float wisps=smoothstep(.14,.86,cloud);
  float tracer=1.0-smoothstep(.004,.028,dot(p,p));
  float opacity=mix(shape*wisps*vAlpha*1.6,tracer*.9,uTracer)*uOpacity;
  if(opacity<.003)discard;
  gl_FragColor=vec4(uColor*(.87+.2*cloud),opacity);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
 }`;

export function chamberSteam(parent,cylinder,chamber,{count=96}={}){
 const state=createChamberCloudState(cylinder,chamber,count),plane=new T.PlaneGeometry(1,1),geometry=new T.InstancedBufferGeometry();
 geometry.index=plane.index.clone();for(const [name,attribute]of Object.entries(plane.attributes))geometry.setAttribute(name,attribute.clone());plane.dispose();
 for(const [name,data,size]of [['aCenter',state.centers,3],['aSize',state.sizes,1],['aAlpha',state.alpha,1],['aSeed',state.seeds,1]])geometry.setAttribute(name,new T.InstancedBufferAttribute(data,size).setUsage(T.DynamicDrawUsage));
 geometry.instanceCount=count;
 const uniforms={uAxis:{value:new T.Vector2(K.cylinderX[cylinder],K.cylinderY)},uBounds:{value:new T.Vector2()},uRadius:{value:K.bore/2},uRodRadius:{value:chamber==='B'?K.rodDiameter/2:0},uColor:{value:new T.Color('#f4f4ee')},uTime:{value:0},uOpacity:{value:.75},uTracer:{value:0}};
 const material=new T.ShaderMaterial({uniforms,vertexShader,fragmentShader,transparent:true,depthTest:true,depthWrite:false,side:T.DoubleSide,clipping:true});
 const mesh=new T.Mesh(geometry,material);mesh.name='Анимированный пар · '+(cylinder+1)+chamber;mesh.frustumCulled=false;mesh.renderOrder=912;mesh.userData={viewOnly:true,steamCloud:true,cylinder,chamber,count};parent.add(mesh);
 return {mesh,state,update(cycle,time,{visible=true,present=true,render='cloud',opacity=.75,color='#f4f4ee',clippingPlanes=[]}={}){
  mesh.visible=visible&&present&&render!=='off';if(!mesh.visible)return;
  state.update(cycle,time,present);
  for(const name of ['aCenter','aSize','aAlpha'])geometry.attributes[name].needsUpdate=true;
  uniforms.uBounds.value.set(state.bounds.low,state.bounds.high);uniforms.uTime.value=time;uniforms.uColor.value.set(color);uniforms.uOpacity.value=opacity;uniforms.uTracer.value=render==='tracers'?1:0;
  material.clippingPlanes=clippingPlanes;
 }};
}
