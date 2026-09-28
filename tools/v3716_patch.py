from pathlib import Path
import re, sys

if len(sys.argv)!=2:
    raise SystemExit('usage: v3716_patch.py <index.html>')
p=Path(sys.argv[1])
h=p.read_text()

def one(old,new,label):
    global h
    c=h.count(old)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 target, found {c}')
    h=h.replace(old,new,1)

# Version marker.
one('<!-- V37.15 // PHYSICAL SAFEHOUSE DEFENSE -->',
    '<!-- V37.15 // PHYSICAL SAFEHOUSE DEFENSE -->\n<!-- V37.16 // SOLID INTEGRATED SAFEHOUSE -->','marker')

# Stop the old late-frame compound painter. It rendered after the entire game frame,
# which is why the safehouse looked like a translucent decal hovering over the map.
one("function v371DrawSafehouseCompound(){\n    if(!state.running)return;",
    "function v371DrawSafehouseCompound(){\n    if(window.__v3716IntegratedSafehouse)return;\n    if(!state.running)return;",'disable ghost painter')

# Tagged base collision proxies are invisible. V37.16 draws the real structure in the map layer.
one("if(d.dead)continue;const spec=DEFENSE_SPECS[d.type];if(!spec)continue;",
    "if(d.dead||d.v3715BasePart)continue;const spec=DEFENSE_SPECS[d.type];if(!spec)continue;",'hide proxy defenses')

# V37.15 migration bug: null became Number(null) === 0, deleting untouched walls on old saves.
old_ensure="function v3715EnsureDefense(b=v35Base){if(!b.defense||typeof b.defense!=='object')b.defense={};for(const k of v3715DefenseKeys()){const max=v3715DefenseMax(b,k),v=Number(b.defense[k]);b.defense[k]=Number.isFinite(v)?Math.max(0,Math.min(max,v)):max}return b.defense}"
new_ensure="function v3715EnsureDefense(b=v35Base){if(!b.defense||typeof b.defense!=='object')b.defense={};const keys=v3715DefenseKeys(),allZero=keys.every(k=>b.defense[k]!=null&&Number(b.defense[k])===0),freshBrokenSave=allZero&&(Number(b.raidsSurvived)||0)===0;if(freshBrokenSave)b.defense={};for(const k of keys){const max=v3715DefenseMax(b,k),raw=b.defense[k],v=Number(raw);b.defense[k]=(raw===null||raw===undefined||raw===''||!Number.isFinite(v))?max:Math.max(0,Math.min(max,v))}return b.defense}"
one(old_ensure,new_ensure,'defense migration')

# Gate stays open during exploration and physically closes for a safehouse raid.
one("for(const k of v3715DefenseKeys()){\n      const hp=v35Base.defense[k],r=g[k];if(hp<=0||!r)continue;",
    "for(const k of v3715DefenseKeys()){\n      if(k==='gate'&&!state.v35RaidActive)continue;\n      const hp=v35Base.defense[k],r=g[k];if(hp<=0||!r)continue;",'raid-only gate collision')

# Keep core + perimeter mounted outside raids so the building is physically present all the time.
old_reset="const v35OldReset=reset;reset=function(mode='waves'){v35OldReset(mode);state.v35RaidPending=false;state.v35RaidActive=false;state.v35MedUsedWave=-1;state.v35AmmoUsedWave=-1;state.v35BaseTurretCds=[];v3715UnmountBaseDefenses();if(net.mode!=='client'){v35TeleportParty();v35ApplyDeployment(player);for(const p of net.remotePlayers.values())v35ApplyDeployment(p);if(v35Base.integrity>0)state.cash+=75*(v35Base.upgrades.generator||0)}v35UpdateHUD();v35BroadcastBase();saveGame(false)};"
new_reset="const v35OldReset=reset;reset=function(mode='waves'){v35OldReset(mode);state.v35RaidPending=false;state.v35RaidActive=false;state.v35MedUsedWave=-1;state.v35AmmoUsedWave=-1;state.v35BaseTurretCds=[];v3715UnmountBaseDefenses();if(net.mode!=='client'){v35TeleportParty();v35ApplyDeployment(player);for(const p of net.remotePlayers.values())v35ApplyDeployment(p);if(v35Base.integrity>0)state.cash+=75*(v35Base.upgrades.generator||0);v3715MountBaseDefenses()}v35UpdateHUD();v35BroadcastBase();saveGame(false)};"
one(old_reset,new_reset,'mount on reset')

old_wc="const v35OldWaveClear=waveClear;waveClear=function(){const cleared=state.wave,wasRaid=!!state.v35RaidActive;state.v35RaidActive=false;v35OldWaveClear();if(net.mode==='client'||state.mode==='endless49')return;let reward=1+(isBossWave(cleared)?2:0);if(wasRaid){reward+=3;v35Base.raidsSurvived++;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+40);v3715RepairDefenseAmount(35)}else if(cleared>=6&&cleared%6===0&&v35Base.integrity>0){state.v35RaidPending=true;ui.shopSub.textContent=`Wave ${cleared} cleared. WARNING: the next non-boss wave is a SAFEHOUSE RAID.`}if(v35Powered()&&(v35Base.upgrades.generator||0)>0){const gen=v35Base.upgrades.generator||0;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+12*gen);v3715RepairDefenseAmount(18*gen)}v35GrantParts(reward,false);showSaveToast(`+${reward} BASE PART${reward===1?'':'S'}`);v35SaveBase();v35BroadcastBase();saveGame(false)};"
new_wc="const v35OldWaveClear=waveClear;waveClear=function(){const cleared=state.wave,wasRaid=!!state.v35RaidActive;state.v35RaidActive=false;v35OldWaveClear();if(net.mode==='client'||state.mode==='endless49')return;let reward=1+(isBossWave(cleared)?2:0);if(wasRaid){reward+=3;v35Base.raidsSurvived++;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+40);v3715RepairDefenseAmount(35)}else if(cleared>=6&&cleared%6===0&&v35Base.integrity>0){state.v35RaidPending=true;ui.shopSub.textContent=`Wave ${cleared} cleared. WARNING: the next non-boss wave is a SAFEHOUSE RAID.`}if(v35Powered()&&(v35Base.upgrades.generator||0)>0){const gen=v35Base.upgrades.generator||0;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+12*gen);v3715RepairDefenseAmount(18*gen)}v35GrantParts(reward,false);showSaveToast(`+${reward} BASE PART${reward===1?'':'S'}`);v35SaveBase();v35BroadcastBase();v3715MountBaseDefenses();saveGame(false)};"
one(old_wc,new_wc,'reopen gate after raid')

old_load="const v35OldLoadSavedRun=loadSavedRun;loadSavedRun=function(){const data=getSavedRun(),ok=v35OldLoadSavedRun();if(ok){state.v35RaidPending=!!data?.state?.v35RaidPending;state.v35RaidActive=false;v35UpdateHUD()}return ok};"
new_load="const v35OldLoadSavedRun=loadSavedRun;loadSavedRun=function(){const data=getSavedRun(),ok=v35OldLoadSavedRun();if(ok){state.v35RaidPending=!!data?.state?.v35RaidPending;state.v35RaidActive=false;if(net.mode!=='client')v3715MountBaseDefenses();v35UpdateHUD()}return ok};"
one(old_load,new_load,'mount on continue')

one("v35Base.selected=id;v35Base.chosen=true;v35Base.integrity=v35BaseMax();v3715ResetDefense(v35Base);v35SaveBase();if(state.running&&net.mode!=='client'){",
    "v35Base.selected=id;v35Base.chosen=true;v35Base.integrity=v35BaseMax();v3715ResetDefense(v35Base);v35SaveBase();if(state.running&&net.mode!=='client'){v3715MountBaseDefenses();",'mount after base move')

one("const newMax=v35BaseMax();v35Base.integrity=Math.min(newMax,v35Base.integrity+Math.max(0,newMax-oldMax));v35SaveBase();v35BroadcastBase();",
    "const newMax=v35BaseMax();v35Base.integrity=Math.min(newMax,v35Base.integrity+Math.max(0,newMax-oldMax));v35SaveBase();if(state.running&&net.mode!=='client')v3715MountBaseDefenses();v35BroadcastBase();",'mount after fort upgrade')

# Integrated opaque renderer. This runs inside the main game IIFE so it is in the same
# world draw order as roads/buildings and underneath survivors/infected.
renderer=r'''

  // V37.16 // SOLID INTEGRATED SAFEHOUSE
  window.__v3716IntegratedSafehouse=true;
  document.title='Undead Afterdark V37.16 Solid Safehouse';
  const v3716mv=document.querySelector('.menuVersion');if(v3716mv)v3716mv.textContent='V37.16 // SOLID SAFEHOUSE';

  function v3716HpFor(b,key,max){const d=b?.defense||{},raw=d[key],v=Number(raw);return raw==null||!Number.isFinite(v)?max:Math.max(0,Math.min(max,v))}
  function v3716DrawBlock(x,y,w,h,fill,edge,damage=1){
    ctx.fillStyle='rgba(0,0,0,.48)';ctx.fillRect(x+7,y+8,w,h);
    ctx.fillStyle=fill;ctx.fillRect(x,y,w,h);
    ctx.strokeStyle=edge;ctx.lineWidth=2;ctx.strokeRect(x+.5,y+.5,w-1,h-1);
    ctx.fillStyle='rgba(255,255,255,.08)';ctx.fillRect(x+2,y+2,w-4,Math.min(3,h-4));
    if(damage<.55){ctx.strokeStyle=damage<.22?'#d85b50':'#9b7658';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x+w*.18,y+2);ctx.lineTo(x+w*.48,y+h-2);ctx.lineTo(x+w*.72,y+3);ctx.stroke()}
  }
  function v3716DrawSafehouse(c){
    if(!state.running)return;
    const b=v35ActiveBase();if(!b)return;const bp=v35BasePos(b);if(!bp)return;
    if(bp.x<c.ox||bp.x>=c.ox+CHUNK||bp.y<c.oy||bp.y>=c.oy+CHUNK)return;
    const s=v35Safehouse(b),lvl=b.upgrades||{},fort=lvl.fort||0,max=net.mode==='client'?(b?.maxIntegrity||700):v35BaseMax(b),corePct=Math.max(0,Math.min(1,(Number(b.integrity)||0)/Math.max(1,max)));
    const wallMax=320+fort*180,gateMax=220+fort*140,t=8+fort*2;
    ctx.save();

    ctx.fillStyle='#111517';ctx.fillRect(bp.x-164,bp.y-126,328,250);
    ctx.fillStyle='#34383a';ctx.fillRect(bp.x-156,bp.y-118,312,234);
    ctx.strokeStyle='#7d7362';ctx.lineWidth=3;ctx.strokeRect(bp.x-156.5,bp.y-118.5,313,235);
    ctx.fillStyle='#292d2f';ctx.fillRect(bp.x-143,bp.y-105,286,210);
    ctx.strokeStyle='#3f4446';ctx.lineWidth=1;
    for(let x=-120;x<=120;x+=40){ctx.beginPath();ctx.moveTo(bp.x+x,bp.y-104);ctx.lineTo(bp.x+x,bp.y+104);ctx.stroke()}
    for(let y=-80;y<=80;y+=40){ctx.beginPath();ctx.moveTo(bp.x-142,bp.y+y);ctx.lineTo(bp.x+142,bp.y+y);ctx.stroke()}

    ctx.fillStyle='rgba(0,0,0,.6)';ctx.fillRect(bp.x-84,bp.y-52,168,120);
    ctx.fillStyle=corePct>0?'#545b5f':'#362b2d';ctx.fillRect(bp.x-78,bp.y-58,156,112);
    ctx.strokeStyle=corePct>0?'#aab0b3':'#7f4747';ctx.lineWidth=3;ctx.strokeRect(bp.x-77,bp.y-57,154,110);
    const roof=b.selected==='guard'?'#39453d':b.selected==='ranger'?'#3d4d40':'#3d4448';
    ctx.fillStyle=corePct>0?roof:'#302326';ctx.fillRect(bp.x-68,bp.y-48,136,79);
    ctx.strokeStyle='#171b1d';ctx.lineWidth=5;ctx.strokeRect(bp.x-66,bp.y-46,132,75);
    ctx.fillStyle='#242a2d';ctx.fillRect(bp.x-25,bp.y+31,50,27);ctx.strokeStyle='#889095';ctx.lineWidth=2;ctx.strokeRect(bp.x-24,bp.y+32,48,25);
    ctx.fillStyle=s.color;ctx.fillRect(bp.x-6,bp.y+38,12,20);
    ctx.fillStyle='#dccb94';for(const wx of [-48,31])for(const wy of [-25,0]){ctx.fillRect(bp.x+wx,bp.y+wy,18,11);ctx.strokeStyle='#202528';ctx.lineWidth=2;ctx.strokeRect(bp.x+wx,bp.y+wy,18,11)}
    ctx.fillStyle='#d0d5d7';ctx.font='1000 10px system-ui';ctx.textAlign='center';ctx.fillText(s.short,bp.x,bp.y-4);

    const wallFill=fort>=3?'#777269':fort?'#68645d':'#5b5853',wallEdge=fort>=3?'#b6afa1':'#8e887d';
    const parts={north:[bp.x-154,bp.y-116,308,t],west:[bp.x-154,bp.y-116,t,232],east:[bp.x+146,bp.y-116,t,232],southL:[bp.x-154,bp.y+108,116,t],southR:[bp.x+38,bp.y+108,116,t]};
    for(const [k,r] of Object.entries(parts)){const hp=v3716HpFor(b,k,wallMax);if(hp<=0)continue;v3716DrawBlock(r[0],r[1],r[2],r[3],wallFill,wallEdge,hp/wallMax)}

    const gateHp=v3716HpFor(b,'gate',gateMax),raid=!!state.v35RaidActive;
    if(gateHp>0){
      if(raid){v3716DrawBlock(bp.x-35,bp.y+106,70,12,'#353d40',s.color,gateHp/gateMax);ctx.fillStyle='#9ca5aa';for(let x=-27;x<=27;x+=9)ctx.fillRect(bp.x+x,bp.y+107,3,10)}
      else{v3716DrawBlock(bp.x-35,bp.y+106,10,36,'#353d40',s.color,gateHp/gateMax);v3716DrawBlock(bp.x+25,bp.y+106,10,36,'#353d40',s.color,gateHp/gateMax);ctx.fillStyle=s.color;ctx.font='900 7px system-ui';ctx.fillText('GATE OPEN',bp.x,bp.y+135)}
    }

    ctx.fillStyle='#5e4934';for(const x of [-118,-82,82,118]){ctx.fillRect(bp.x+x-14,bp.y+78,28,16);ctx.strokeStyle='#9b7a50';ctx.strokeRect(bp.x+x-13,bp.y+79,26,14)}
    if(lvl.generator){ctx.fillStyle='#b28838';ctx.fillRect(bp.x-134,bp.y-72,50,40);ctx.strokeStyle='#1b2022';ctx.lineWidth=3;ctx.strokeRect(bp.x-132,bp.y-70,46,36);ctx.fillStyle='#202629';ctx.fillRect(bp.x-125,bp.y-63,30,20)}
    if(lvl.medical){ctx.fillStyle='#8d3b43';ctx.fillRect(bp.x+86,bp.y-77,52,43);ctx.fillStyle='#eee';ctx.fillRect(bp.x+106,bp.y-69,12,27);ctx.fillRect(bp.x+98,bp.y-61,28,12)}
    if(lvl.ammo){ctx.fillStyle='#465963';ctx.fillRect(bp.x+86,bp.y+38,52,40);ctx.strokeStyle='#8e9aa0';ctx.strokeRect(bp.x+87,bp.y+39,50,38);ctx.fillStyle='#caa858';ctx.fillRect(bp.x+94,bp.y+47,36,6);ctx.fillRect(bp.x+94,bp.y+60,36,6)}

    ctx.fillStyle='#090c0e';ctx.fillRect(bp.x-108,bp.y-151,216,31);ctx.strokeStyle=s.color;ctx.lineWidth=1;ctx.strokeRect(bp.x-108,bp.y-151,216,31);
    ctx.fillStyle='#20272a';ctx.fillRect(bp.x-94,bp.y-132,188,5);ctx.fillStyle=corePct>.5?'#6eae70':corePct>.25?'#d6a74c':'#b54343';ctx.fillRect(bp.x-94,bp.y-132,188*corePct,5);
    ctx.fillStyle=s.color;ctx.font='1000 9px system-ui';ctx.fillText(`${s.short} • CORE ${Math.round(corePct*100)}%`,bp.x,bp.y-139);
    ctx.restore();
  }

  const v3716OldDrawChunkVisual=drawChunkVisual;
  drawChunkVisual=function(c){v3716OldDrawChunkVisual(c);v3716DrawSafehouse(c)};
  window.__v3716Test={version:'V37.16',integrated:()=>!!window.__v3716IntegratedSafehouse,baseParts:()=>state.defenses.filter(d=>d.v3715BasePart).map(d=>({part:d.v3715BasePart,hp:Math.round(d.hp),dead:!!d.dead,w:d.w,h:d.h})),raid:()=>!!state.v35RaidActive};
'''

sentinel='\n\n})();\n</script>\n\n<script id="v3710-native-button-recovery">'
if h.count(sentinel)!=1: raise RuntimeError(f'main closure: expected 1 target, found {h.count(sentinel)}')
h=h.replace(sentinel,renderer+sentinel,1)

# Later compatibility script otherwise overwrites the visible build label.
one("document.title='Undead Afterdark V37.15 Physical Safehouse Defense';",
    "document.title='Undead Afterdark V37.16 Solid Safehouse';",'late title')
one("if(mv)mv.textContent='V37.15 // PHYSICAL SAFEHOUSE DEFENSE';",
    "if(mv)mv.textContent='V37.16 // SOLID SAFEHOUSE';",'late menu version')

p.write_text(h)

# Syntax check materialization helper for CI.
scripts=re.findall(r'<script[^>]*>(.*?)</script>',h,re.S)
for i,s in enumerate(scripts):
    Path(f'/tmp/v3716-script-{i}.js').write_text(s)
