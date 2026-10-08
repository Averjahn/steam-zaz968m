import * as T from 'three';
// Actual circular elbows in arbitrary planes. Radius never silently shrinks.
class CircularElbow extends T.Curve {
 constructor(center,radial,axis,angle,radius){super();this.center=center;this.radial=radial;this.axis=axis;this.angle=angle;this.radius=radius;}
 getPoint(t,target=new T.Vector3()){return target.copy(this.radial).applyAxisAngle(this.axis,this.angle*t).multiplyScalar(this.radius).add(this.center);}
 getLength(){return this.radius*this.angle;}
 getTangent(t,target=new T.Vector3()){return target.crossVectors(this.axis,this.radial.clone().applyAxisAngle(this.axis,this.angle*t)).normalize();}
}
export function pipeCurve(spec){const p=spec.points.map(x=>new T.Vector3(...x)),curve=new T.CurvePath();curve.arcLengthDivisions=1200;
 // CurvePath.getPoint already uses physical arc length. Avoid a second sampled remap.
 curve.getPointAt=(t,target)=>curve.getPoint(t,target);curve.getTangentAt=(t,target)=>curve.getTangent(t,target);
 if(!spec.geometry_valid){for(let i=1;i<p.length;i++)curve.add(new T.LineCurve3(p[i-1],p[i]));curve.userData={invalid:true};return curve;}
 let start=p[0];for(let i=1;i<p.length-1;i++){const u=p[i].clone().sub(p[i-1]).normalize(),v=p[i+1].clone().sub(p[i]).normalize(),angle=Math.acos(T.MathUtils.clamp(u.dot(v),-1,1));if(angle<1e-7)continue;
 const R=spec.bend_radius_mm,trim=R*Math.tan(angle/2),before=p[i].clone().addScaledVector(u,-trim),after=p[i].clone().addScaledVector(v,trim),axis=new T.Vector3().crossVectors(u,v).normalize(),normal=new T.Vector3().crossVectors(axis,u).normalize(),center=before.clone().addScaledVector(normal,R);
 if(start.distanceTo(before)>.0001)curve.add(new T.LineCurve3(start,before));curve.add(new CircularElbow(center,before.clone().sub(center).normalize(),axis,angle,R));start=after;
 }if(start.distanceTo(p.at(-1))>.0001)curve.add(new T.LineCurve3(start,p.at(-1)));return curve;
}
