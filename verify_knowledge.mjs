import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createSearchIndex} from './web/search-core.js';
const checks=[],test=(name,pass,detail)=>{checks.push({name,pass:!!pass,detail});assert.ok(pass,name);};
const manifest=JSON.parse(fs.readFileSync('docs/knowledge-manifest.json')),buffers={};
for(const [name,a]of Object.entries(manifest.assets)){const b=fs.readFileSync('docs/'+a.path);test(name+' matches byte count and SHA-256',b.byteLength===a.bytes&&createHash('sha256').update(b).digest('hex')===a.sha256);buffers[name]=b;}
const model=JSON.parse(buffers.model),chunks=JSON.parse(buffers.passages),float=b=>new Float32Array(b.buffer,b.byteOffset,b.byteLength/4),basis=float(buffers.basis),vectors=float(buffers.vectors),index=createSearchIndex(model,chunks,basis,vectors);
test('Corpus covers at least 20 project sources',manifest.source_count>=20);
test('Corpus has at least 500 actual passages',chunks.length>=500&&chunks.length===manifest.passage_count);
test('Index contains actual 96-dimensional floating-point document vectors',model.rank===96&&vectors.length===chunks.length*96);
let maxNormError=0;for(let i=0;i<chunks.length;i++){let norm=0;for(let j=0;j<96;j++)norm+=vectors[i*96+j]**2;maxNormError=Math.max(maxNormError,Math.abs(norm-1));}
test('Cosine vectors are normalized',maxNormError<1e-5,maxNormError);
const cases=[
 ['Как рассчитаны обороты колёс',r=>/Обороты колёс/.test(r.title)],
 ['Как работает двигатель двойного действия',r=>r.url==='assembly.html#doubleActingPanel'],
 ['steam engine double acting',r=>r.url==='assembly.html#doubleActingPanel'],
 ['Масса нагрузка на каждое колесо',r=>r.url.startsWith('physics.html')&&/Нагрузка/.test(r.title)],
 ['Теплопотери изоляции трубы',r=>r.url.startsWith('piping.html')&&/Теплопотери|сопротивление/.test(r.title)],
 ['Белов баланс энергии фазовый переход',r=>r.source==='thermal-reference.json'],
 ['Белов энтропия необратимость',r=>r.source==='thermal-reference.json'],
 ['Дрова расход влажность',r=>r.url.startsWith('heat.html')],
 ['Где купить насос',r=>r.source==='component-purchases.json'],
 ['Конденсатор теплоотвод ограничения',r=>r.url.startsWith('literature.html')],
 ['Дизель расход топлива',r=>r.url.startsWith('heat.html')||r.url.startsWith('report.html')],
 ['Как изменяется температура при конденсации',r=>r.url==='physics.html#node-CND'],
 ['Где хранить воду',r=>r.url==='physics.html#node-WTR'],
 ['Стыки труб герметичность',r=>r.source==='connection-specs.json'],
];
for(const [query,wanted]of cases){const results=index.query(query,{limit:5});test('Relevant source retrieved: '+query,results.some(wanted),results.map(r=>({title:r.title,url:r.url})));}
test('No invented answer for an unsupported topic',index.query('квантовый звездолёт Марса').length===0);
test('Empty and stopword-only queries return no passages',index.query('').length===0&&index.query('и в на что').length===0);
test('Retrieved text is exactly an indexed source passage',index.query('Теплопотери труб').every(r=>chunks.some(c=>c.id===r.id&&c.text===r.text)));
test('Search links remain inside project sources',chunks.every(c=>!/^(https?:|javascript:|data:)/i.test(c.url)&&!c.url.includes('..')));
test('Full external books are not in the public corpus',!Object.keys(manifest.sources).some(s=>s.endsWith('.pdf')));
for(const [name,s]of Object.entries(manifest.sources)){const path=fs.existsSync('docs/'+name)?'docs/'+name:name;test('Indexed source provenance: '+name,createHash('sha256').update(fs.readFileSync(path)).digest('hex')===s.sha256);}
const result={status:'passed',scope:'Project-source retrieval and relevance of representative engineering questions, not a neural LLM or new physics computation.',checks,max_vector_norm_error:maxNormError,manifest_sha256:createHash('sha256').update(fs.readFileSync('docs/knowledge-manifest.json')).digest('hex'),source_sha256:Object.fromEntries(['build_knowledge.py','web/search-core.js','web/search-worker.js','verify_knowledge.mjs'].map(name=>[name,createHash('sha256').update(fs.readFileSync(name)).digest('hex')]))};
fs.writeFileSync('knowledge-checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length,passages:chunks.length,sources:manifest.source_count,dimension:model.rank}));
