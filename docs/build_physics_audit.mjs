import fs from 'node:fs';
import {selectCalculation} from './web/calculation-model.js';
const data=JSON.parse(fs.readFileSync(new URL('./results.json',import.meta.url)));
data.target_layout=JSON.parse(fs.readFileSync(new URL('./layout.json',import.meta.url)));
const scenarios=data.scenarios.map(s=>({case:s.case.id,modes:[
 {mode:'rated',speed:s.case.target_kmh},
 {mode:'road',speed:s.case.target_kmh},
 {mode:'road',speed:20},
 {mode:'road',speed:0}
].map(options=>{const c=selectCalculation(data,{caseId:s.case.id,...options});return {...options,transmission:c.transmission,checks:c.checks,drive_kW:c.drive,gross_engine_kW:c.cycle.values.gross_engine_kW,burner_kW:c.cycle.burner,net_efficiency:c.cycle.eta,condenser_kW:c.cycle.values.condenser_kW,air_m3_s:c.cycle.values.air_m3_s,pump_flow_L_min:c.cycle.values.pump_flow,pump_rpm:c.cycle.values.pump_rpm};})}));
fs.writeFileSync(new URL('./physics-audit.json',import.meta.url),JSON.stringify({date:'2026-10-08',status:'Арифметика проверена; физическая реализуемость не установлена',corrections:['III передача исправлена с 1,489 на 1,409 по разделу коробки передач и руководству по ремонту','Обороты колёс, входа КПП и машины разделены; добавлены выбор передачи и отношение адаптера','Проверены нижние пределы горелки, давление и обороты насоса; проверка максимума недостаточна'],sources:{zaz:'https://djvu.online/file/yS7dQhMxx1lMm',repair:'https://ru.scribd.com/document/541582918/Автомобиль-ЗАЗ-968М-Запорожец',pump:'https://www.catpumps.com/sites/default/files/2025-09/5CP2120W_L.pdf',hot_water:'https://www.catpumps.com/sites/default/files/2025-12/TB002_B.pdf',burner:'https://www.riello.com/international/products/commercial-boilers?action=download&id=3474633-be830acd70075689c19a0b24d7b1ef8c'},limitations:['Расчёт при нулевой скорости — формальная стационарная нагрузка вспомогательных систем, а не модель пуска или холостого хода','Радиус качения, КПД, обдув, массы и осевые нагрузки требуют измерений или паспортов','Для выбранных P/T нет конкретной паровой машины и парогенератора; нет карты мощности/расхода','Нет характеристики конденсатора при расчётных температуре, расходе и сопротивлении','Фактическая внутренняя геометрия кузова и крепления не подтверждены'],scenarios},null,2)+'\n');
console.log('Built physical audit: nominal, target cruise, 20 km/h and stationary screening for A/B/C');
