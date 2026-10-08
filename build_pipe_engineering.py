"""Conditional pipe/insulation calculation. No pressure-wall or relief-valve certification.
Run with PYTHONPATH=.deps; generates the one route manifest used by native 3D and documents.
"""
from pathlib import Path
import json, math, hashlib
from CoolProp.CoolProp import PropsSI
ROOT=Path(__file__).resolve().parent
old=json.loads((ROOT/'pipe-routes-input.json').read_text())['routes']
b=next(x for x in json.loads((ROOT/'results.json').read_text())['scenarios'] if x['case']['id']=='B');r=b['rated'];mdot=r['steam_kg_h']/3600
sources=[{'title':'Armacell ArmaGel HT · thermal conductivity versus mean temperature','url':'https://www.armacell.com/lt-LT/product/technical-specs/armagel-ht'}, {'title':'ROCKWOOL ProRox PS 960 · thermal conductivity versus mean temperature','url':'https://rti.rockwool.com/siteassets/tools--documentation/products-industrial/product-data-sheets/english/rw-ti-pds-prorox-ps-960-en-UM.pdf'}, {'title':'Spirax Sarco · pipes and pipe sizing','url':'https://www.spiraxsarco.com/learn-about-steam/steam-distribution/pipes-and-pipe-sizing?sc_lang=en-GB'}, {'title':'CoolProp · Water IAPWS-95','url':'https://coolprop.org/fluid_properties/fluids/Water.html'}, {'title':'Haaland (1983) · Simple and Explicit Formulas for the Friction Factor in Turbulent Pipe Flow','url':'https://doi.org/10.1115/1.3240948'}]
materials={'aerogel':dict(name='ArmaGel HT',temperature_C=[24,38,93,149,204,260,316,371],lambda_W_mK=[.021,.022,.023,.025,.029,.032,.036,.043],max_temperature_C=650), 'stone_wool':dict(name='ProRox PS 960',temperature_C=[50,100,150,200,250,300,350],lambda_W_mK=[.040,.046,.054,.064,.077,.092,.112],max_temperature_C=650)}
def interpolate(x,xs,ys):
 if x<xs[0]: return ys[0] # conservative endpoint, explicitly declared
 if x>xs[-1]: raise ValueError('Mean insulation temperature outside source table')
 for i in range(1,len(xs)):
  if x<=xs[i]: return ys[i-1]+(ys[i]-ys[i-1])*(x-xs[i-1])/(xs[i]-xs[i-1])
def thermal(od,delta,tw,key,h=8,ambient=40):
 ri=od/2000;ro=ri+delta/1000;ts=(tw+ambient)/2
 for _ in range(200):
  k=interpolate((tw+ts)/2,materials[key]['temperature_C'],materials[key]['lambda_W_mK']);rc=math.log(ro/ri)/(2*math.pi*k);rs=1/(2*math.pi*(ro+.0006)*h);q=(tw-ambient)/(rc+rs);new=ambient+q*rs
  if abs(new-ts)<1e-10: break
  ts=.5*(ts+new)
 return dict(thickness_mm=delta,lambda_W_mK=k,heat_W_m=q,surface_C=new,R_cond_mK_W=rc,R_external_mK_W=rs,external_jacket_radius_m=ro+.0006,h_W_m2K=h,ambient_C=ambient)
def thickness(od,tw,key):
 for delta in range(5,301,5):
  t=thermal(od,delta,tw,key)
  if t['surface_C']<=55: return t
 raise ValueError('Insulation exceeds screen limit')
def vec(a,b): return [b[i]-a[i] for i in range(3)]
def length(v): return math.sqrt(sum(x*x for x in v))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def bend_geometry(points,radius):
 ls=[length(vec(a,b)) for a,b in zip(points,points[1:])];trims=[0]*len(points);bends=[]
 for i in range(1,len(points)-1):
  u=vec(points[i-1],points[i]);v=vec(points[i],points[i+1]);theta=math.acos(max(-1,min(1,dot(u,v)/(length(u)*length(v)))))
  if theta<1e-7: continue
  trim=radius*math.tan(theta/2);trims[i]=trim;bends.append(dict(vertex=i,angle_deg=math.degrees(theta),radius_mm=radius,tangent_mm=trim))
 violations=[dict(segment=i,available_mm=l,required_mm=trims[i]+trims[i+1]) for i,l in enumerate(ls) if trims[i]+trims[i+1]>l+1e-6]
 route_length=(sum(ls)-2*sum(trims)+sum(math.radians(x['angle_deg'])*radius for x in bends))/1000 if not violations else sum(ls)/1000
 return bends,violations,route_length
# Rerouting changes vertices, never scale pipe diameter or insulation to hide collisions.
updates={
 'PIPE_STEAM':[[2530,300,1180],[2650,300,1180],[2770,100,900],[3080,0,745]],
 'PIPE_SUCTION':[[800,480,675],[1000,480,675],[1010,340,930],[925,340,930],[925,190,930],[1020,190,840],[1130,190,840],[1130,625,420],[2010,625,420],[2010,-140,420],[2010,-140,500],[2160,-140,500]],
 'PIPE_FLUE':[[2480,460,1190],[2720,460,1190],[2850,293,920],[3010,293,700],[3200,303,700],[3725,303,700]],
 'PIPE_EXHAUST_L':[[3370,110,730],[3370,110,520],[3670,110,520],[3670,440,520],[3430,440,780]],
 'PIPE_RETURN':[[3450,-410,600],[3580,-410,600],[3580,-280,550],[3100,-280,550],[3030,-280,760],[2650,-280,760],[2650,-665,760],[1100,-665,760],[1020,-460,760],[800,260,890]],
 'PIPE_MAKEUP':[[850,-100,670],[900,-100,670],[900,10,670],[820,10,670]],
 'PIPE_FUEL':[[2190,180,540],[2075,120,540],[2075,-470,540],[2075,-470,720],[2300,-470,720],[2300,-250,720]],
 'WIRE_ENGINE':[[2000,60,500],[2000,-625,500],[2000,-625,1000],[2660,-625,1000],[2660,-200,1000],[2660,100,1100],[2520,100,1100]],
 'PIPE_FEED':[[2230,-250,560],[2710,-250,560],[2710,-250,750],[2710,100,750],[2530,100,750],[2530,300,750]]
}
rows=[]
for original in old:
 s=dict(original);s.pop('insulation',None);id=s['id'];s['points']=updates.get(id,s['points']);s['wall_status']='Assumed geometric wall only; pressure strength, material grade and fittings not selected'
 if id=='PIPE_RELIEF':s['points'][-1]=[2340,-520,850]
 if id=='PIPE_FLUE':s['od']=82;s['inside_id_mm']=80 # geometric single-wall duct candidate: 160 ID + 2 x 1 mm, not pressure equipment
 kind='steam' if id in ['PIPE_STEAM','PIPE_RELIEF'] else 'exhaust' if id.startswith('PIPE_EXHAUST') else 'flue' if id=='PIPE_FLUE' else 'fuel' if id=='PIPE_FUEL' else 'wire' if id.startswith('WIRE') else 'water'
 s['fluid']=kind;tw={'steam':250,'exhaust':r['exhaust_temperature_C'],'water':r['feed_temperature_C'] if 'feed_temperature_C' in r else 78.2041,'fuel':25,'flue':250,'wire':40}[kind];tw=25 if id=='PIPE_MAKEUP' else tw;s['wall_temperature_C']=tw
 if kind in ['steam','exhaust','water','flue'] and id!='PIPE_MAKEUP':
  chosen=thickness(s['od'],tw,'aerogel');comparison=thickness(s['od'],tw,'stone_wool');s['thermal']={**chosen,'material':'aerogel','target_surface_C':55,'stone_wool_comparison':comparison,'h_sensitivity':[thermal(s['od'],chosen['thickness_mm'],tw,'aerogel',h) for h in [5,8,15]],'notes':'Steady cylindrical screen, h=8 includes assumed net external exchange; radiation not resolved separately. No supports/valves bridges, transient soak, moisture or contact-temperature certification. Diesel flue wall 250 C is a design hypothesis; solid-fuel variant 350 C is calculated separately; below first table entry lambda is held at first source value.'};s['insulation_mm']=chosen['thickness_mm'];s['jacket_mm']=.6
 else:s['insulation_mm']=0;s['jacket_mm']=0
 s['outer_envelope_mm']=s['od']+2*s['insulation_mm']+2*s['jacket_mm'];s['inside_id_mm']=s.get('inside_id_mm');s['wall_mm']=(s['od']-s['inside_id_mm'])/2 if s['inside_id_mm'] else None
 radius=math.ceil(max(1.5*s['od'],s['outer_envelope_mm']/2+15,30 if kind=='wire' else 0)/5)*5
 if id=='PIPE_STEAM':radius=max(radius,90)
 s['bend_radius_mm']=radius;s['bend_radius_basis']='Chosen geometric screening radius max(1.5 x bare OD, insulated outer radius + 15 mm), rounded up to 5 mm. Not a catalog bend specification or material forming limit.'
 bends,violations,L=bend_geometry(s['points'],radius);s['bends']=bends;s['bend_violations']=violations;s['geometry_valid']=not violations;s['centerline_length_m']=L
 s['endpoint_status']='Ports on concept parts only; pump thread axes, tees, feedthroughs, clamps and expansion supports unresolved'
 if id=='PIPE_FLUE':
  s['name']='Дымовой канал · генератор → задний выпуск'
  s['ends']=['STM.flueOutlet','BODY.flushRearExhaust'];s['connected']=True;s['routing_note']='Complete concept route for compact 120 kW heat source, not RL50 at 471 kW. ID80 sized against gas flow/pressure; wall 250 C and passive insulation declared. Rear outlet needs a sealed body aperture and heat shield; real fit remains unverified.'
 if id=='PIPE_RETURN':s['routing_note']='Return bypasses exhaust at rear, then uses Y-280/Z760 and side corridor Y-665; actual stock travel, body penetration and supports still require validation.'
 if kind in ['steam','exhaust','water']:
  if kind=='steam':p,t,flow=1e6,523.15,mdot
  elif kind=='exhaust':p,t,flow=1.2e5,r['exhaust_temperature_C']+273.15,mdot/2
  else:p,t,flow=(1e6 if id=='PIPE_FEED' else 2e5),tw+273.15,mdot/2 if id=='PIPE_BALANCE' else mdot
  rho=PropsSI('D','P',p,'T',t,'Water');mu=PropsSI('V','P',p,'T',t,'Water');di=s['inside_id_mm']/1000;speed=4*flow/(rho*math.pi*di*di);Re=rho*speed*di/mu;epsilon=.000045;fr=64/Re if Re<2300 else (-1.8*math.log10((epsilon/(3.7*di))**1.11+6.9/Re))**-2;kb=.2;kv=1.0;ks=len(bends)*kb+kv;dp=(fr*L/di+ks)*rho*speed*speed/2;dz=(s['points'][-1][2]-s['points'][0][2])/1000;static=rho*9.81*dz if kind=='water' else 0
  s['hydraulics']=dict(mass_kg_s=flow,pressure_Pa=p,temperature_C=t-273.15,density_kg_m3=rho,viscosity_Pa_s=mu,speed_m_s=speed,Re=Re,roughness_mm=epsilon*1000,Darcy_f=fr,K_per_bend=kb,K_other=kv,K_sum=ks,friction_minor_Pa=dp,static_head_Pa=static,total_estimated_Pa=dp+static,fraction_of_reference_pressure=dp/p,notes='Single-phase constant-state screen; bend K=0.2 and other K=1 are assumptions, not selected valve/CAD data. Water total excludes generator pressure. Property reference P=2 bar abs for return/suction or 10 bar abs for feed is not a selected pump/booster setpoint; cold makeup is assumed 25 C. Condensate may flash/two-phase. Relief mass flow here only illustrates B; not sizing a safety discharge. Makeup shown at full B as conservative flow hypothesis.')
  s['pressure_loss_screen_valid']=not violations and dp/p<=.1
 else:s['hydraulics']=None
 if s.get('thermal'):s['thermal']['route_heat_W']=s['thermal']['heat_W_m']*L
 rows.append(s)
meta=dict(status='Conditional engineering candidate, geometric/thermal/hydraulic screening only',scenario='B, 551.74 kg/h nominal steam; baseline cycle unchanged',assumptions=dict(ambient_C=40,target_surface_C=55,h_W_m2K=8,jacket_mm=.6,pipe_roughness_mm=.045,K_per_bend=.2,K_other=1,flue_wall_C=250,flue_flow='Compact diesel 120 kW: stoichiometric air 14.5 kg/kg, excess 1.4, ideal gas at 250 C; source-specific pressure check in heat comparison.',fixed_supports='Not designed; symbols are not verified load paths'),materials=materials,sources=sources,routes=rows,invalid_bend_routes=[s['id'] for s in rows if not s['geometry_valid']],conclusion='Routing cannot by itself solve B cooling/volume. Full insulated envelopes are used without shrinking; unresolved intersections remain visible in the audit.')
(ROOT/'pipe-engineering.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(ROOT/'web/pipe-data.js').write_text('// Generated by build_pipe_engineering.py; millimetres, no hidden scale reduction.\nexport const pipeEngineering='+json.dumps(meta,ensure_ascii=False,separators=(',',':'))+';\nexport const pipeRoutes=pipeEngineering.routes;\n')
print(json.dumps({'routes':len(rows),'invalid_bends':meta['invalid_bend_routes'],'thermal':[{k:s.get(k) for k in ['id','od','insulation_mm','outer_envelope_mm','bend_radius_mm']} for s in rows if s.get('thermal')]},ensure_ascii=False))
