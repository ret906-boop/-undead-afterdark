from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
a="  document.getElementById('dashBtn').addEventListener('pointerdown',dash);"
patch=r'''  document.getElementById('dashBtn').addEventListener('pointerdown',dash);

  // iPhone/iPad Safari native touch fallback.
  document.querySelector('.touch').style.pointerEvents='auto';
  const dashTouchBtn=document.getElementById('dashBtn');
  const touchPos=e=>(e.touches&&e.touches[0])||(e.changedTouches&&e.changedTouches[0]);
  const endJoyTouch=e=>{e.preventDefault();state.joy={x:0,y:0,active:false};knob.style.transform='translate(0,0)'};
  pad.addEventListener('touchstart',e=>{e.preventDefault();const t=touchPos(e);if(t)joyPoint(t.clientX,t.clientY)},{passive:false});
  pad.addEventListener('touchmove',e=>{e.preventDefault();const t=touchPos(e);if(t)joyPoint(t.clientX,t.clientY)},{passive:false});
  pad.addEventListener('touchend',endJoyTouch,{passive:false});
  pad.addEventListener('touchcancel',endJoyTouch,{passive:false});
  fireBtn.addEventListener('touchstart',e=>{e.preventDefault();state.fireHeld=true;const t=touchPos(e);if(t)updateFireAim(t.clientX,t.clientY)},{passive:false});
  fireBtn.addEventListener('touchmove',e=>{e.preventDefault();const t=touchPos(e);if(t&&state.fireHeld)updateFireAim(t.clientX,t.clientY)},{passive:false});
  fireBtn.addEventListener('touchend',e=>{e.preventDefault();stopFireAim()},{passive:false});
  fireBtn.addEventListener('touchcancel',e=>{e.preventDefault();stopFireAim()},{passive:false});
  dashTouchBtn.addEventListener('touchstart',e=>{e.preventDefault();dash()},{passive:false});'''
if a not in s: raise SystemExit('touch patch anchor missing')
p.write_text(s.replace(a,patch,1))
