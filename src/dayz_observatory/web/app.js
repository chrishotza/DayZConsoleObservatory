const state={players:[],events:[]};
const fmt=p=>p===null||p===undefined?'—':String(p);
function paintMap(){
 const canvas=document.getElementById('map'), ctx=canvas.getContext('2d'), w=canvas.width,h=canvas.height;
 ctx.clearRect(0,0,w,h);ctx.fillStyle='#0d1718';ctx.fillRect(0,0,w,h);
 const pts=state.players.filter(x=>Number.isFinite(x.x)&&Number.isFinite(x.z));
 const xs=pts.map(x=>x.x),zs=pts.map(x=>x.z);let loX=Math.min(0,...xs),hiX=Math.max(15360,...xs),loZ=Math.min(0,...zs),hiZ=Math.max(15360,...zs);
 const mx=72,my=54, iw=w-2*mx,ih=h-2*my;
 const X=n=>mx+iw*(n-loX)/(hiX-loX||1), Y=n=>h-my-ih*(n-loZ)/(hiZ-loZ||1);
 ctx.strokeStyle='#1f3533';ctx.lineWidth=1;ctx.font='14px monospace';ctx.fillStyle='#6e9387';
 for(let i=0;i<=8;i++){let a=i/8;const x=mx+iw*a,y=my+ih*a;ctx.beginPath();ctx.moveTo(x,my);ctx.lineTo(x,h-my);ctx.moveTo(mx,y);ctx.lineTo(w-mx,y);ctx.stroke();ctx.fillText(Math.round(loX+(hiX-loX)*a),x-18,h-my+23);}
 ctx.fillStyle='#85a99c';ctx.fillText('Z ↑',17,22);ctx.fillText('X →',w-57,h-12);
 if(!pts.length){ctx.fillStyle='#7faba0';ctx.font='19px sans-serif';ctx.textAlign='center';ctx.fillText('No location observations imported yet',w/2,h/2);ctx.textAlign='left';return;}
 pts.forEach((p,i)=>{const x=X(p.x),y=Y(p.z);ctx.fillStyle='#81e2b5';ctx.globalAlpha=.8;ctx.beginPath();ctx.arc(x,y,7,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;ctx.strokeStyle='#d5ffe9';ctx.beginPath();ctx.arc(x,y,12,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#d2efdf';ctx.font='13px sans-serif';ctx.fillText((p.player_name||'Unknown').slice(0,24),x+15,y-9);});
}
function paintEvents(){const root=document.getElementById('events');root.replaceChildren();const kind=document.getElementById('kind').value;
const filtered=state.events.filter(e=>!kind||e.kind===kind);
for(const e of filtered.slice(0,100)){
 const row=document.createElement('div');row.className='event';const tag=document.createElement('div');tag.className='tag '+e.kind;tag.textContent=e.kind;
 const details=document.createElement('div');const name=document.createElement('div');name.className='ename';name.textContent=e.player_name||'Server event';
 const extra=document.createElement('div');extra.className='detail';const coords=e.x===null?'':` • X ${e.x} / Z ${e.z}`;
 extra.textContent=(e.occurred_at||e.clock||'Time unavailable')+coords;details.append(name,extra);row.append(tag,details);root.append(row);
}}
async function refresh(){try{
 const [p,e]=await Promise.all([fetch('/api/players'),fetch('/api/events?limit=500')]);if(!p.ok||!e.ok)throw Error('Local API request failed');
 state.players=await p.json();state.events=await e.json();
 document.getElementById('playerCount').textContent=state.players.length;
 document.getElementById('eventCount').textContent=state.events.length+' latest';
 const last=state.players[0];document.getElementById('lastSample').textContent=last?.occurred_at?.replace('T',' ')||'Not dated';
 document.getElementById('status').textContent='Local API connected • Imported records only';paintMap();paintEvents();
 }catch(err){document.getElementById('status').textContent='Unable to read local API';}}
document.getElementById('kind').addEventListener('change',paintEvents);refresh();setInterval(refresh,20000);
