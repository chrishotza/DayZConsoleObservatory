const state={players:[],events:[],knownPlayers:[],selectedId:'',history:null,quality:null,scope:'local'};
const $=id=>document.getElementById(id);
function scopedUrl(path){const url=new URL(path,location.origin);url.searchParams.set('scope',state.scope);return url.pathname+url.search;}
function setFeedback(message){$('workspaceFeedback').textContent=message;}
function paintMap(){
 const canvas=$('map'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#0d1718';ctx.fillRect(0,0,w,h);
 const pts=state.players.filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.z));
 const xs=pts.map(p=>p.x),zs=pts.map(p=>p.z);
 const loX=Math.min(0,...xs),hiX=Math.max(15360,...xs),loZ=Math.min(0,...zs),hiZ=Math.max(15360,...zs);
 const mx=72,my=54,iw=w-2*mx,ih=h-2*my,X=n=>mx+iw*(n-loX)/(hiX-loX||1),Y=n=>h-my-ih*(n-loZ)/(hiZ-loZ||1);
 ctx.strokeStyle='#244039';ctx.lineWidth=1;ctx.font='14px monospace';ctx.fillStyle='#85a99c';
 for(let i=0;i<=8;i++){const a=i/8,x=mx+iw*a,y=my+ih*a;ctx.beginPath();ctx.moveTo(x,my);ctx.lineTo(x,h-my);ctx.moveTo(mx,y);ctx.lineTo(w-mx,y);ctx.stroke();ctx.fillText(Math.round(loX+(hiX-loX)*a),x-18,h-my+23);}
 ctx.fillStyle='#85a99c';ctx.fillText('Z ↑',17,22);ctx.fillText('X →',w-57,h-12);
 if(!pts.length){ctx.font='19px sans-serif';ctx.textAlign='center';ctx.fillText('No recorded positions in this workspace',w/2,h/2);ctx.textAlign='left';return;}
 for(const p of pts){const x=X(p.x),y=Y(p.z),selected=state.selectedId===p.player_id;ctx.fillStyle=selected?'#ffdc93':'#81e2b5';ctx.beginPath();ctx.arc(x,y,selected?9:6,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#d5ffe9';ctx.beginPath();ctx.arc(x,y,selected?15:11,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#d2efdf';ctx.font='13px sans-serif';ctx.fillText((p.player_name||'Unknown').slice(0,24),x+14,y-8);}
}
function paintEvents(){
 const root=$('events');root.replaceChildren();const kind=$('kind').value,events=state.selectedId?(state.history?.events||[]):state.events;
 const filtered=events.filter(e=>!kind||e.kind===kind);
 if(!filtered.length){const empty=document.createElement('div');empty.className='event';empty.textContent='No recorded events matching this filter.';root.append(empty);return;}
 for(const e of filtered.slice(0,300)){const row=document.createElement('div');row.className='event';const tag=document.createElement('div');tag.className='tag '+e.kind;tag.textContent=e.kind;
  const details=document.createElement('div'),name=document.createElement('div');name.className='ename';name.textContent=e.player_name||'Server event';
  const extra=document.createElement('div');extra.className='detail';const coords=e.x===null?'': ' · X '+e.x+' / Z '+e.z;
  extra.textContent=(e.occurred_at||e.clock||'Time unavailable')+coords;details.append(name,extra);row.append(tag,details);root.append(row);}
}
function updatePlayerOptions(){
 const selector=$('playerFilter'),current=state.selectedId;selector.replaceChildren();
 const all=document.createElement('option');all.value='';all.textContent='All players';selector.append(all);
 for(const p of state.knownPlayers){const opt=document.createElement('option');opt.value=p.player_id;opt.textContent=(p.player_name||'Unknown')+' ('+p.player_id.slice(0,8)+'…)';selector.append(opt);}
 selector.value=current;
}
let historySequence=0,refreshSequence=0;
async function loadHistory(){
 const seq=++historySequence,selected=state.selectedId;
 if(!selected){state.history=null;$('eventCaption').textContent='Imported observations, newest first';paintMap();paintEvents();return;}
 try{const response=await fetch(scopedUrl('/api/investigate?player_id='+encodeURIComponent(selected)+'&limit=500'));
  if(!response.ok)throw Error('History request failed');const history=await response.json();if(seq!==historySequence)return;
  state.history=history;const complete=history.sessions.filter(s=>s.status==='complete').length;
  $('eventCaption').textContent='History · '+history.sessions.length+' logged sessions ('+complete+' complete), not proof of current presence';paintMap();paintEvents();
 }catch{if(seq===historySequence){state.history=null;$('eventCaption').textContent='Player history unavailable';paintEvents();}}
}
async function refresh(){
 const seq=++refreshSequence;
 try{const urls=['/api/players','/api/events?limit=500','/api/known-players','/api/quality'];
  const responses=await Promise.all(urls.map(path=>fetch(scopedUrl(path))));if(responses.some(r=>!r.ok))throw Error('API not available');
  const [players,events,knownPlayers,quality]=await Promise.all(responses.map(r=>r.json()));if(seq!==refreshSequence)return;
  Object.assign(state,{players,events,knownPlayers,quality});
  $('qualityPositions').textContent=quality.position_observations;
  $('qualityUndated').textContent=quality.undated_events;
  $('qualityUnknown').textContent=quality.unclassified_events;
  $('qualitySources').textContent=quality.imported_sources;
  $('playerCount').textContent=players.length;
  $('eventCount').textContent=quality.events+' total';
  $('lastSample').textContent=quality.last_observed?.replace('T',' ')||'Not dated';
  $('modeHeadline').textContent=state.scope==='demo'?'SYNTHETIC DEMONSTRATION':'Your imported records';
  $('modeDescription').textContent=state.scope==='demo'?'Example players and positions only. Never mixed with your logs.':'Historical imported records only. No live server telemetry.';
  $('status').textContent=state.scope==='demo'?'SYNTHETIC DEMO · local API':'Local workspace · imported history';
  updatePlayerOptions();await loadHistory();paintMap();paintEvents();
 }catch{if(seq===refreshSequence)$('status').textContent='Unable to read local API';}
}
const postHeaders={'X-DayZ-Local-UI':'v1'};
async function launchDemo(){
 const button=$('demoButton');button.disabled=true;setFeedback('Preparing isolated synthetic demo…');
 try{const response=await fetch('/api/demo',{method:'POST',headers:postHeaders,body:''});if(!response.ok)throw Error();
  state.scope='demo';state.selectedId='';$('modeSelect').value='demo';await refresh();
  setFeedback('SYNTHETIC DEMO loaded. These are sample players, not real server data.');
 }catch{setFeedback('Demo could not be loaded. Check that the local service is running.');}
 finally{button.disabled=false;}
}
async function importADM(){
 const file=$('admFile').files[0],button=$('importButton');
 if(!file){setFeedback('Choose an .ADM file to import.');return;}
 if(!file.name.toLowerCase().endsWith('.adm')||file.size<1||file.size>8*1024*1024){setFeedback('Choose a non-empty .ADM file up to 8 MiB.');return;}
 button.disabled=true;setFeedback('Importing selected ADM into local workspace…');
 try{
  const response=await fetch('/api/import?name='+encodeURIComponent(file.name),{
   method:'POST',headers:{...postHeaders,'Content-Type':'application/octet-stream'},body:await file.arrayBuffer()});
  if(!response.ok)throw Error();
  const imported=await response.json();state.scope='local';state.selectedId='';$('modeSelect').value='local';await refresh();
  setFeedback('Imported '+imported.new_events+' new event(s). '+(imported.new_events===0?'No new complete log lines found.':'Records are now shown below.'));
 }catch{setFeedback('Import failed. Check .ADM format and 8 MiB limit; no remote service was contacted.');}
 finally{button.disabled=false;}
}
async function searchIncidentTimeline(){
 const root=$('incidentOutput'),start=$('incidentStart').value,end=$('incidentEnd').value;
 const isSecondPrecision=s=>/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/.test(s);
 if(!isSecondPrecision(start)||!isSecondPrecision(end)){root.textContent='Choose valid start/end times from the server clock.';return;}
 const normalize=s=>s.length===16?s+':00':s;
 root.textContent='Searching imported records…';
 const params=new URLSearchParams({start:normalize(start),end:normalize(end),details:'1',max_records:'500',scope:state.scope});
 if(state.selectedId)params.set('player_id',state.selectedId);
 try{
  const response=await fetch('/api/incidents?'+params);if(!response.ok)throw Error();
  const data=await response.json();root.replaceChildren();
  const summary=document.createElement('p');summary.textContent=data.group_count+' review windows · '+data.selected_records+' imported records'+(data.truncated?' · TRUNCATED; refine interval':'');root.append(summary);
  for(const group of data.groups){const card=document.createElement('div');card.className='incident-item';
   const title=document.createElement('strong');title.textContent='Window '+group.index+': '+group.first_observed.replace('T',' ')+' to '+group.last_observed.replace('T',' ');
   const detail=document.createElement('p');detail.textContent=group.record_count+' records · '+group.known_players+' linked players · '+Object.entries(group.kind_counts).map(([kind,n])=>kind+' '+n).join(', ');
   card.append(title,detail);root.append(card);}
  if(!data.groups.length){const empty=document.createElement('p');empty.textContent='No matching review windows in dated logs.';root.append(empty);}
 }catch{root.textContent='Search unavailable or invalid interval (48 hours maximum).';}
}
$('kind').addEventListener('change',paintEvents);
$('playerFilter').addEventListener('change',e=>{state.selectedId=e.target.value;loadHistory();});
$('modeSelect').addEventListener('change',e=>{state.scope=e.target.value;state.selectedId='';state.history=null;$('incidentOutput').textContent='Choose an interval up to 48 hours.';refresh();});
$('demoButton').addEventListener('click',launchDemo);
$('importButton').addEventListener('click',importADM);
$('incidentSearch').addEventListener('click',searchIncidentTimeline);
refresh();setInterval(refresh,20000);
