"""Meaningful checks for thermodynamic balance, road loads and exported geometry."""
import json
import math
from pathlib import Path
from calculate import cycle, road, mass_model, run
from build_geometry import checks
ROOT=Path(__file__).resolve().parent

def main():
    d=json.loads((ROOT/'results.json').read_text());v=d['inputs']['vehicle'];cfg=d['inputs']['cycle']
    passed=[]
    for s in d['scenarios']:
        c=s['case'];r=s['rated'];o=s['open_cycle']
        assert abs(r['balance_residual_kW']) < 1e-8
        # Shaft accounting including electrical conversion, fans and feed pump.
        assert abs(r['gross_engine_kW']-r['feed_pump_kW']-r['total_aux_shaft_kW']-c['net_drive_kW']) < 1e-8
        assert r['h1_kJ_kg']>r['h2_kJ_kg']>=r['h2s_kJ_kg']
        assert r['h4_kJ_kg']>r['h3_kJ_kg']
        assert abs(r['makeup_kg_h']/r['steam_kg_h']-.03)<1e-12
        assert abs(o['makeup_kg_h']-o['steam_kg_h'])<1e-8 and o['condenser_kW']==0
        assert abs(mass_model(c,v)['front_kg_assumed']+mass_model(c,v)['rear_kg_assumed']-s['mass']['running_mass_kg'])<1e-8
        passed.append(c['id']+': баланс энергии, баланс вала, состояния, открытый цикл и сумма осей')
    # Independent known case: rolling load only at 36 km/h, 1000 kg.
    test={**v,'CdA_m2':0,'transmission_efficiency':1}
    r=road(36,1000,test)
    assert abs(r['wheel_kW']-1000*9.80665*.015*10/1000)<1e-12
    r2=road(72,1000,test)
    assert abs(r2['wheel_kW']-2*r['wheel_kW'])<1e-12
    assert road(80,1200,v,.05)['drive_kW']>road(80,1200,v)['drive_kW']
    passed.append('Дорожная мощность: независимый контроль качения и влияние уклона')
    # Carnot bound on useful fuel-to-drive efficiency (generous upper bound).
    for s in d['scenarios']:
        carnot=1-(80+273.15)/(s['case']['T_C']+273.15)
        assert s['rated']['net_efficiency_LHV']<carnot
    passed.append('КПД полезного привода ниже верхней границы Карно')
    invalid={**cfg,'pump_efficiency':0}
    try:cycle(18,d['scenarios'][1]['case'],invalid)
    except ValueError:pass
    else:raise AssertionError('invalid pump efficiency accepted')
    invalid={**d['scenarios'][1]['case'],'p_bar_abs':1}
    try:cycle(18,invalid,cfg)
    except ValueError:pass
    else:raise AssertionError('invalid pressure accepted')
    passed.append('Некорректные давления и КПД отклоняются')
    g=checks();assert not g['solid_intersections']
    passed.append('Целевые AABB: прямых пересечений нет; малые зазоры зарегистрированы')
    import xml.etree.ElementTree as ET
    for p in (ROOT/'drawings').glob('*.svg'):ET.parse(p)
    obj=(ROOT/'assembly.obj').read_text();assert sum(x.startswith('v ') for x in obj.splitlines())==64
    passed.append('Все SVG читаются как XML; OBJ содержит 8 габаритных тел')
    (ROOT/'verification.json').write_text(json.dumps({'date':'2026-10-08','passed':passed,'limitations':'Проверены арифметика и целевые габариты. Физические допущения, посадка реальных изделий, прочность и дорожный допуск не подтверждены.'},ensure_ascii=False,indent=2))
    print('\n'.join(passed))

if __name__=='__main__':main()
