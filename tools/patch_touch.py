from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
a="  document.getElementById('dashBtn').addEventListener('pointerdown',dash);"
patch=r'''  document.getElementById('dashBtn').addEventListener('pointerdown',dash);

  // iPhone/iPad Safari native touch fallback.
  // Track each thumb independently so movement cannot hijack aim/fire.
  document.querySelector('.touch').style.pointerEvents='auto';
  pad.style.touchAction='none';
  fireBtn.style.touchAction='none';
  const dashTouchBtn=document.getElementById('dashBtn');
  dashTouchBtn.style.touchAction='none';

  let moveTouchId=null;
  let fireTouchId=null;
  const firstChanged=e=>(e.changedTouches&&e.changedTouches.length)?e.changedTouches[0]:null;
  const byId=(list,id)=>{
    if(id===null||!list)return null;
    for(let i=0;i<list.length;i++) if(list[i].identifier===id) return list[i];
    return null;
  };
  const changedHas=(e,id)=>!!byId(e.changedTouches,id);

  const resetJoy=()=>{
    moveTouchId=null;
    state.joy={x:0,y:0,active:false};
    knob.style.transform='translate(0,0)';
  };

  pad.addEventListener('touchstart',e=>{
    e.preventDefault();
    if(moveTouchId!==null)return;
    const t=firstChanged(e); if(!t)return;
    moveTouchId=t.identifier;
    joyPoint(t.clientX,t.clientY);
  },{passive:false});

  pad.addEventListener('touchmove',e=>{
    e.preventDefault();
    const t=byId(e.touches,moveTouchId);
    if(t) joyPoint(t.clientX,t.clientY);
  },{passive:false});

  const endMove=e=>{
    e.preventDefault();
    if(changedHas(e,moveTouchId)) resetJoy();
  };
  pad.addEventListener('touchend',endMove,{passive:false});
  pad.addEventListener('touchcancel',endMove,{passive:false});

  fireBtn.addEventListener('touchstart',e=>{
    e.preventDefault();
    if(fireTouchId!==null)return;
    const t=firstChanged(e); if(!t)return;
    fireTouchId=t.identifier;
    state.fireHeld=true;
    updateFireAim(t.clientX,t.clientY);
  },{passive:false});

  fireBtn.addEventListener('touchmove',e=>{
    e.preventDefault();
    const t=byId(e.touches,fireTouchId);
    if(t&&state.fireHeld) updateFireAim(t.clientX,t.clientY);
  },{passive:false});

  const endFire=e=>{
    e.preventDefault();
    if(changedHas(e,fireTouchId)){
      fireTouchId=null;
      stopFireAim();
    }
  };
  fireBtn.addEventListener('touchend',endFire,{passive:false});
  fireBtn.addEventListener('touchcancel',endFire,{passive:false});

  dashTouchBtn.addEventListener('touchstart',e=>{
    e.preventDefault();
    e.stopPropagation();
    dash();
  },{passive:false});'''
if a not in s: raise SystemExit('touch patch anchor missing')
s=s.replace(a,patch,1)

# iPhone Safari/embedded browser viewport fix. 100vh often extends beneath browser chrome,
# which was pushing the controls off the visible screen.
style=r'''<style id="ios-visible-viewport-fix">
html,body{width:100%;height:100%;overflow:hidden;overscroll-behavior:none;}
#wrap{position:fixed!important;left:0!important;top:0!important;width:100%!important;height:var(--game-vh,100dvh)!important;min-height:0!important;overflow:hidden!important;}
#game{width:100%!important;height:100%!important;}
.hud{top:calc(8px + env(safe-area-inset-top))!important;left:calc(8px + env(safe-area-inset-left))!important;right:calc(8px + env(safe-area-inset-right))!important;}
.touch{bottom:calc(10px + env(safe-area-inset-bottom))!important;padding-left:calc(14px + env(safe-area-inset-left))!important;padding-right:calc(14px + env(safe-area-inset-right))!important;}
@media (orientation:portrait){
  .touch{bottom:calc(8px + env(safe-area-inset-bottom))!important;}
  .dir{width:82px!important;height:82px!important;}
  .btn{width:68px!important;height:68px!important;}
  .btn.small{width:56px!important;height:56px!important;}
  .knob{left:24px!important;top:24px!important;}
}
</style>'''
if '</head>' not in s: raise SystemExit('head close missing')
s=s.replace('</head>',style+'\n</head>',1)

# Make the canvas/game world use the visible viewport height, not Safari's hidden layout viewport.
s=s.replace('let W=innerWidth,H=innerHeight;',"let W=innerWidth,H=(window.visualViewport?window.visualViewport.height:innerHeight);",1)
s=s.replace('W=innerWidth;H=innerHeight;',"W=(window.visualViewport?window.visualViewport.width:innerWidth);H=(window.visualViewport?window.visualViewport.height:innerHeight);document.documentElement.style.setProperty('--game-vh',H+'px');",1)
resize_anchor="addEventListener('resize',resize); resize();"
if resize_anchor in s:
    s=s.replace(resize_anchor,"addEventListener('resize',resize); if(window.visualViewport){visualViewport.addEventListener('resize',resize);visualViewport.addEventListener('scroll',resize);} resize();",1)
else:
    s=s.replace("addEventListener('resize',resize);", "addEventListener('resize',resize); if(window.visualViewport){visualViewport.addEventListener('resize',resize);visualViewport.addEventListener('scroll',resize);}",1)

p.write_text(s)
