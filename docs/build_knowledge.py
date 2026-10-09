"""Reproducible local TF-IDF + latent semantic analysis index. No hosted API."""
from pathlib import Path
from html.parser import HTMLParser
from collections import Counter
import hashlib
import json
import re
import numpy as np

STOP = 'и в во на для с со к ко из по от до у о об обо а но или как что это то так же не нет да при мы наш наши нам где какой какая какие зачем чем чтобы можно нужно необходимо будет будут который которые ли все всего уже еще теперь здесь этого этих через только также например the a an of to in and or is are for with how what why'.split()
ENDINGS = ['иями','ями','ами','ого','ему','ому','ость','ости','ить','ать','ять','ов','ах','ях','ая','яя','ое','ее','ый','ий','ой','ые','ие','ей','ем','ом','ам','ям','ию','ия','ся','ет','ют','ит','ат','ят','ли','ла','ло','а','я','ы','и','у','ю','е','о']
ALIASES = {'rpm':'оборот','обмин':'оборот','оборот':'оборот','движок':'двигател','motor':'двигател','engine':'двигател','steam':'пар','boiler':'парогенератор','котел':'парогенератор','condens':'конденсатор','condenser':'конденсатор','pipe':'труб','трубк':'труб','pump':'насос','water':'вод','heat':'тепл','temperature':'температур','температура':'температур','pressure':'давлен','diesel':'дизел','wood':'дров','fuel':'топлив','wheel':'колес','wheels':'колес','thermal':'тепл','изоляц':'изоляц','double':'двойн','acting':'действ','действи':'действ','купить':'покуп','покупк':'покуп','buy':'покуп'}
ALIASES.update({'куп':'покуп','вращен':'оборот','вращени':'оборот','хранен':'хран','joint':'стык','joints':'стык','sealing':'герметичн','герметичност':'герметичн'})

def tokenize(text):
    words=[]
    for word in re.findall(r'[a-zа-я0-9_]+',text.lower().replace('ё','е')):
        if word in STOP or len(word)<2 or word.isdigit():continue
        if re.search('[а-я]',word):
            for ending in ENDINGS:
                if word.endswith(ending) and len(word)-len(ending)>=3:
                    word=word[:-len(ending)];break
        words.append(ALIASES.get(word,word))
    return words

class Sections(HTMLParser):
    def __init__(self):
        super().__init__();self.main=False;self.ignore=0;self.heading=None;self.heading_parts=[];self.title='';self.anchor='';self.parts=[];self.sections=[];self.title_parts=[];self.in_title=False;self.details=[];self.detail_names=[]
    def flush(self):
        text=re.sub(r'[ \t]+',' ',' '.join(self.parts)).strip()
        if text:self.sections.append((self.title,self.anchor,text))
        self.parts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.in_title=True
        if tag=='main':self.main=True
        if not self.main:return
        if tag in ['script','style','svg','select','button','input','nav']:self.ignore+=1 if tag not in ['input'] else 0
        if self.ignore:return
        if tag=='details':self.details.append(a.get('id',''));self.detail_names.append('')
        if tag in ['h1','h2','h3','summary']:
            self.flush();self.heading=tag;self.heading_parts=[];self.anchor=a.get('id','') or (self.details[-1] if tag=='summary' and self.details else '')
        if tag in ['p','li','div','tr','article','code']:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag in ['script','style','svg','select','button','nav'] and self.ignore:self.ignore-=1;return
        if self.ignore:return
        if tag==self.heading:
            self.title=''.join(self.heading_parts).strip()
            if tag=='summary' and self.detail_names:self.detail_names[-1]=self.title
            if tag=='h3' and self.detail_names and self.detail_names[-1].startswith('PIPE_'):self.title=self.detail_names[-1]+' · '+self.title
            self.parts.append(self.title);self.heading=None
        if tag=='details' and self.details:self.details.pop();self.detail_names.pop()
        if tag in ['p','li','tr','article','code']:self.parts.append('\n')
        if tag=='main':self.flush();self.main=False
    def handle_data(self,text):
        if self.in_title:self.title_parts.append(text)
        if not self.main or self.ignore:return
        if self.heading:self.heading_parts.append(text)
        else:self.parts.append(text)

def readable(value):
    if isinstance(value,dict):return '\n'.join(k.replace('_',' ') + ': '+readable(v) for k,v in value.items() if k not in ['sha256','input_sha256','file_sha256','url','sources','points','xyz_mm','mass_rows','h_sensitivity'])
    if isinstance(value,list):return '; '.join(readable(v) for v in value)
    return str(value)

def build_knowledge(root,out):
    chunks=[];sources={};seen=set()
    def add(title,text,url,category,source,context=''):
        text=re.sub(r'[ \t]+',' ',text).strip()
        if len(text)<45:return
        text=text.replace('\r','')
        # Bounded passages keep long tables and formula lists useful without huge responses.
        words=text.split();pieces=[];current=[];size=0
        if len(text)<=1450:pieces=[text];words=[]
        for word in words:
            if size+len(word)>1450 and current:
                pieces.append(' '.join(current));current=current[-20:];size=sum(len(v)+1 for v in current)
            current.append(word);size+=len(word)+1
        if current:pieces.append(' '.join(current))
        for piece in pieces:
            key=(url,piece)
            if key in seen:continue
            seen.add(key);chunks.append({'id':'k'+str(len(chunks)+1),'title':title,'text':piece,'url':url,'category':category,'source':source,'context':context})
    categories={'fitted-engine.html':'Семь цилиндров по свободному месту в кузове','compact-radial.html':'Компактная звезда и размещение двигателя','aging.html':'Старение, ресурс и зимняя эксплуатация','engine-sizing.html':'Размеры и мощность двигателя','radial-engine.html':'Паровая машина и рабочий объём','assembly.html':'3D и симуляция','heat.html':'Источники тепла','physics.html':'Физика','piping.html':'Трубопроводы','procurement.html':'Комплектующие','literature.html':'Литература','report.html':'Отчёт','internal.html':'Компоновка','packaging.html':'Компоновка','reconstruction.html':'Кузов','user-model.html':'Кузов','calculations.html':'Расчёты','lab.html':'Архив сценариев','literature-audit.html':'Литература'}
    for name,category in categories.items():
        path=out/name
        if not path.exists():continue
        raw=path.read_text();parser=Sections();parser.feed(raw);parser.flush();source=''.join(parser.title_parts).split('—')[0].strip()
        sources[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'kind':'HTML','title':source}
        for title,anchor,text in parser.sections:add(title or source,text,name+('#'+anchor if anchor else ''),category,source)
    def load(name):
        path=root/name;sources[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'kind':'JSON','title':name};return json.loads(path.read_text())
    groups={'Дорожная нагрузка':'road-formulas','Паровой цикл и тепло':'cycle-formulas','Масса и нагрузки':'mass-formulas','Запас воды и топлива':'range-formulas'}
    for case in load('calculation-workbook.json'):
        for step in case['steps']:
            text='Формула: '+step['formula']+'\nПодстановка: '+step['substitution']+'\nРезультат: '+step['display_value']+' '+step['unit']+'\n'+step.get('terms','')+'\n'+step.get('note','')
            add('Сценарий '+case['case']['id']+' · '+step['title'],text,'calculations.html?scenario='+case['case']['id']+'#formula-'+step['key'],'Формулы','calculation-workbook.json','Номинальная модель сценария '+case['case']['id']+'; не показания текущей симуляции')
    sim=load('simulation-data.json')
    for id,node in sim['nodes'].items():add(id+' · '+node['name'],readable(node),'physics.html#node-'+id,'Физика узлов','simulation-data.json',sim['status'])
    for id,item in load('component-purchases.json')['components'].items():add(id+' · '+item['name'],'Материалы и покупка. '+readable(item),'procurement.html#part-'+id,'Комплектующие','component-purchases.json','Кандидаты и материалы; совместимость требует проверки')
    for route in load('pipe-engineering.json')['routes']:add(route['id']+' · '+route['name'],readable(route),'piping.html','Трубопроводы','pipe-engineering.json','Гипотезы расчёта трубопровода; не пространственная переходная модель')
    for item in load('heat-sources.json')['sources']:add(item['name'],readable(item),'heat.html','Источники тепла','heat-sources.json','Расчётные источники и реальные размерные эталоны')
    book=load('thermal-reference.json')
    for item in book['applications']:add('Белов · '+item['topic'],readable(item)+'\n'+book['book']['title']+'\n'+'\n'.join(book['limitations']),'thermal-reference.json','Литература','thermal-reference.json','Наш разбор книги; полный текст книги не индексирован')
    for item in load('literature-audit.json')['findings']:add(item['title'],readable(item),'literature.html','Литература','literature-audit.json','Проверка и исправления; собственный разбор литературы')
    connections=load('connection-specs.json')
    add('Стыки труб: патрубки, муфты и герметичность',connections['status']+'\n'+readable(connections['limitations']),'connection-specs.json','Трубопроводы','connection-specs.json','Геометрические стыки не подтверждают герметичность или прочность')
    for id,port in connections['ports'].items():add('Стык '+id+' · патрубок трубы',readable(port),'connection-specs.json','Трубопроводы','connection-specs.json','Проектный патрубок; изделие и прочность не подтверждены')
    # Statistics and model fit are deterministic for identical source passages.
    counters=[Counter(tokenize(c['title']+' '+c['title']+' '+c['text'])) for c in chunks]
    df=Counter(w for row in counters for w in row);vocab=sorted(df,key=lambda w:(-df[w],w))[:7000];positions={w:i for i,w in enumerate(vocab)}
    n=len(chunks);idf=np.array([np.log((1+n)/(1+df[w]))+1 for w in vocab],dtype=np.float32);X=np.zeros((n,len(vocab)),dtype=np.float32)
    for i,row in enumerate(counters):
        for w,count in row.items():
            if w in positions:X[i,positions[w]]=(1+np.log(count))*idf[positions[w]]
    X/=np.maximum(np.linalg.norm(X,axis=1,keepdims=True),1e-12)
    rank=min(96,n-1,len(vocab)-1);rng=np.random.default_rng(968);omega=rng.standard_normal((len(vocab),rank+12)).astype(np.float32);Y=X@omega
    for _ in range(2):
        Q,_=np.linalg.qr(Y,mode='reduced');Y=X@(X.T@Q)
    Q,_=np.linalg.qr(Y,mode='reduced');_,_,basis=np.linalg.svd(Q.T@X,full_matrices=False);basis=np.ascontiguousarray(basis[:rank].T,dtype='<f4');vectors=X@basis;vectors/=np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12);vectors=np.ascontiguousarray(vectors,dtype='<f4')
    for i,c in enumerate(chunks):
        indices=np.flatnonzero(X[i]);c['terms']=[[int(j),round(float(X[i,j]),6)] for j in indices]
    folder=out/'knowledge';folder.mkdir(exist_ok=True)
    for old in folder.iterdir():
        if old.is_file():old.unlink()
    assets={}
    def save(label,raw,ext):
        digest=hashlib.sha256(raw).hexdigest();name=label+'-'+digest[:12]+'.'+ext;(folder/name).write_bytes(raw);assets[label]={'path':'knowledge/'+name,'sha256':digest,'bytes':len(raw)}
    save('passages',json.dumps(chunks,ensure_ascii=False,separators=(',',':')).encode(),'json')
    model={'vocabulary':vocab,'idf':idf.tolist(),'rank':rank,'stop':STOP,'endings':ENDINGS,'aliases':ALIASES}
    save('model',json.dumps(model,ensure_ascii=False,separators=(',',':')).encode(),'json');save('basis',basis.tobytes(),'bin');save('vectors',vectors.tobytes(),'bin')
    manifest={'version':1,'method':'TF-IDF + randomized truncated SVD / LSA; normalized cosine vectors + lexical reranking','dimension':rank,'passage_count':n,'source_count':len(sources),'vocabulary_size':len(vocab),'assets':assets,'sources':sources,'total_bytes':sum(v['bytes'] for v in assets.values()),'privacy':'Requests are processed locally in a browser worker; no hosted embedding or LLM service.','rag_scope':'Retrieval with source passages, not generated reasoning or a new calculation. Public project documents and our book summaries; no full third-party books.','training_seed':968,'references':['https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction','https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html']}
    (out/'knowledge-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Knowledge index:',n,'passages,',len(sources),'sources,',rank,'dimensions,',round(manifest['total_bytes']/1024/1024,2),'MB')
    return manifest

if __name__=='__main__':
    root=Path(__file__).resolve().parent;build_knowledge(root,root/'docs')
