// Shared cards for the 3D selection and the procurement register.
const labels={product:'Товар',material:'Материалы',catalogue:'Каталог',inquiry:'Запрос изготовителю',documentation:'Документация'};
const statuses={custom:'Проект / изготовление',candidate:'Конкретный размерный кандидат',retained:'Сохраняем штатное',choice:'Выбрать готовое изделие'};
const markets={FI:'Финляндия',EU:'Европа',RU:'Россия',ALL:'Изготовитель / все регионы'};
const element=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
export async function loadPurchases(){const r=await fetch('component-purchases.json?v=d0a5e72512a8');if(!r.ok)throw Error('Каталог покупок: HTTP '+r.status);return r.json();}
export function purchaseRecord(data,id){return data?.components?.[id]||{id,name:'Импортированная деталь',status:'choice',description:'Изделие не идентифицировано. Для ссылки на покупку нужны изготовитель, артикул и технические данные.',requirements:[],links:[]};}
export function renderPurchaseCard(container,record,{market='all',node='',layer='',checked=''}={}){
 container.replaceChildren();container.dataset.selectionId=record.id;container.dataset.selectionNode=node;container.dataset.selectionLayer=layer;
 container.append(element('span',statuses[record.status]||record.status,'purchase-badge'));
 if(node)container.append(element('p','Конкретная деталь: '+node,'purchase-node'));
 if(layer)container.append(element('p','Выбран слой: '+({pipe:'труба',insulation:'теплоизоляция',jacket:'защитный кожух'}[layer]||layer),'purchase-node'));
 container.append(element('p',record.description));
 if(record.requirements.length){const ul=element('ul',null,'purchase-requirements');for(const text of record.requirements)ul.append(element('li',text));container.append(ul);}
 const relevant=record.links.filter(l=>market==='all'||l.markets.includes('ALL')||(market==='eu'&&l.markets.some(x=>['FI','EU'].includes(x)))||(market==='ru'&&l.markets.includes('RU')));
 // Show purchase/material/supplier links first; documentation stays available below.
 const sorted=relevant.toSorted((a,b)=>Number(a.kind==='documentation')-Number(b.kind==='documentation')||Number(b.layer===layer&&!!layer)-Number(a.layer===layer&&!!layer));
 if(!relevant.some(l=>l.kind!=='documentation'))container.append(element('p','Для этого региона ссылка на покупку пока не найдена; ниже доступна документация.','fine-print'));
 const list=element('ul',null,'purchase-links');
 for(const l of sorted){const item=element('li');let url;try{url=new URL(l.url);}catch{continue;}if(url.protocol!=='https:')continue;
  const a=element('a',l.title+' ↗');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';a.dataset.linkKind=l.kind;item.append(a,element('span',labels[l.kind]+' · '+l.markets.map(m=>markets[m]).join(' / '),'purchase-link-type'));
  if(l.note)item.append(element('span',l.note,'purchase-link-note'));if(layer&&l.layer===layer)item.classList.add('purchase-layer-match');list.append(item);
 }
 if(!list.children.length)container.append(element('p','Для этого региона проверенной ссылки пока нет. Выберите «Все» или запросите поставщика у изготовителя.','fine-print'));else container.append(list);
 container.append(element('p','Ссылка не подтверждает посадку, наличие или доставку. '+(checked?'Источники просмотрены '+checked+'.':''),'fine-print'));
}
