"""Documented reference data plus explicit prototype assumptions, all efficiencies on LHV."""
from pathlib import Path
import json, math, copy
R=Path(__file__).resolve().parent
sources=[
 dict(id='diesel',name='Дизель · компактная горелка',fuel='Дизель',unit='кг',LHV_MJ_kg=42.6,density_kg_L=.835,efficiency=.85,efficiency_range=[.80,.88],max_input_kW=120,min_input_kW=54,aux_W=170,tau_s=2,stock=17.8*.835,geometry='oil',size_mm=[305,369,262],xyz_mm=[2220,-317,650],dry_mass_kg=13,geometry_basis='Размерный ориентир Riello G10: A305/D262/E261/F108 мм; глубина 261+108=369 мм; масса 13 кг. Форма приближённая, камера и автомобильное применение не подтверждены.',reference='Riello G10 24V, 54–120 кВт; 4,5–10 кг/ч. Это не прежняя RL50 148–593 кВт.',links=[dict(title='Riello: G7/G10, размеры и мощность',url='https://www.riello.com/international/files/catalogo-pdf/riello_products_catalogue_international-markets_process_burners_eng.pdf')]),
 dict(id='wood',name='Дрова · прототип газифицирующей топки',fuel='Дрова',unit='кг',dry_LHV_MJ_kg=19,moisture_percent=20,bulk_kg_L=.18,efficiency=.70,efficiency_range=[.55,.80],max_input_kW=90,min_input_kW=25,aux_W=150,tau_s=90,stock=22.3*.18,geometry='logs',size_mm=[380,350,460],xyz_mm=[2180,-340,650],dry_mass_kg=75,geometry_basis='380×350×460 мм и 75 кг — резерв прототипа, не уменьшенный заводской котёл. Загрузка, огнеупор и теплообмен должны быть разработаны.',reference='Fröling S4 22: около 90,7% при номинале, но стационарный агрегат порядка 645 кг не подходит этому кузову. Компактной топке его КПД не присвоен.',links=[dict(title='Fröling: испытания S4 Turbo, стр. 86',url='https://www.froeling-tsd.be/files/97346.pdf'),dict(title='Forest Research: влажность и теплота сгорания',url='https://cdn.forestresearch.gov.uk/2022/02/fr_bec_wood_as_fuel_technical_supplement_2010-1.pdf')]),
 dict(id='pellets',name='Пеллеты · шнек и топочная реторта',fuel='Пеллеты',unit='кг',dry_LHV_MJ_kg=19,moisture_percent=8,bulk_kg_L=.65,efficiency=.80,efficiency_range=[.72,.87],max_input_kW=100,min_input_kW=20,aux_W=180,tau_s=25,stock=22.3*.65,geometry='pellets',size_mm=[360,330,400],xyz_mm=[2180,-330,650],dry_mass_kg=60,geometry_basis='Топка, шнек и огнеупор — отдельный резерв прототипа. Паспортный комплект не выбран.',reference='Влажность 8%, насыпная плотность и КПД — гипотезы. LHV пересчитывается по той же формуле влажности.',links=[dict(title='Forest Research: расчёт LHV влажной древесины',url='https://cdn.forestresearch.gov.uk/2022/02/fr_bec_wood_as_fuel_technical_supplement_2010-1.pdf')]),
 dict(id='lpg',name='LPG · газовая горелка и арматура',fuel='LPG',unit='кг',LHV_MJ_kg=25.8/2.02*3.6,density_kg_L=.54,efficiency=.87,efficiency_range=[.82,.90],max_input_kW=91,min_input_kW=35,aux_W=180,tau_s=1,stock=4.25*.54,geometry='gas',size_mm=[350,410,300],xyz_mm=[2180,-330,650],dry_mass_kg=18,geometry_basis='Форма горелки/газовой рампы и малый баллон Ø130×400 мм — размерные резервы, не сертифицированные изделия.',reference='Riello BS2: 35–91 кВт, 180 Вт; LPG 25,8 кВт·ч/Нм³ и 2,02 кг/Нм³. КПД газового парогенератора задан отдельно.',links=[dict(title='Riello BS: топливо и мощности, стр. 3',url='https://www.riello.com/international/products/burners?action=download&id=11ACGABWRF-d1c2d497ef53d36810df9e8cc867411d')]),
 dict(id='electric',name='Электричество · ТЭНы и аккумулятор',fuel='Электроэнергия',unit='кВт·ч',LHV_MJ_kg=3.6,efficiency=.97,efficiency_range=[.94,.99],max_input_kW=60,min_input_kW=0,aux_W=30,tau_s=.2,stock=4,geometry='electric',size_mm=[300,400,260],xyz_mm=[2180,-280,650],dry_mass_kg=12,battery_mass_kg=4/.15,geometry_basis='ТЭНы, силовой шкаф и батарея 4 кВт·ч: расчётные резервы; 150 Вт·ч/кг батареи — гипотеза, не паспорт.',reference='Электрический нагрев почти полностью даёт тепло; потери корпуса, преобразователя и парового цикла остаются. Дымоход не нужен.',links=[dict(title='Chromalox: фланцевые нагреватели',url='https://www.chromalox.com/en/products-and-technologies/industrial-heaters-and-systems/immersion-heaters/flanged-heaters/process-water-and-corrosive-solution-flanged-heaters')])]
for s in sources:
 if 'dry_LHV_MJ_kg' in s:s['LHV_MJ_kg']=s['dry_LHV_MJ_kg']*(1-s['moisture_percent']/100)-.02441*s['moisture_percent']
 s['control_basis']='Одноступенчатый ориентир: в переходном опыте фиксированный максимум при включении, отключение по модельному регулятору. Диапазон каталога означает подбор/настройку, не плавное регулирование.' if s['id'] in ['diesel','lpg'] else 'Регулирование мощности и инерция прототипа заданы гипотезами.'
 s['energy_MJ_per_unit']=s['LHV_MJ_kg'];s['energy_per_unit_J']=s['energy_MJ_per_unit']*1e6
 if s['id']=='electric':s['LHV_MJ_kg']=None
 s['efficiency_basis']='Расчётная оценка переноса энергии топлива в воду/пар на базе LHV, не измеренный КПД этого прототипа; диапазон показывает неопределённость.'
 s['fuel_storage_L']=4.25 if s['id']=='lpg' else 22.3
 s['flue']=None if s['id']=='electric' else dict(inside_mm=80 if s['id'] in ['diesel','lpg'] else 100,wall_C=250 if s['id'] in ['diesel','lpg'] else 350,excess_air=1.4 if s['id'] in ['diesel','lpg'] else 1.8,stoich_air=14.5 if s['id']=='diesel' else 15.7 if s['id']=='lpg' else 6,cp_J_kgK=1100,gas_R_J_kgK=287,friction_factor=.035)
# Mass of the displayed pipes; prototype blower/struts add an explicit 3 kg allowance.
pipes={r['id']:r for r in json.loads((R/'pipe-engineering.json').read_text())['routes']}
def pipe_mass(r):
 L=r['centerline_length_m'];d=r['od']/1000;di=(r.get('inside_id_mm') or 0)/1000;ri=d/2;ro=ri+r['insulation_mm']/1000;j=r['jacket_mm']/1000
 return L*math.pi*((d*d-di*di)*7850/4+(ro*ro-ri*ri)*150+((ro+j)**2-ro**2)*8000)
def route_length(points,radius):
 total=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
 for a,b,c in zip(points,points[1:],points[2:]):
  u=[b[i]-a[i] for i in range(3)];v=[c[i]-b[i] for i in range(3)];angle=math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/(math.dist(a,b)*math.dist(b,c)))))
  total+=radius*(angle-2*math.tan(angle/2))
 return total/1000
base_flue=pipe_mass(pipes['PIPE_FLUE'])+3;base_fuel=pipe_mass(pipes['PIPE_FUEL'])
for source in sources:
 flue=copy.deepcopy(pipes['PIPE_FLUE'])
 if source['flue'] and source['flue']['inside_mm']==100:
  flue.update(od=102,inside_id_mm=100,insulation_mm=55,bend_radius_mm=155)
  flue['centerline_length_m']=route_length(flue['points'],155)
 source['flue_mass_kg']=pipe_mass(flue)+3 if source['flue'] else 0
 fuel=copy.deepcopy(pipes['PIPE_FUEL'])
 if source['id']=='lpg':
  fuel['points'][0][1]=345;fuel['points'][1][1]=345;fuel['centerline_length_m']=route_length(fuel['points'],fuel['bend_radius_mm'])
 source['fuel_pipe_mass_kg']=pipe_mass(fuel) if source['id'] in ['diesel','lpg'] else 0
 source['hardware_mass_delta_kg']=source['dry_mass_kg']-13+source['flue_mass_kg']-base_flue+source['fuel_pipe_mass_kg']-base_fuel
 source['mass_basis']='Плотности трубы 7850, изоляции 150, кожуха 8000 кг/м³ — допущения. Масса показанных трасс плюс 3 кг дымосос/кронштейны; все прочие крепления и усиления пока не взвешены.'
result=dict(status='Сравнение пяти источников; реальные эталоны отделены от размеров/КПД прототипов',sources=sources,assumptions=['КПД всех источников на LHV; КПД горелки не равен КПД машины. Не переносятся AFUE или КПД конденсационного отопительного котла на горячий пар.','Дрова и пеллеты зависят от влажности; мощность топки запаздывает, накопленное тепло продолжается при останове.','Габариты топлива, горелок, аккумулятора и масс различаются. Дровяная топка и газовый резерв ещё не выбраны как изделия.','Замкнутый водопаровой контур: конденсатный насос, возврат 99,9%, улавливание пускового пара 99,5%. Это целевые гипотезы герметичности, а не гарантированный ресурс.','Дымовые газы выходят наружу через выпуск; замкнутость воды не означает замкнутую камеру сгорания.'])
(R/'heat-sources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Heat sources:',len(sources))
