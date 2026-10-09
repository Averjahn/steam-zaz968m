const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'../tower-battle/node_modules/playwright-core');
const fs=require('node:fs'),assert=require('node:assert/strict');
const base=process.env.ZAZ_TEST_URL||'http://127.0.0.1:8768/docs/';
const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--enable-unsafe-swiftshader']});
 const checks=[],errors=[];const test=(name,ok)=>{assert.ok(ok,name);checks.push({name,passed:true});console.log(name);};
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000},ignoreHTTPSErrors:true});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'assembly.html',{timeout:120000});await page.waitForFunction(()=>window.steamAssemblyProject?.systems,{timeout:120000});
  const pose=()=>page.evaluate(()=>{const p=window.steamAssemblyProject;return {position:p.camera.position.toArray(),quaternion:p.camera.quaternion.toArray(),fov:p.camera.fov,locked:p.cameraNavigation.locked,orbit:p.controls.enabled,rotation:document.getElementById('rotationMode').value};});
  const canvas=page.locator('#cadViewport canvas');
  async function drag(dx,dy,button='left'){
   await canvas.scrollIntoViewIfNeeded();const box=await canvas.boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
   await page.mouse.move(x,y);await page.mouse.down({button});await page.mouse.move(x+dx,y+dy,{steps:12});await page.mouse.up({button});await page.waitForTimeout(250);
  }
  const initial=await pose();await page.locator('#cameraLockToggle').click();const locked=await pose();
  test('Lock freezes exact eye without an initial jump',locked.locked&&!locked.orbit&&distance(initial.position,locked.position)<1e-8&&distance(initial.quaternion,locked.quaternion)<1e-8);
  test('Lock is accessible and disables the orbit direction selector',await page.locator('#cameraLockToggle').getAttribute('aria-pressed')==='true'&&await page.locator('#rotationMode').isDisabled());
  await drag(130,45);const looked=await pose();test('Dragging changes only viewing direction',distance(locked.position,looked.position)<1e-8&&distance(locked.quaternion,looked.quaternion)>.01);
  test('Dragging right turns the gaze to camera right',await page.evaluate(q=>{const p=window.steamAssemblyProject,T=p.camera.position.constructor,forward=new T(0,0,-1).applyQuaternion(p.camera.quaternion.clone().fromArray(q)),right=forward.clone().cross(p.camera.up).normalize(),now=p.camera.getWorldDirection(new T());return now.sub(forward).dot(right)>0;},locked.quaternion));
  const beforePan=await pose();await drag(100,-30,'right');await drag(-100,40,'middle');const noPan=await pose();test('Right and middle drag cannot move a fixed camera',distance(beforePan.position,noPan.position)<1e-8&&distance(beforePan.quaternion,noPan.quaternion)<1e-8);
  await canvas.hover();await page.mouse.wheel(0,-240);await page.waitForTimeout(250);const zoomed=await pose();test('Wheel changes field of view without dolly',zoomed.fov<noPan.fov&&distance(zoomed.position,locked.position)<1e-8);
  await canvas.focus();await page.keyboard.press('ArrowLeft');const keyed=await pose();test('Arrow keys turn the gaze from the same eye',distance(keyed.position,locked.position)<1e-8&&distance(keyed.quaternion,zoomed.quaternion)>.001);
  await page.setViewportSize({width:1260,height:900});await page.waitForTimeout(500);test('Resize keeps fixed camera position and orientation',distance((await pose()).position,keyed.position)<1e-8&&distance((await pose()).quaternion,keyed.quaternion)<1e-8);
  await page.locator('#fullscreenToggle').click();await page.waitForTimeout(600);test('Fullscreen keeps the lock and eye',await page.locator('#cameraLockToggle').isVisible()&&(await pose()).locked&&distance((await pose()).position,keyed.position)<1e-8);await page.locator('#fullscreenToggle').click();await page.waitForTimeout(500);
  const beforeUnlock=await pose();await page.locator('#cameraLockToggle').click();await page.waitForTimeout(500);const unlocked=await pose();test('Unlock restores orbit with no pose jump and keeps direction preference',!unlocked.locked&&unlocked.orbit&&distance(unlocked.position,beforeUnlock.position)<1e-8&&distance(unlocked.quaternion,beforeUnlock.quaternion)<1e-6&&unlocked.rotation===initial.rotation);
  await drag(100,0);test('Normal orbit moves the eye again',distance((await pose()).position,unlocked.position)>10);
  // Capture while damping is still settling, and check for later drift.
  await page.locator('#cameraLockToggle').click();const settling=await pose();await page.waitForTimeout(1200);test('Pending orbit damping cannot move the locked eye',distance((await pose()).position,settling.position)<1e-8);
  await page.locator('#componentView').selectOption('ENG');await page.waitForTimeout(500);test('Explicit component navigation releases lock',!(await pose()).locked);
  await page.locator('#cameraLockToggle').click();const isolated=await pose();await page.setViewportSize({width:1440,height:1000});await page.waitForTimeout(500);test('Resize of isolated component does not recenter locked eye',distance((await pose()).position,isolated.position)<1e-8);
  await page.locator('#viewTop').evaluate(e=>e.click());test('Preset view releases lock',!(await pose()).locked);
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,ignoreHTTPSErrors:true}),mobile=await context.newPage();mobile.on('pageerror',e=>errors.push(e.message));
  await mobile.goto(base+'assembly.html?component=ENG',{timeout:120000});await mobile.waitForFunction(()=>window.steamAssemblyProject?.systems,{timeout:120000});await mobile.locator('#cameraLockToggle').tap();const mobilePose=()=>mobile.evaluate(()=>{const p=window.steamAssemblyProject;return {position:p.camera.position.toArray(),quaternion:p.camera.quaternion.toArray(),fov:p.camera.fov};});
  const m0=await mobilePose(),mc=mobile.locator('#cadViewport canvas');await mc.scrollIntoViewIfNeeded();const rect=await mc.boundingBox(),x=rect.x+rect.width/2,y=rect.y+rect.height/2,cdp=await context.newCDPSession(mobile);
  const touch=(type,points)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points.map((q,i)=>({x:q[0],y:q[1],id:i}))});
  await touch('touchStart',[[x,y]]);await touch('touchMove',[[x+45,y-35]]);await touch('touchEnd',[]);const m1=await mobilePose();test('Touch drag rotates fixed-eye gaze',distance(m0.position,m1.position)<1e-8&&distance(m0.quaternion,m1.quaternion)>.01);
  await touch('touchStart',[[x-30,y],[x+30,y]]);await touch('touchMove',[[x-60,y],[x+60,y]]);await touch('touchEnd',[]);const m2=await mobilePose();test('Pinch zoom changes FOV without translation',distance(m0.position,m2.position)<1e-8&&m2.fov<m1.fov);
  test('Camera toolbar fits a narrow screen',await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  test('No browser exceptions',errors.length===0);
  const result={status:'passed',checks,url:base,errors};fs.writeFileSync('camera-navigation-checks.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:'passed',checks:checks.length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
