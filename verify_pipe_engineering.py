"""Independent balance/invariant checks; passing does not certify real equipment."""
from pathlib import Path
import json,math,hashlib
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'pipe-engineering.json').read_text());checks=[]
def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
for s in m['routes']:
 id=s['id'];check(id+' layers sum',abs(s['outer_envelope_mm']-(s['od']+2*s['insulation_mm']+2*s['jacket_mm']))<1e-10)
 check(id+' bends fit without radius shrink',s['geometry_valid'] and not s['bend_violations'])
 check(id+' curve radius clears insulated cross section',s['bend_radius_mm']>s['outer_envelope_mm']/2)
 actual_length=sum(math.dist(a,b) for a,b in zip(s['points'],s['points'][1:]))
 for b in s['bends']:
  i=b['vertex'];u=[y-x for x,y in zip(s['points'][i-1],s['points'][i])];v=[y-x for x,y in zip(s['points'][i],s['points'][i+1])];theta=math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/math.sqrt(sum(x*x for x in u)*sum(y*y for y in v)))));actual_length+=s['bend_radius_mm']*(theta-2*math.tan(theta/2))
 check(id+' length matches actual endpoints and circular arcs',abs(actual_length/1000-s['centerline_length_m'])<1e-8)
 if s.get('hydraulics'):
  h=s['hydraulics'];A=math.pi*(s['inside_id_mm']/1000)**2/4
  check(id+' mass conservation',abs(h['density_kg_m3']*A*h['speed_m_s']-h['mass_kg_s'])<1e-10)
  check(id+' positive dissipative pressure loss',h['friction_minor_Pa']>0)
 if s.get('thermal'):
  t=s['thermal'];r1=s['od']/2000;r2=r1+s['insulation_mm']/1000;inner=2*math.pi*t['lambda_W_mK']*(s['wall_temperature_C']-t['surface_C'])/math.log(r2/r1);outer=2*math.pi*t['external_jacket_radius_m']*t['h_W_m2K']*(t['surface_C']-t['ambient_C'])
  check(id+' conduction/external heat balance',abs(inner-outer)<1e-6,dict(conduction_W_m=inner,external_W_m=outer))
  check(id+' target only at declared h=8',t['surface_C']<=55 and t['h_sensitivity'][0]['surface_C']>t['surface_C'])
  delta=t['thickness_mm'];compar=t['stone_wool_comparison']['thickness_mm'];check(id+' aerogel/wool comparison',compar>=delta)
audit=json.loads((ROOT/'internal-fit-audit.json').read_text());keys=['id','points','od','inside_id_mm','insulation_mm','jacket_mm','outer_envelope_mm','bend_radius_mm','geometry_valid']
digest=hashlib.sha256(json.dumps([{k:r[k] for k in keys} for r in m['routes']],sort_keys=True).encode()).hexdigest()
check('Published mesh audit matches current pipe dimensions and vertices',audit['provenance']['geometry_parameter_sha256']==digest)
for path,digest in audit['provenance']['source_sha256'].items():check('Mesh audit source '+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
expected='5db080a3c9b362caf09a03122f3faabfd260c607914dda56adb471f2c19b6cbd'
check('Supplied body GLB remains unchanged',hashlib.sha256((ROOT/'models/zaz-968m-yatloo.glb').read_bytes()).hexdigest()==expected)
check('Cooling limitation is explicit',json.loads((ROOT/'internal-feasibility.json').read_text())['formula_rows'][4]['value']>100)
result=dict(status='passed' if all(c['pass'] for c in checks) else 'failed',checks=checks,scope='Arithmetic, heat balance and geometric routing invariants; real-car fit, gas duct, two-phase condensate, material/pressure ratings and mount strength unresolved')
(ROOT/'models/pipe-engineering-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],checks=len(checks))))
if result['status']!='passed':raise SystemExit(1)
