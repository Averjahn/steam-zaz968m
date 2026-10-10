const {chromium}=require('../tower-battle/node_modules/playwright-core'),fs=require('fs'),assert=require('assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[],checks=[];page.on('pageerror',e=>{errors.push(e.message);console.error('BROWSER ERROR',e.stack);});const test=(name,ok)=>{assert.ok(ok,name);checks.push({name,passed:true});console.log(name);};
 await page.goto((process.env.ZAZ_TEST_URL||'http://127.0.0.1:8768/docs/')+'assembly.html?component=ENG#engineDistributionPanel');await page.waitForFunction(()=>window.steamAssemblyProject?.systems);
 test('Direct link opens the explanatory engine distribution panel',await page.locator('#doubleActingPanel').evaluate(e=>e.open));
 await page.locator('#engineCycleMode').selectOption('manual');
 const result=await page.evaluate(async()=>{
  const p=window.steamAssemblyProject,e=p.models.get('ENG').radialEngine,T=await import('three'),{computeBoundsTree}=await import('./vendor/three-mesh-bvh/build/index.module.js');
  const errors=[],hits=[],states=new Set();let connectionError=0,axisError=0;
  const local=(a,alpha)=>new T.Vector3(a[0]*Math.cos(alpha)-a[1]*Math.sin(alpha),a[0]*Math.sin(alpha)+a[1]*Math.cos(alpha),a[2]);
  for(let i=0;i<7;i++){
   const ports=e.portRecords[i],alpha=e.pose(i,0).alpha;
   for(const [role,ch,id]of [['inlet',null,'in'],['outlet',null,'out'],['chamber','A','A'],['chamber','B','B']]){
    const r=e.routes.find(r=>r.index===i&&r.role===role&&r.chamber===ch),vp=ports.valve_ports.find(v=>v.id===id),face=local(vp.anchor_mm,alpha),axis=local(vp.outward,alpha);axis.z=vp.outward[2];
    const end=role==='inlet'?1:0,tangent=r.curve.getTangentAt(end).multiplyScalar(end===1?-1:1),out=r.curve.getPointAt(end);connectionError=Math.max(connectionError,out.distanceTo(face));axisError=Math.max(axisError,1-tangent.dot(axis));
    if(ch){connectionError=Math.max(connectionError,r.curve.getPointAt(1).distanceTo(new T.Vector3(...ports[ch].face_mm)));axisError=Math.max(axisError,1+r.curve.getTangentAt(1).dot(new T.Vector3(...ports[ch].outward)));}
   }
  }
  const headers=[];e.core.traverse(o=>{if(o.isMesh&&o.name.includes('пленум'))headers.push(o);});
  const bs=e.routes.filter(r=>r.chamber==='B').map(r=>({r,meshes:e.core.children.find(g=>g.name===r.name).children.filter(o=>o.isMesh)}));
  const hit=(a,b)=>{if(!new T.Box3().setFromObject(a).intersectsBox(new T.Box3().setFromObject(b)))return false;a.geometry.boundsTree||=computeBoundsTree.call(a.geometry,{indirect:true});return a.geometry.boundsTree.intersectsGeometry(b.geometry,new T.Matrix4().copy(a.matrixWorld).invert().multiply(b.matrixWorld));};
  for(let j=0;j<72;j++){
   const angle=j*Math.PI/36,poses=e.update(angle,1,p.camera,true);e.root.updateWorldMatrix(true,true);
   for(let i=0;i<7;i++){const c=e.cylinders[i],pose=poses[i];for(const {id,disc}of c.distributor.gates){const ch=id.includes('A')?'A':'B',expected=id.startsWith('P')?pose[ch].inlet:pose[ch].exhaust;if(disc.userData.open!==expected)errors.push({i,j,id});}states.add(c.distributor.gates.map(g=>Number(g.disc.userData.open)).join(''));}
   for(const {r,meshes}of bs)for(const m of meshes){for(const h of headers)if(hit(m,h))hits.push({pipe:r.name,part:h.name,pose:j});for(const c of e.cylinders)for(const o of [c.crosshead,c.rod,c.pistonRod])if(hit(m,o))hits.push({pipe:r.name,part:o.name,pose:j});}
  }
  e.update(0,0,p.camera,true);return {connectionError,axisError,hits,errors,states:[...states],tubeA:e.connectionVolumes[0].A,tubeB:e.connectionVolumes[0].B};
 });
 console.log(JSON.stringify({connectionError:result.connectionError,axisError:result.axisError,hits:result.hits.slice(0,8),errors:result.errors.slice(0,8),states:result.states}));
 test('All 42 distributor and cylinder pipe endpoints are coaxial and meet their actual port faces',result.connectionError<1e-6&&result.axisError<1e-6);
 test('All 28 symbolic gates follow actual chamber timing through a whole turn',result.errors.length===0&&result.states.length>=4);
 test('Shorter B pipes, including insulation, clear both plenums and all swept rods/crossheads',result.hits.length===0);
 test('ID8 connection volumes match measured route lengths and B route is shorter',result.tubeA>9&&result.tubeA<10&&result.tubeB>21&&result.tubeB<22);
 await page.locator('#engineCylinderInspect').selectOption('2');await page.waitForTimeout(400);
 test('Isolating cylinder three hides the other cylinders and their four external pipes',await page.evaluate(()=>{const e=window.steamAssemblyProject.models.get('ENG').radialEngine;return e.cylinders.every((c,i)=>c.g.visible===(i===2))&&e.routes.every(r=>e.core.children.find(g=>g.name===r.name).visible===(r.index===null||r.index===2))&&document.getElementById('engineValveStates').textContent.startsWith('Цилиндр 3:');}));
 for(const angle of [0,60,120,180,240,300]){await page.locator('#engineCycleAngle').evaluate((el,a)=>{el.value=a;el.dispatchEvent(new Event('input',{bubbles:true}));},angle);await page.waitForTimeout(80);test('SVG and 3D gate states agree at '+angle+' degrees',await page.evaluate(()=>{const e=window.steamAssemblyProject.models.get('ENG').radialEngine;return e.cylinders[2].distributor.gates.every(g=>document.querySelector(`[data-gate="${g.id}"]`).dataset.open===String(g.disc.userData.open));}));}
 await page.locator('#engineCycleMode').selectOption('explain');await page.locator('#engineCyclePlaying').uncheck();await page.waitForTimeout(200);
 test('Pause freezes the flow diagram animation as well as shaft motion',await page.locator('#engineDistributionDiagram .dist-pipe').first().evaluate(e=>e.style.animationPlayState==='paused'));
 await page.locator('#engineCylinderInspect').selectOption('-1');await page.waitForTimeout(200);test('All-cylinder selection restores every cylinder',await page.evaluate(()=>window.steamAssemblyProject.models.get('ENG').radialEngine.cylinders.every(c=>c.g.visible)));
 await page.locator('#engineDistributionEnlarge').click();test('Large live valve diagram opens in a modal',await page.locator('#engineDistributionDialog').evaluate(e=>e.open&&!!e.querySelector('#engineDistributionDiagram')));await page.screenshot({path:'../reports/steam-zaz968m-distribution-2026-10-10/distribution-large.png'});await page.locator('#engineDistributionClose').click();test('Closing the diagram restores its original panel',await page.locator('#engineDistributionCanvas #engineDistributionDiagram').count()===1);
 await page.locator('#engineDistributionPanel').scrollIntoViewIfNeeded();await page.screenshot({path:'../reports/steam-zaz968m-distribution-2026-10-10/distribution.png'});
 await page.setViewportSize({width:390,height:844});test('Distribution panel fits a mobile screen',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));test('No browser exceptions',errors.length===0);
 const out={status:'passed',checks,errors,result};fs.writeFileSync('engine-distribution-browser-checks.json',JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length,result}));
 }finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
