export function attachFullscreenViewer(stage){
 const button=document.getElementById('fullscreenToggle'),panel=document.getElementById('fullscreenControls'),controls=document.getElementById('cadViewerControls');
 let fallback=false,busy=false,savedFocus=null,savedScroll=null;
 const nativeElement=()=>document.fullscreenElement||document.webkitFullscreenElement;
 const isActive=()=>fallback||nativeElement()===stage;
 function sync(){const active=isActive();stage.classList.toggle('viewer-fullscreen',active);document.body.classList.toggle('viewer-expanded',fallback);button.textContent=active?'Выйти из полного экрана':'На весь экран';button.setAttribute('aria-pressed',String(active));panel.hidden=!active;if(!active){stage.classList.remove('viewer-controls-open');panel.setAttribute('aria-expanded','false');panel.textContent='Управление';if(savedFocus){savedFocus.focus({preventScroll:true});savedFocus=null;}if(savedScroll){const pos=savedScroll;savedScroll=null;requestAnimationFrame(()=>window.scrollTo(pos.x,pos.y));}}}
 panel.onclick=()=>{const open=stage.classList.toggle('viewer-controls-open');panel.setAttribute('aria-expanded',String(open));panel.textContent=open?'Скрыть управление':'Управление';if(!open&&controls.contains(document.activeElement))panel.focus();};
 async function exit(){if(fallback){fallback=false;sync();}else{const leave=document.exitFullscreen||document.webkitExitFullscreen;if(leave)await leave.call(document);sync();}}
 button.onclick=async()=>{if(busy)return;busy=true;try{if(isActive())await exit();else{savedFocus=document.activeElement;savedScroll={x:scrollX,y:scrollY};const enter=stage.requestFullscreen||stage.webkitRequestFullscreen;try{if(!enter)throw Error('Use viewport mode');await enter.call(stage);}catch{fallback=true;}sync();button.focus({preventScroll:true});}}finally{busy=false;}};
 document.addEventListener('fullscreenchange',sync);document.addEventListener('webkitfullscreenchange',sync);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&fallback){e.preventDefault();exit();}else if(e.key==='Tab'&&isActive()){const items=[...stage.querySelectorAll('button,input,select,a[href],[tabindex]')].filter(o=>!o.disabled&&o.tabIndex>=0&&o.getClientRects().length),first=items[0],last=items.at(-1);if(first&&(!stage.contains(document.activeElement)||(e.shiftKey?document.activeElement===first:document.activeElement===last))){e.preventDefault();(e.shiftKey?last:first).focus();}}});
 sync();
}
