import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {runAging} from './web/aging-model.js';
const pipes=JSON.parse(fs.readFileSync('pipe-engineering.json')),sizing=JSON.parse(fs.readFileSync('engine-sizing.json'));
const pressures={PIPE_STEAM:9,PIPE_EXHAUST_R:.2,PIPE_EXHAUST_L:.2,PIPE_RETURN:1,PIPE_BALANCE:1,PIPE_MAKEUP:0,PIPE_SUCTION:1,PIPE_FEED:9,PIPE_FUEL:null,PIPE_FLUE:null,PIPE_RELIEF:9};
const temperatures={PIPE_STEAM:250,PIPE_EXHAUST_R:104.78354962909657,PIPE_EXHAUST_L:104.78354962909657,PIPE_RETURN:60,PIPE_BALANCE:60,PIPE_MAKEUP:25,PIPE_SUCTION:60,PIPE_FEED:60,PIPE_FUEL:25,PIPE_FLUE:250,PIPE_RELIEF:250};
const parts=pipes.routes.filter(p=>p.wall_mm!==null).map(p=>({id:p.id,name:p.name,inside_mm:p.inside_id_mm,outside_mm:p.od,length_m:p.centerline_length_m,hot_C:temperatures[p.id],pressure_bar_g:pressures[p.id],material:null,geometry_basis:'pipe-engineering.json: проектные диаметры, марка металла не выбрана',pressure_basis:'Условный прямой участок: давление среды минус 1 бар внешнего воздуха; приёмник 2 бар abs, выпуск 1,2 бар abs. Насосные пульсации, сброс, гидроудары и вакуум не рассчитаны.'}));
parts.push({id:'STM_COIL',name:'Змеевик генератора · условная стенка',inside_mm:14,outside_mm:22,length_m:null,hot_C:250,pressure_bar_g:9,material:null,geometry_basis:'web/internal-assembly.js: OD22 / ID14; 250 °C — условная верхняя температура металла, не вычисленный перегрев стенки со стороны огня',pressure_basis:'10 бар abs внутри, 1 бар снаружи. Формула прямого цилиндра не учитывает кривизну змеевика.'});
const input={engine_id:'compact-seven',engine_label:'Семь цилиндров Ø32 × 36 мм',crank_rpm:sizing.default_rows[2].crank_rpm,output_ratio:2,parts};
const sources=[
 {title:'University of Western Australia: Lamé cylinder stresses',url:'https://danotes.mech.uwa.edu.au/cylinders/thick/thick.html'},
 {title:'FAA AC 23-13A: cumulative fatigue and supporting tests',url:'https://www.faa.gov/documentLibrary/media/Advisory_Circular/AC_23-13A.pdf'},
 {title:'HSE: corrosion and material selection',url:'https://www.hse.gov.uk/comah/sragtech/techmeasmaterial.htm'},
 {title:'HSE: low-temperature pressure vessels',url:'https://www.hse.gov.uk/pubns/books/hsg93.htm'},
 {title:'Spirax Sarco: winter conditions and trapped condensate',url:'https://www.spiraxsarco.com/promo/winter-ready?sc_lang=en-GB'},
 {title:'Virginia Tech: restrained thermal expansion',url:'https://www.setareh.arch.vt.edu/safas/007_fdmtl_29_stress_due_to_temperature_change.html'},
 {title:'NIST: temperature-dependent steel model',url:'https://www.nist.gov/publications/temperature-dependent-material-modeling-structural-steels-formulation-and-application'}
];
const scenarios=[];for(const climate of ['seasonal','hot','cold'])for(const winter of ['filled','drained','heated']){const v=runAging(input,{climate,winter});scenarios.push({climate,winter,assumptions:v.assumptions,summary:v.summary,system_life:v.system_life});}
const data={date:'2026-10-09',status:'Предварительная модель календарной нагрузки; ресурс и работоспособность автомобиля не подтверждены',input,sources,default_run:runAging(input),scenarios,corrosion_sensitivity:[0,.02,.1,.3].map(rate=>({rate_mm_year:rate,summary:runAging(input,{corrosion_mm_year:rate}).summary})),limitations:[
 '730 расчётных суток по 50 км = 36500 км. Синусоида 5 + 30 cos(2πd/365) — синтетический диапазон −25…+35 °C, не метеоданные Финляндии или России.',
 '50 км/ч и постоянные обороты прежнего теплового режима задают экспозицию; тяга, передачи и достижимость маршрута не моделируются. Ускорения и холостой ход не добавлены.',
 'Один полный цикл поршня на оборот локального кривошипа, два хода при двойном действии. Пусковые циклы труб не равны оборотам двигателя. Общий вал вращается вдвое медленнее.',
 'Потеря стенки 0 / 0,02 / 0,10 / 0,30 мм/год — выбранные сценарии равномерной наружной коррозии, не измеренная скорость. Дорожная соль, химия воды, влажная изоляция и питтинг требуют собственных данных; влияние температуры не выдумано.',
 'E=200 ГПа, α=12·10⁻⁶ К⁻¹, ограничение удлинения 10% — условные постоянные свойства для сравнения. Реальные E(T), α(T), предел текучести, вязкость разрушения, швы и концентрация напряжений неизвестны.',
 'Ламе оценивает только номинальное окружное напряжение прямой цилиндрической стенки; осевые термические напряжения выводятся отдельно. Это не расчёт прочности фланцев, сварки, кривизны или допускаемого давления.',
 'Усталость без кривой S–N остаётся null. Импорт кривой R=0 позволяет лишь сумму Минера для пускового давления выбранной трубы при её горячей температуре; термическая усталость, швы, средние напряжения и общая долговечность остаются неопределёнными.',
 'Для ползучести нужны данные материала σ–T–время. Она не считается нулевой; часы горячего состояния записаны, повреждение null.',
 'Холодная стоянка считается достаточно долгой для выравнивания с воздухом. Ни лёд, ни давление его расширения не вычисляются. Заполненная незащищённая система при воздухе ниже нуля отмечает неразрешённую возможность замерзания.',
 'Осушение предполагается полным и подтверждённым; геометрия слива и остаточные карманы не проверены. Подогрев предполагает поддержание всей водосодержащей зоны ≥+5 °C с UA=5 Вт/К; это гипотеза, не выбранный нагреватель.',
 'Для кузова, подвески, опор, вала и цилиндров нет подтверждённых материалов, толщин и дорожного спектра: их срок службы не определён. Изменение мощности из возраста без измерений износа не назначается.'
],input_sha256:Object.fromEntries(['pipe-engineering.json','engine-sizing.json','web/aging-model.js','web/internal-assembly.js'].map(p=>[p,createHash('sha256').update(fs.readFileSync(p)).digest('hex')]))};
fs.writeFileSync('aging-study.json',JSON.stringify(data,null,2)+'\n');
fs.writeFileSync('aging-fatigue-template.json',JSON.stringify({component_id:'PIPE_STEAM',material:'Укажите марку и состояние материала',reference:'Укажите протокол испытаний или точный источник',stress_ratio_R:0,temperature_range_C:[250,250],stress_definition:'Номинальная амплитуда окружного напряжения прямой трубы; пуск 0 → рабочее давление',points:[]},null,2)+'\n');
console.log(JSON.stringify({km:data.default_run.summary.km,crank_cycles:data.default_run.summary.crank_cycles_per_cylinder,frost_days:data.default_run.summary.frost_exposure_days,scenarios:scenarios.length}));
