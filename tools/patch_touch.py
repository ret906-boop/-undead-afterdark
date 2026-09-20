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
p.write_text(s.replace(a,patch,1))
