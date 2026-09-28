from pathlib import Path
import re

import sys
if len(sys.argv)!=2: raise SystemExit('usage: v3715_patch.py <index.html>')
src=Path(sys.argv[1])
out=src
h=src.read_text()

def one(old,new,label):
    global h
    c=h.count(old)
    if c!=1:
        raise RuntimeError(f'{label}: expected 1 target, found {c}')
    h=h.replace(old,new,1)

def rex(pattern,repl,label,flags=0):
    global h
    h2,n=re.subn(pattern,repl,h,count=1,flags=flags)
    if n!=1: raise RuntimeError(f'{label}: expected 1 regex target, found {n}')
    h=h2

# Marker after V37.14.
one('<!-- V37.14 // INVENTORY CLOSE FIX -->','<!-- V37.14 // INVENTORY CLOSE FIX -->\n<!-- V37.15 // PHYSICAL SAFEHOUSE DEFENSE -->','marker')

# Add persistent defense state to the base save model.
one(
"function v35DefaultBase(){return {v:35,selected:'plaza',parts:8,upgrades:{fort:0,generator:0,ammo:0,medical:0,storage:0,perimeter:0},stash:{medkit:0,plate:0,grenade:0,ammo:0},integrity:700,raidsSurvived:0,chosen:false}}",
"function v35DefaultBase(){return {v:35,selected:'plaza',parts:8,upgrades:{fort:0,generator:0,ammo:0,medical:0,storage:0,perimeter:0},stash:{medkit:0,plate:0,grenade:0,ammo:0},integrity:700,defense:{north:null,west:null,east:null,southL:null,southR:null,gate:null},raidsSurvived:0,chosen:false}}",
'default defense')
one(
"d.integrity=Math.max(0,Number(r.integrity)||0);d.raidsSurvived=Math.max(0,Math.floor(Number(r.raidsSurvived)||0));d.chosen=!!r.chosen;return d",
"d.integrity=Math.max(0,Number(r.integrity)||0);if(r.defense&&typeof r.defense==='object')d.defense={...d.defense,...r.defense};d.raidsSurvived=Math.max(0,Math.floor(Number(r.raidsSurvived)||0));d.chosen=!!r.chosen;return d",
'load defense')

# Add helpers next to the existing base max function.
one(
"function v35BaseMax(b=v35Base){return 700+(b.upgrades?.fort||0)*250+(b.upgrades?.perimeter||0)*100}",
"""function v3715DefenseMax(b=v35Base,part='north'){const fort=b?.upgrades?.fort||0;return part==='gate'?220+fort*140:320+fort*180}
  function v3715DefenseKeys(){return ['north','west','east','southL','southR','gate']}
  function v3715EnsureDefense(b=v35Base){if(!b.defense||typeof b.defense!=='object')b.defense={};for(const k of v3715DefenseKeys()){const max=v3715DefenseMax(b,k),v=Number(b.defense[k]);b.defense[k]=Number.isFinite(v)?Math.max(0,Math.min(max,v)):max}return b.defense}
  function v3715ResetDefense(b=v35Base){b.defense={};v3715EnsureDefense(b);return b.defense}
  function v3715DefenseMissing(b=v35Base){v3715EnsureDefense(b);let n=0;for(const k of v3715DefenseKeys())n+=v3715DefenseMax(b,k)-b.defense[k];return n}
  function v3715RepairDefenseAmount(amount,b=v35Base){v3715EnsureDefense(b);for(const k of v3715DefenseKeys())b.defense[k]=Math.min(v3715DefenseMax(b,k),b.defense[k]+amount)}
  function v3715DefenseSummary(b=v35Base){v3715EnsureDefense(b);const walls=['north','west','east','southL','southR'],cur=walls.reduce((a,k)=>a+b.defense[k],0),max=walls.reduce((a,k)=>a+v3715DefenseMax(b,k),0);return `WALLS ${Math.round(cur)}/${Math.round(max)} • GATE ${Math.round(b.defense.gate)}/${v3715DefenseMax(b,'gate')}`}
  function v35BaseMax(b=v35Base){return 700+(b.upgrades?.fort||0)*250+(b.upgrades?.perimeter||0)*100}""",
'defense helpers')
one(
"function v35ClampBase(){v35Base.integrity=Math.max(0,Math.min(v35BaseMax(),Number(v35Base.integrity)||0));const cap=v35StorageCap();",
"function v35ClampBase(){v35Base.integrity=Math.max(0,Math.min(v35BaseMax(),Number(v35Base.integrity)||0));v3715EnsureDefense(v35Base);const cap=v35StorageCap();",
'clamp defense')
one(
"function v35PublicBase(){return {selected:v35Base.selected,upgrades:{...v35Base.upgrades},integrity:v35Base.integrity,maxIntegrity:v35BaseMax(),raidActive:!!state.v35RaidActive,raidPending:!!state.v35RaidPending,raidsSurvived:v35Base.raidsSurvived}}",
"function v35PublicBase(){v3715EnsureDefense(v35Base);return {selected:v35Base.selected,upgrades:{...v35Base.upgrades},integrity:v35Base.integrity,maxIntegrity:v35BaseMax(),defense:{...v35Base.defense},raidActive:!!state.v35RaidActive,raidPending:!!state.v35RaidPending,raidsSurvived:v35Base.raidsSurvived}}",
'public defense')

# Reset physical perimeter when moving safehouses.
one("v35Base.selected=id;v35Base.chosen=true;v35Base.integrity=v35BaseMax();v35SaveBase();","v35Base.selected=id;v35Base.chosen=true;v35Base.integrity=v35BaseMax();v3715ResetDefense(v35Base);v35SaveBase();",'select reset defense')

# Repair now restores the core, walls, and gate.
rex(r"function v35Repair\(\)\{const max=v35BaseMax\(\),missing=max-v35Base\.integrity;if\(missing<=0\)return;const cost=Math\.max\(1,Math\.ceil\(\(missing/max\)\*\(5\+\(v35Base\.upgrades\.fort\|\|0\)\*2\)\)\);if\(v35Base\.parts<cost\)return;v35Base\.parts-=cost;v35Base\.integrity=max;v35SaveBase\(\);v35BroadcastBase\(\)\}",
"function v35Repair(){const max=v35BaseMax(),coreMissing=max-v35Base.integrity,defMissing=v3715DefenseMissing(v35Base),totalMax=max+v3715DefenseKeys().reduce((a,k)=>a+v3715DefenseMax(v35Base,k),0),missing=coreMissing+defMissing;if(missing<=0)return;const cost=Math.max(1,Math.ceil((missing/Math.max(1,totalMax))*(8+(v35Base.upgrades.fort||0)*3)));if(v35Base.parts<cost)return;v35Base.parts-=cost;v35Base.integrity=max;v3715ResetDefense(v35Base);v35SaveBase();v35BroadcastBase();v3715MountBaseDefenses()}",
'repair physical base')

# Base menu recognizes damaged perimeter and displays it.
one(
"const el=document.getElementById('v35BaseContent');if(!el)return;v35ClampBase();const b=v35Base,max=v35BaseMax(),pct=max?Math.round(b.integrity/max*100):0,manage=v35CanManage(),near=!state.running||v35NearBase(player,480),stationReady=manage&&v35CanStation();",
"const el=document.getElementById('v35BaseContent');if(!el)return;v35ClampBase();const b=v35Base,max=v35BaseMax(),pct=max?Math.round(b.integrity/max*100):0,manage=v35CanManage(),near=!state.running||v35NearBase(player,480),stationReady=manage&&v35CanStation();v3715EnsureDefense(b);",
'render ensure')
one(
"const repairCost=Math.max(1,Math.ceil(((max-b.integrity)/max)*(5+(b.upgrades.fort||0)*2)));",
"const totalDefenseMax=v3715DefenseKeys().reduce((a,k)=>a+v3715DefenseMax(b,k),0),repairMissing=(max-b.integrity)+v3715DefenseMissing(b),repairCost=Math.max(1,Math.ceil((repairMissing/Math.max(1,max+totalDefenseMax))*(8+(b.upgrades.fort||0)*3)));",
'render repair cost')
one(
"Raids survived: ${b.raidsSurvived} • ${b.integrity>0?'stations online when powered':'BASE DISABLED — repair required'}",
"Raids survived: ${b.raidsSurvived} • ${v3715DefenseSummary(b)} • ${b.integrity>0?'stations online when powered':'BASE DISABLED — repair required'}",
'render defense status')
one(
"${!manage||b.integrity>=max||b.parts<repairCost?'disabled':''}>REPAIR BASE",
"${!manage||(b.integrity>=max&&v3715DefenseMissing(b)<=0)||b.parts<repairCost?'disabled':''}>REPAIR BASE",
'repair button condition')

# Physical base objects use the game's existing defense/collision system.
insert_after="function v35TeleportParty(){const s=v35SafeSpawn();player.x=s.x;player.y=s.y;let i=0;for(const p of net.remotePlayers.values()){if(p.disconnected)continue;const a=(i++/Math.max(1,net.remotePlayers.size))*Math.PI*2;p.x=s.x+Math.cos(a)*52;p.y=s.y+Math.sin(a)*52}}"
physical=r'''

  function v3715BaseDefenseGeometry(b=v35Base){
    const bp=v35BasePos(b),fort=b?.upgrades?.fort||0,t=8+fort*2;
    return {
      north:{x:bp.x,y:bp.y-116+t/2,w:308,h:t},
      west:{x:bp.x-154+t/2,y:bp.y,w:t,h:232},
      east:{x:bp.x+154-t/2,y:bp.y,w:t,h:232},
      southL:{x:bp.x-96,y:bp.y+108+t/2,w:116,h:t},
      southR:{x:bp.x+96,y:bp.y+108+t/2,w:116,h:t},
      gate:{x:bp.x,y:bp.y+112,w:70,h:12},
      core:{x:bp.x,y:bp.y-2,w:156,h:112}
    };
  }
  function v3715UnmountBaseDefenses(){state.defenses=state.defenses.filter(d=>!d.v3715BasePart)}
  function v3715MountBaseDefenses(){
    if(net.mode==='client'||!state.running)return;
    v3715EnsureDefense(v35Base);v3715UnmountBaseDefenses();
    const g=v3715BaseDefenseGeometry(v35Base);
    for(const k of v3715DefenseKeys()){
      const hp=v35Base.defense[k],r=g[k];if(hp<=0||!r)continue;
      state.defenses.push({id:`base-${k}`,type:'metal',x:r.x,y:r.y,w:r.w,h:r.h,rot:0,hp,maxHp:v3715DefenseMax(v35Base,k),fireCd:0,aimAngle:0,dead:false,v3715BasePart:k});
    }
    if(v35Base.integrity>0){const r=g.core;state.defenses.push({id:'base-core',type:'steel',x:r.x,y:r.y,w:r.w,h:r.h,rot:0,hp:v35Base.integrity,maxHp:v35BaseMax(),fireCd:0,aimAngle:0,dead:false,v3715BasePart:'core'})}
  }
  window.__v3715RaidTarget=z=>{
    if(!state.v35RaidActive||!z||z.dead)return null;
    if(z.kind==='spitter'||z.kind==='screamer'||z.kind==='stalker')return null;
    const bp=v35BasePos(v35Base);return {x:bp.x,y:bp.y-2,r:56,_v3715Base:true};
  };
  window.__v3715SyncBaseDefense=d=>{
    if(!d?.v3715BasePart||net.mode==='client')return;
    if(d.v3715BasePart==='core')v35Base.integrity=Math.max(0,Math.min(v35BaseMax(),d.hp));
    else{v3715EnsureDefense(v35Base);v35Base.defense[d.v3715BasePart]=Math.max(0,Math.min(v3715DefenseMax(v35Base,d.v3715BasePart),d.hp))}
    v35SaveBase();v35BroadcastBase();
    if(v35Base.integrity<=0){ui.bossWarn.textContent='⚠ SAFEHOUSE CORE DESTROYED • STATIONS OFFLINE';ui.bossWarn.style.display='block'}
  };
'''
one(insert_after,insert_after+physical,'insert physical helpers')

# Recreate base defenses on reset and raids, while raids make the horde target the core.
one(
"const v35OldReset=reset;reset=function(mode='waves'){v35OldReset(mode);state.v35RaidPending=false;state.v35RaidActive=false;state.v35MedUsedWave=-1;state.v35AmmoUsedWave=-1;state.v35BaseTurretCds=[];",
"const v35OldReset=reset;reset=function(mode='waves'){v35OldReset(mode);state.v35RaidPending=false;state.v35RaidActive=false;state.v35MedUsedWave=-1;state.v35AmmoUsedWave=-1;state.v35BaseTurretCds=[];v3715UnmountBaseDefenses();",
'reset unmount')
one(
"if(raid){state.v35RaidPending=false;state.v35RaidActive=true;v35TeleportParty();",
"if(raid){state.v35RaidPending=false;state.v35RaidActive=true;v35TeleportParty();v3715MountBaseDefenses();",
'raid mount')

# Repair some perimeter damage on a successful raid / powered wave clear.
one(
"if(wasRaid){reward+=3;v35Base.raidsSurvived++;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+40)}",
"if(wasRaid){reward+=3;v35Base.raidsSurvived++;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+40);v3715RepairDefenseAmount(35)}",
'raid clear wall repair')
one(
"if(v35Powered()&&(v35Base.upgrades.generator||0)>0)v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+12*(v35Base.upgrades.generator||0));",
"if(v35Powered()&&(v35Base.upgrades.generator||0)>0){const gen=v35Base.upgrades.generator||0;v35Base.integrity=Math.min(v35BaseMax(),v35Base.integrity+12*gen);v3715RepairDefenseAmount(18*gen)}",
'generator wall repair')

# The old invisible circular damage trigger is disabled. Physical defense collision now handles all structure damage.
rex(r"function v35RaidDamage\(dt\)\{.*?\n  \}","function v35RaidDamage(dt){return}", 'disable ghost raid damage', re.S)

# Remove the older circle/arc safehouse overlay. V37.1 compound remains the renderer.
rex(r"const v35OldDraw=draw;draw=function\(\)\{v35OldDraw\(\);if\(!state\.running\)return;.*?ctx\.restore\(\)\};",
"const v35OldDraw=draw;draw=function(){v35OldDraw()};",'remove ghost overlay',re.S)

# Route melee infected toward the safehouse core during raids.
one(
"let target=nearestPartyTarget(z);const special=updateZombieSpecial(z,dt,target);",
"let target=(window.__v3715RaidTarget?.(z)||nearestPartyTarget(z));const special=updateZombieSpecial(z,dt,target);",
'raid target')

# Base perimeter is not leap-skippable.
one(
"if(z.kind==='leaper'&&z.abilityCd<=0){const jump=155",
"if(z.kind==='leaper'&&!defenseBlock.v3715BasePart&&z.abilityCd<=0){const jump=155",
'leaper safehouse wall')

# Synchronize tagged base defense HP back to persistent base state.
one(
"function damageDefense(d,amount){\n    if(!d||d.dead)return;d.hp-=amount;if(d.hp<=0){d.dead=true;state.screenShake=Math.max(state.screenShake,.7);noiseBurst(.12,.05,420,'lowpass')}\n  }",
"function damageDefense(d,amount){\n    if(!d||d.dead)return;d.hp-=amount;if(d.v3715BasePart&&window.__v3715SyncBaseDefense)window.__v3715SyncBaseDefense(d);if(d.hp<=0){d.dead=true;state.screenShake=Math.max(state.screenShake,.7);noiseBurst(.12,.05,420,'lowpass')}\n  }",
'sync defense damage')

# Make the V37.1 compound show persistent damage instead of drawing immortal walls.
old_wall="""// Outer walls with a south gate. Fort upgrades make them heavier.
    const wallCol=fort>=3?'#8f8069':fort?'#756958':'#5e5549';ctx.fillStyle=wallCol;const t=8+fort*2;
    ctx.fillRect(bp.x-154,bp.y-116,308,t);ctx.fillRect(bp.x-154,bp.y+108,116,t);ctx.fillRect(bp.x+38,bp.y+108,116,t);ctx.fillRect(bp.x-154,bp.y-116,t,232);ctx.fillRect(bp.x+146,bp.y-116,t,232);
    ctx.fillStyle='#2b3032';ctx.fillRect(bp.x-35,bp.y+106,70,12);ctx.strokeStyle=s.color;ctx.lineWidth=2;ctx.strokeRect(bp.x-35,bp.y+106,70,12);"""
new_wall="""// Physical perimeter. Destroyed segments disappear and become real breaches.
    const wallCol=fort>=3?'#8f8069':fort?'#756958':'#5e5549',t=8+fort*2,d=b?.defense||{},wallMax=320+fort*180,gateMax=220+fort*140;
    const seg=(k,x,y,w,h)=>{const hp=Number.isFinite(Number(d[k]))?Number(d[k]):wallMax;if(hp<=0)return;const pct=Math.max(0,Math.min(1,hp/wallMax));ctx.fillStyle=pct>.5?wallCol:(pct>.2?'#665340':'#4d3830');ctx.fillRect(x,y,w,h);if(pct<.55){ctx.strokeStyle='rgba(184,76,65,.8)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x+w*.22,y);ctx.lineTo(x+w*.55,y+h);ctx.stroke()}};
    seg('north',bp.x-154,bp.y-116,308,t);seg('southL',bp.x-154,bp.y+108,116,t);seg('southR',bp.x+38,bp.y+108,116,t);seg('west',bp.x-154,bp.y-116,t,232);seg('east',bp.x+146,bp.y-116,t,232);
    const gateHp=Number.isFinite(Number(d.gate))?Number(d.gate):gateMax;if(gateHp>0){ctx.fillStyle=gateHp/gateMax>.45?'#2b3032':'#4a3030';ctx.fillRect(bp.x-35,bp.y+106,70,12);ctx.strokeStyle=s.color;ctx.lineWidth=2;ctx.strokeRect(bp.x-35,bp.y+106,70,12)}"""
one(old_wall,new_wall,'damaged walls draw')

old_core="""// Main safehouse building exists at level zero.
    const roof=b?.selected==='guard'?'#485148':b?.selected==='ranger'?'#485447':'#444b50';
    ctx.fillStyle='#1a1f22';ctx.strokeStyle='#899297';ctx.lineWidth=2;ctx.beginPath();ctx.roundRect(bp.x-78,bp.y-58,156,112,10);ctx.fill();ctx.stroke();
    ctx.fillStyle=roof;ctx.beginPath();ctx.roundRect(bp.x-70,bp.y-50,140,88,8);ctx.fill();"""
new_core="""// Main safehouse is the final destructible target after the perimeter is breached.
    const roof=b?.selected==='guard'?'#485148':b?.selected==='ranger'?'#485447':'#444b50',coreAlive=(b?.integrity||0)>0;
    ctx.fillStyle=coreAlive?'#1a1f22':'#24191a';ctx.strokeStyle=coreAlive?'#899297':'#7e3e3e';ctx.lineWidth=2;ctx.beginPath();ctx.roundRect(bp.x-78,bp.y-58,156,112,10);ctx.fill();ctx.stroke();
    ctx.fillStyle=coreAlive?roof:'#38282a';ctx.beginPath();ctx.roundRect(bp.x-70,bp.y-50,140,88,8);ctx.fill();"""
one(old_core,new_core,'core damaged draw')

# Add perimeter HP readout under world label.
one(
"ctx.fillStyle=s.color;ctx.font='1000 10px system-ui';ctx.fillText(`${s.short} • ${Math.round(pct*100)}%`,bp.x,bp.y-138);",
"ctx.fillStyle=s.color;ctx.font='1000 10px system-ui';ctx.fillText(`${s.short} • CORE ${Math.round(pct*100)}%`,bp.x,bp.y-138);const wallKeys=['north','west','east','southL','southR'],wallCur=wallKeys.reduce((a,k)=>a+(Number.isFinite(Number(d[k]))?Number(d[k]):wallMax),0),wallAll=wallKeys.length*wallMax,gateCur=Number.isFinite(Number(d.gate))?Number(d.gate):gateMax;ctx.fillStyle='#c7cdd0';ctx.font='800 7px system-ui';ctx.fillText(`WALLS ${Math.round(wallCur/wallAll*100)}% • GATE ${Math.round(gateCur/gateMax*100)}%`,bp.x,bp.y-120);",
'world defense readout')

# Version labels.
one("document.title='Undead Afterdark V37.14 Inventory Close Fix';","document.title='Undead Afterdark V37.15 Physical Safehouse Defense';",'title')
one("if(mv)mv.textContent='V37.14 // INVENTORY CLOSE FIX';","if(mv)mv.textContent='V37.15 // PHYSICAL SAFEHOUSE DEFENSE';",'menu version')

out.write_text(h)
print('patched',out,'bytes',len(h))
