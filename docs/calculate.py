"""Screening model: SI units internally, IAPWS IF97 via CoolProp 7.2.0.
Run: PYTHONPATH=.deps python3 calculate.py; change inputs.json first.
This model does not size pressure-containing parts or establish road approval.
"""
import csv
import json
import math
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from CoolProp.CoolProp import PropsSI

ROOT = Path(__file__).resolve().parent
FLUID = 'IF97::Water'

def road(v_kmh, mass, cfg, grade=0, acceleration=0):
    v = v_kmh / 3.6
    angle = math.atan(grade)
    roll = mass * 9.80665 * cfg['rolling_coefficient'] * math.cos(angle)
    aero = 0.5 * cfg['air_density_kg_m3'] * cfg['CdA_m2'] * v*v
    slope = mass * 9.80665 * math.sin(angle)
    force = roll + aero + slope + mass * acceleration
    return {'speed_kmh': v_kmh, 'grade_fraction': grade, 'acceleration_m_s2': acceleration,
            'force_N': force, 'wheel_kW': force*v/1000,
            'drive_kW': force*v/1000/cfg['transmission_efficiency'],
            'wheel_torque_Nm': force * cfg['wheel_rolling_radius_m'],
            'wheel_rpm': 60*v/(2*math.pi*cfg['wheel_rolling_radius_m'])}

def transmission(speed, case, vehicle, gear=4, adapter=1):
    """i_adapter = engine/input RPM; gear alternatives are not wheel RPM."""
    if gear not in range(1,5) or adapter <= 0: raise ValueError('Invalid transmission')
    circumference = 2*math.pi*vehicle['wheel_rolling_radius_m']
    wheel = speed/3.6/circumference*60
    ratio = vehicle['final_drive']*vehicle['gears'][gear-1]
    input_rpm = wheel*ratio
    return {'wheel_rpm':wheel, 'input_rpm':input_rpm, 'engine_rpm':input_rpm*adapter,
            'match_ratio':case['rpm']/input_rpm if input_rpm else None,
            'speed_at_target_rpm':case['rpm']/(adapter*ratio)*circumference/60*3.6}

def cycle(drive_kw, case, cfg, return_fraction=None):
    p1, p2 = case['p_bar_abs'] * 1e5, cfg['exhaust_pressure_bar_abs'] * 1e5
    if p1 <= p2: raise ValueError('Inlet pressure must exceed exhaust pressure')
    t1 = case['T_C'] + 273.15
    if t1 <= PropsSI('T','P',p1,'Q',1,FLUID): raise ValueError('Superheated inlet required')
    r = cfg['return_fraction'] if return_fraction is None else return_fraction
    if not 0 <= r <= 1: raise ValueError('Return fraction must be within [0,1]')
    for k in ['mechanical_efficiency','pump_efficiency','boiler_efficiency_LHV']:
        if not 0 < cfg[k] <= 1: raise ValueError(k)
    if not 0 < case['eta_is'] <= 1: raise ValueError('eta_is')
    if drive_kw < 0: raise ValueError('Nonnegative drive power required')
    h1 = PropsSI('H','P',p1,'T',t1,FLUID)
    s1 = PropsSI('S','P',p1,'T',t1,FLUID)
    h2s = PropsSI('H','P',p2,'S',s1,FLUID)
    h2 = h1 - case['eta_is']*(h1-h2s)
    hc = PropsSI('H','P',p2,'T',cfg['condensate_temperature_C']+273.15,FLUID)
    hm = PropsSI('H','P',p2,'T',cfg['makeup_temperature_C']+273.15,FLUID)
    h3 = r*hc + (1-r)*hm
    rho3 = PropsSI('D','P',p2,'H',h3,FLUID)
    wp = (p1-p2)/rho3/cfg['pump_efficiency']
    h4 = h3 + wp
    work = (h1-h2)*cfg['mechanical_efficiency']
    # Couple condenser airflow and fan demand to steam flow; do not hide fans
    # in a fixed accessory allowance. Fan coefficient is J/kg of circulating steam.
    air_per_steam = r*(h2-hc)/(1000*cfg['air_heat_capacity_kJ_kgK']*cfg['air_temperature_rise_K'])
    fan_electric_per_steam = air_per_steam/cfg['cooling_air_density_kg_m3']*cfg['fan_pressure_drop_Pa']/cfg['fan_efficiency']
    fan_shaft_per_steam = fan_electric_per_steam/cfg['generator_efficiency']
    available_work = work-wp-fan_shaft_per_steam
    if available_work <= 0: raise ValueError('Cooling parasitics exceed cycle work')
    mdot = (drive_kw+case['aux_shaft_kW'])*1000/available_work
    qboiler = mdot*(h1-h4)/1000
    qcond = r*mdot*(h2-hc)/1000
    qloststeam = (1-r)*mdot*(h2-hm)/1000
    qmech = mdot*(h1-h2)*(1-cfg['mechanical_efficiency'])/1000
    gross = mdot*work/1000
    pump = mdot*wp/1000
    residual = qboiler+pump - (qcond+qloststeam+gross+qmech)
    burner = qboiler/cfg['boiler_efficiency_LHV']
    fuel_kg_h = burner*3.6/cfg['diesel_LHV_MJ_kg']
    fuel_L_h = fuel_kg_h/cfg['diesel_density_kg_L']
    air_kg_s = qcond/(cfg['air_heat_capacity_kJ_kgK']*cfg['air_temperature_rise_K'])
    air_m3_s = air_kg_s/cfg['cooling_air_density_kg_m3']  # screening density at warm ambient, assumed
    fan_kw = air_m3_s*cfg['fan_pressure_drop_Pa']/cfg['fan_efficiency']/1000
    q2 = PropsSI('Q','P',p2,'H',h2,FLUID)
    return {'drive_kW':drive_kw, 'steam_kg_h':mdot*3600, 'makeup_kg_h':(1-r)*mdot*3600,
            'boiler_kW':qboiler, 'burner_LHV_kW':burner, 'condenser_kW':qcond,
            'fuel_kg_h':fuel_kg_h, 'diesel_L_h':fuel_L_h, 'gross_engine_kW':gross,
            'feed_pump_kW':pump, 'net_efficiency_LHV':drive_kw/burner,
            'specific_steam_kg_kWh_drive':mdot*3600/drive_kw if drive_kw else None,
            'fan_lower_estimate_kW':fan_kw, 'fan_shaft_kW':fan_kw/cfg['generator_efficiency'],
            'total_aux_shaft_kW':case['aux_shaft_kW']+fan_kw/cfg['generator_efficiency'],
            'air_m3_s':air_m3_s,
            'exchange_area_m2':qcond*1000/(cfg['heat_exchanger_U_W_m2K']*cfg['heat_exchanger_LMTD_K']),
            'shaft_torque_at_rpm_Nm':60000*gross/(2*math.pi*case['rpm']),
            'condensate_h_kJ_kg':hc/1000, 'makeup_h_kJ_kg':hm/1000, 'feed_density_kg_m3':rho3,
            'exhaust_liquid_h_kJ_kg':PropsSI('H','P',p2,'Q',0,FLUID)/1000,
            'exhaust_vapor_h_kJ_kg':PropsSI('H','P',p2,'Q',1,FLUID)/1000,
            'feed_temperature_C':PropsSI('T','P',p2,'H',h3,FLUID)-273.15,
            'inlet_saturation_temperature_C':PropsSI('T','P',p1,'Q',1,FLUID)-273.15,
            'return_fraction':r, 'pump_specific_work_kJ_kg':wp/1000,
            'h1_kJ_kg':h1/1000, 'h2s_kJ_kg':h2s/1000, 'h2_kJ_kg':h2/1000,
            'h3_kJ_kg':h3/1000, 'h4_kJ_kg':h4/1000, 's1_kJ_kgK':s1/1000,
            'inlet_density_kg_m3':PropsSI('D','P',p1,'T',t1,FLUID),
            'exhaust_quality':q2 if 0 <= q2 <= 1 else None,
            'exhaust_temperature_C':PropsSI('T','P',p2,'H',h2,FLUID)-273.15,
            'lost_steam_energy_kW':qloststeam, 'mechanical_loss_kW':qmech,
            'balance_residual_kW':residual}

def mass_model(case, v, fuel_density=.835):
    # Curb mass includes old fuel: subtract removed mass incl. estimated old fuel.
    dry = case['dry_plant_kg']
    items = [(-v['removed_mass_kg'],v['removed_x_mm']),
             (dry*.64,3250),(dry*.20,420),(dry*.10,550),(dry*.06,1800),
             (case['water_L']*v['cold_water_density_kg_L'],600),(case['loop_water_kg'],3100),(case['fuel_L']*fuel_density,2800),
             (v['driver_mass_kg'],v['driver_x_mm'])]
    base_rear = v['curb_mass_kg']*(1-v['curb_front_fraction'])
    rear = base_rear + sum(m*(x-v['front_axle_x_mm'])/v['wheelbase_mm'] for m,x in items)
    mass = v['curb_mass_kg'] + sum(m for m,_ in items)
    return {'running_mass_kg':mass, 'front_kg_assumed':mass-rear, 'rear_kg_assumed':rear,
            'remaining_total_payload_kg':v['reference_full_mass_kg']-mass,
            'mass_status':'Осевые результаты — прогноз; допустимые нагрузки на оси не установлены'}

def readable_round(value, digits):
    return float(Decimal(str(value)).quantize(Decimal(10)**-digits,rounding=ROUND_HALF_UP)) + 0.0

def run():
    inp = json.loads((ROOT/'inputs.json').read_text())
    v,c = inp['vehicle'],inp['cycle']
    road_rows=[road(speed,1200,v,g) for speed in [30,50,60,80,90,100,110] for g in [0,.05,.10]]
    scenarios=[]
    sensitivity=[]
    for case in inp['scenarios']:
        mass=mass_model(case,v,c['diesel_density_kg_L'])
        result=cycle(case['net_drive_kW'],case,c)
        open_cycle=cycle(case['net_drive_kW'],case,c,0)
        target=road(case['target_kmh'],mass['running_mass_kg'],v)
        cruise=cycle(target['drive_kW'],case,c)
        usable_water=case['water_L']*v['cold_water_density_kg_L']*v['usable_water_fraction']  # excludes 20% reserve; loop inventory separate
        water_hours=usable_water/result['makeup_kg_h']
        fuel_hours=case['fuel_L']/result['diesel_L_h']
        cruise_range=case['target_kmh']*min(usable_water/cruise['makeup_kg_h'],case['fuel_L']/cruise['diesel_L_h'])
        low,high=0.,160.
        for _ in range(60):
            mid=(low+high)/2
            if road(mid,mass['running_mass_kg'],v)['drive_kW']<=case['net_drive_kW']: low=mid
            else: high=mid
        scenarios.append({'case':case,'rated':result,'open_cycle':open_cycle,'mass':mass,
                          'target_road':target,'cruise':cruise,'flat_speed_power_bound_kmh':low,
                          'transmission':transmission(case['target_kmh'],case,v),
                          'rated_water_duration_h':water_hours,'rated_fuel_duration_h':fuel_hours,
                          'steady_cruise_range_km':cruise_range,
                          'open_water_duration_min':60*usable_water/open_cycle['makeup_kg_h'],
                          'loop_inventory_note':'Рабочая вода в генераторе/конденсаторе/приемнике учтена отдельно; фактический объем неизвестен'})
        for efficiency in [.30,.40,.50,.60,.70]:
            alt={**case,'eta_is':efficiency}
            r=cycle(case['net_drive_kW'],alt,c)
            sensitivity.append({'case':case['id'],'eta_is':efficiency,**r})
    data={'inputs':inp,'scenarios':scenarios,'road':road_rows,'sensitivity':sensitivity}
    (ROOT/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    for name,rows in [('road_load',road_rows),('sensitivity',sensitivity),('scenario_summary',[{'case':s['case']['id'],**s['rated'],**s['mass'],'steady_cruise_range_km':s['steady_cruise_range_km']} for s in scenarios])]:
        with (ROOT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader()
            # Human-readable exports; JSON retains unrounded computational values.
            for row in rows:
                w.writerow({k:readable_round(val,0 if k.endswith('rpm') else 4 if k in ['eta_is','net_efficiency_LHV','grade_fraction','return_fraction','s1_kJ_kgK'] else 3 if 'density' in k else 1) if isinstance(val,float) else val for k,val in row.items()})
    for s in scenarios:
        r=s['rated'];m=s['mass']
        print(s['case']['id'], {k:round(r[k],2) for k in ['drive_kW','steam_kg_h','boiler_kW','burner_LHV_kW','condenser_kW','diesel_L_h','makeup_kg_h','fan_lower_estimate_kW']},'mass',round(m['running_mass_kg'],1),'payload',round(m['remaining_total_payload_kg'],1))
    return data

if __name__=='__main__': run()
