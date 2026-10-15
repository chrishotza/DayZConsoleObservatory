const state={players:[],events:[],knownPlayers:[],selectedId:'',history:null};
function paintMap(){
 const canvas=document.getElementById('map'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#0d1718';ctx.fillRect(0,0,w,h);
 const pts=state.players.filter(x=>Number.isFinite(x.x)&&Number.isFinite(x.z));
 const xs=pts.map(x=>x.x),zs=pts.map(x=>x.z);const loX=Math.min(0,...xs),hiX=Math.max(15360,...xs),loZ=Math.min(0,...zs),hiZ=Math.max(15360,...zs);
 const mx=72,my=54,iw=w-2*mx,ih=h-2*my;
 const X=n=>mx+iw*(n-loX)/(hiX-loX||1),Y=n=>h-my-ih*(n-loZ)/(hiZ-loZ||1);
 ctx.strokeStyle='#1f3533';ctx.lineWidth=1;ctx.font='14px monospace';ctx.fillStyle='#6e9387';
 for(let i=0;i<=8;i++){const a=i/8,x=mx+iw*a,y=my+ih*a;ctx.beginPath();ctx.moveTo(x,my);ctx.lineTo(x,h-my);ctx.moveTo(mx,y);ctx.lineTo(w-mx,y);ctx.stroke();ctx.fillText(Math.round(loX+(hiX-loX)*a),x-18,h-my+23);}
 ctx.fillStyle='#85a99c';ctx.fillText('Z ↑',17,22);ctx.fillText('X →',w-57,h-12);
 if(!pts.length){ctx.fillStyle='#7faba0';ctx.font='19px sans-serif';ctx.textAlign='center';ctx.fillText('No recorded positions imported yet',w/2,h/2);ctx.textAlign='left';return;}
 pts.forEach(p=>{const x=X(p.x),y=Y(p.z),selected=state.selectedId===p.player_id;
  ctx.fillStyle=selected?'#ffdc93':'#81e2b5';ctx.globalAlpha=.8;ctx.beginPath();ctx.arc(x,y,selected?10:7,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;
  ctx.strokeStyle=selected?'#fff2c8':'#d5ffe9';ctx.beginPath();ctx.arc(x,y,selected?16:12,0,Math.PI*2);ctx.stroke();
  ctx.fillStyle='#d2efdf';ctx.font='13px sans-serif';ctx.fillText((p.player_name||'Unknown').slice(0,24),x+15,y-9);
 });
}
function paintEvents(){
 const root=document.getElementById('events');root.replaceChildren();const kind=document.getElementById('kind').value;
 const events=state.selectedId?(state.history?.events||[]):state.events;
 const filtered=events.filter(e=>!kind||e.kind===kind);
 if(!filtered.length){const empty=document.createElement('div');empty.className='event';empty.textContent='No recorded events matching this filter';root.append(empty);return;}
 for(const e of filtered.slice(0,300)){
  const row=document.createElement('div');row.className='event';const tag=document.createElement('div');tag.className='tag '+e.kind;tag.textContent=e.kind;
  const details=document.createElement('div');const name=document.createElement('div');name.className='ename';name.textContent=e.player_name||'Server event';
  const extra=document.createElement('div');extra.className='detail';const coords=e.x===null?'':` • X ${e.x} / Z ${e.z}`;
  extra.textContent=(e.occurred_at||e.clock||'Time unavailable')+coords;details.append(name,extra);row.append(tag,details);root.append(row);
 }
}
function updatePlayerOptions(){
 const selector=document.getElementById('playerFilter');const choice=state.selectedId;selector.replaceChildren();
 const all=document.createElement('option');all.value='';all.textContent='All players';selector.append(all);
 for(const p of state.knownPlayers){const opt=document.createElement('option');opt.value=p.player_id;opt.textContent=`${p.player_name||'Unknown'} (${p.player_id.slice(0,8)}…)`;selector.append(opt);}
 selector.value=choice;
}
let historySequence=0;
async function loadHistory(){
 const seq=++historySequence,selected=state.selectedId;
 if(!selected){state.history=null;document.getElementById('eventCaption').textContent='Imported observations, newest first';paintMap();paintEvents();return;}
 try{
  const response=await fetch('/api/investigate?player_id='+encodeURIComponent(selected)+'&limit=500');
  if(!response.ok)throw Error('Investigation request failed');const history=await response.json();
  if(seq!==historySequence)return;
  state.history=history;
  const complete=history.sessions.filter(s=>s.status==='complete').length;
  document.getElementById('eventCaption').textContent=`Player history • ${history.sessions.length} logged sessions (${complete} complete) • No live presence inferred`;
  paintMap();paintEvents();
 }catch{if(seq!==historySequence)return;document.getElementById('eventCaption').textContent='Player history unavailable';}
}
async function refresh(){try{
 const responses=await Promise.all(['/api/players','/api/events?limit=500','/api/known-players'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Local API request failed');
 [state.players,state.events,state.knownPlayers]=await Promise.all(responses.map(r=>r.json()));
 document.getElementById('playerCount').textContent=state.players.length;
 document.getElementById('eventCount').textContent=state.events.length+' latest';
 const last=state.players[0];document.getElementById('lastSample').textContent=last?.occurred_at?.replace('T',' ')||'Not dated';
 document.getElementById('status').textContent='Local API connected • Imported records only';
 updatePlayerOptions();await loadHistory();paintMap();paintEvents();
 }catch{document.getElementById('status').textContent='Unable to read local API';}}
document.getElementById('kind').addEventListener('change',paintEvents);
document.getElementById('playerFilter').addEventListener('change',e=>{state.selectedId=e.target.value;loadHistory();});
refresh();setInterval(refresh,20000);
