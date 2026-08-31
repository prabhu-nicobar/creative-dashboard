const D = JSON.parse(document.getElementById('payload').textContent);
let W = 'l7', V = 'groups', CK = D.cohortOrder[0], F = 'All', Q = '';
const SEL = new Set();

const TIP = {
 'CPM':'What it costs to show this creative to 1,000 people. Lower is cheaper reach.',
 'Outbound CTR':'Of everyone who saw it, the share who clicked through to the site.',
 'Click to page':'Of everyone who clicked, the share who actually reached the page. Below 70% means people are dropping before the page loads.',
 'Page to cart':'Of everyone who reached the page, the share who added something to the basket.',
 'Cost per cart':'What you paid, on average, for each item added to a basket.',
 'ROAS':'Revenue divided by spend. 2.00x means two rupees back for every rupee in.',
 'AOV':'Average order value — what a single order from this creative is worth.',
 'Frequency':'How many times the average person saw this creative.',
 'Landing page views':'Times someone actually arrived on the site from this creative.',
 'Impressions':'Times the creative was shown.','Spend':'What has been spent on this creative in this window.',
 'Add to carts':'Items added to basket, attributed to this creative.',
 'Purchases':'Orders attributed to this creative.','Revenue':'Order value attributed to this creative.'
};
const R = v => '₹' + (v==null ? '—' : Math.round(v).toLocaleString('en-IN'));
const cls = b => ({'Strong':'strong','Above par':'above','At par':'par','Below par':'below','Weak':'weak'}[b] || 'na');
const esc = s => String(s??'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const win = () => D.data[W];
const wlabel = k => D.windows.find(x=>x.k===k).label;

function spark(vals){
 const pts = vals.map((v,i)=>[i,v]).filter(p=>p[1]!=null);
 if(pts.length<2) return '';
 const lo=Math.min(...pts.map(p=>p[1])), hi=Math.max(...pts.map(p=>p[1])), rg=Math.max(hi-lo,1);
 const d = pts.map(p=>`${(p[0]/3)*46},${18-((p[1]-lo)/rg)*15}`).join(' ');
 const last=pts[pts.length-1], up=last[1]>=pts[0][1];
 return `<svg class="spk" width="50" height="20" viewBox="0 0 50 20" fill="none">
  <polyline points="${d}" stroke="${up?'#1f6b4f':'#a8483c'}" stroke-width="1.5"
   stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="${(last[0]/3)*46}" cy="${18-((last[1]-lo)/rg)*15}" r="2" fill="${up?'#1f6b4f':'#a8483c'}"/></svg>`;
}

function scoreCell(label,val,bandTxt,extra,delta){
 const d = delta==null ? '' :
   `<span class="dlt ${delta>2?'up':delta<-2?'dn':'fl'}" title="Change against ${esc(wlabel(nextWider()))}">${delta>0?'+':''}${delta}</span>`;
 return `<div class="sc ${cls(bandTxt)}${extra||''}">${d}
  <span class="sl">${label}</span>
  <span class="sv">${val==null?'n/a':val}</span>
  <span class="sb">${esc(val==null?'Data inadequate':bandTxt)}</span></div>`;
}
const nextWider = () => ({l7:'l14',l14:'mtd',mtd:'d90',d90:'d90'})[W];

function metricRows(m){
 const rows = [['Spend',R(m.sp)],['Impressions',(m.im||0).toLocaleString('en-IN')],
  ['CPM',R(m.cpm)],['Outbound CTR',(m.ctr??0)+'%'],['Click to page',(m.c2l??0)+'%'],
  ['Landing page views',(m.lpv||0).toLocaleString('en-IN')],['Page to cart',(m.l2a??0)+'%'],
  ['Add to carts',(m.atc||0).toLocaleString('en-IN')],['Cost per cart',R(m.cpa)],
  ['Purchases',(m.pur||0).toLocaleString('en-IN')],['Revenue',R(m.rev)],
  ['ROAS',m.roas?m.roas+'x':'—'],['AOV',R(m.aov)],['Frequency',m.fq??'—']];
 return rows.map(([k,v])=>`<div class="m"><span class="tt" title="${esc(TIP[k]||'')}">${k}</span><b>${v}</b></div>`).join('');
}

function vlabel(a){
 const m = a.n.match(/\b(V\d)\b/i);
 if(m) return 'Version '+m[1].toUpperCase();
 const stop=/^(PDP|PLP|COPY|SNG|GIF|VIDEO|CAROUSEL|CATALOGUE|A\d\d|D-?\d+|\d+)$/i;
 const p = a.n.split(/[-\s]+/).filter(x=>x && !stop.test(x));
 return p.slice(-2).join(' ') || a.f;
}
function card(a, opts={}){
 const top = a.rankable && a.rk <= Math.max(1, Math.ceil(a.of/3));
 const rk = a.rankable ? `<span class="rk ${top?'top':''}">#${a.rk} of ${a.of}</span>`
                       : `<span class="rk none">unranked</span>`;
 const fb = a.fb ? `<div class="fb"><h5>Creative feedback</h5><p>${esc(a.fb)}</p></div>`
                 : `<div class="fb thin"><h5>Creative feedback</h5><p>${esc(a.fbBlock)}</p></div>`;
 return `<article class="card ${SEL.has(a.id)?'sel':''}" data-id="${a.id}">
  <div class="chd"><div>
   <div class="tags">${rk}<span class="tag">${esc(a.f)}</span>
    ${a.d?`<span class="tag dest">${esc(a.d)}</span>`:''}
    ${a.st==='Paused'?'<span class="tag paused">Paused</span>':''}</div>
   <h4>${esc(a.th)}</h4><p class="fn2">${esc(a.n)}</p></div>
   <div class="cbox ${SEL.has(a.id)?'on':''}" data-cmp="${a.id}" title="Add to comparison">✓</div></div>
  <div class="thumb">${a.cid?`<img loading="lazy" src="images/${a.cid}.jpg" alt="${esc(a.th)}"
    onerror="this.parentNode.classList.add('noimg');this.remove();">`:''}
   <span>preview not downloaded yet</span></div>
  <div class="scores">
   ${scoreCell('Pre-Click',a.pre,a.preB)}
   ${scoreCell('Post-Click',a.post,a.postB)}
   ${scoreCell('Overall',a.ov,a.ovB,' ov',a.delta)}</div>
  <div class="meta">
   <span class="conf ${a.conf}" title="${esc(a.confN)}"><i class="dot"></i>${esc(a.confL)}</span>
   <span>·</span><span>${a.dl} days live</span><span>·</span><span>${esc(a.camp)}</span>
   ${spark(a.spark)}</div>
  ${a.dead?`<p class="dead">Too close to call — this sits in the inconclusive band. Read it again next week before acting on it.</p>`:''}
  ${a.proj?`<p class="proj">${esc(a.proj)}</p>`:''}
  <div>
   <div class="tabs2"><button class="on" data-p="a">What this means</button><button data-p="m">Numbers</button></div>
   <div class="pane a on" style="margin-top:9px"><p>${esc(a.an)}</p></div>
   <div class="pane m" style="margin-top:9px"><div class="mgrid">${metricRows(a.m)}</div>
    <a class="cta" target="_blank" rel="noopener"
     href="https://adsmanager.facebook.com/adsmanager/manage/ads?act=${D.account}&selected_ad_ids=${a.id}">Open in Ads Manager ↗</a></div>
  </div>${fb}</article>`;
}

function filtered(){
 const q = Q.toLowerCase();
 return win().ads.filter(a =>
   (F==='All' || a.f===F) &&
   (!q || (a.n+' '+a.th+' '+a.col+' '+a.pt+' '+a.c+' '+a.r).toLowerCase().includes(q)));
}

/* ------------------------------------------------ shared blocks */
const ARCH = `<div class="arch"><h4>Archive<span class="tbd">TBD</span></h4>
 <p>Month-by-month history will live here, each period stored as its own snapshot so any past
 month can be reopened and compared. Not built yet — until it is, <b>Last 90 days</b> is the
 longest look back available, covering 2 June to 30 August 2026.</p></div>`;

const MSG = `<div class="msg"><h4>Message for the brand team</h4><div class="msgrid">
 <p><b>Start with a group, not a leaderboard.</b> Everything inside a campaign group is comparable.
  Nothing across groups is. A 62 in Menswear testing and a 62 in Jewellery both mean "better than
  most of your peers" — not "equally good ads".</p>
 <p><b>Read the two scores against each other.</b> Pre-Click is whether it got noticed. Post-Click
  is whether that turned into money. When they disagree, the disagreement is the brief: high
  attention with low conversion means the picture promised something the page didn't keep.</p>
 <p><b>Check a second window before acting.</b> Seven days rewards whatever launched last week;
  ninety days rewards whatever has run longest. Neither is the truth alone — the cards tell you
  when they disagree.</p>
 <p><b>What this is not.</b> It won't tell you what to switch off or where to move budget. That is
  a media decision and it lives elsewhere. This exists so the next thing you brief is better than
  the last thing you shipped.</p></div></div>`;

const LEGEND = `<div class="legend"><h4>How to read the scores</h4><div class="lg2">
 <p><b>50 is the middle of the group.</b> A creative scoring 50 performs exactly like the median
  creative in its category and audience. 100 is twice as good. Nothing here is an absolute grade.</p>
 <p><b>Pre-Click</b> is how well it earns attention — how cheaply it reaches people, how many
  click, and how many of those clicks actually land on the page.</p>
 <p><b>Post-Click</b> is what happens next: carts, orders and return on spend.
  <b>Overall</b> combines the two, weighted toward sales in high-volume groups.</p></div>
 <div class="bands">
  <span class="bd" style="color:var(--strong)">Strong 65+</span>
  <span class="bd" style="color:var(--above)">Above par 55–64</span>
  <span class="bd" style="color:var(--par)">At par 45–54</span>
  <span class="bd" style="color:var(--below)">Below par 35–44</span>
  <span class="bd" style="color:var(--weak)">Weak under 35</span>
  <span class="bd" style="border-color:var(--amber);background:#fffdf6">▲ Amber marks the top third</span>
 </div></div>`;

const FUTURE = `<div class="future"><h5>What this dashboard will be able to tell you later</h5>
 <p>Everything above is derived from delivery numbers alone, so it can tell you <i>that</i> a
 creative worked without telling you <i>why</i>. Once every creative is tagged on a fixed set of
 attributes — flat-lay versus styled, model present or not, natural versus studio light, warm or
 cool palette, text overlay, whether an offer is visible, how large the hero product sits in
 frame — the same engine starts answering craft questions:</p>
 <ul>
  <li>“Across 47 creatives, flat-lay on warm ground beats styled interiors in House &amp; Home
   bottom-of-funnel by 22 points.”</li>
  <li>“Creatives with a visible price convert 30% better in Menswear and 15% worse in Womenswear.”</li>
  <li>“Every Jewellery creative in the top third this quarter had a single hero product filling
   more than half the frame.”</li>
 </ul>
 <p style="margin-top:9px">That work begins when the Secondary Variables sheet is ready. The
 fields are already built into this tool and sitting empty.</p></div>`;

function insightsBlock(){
 const items = win().insights;
 if(!items.length) return '';
 return `<section class="insights"><h3>Insights for the brand team</h3>
  <p class="isub">Patterns across everything running in this window, not just the group you have
  selected. These are the things worth carrying into the next planning conversation.</p>
  <div class="igrid">${items.map(i=>`<div class="ins"><h5>${esc(i.t)}</h5><p>${i.b}</p>
   <p class="idet">${esc(i.d)}</p></div>`).join('')}</div>${FUTURE}</section>`;
}

function emptyState(msg, sub){
 return `<div class="empty"><b>${esc(msg)}</b>${esc(sub)}</div>`;
}

/* ------------------------------------------------ views */
function viewGroups(){
 const m = win().cohorts[CK];
 if(!m) return ARCH+MSG+LEGEND+emptyState('Nothing ran in this group during '+wlabel(W)+'.',
   'This campaign may not have launched yet, or had no spend in this window. Try a wider window.')
   + insightsBlock();
 const ads = filtered().filter(a=>a.ck===CK).sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0));
 const notes = [];
 if(m.pcw!==W && m.pcq!=='none')
  notes.push(`<div class="note warn"><b>Post-click is scored on ${wlabel(m.pcw)} — a bigger data
   set than the ${wlabel(W).toLowerCase()} view you have selected.</b> There weren't enough carts
   and orders in ${wlabel(W).toLowerCase()} to read this group reliably, so the Post-Click and
   Overall scores use ${wlabel(m.pcw).toLowerCase()} (${m.pcAtc.toLocaleString('en-IN')} carts,
   ${m.pcPur.toLocaleString('en-IN')} orders). Pre-Click still uses ${wlabel(W).toLowerCase()}.</div>`);
 if(m.pcq==='thin')
  notes.push(`<div class="note warn">This group is thin even over ${wlabel(m.pcw).toLowerCase()} —
   ${m.pcAtc.toLocaleString('en-IN')} carts and ${m.pcPur} orders across ${m.n} creatives. Post-click
   scores are shown so you can see the shape of it, not so you can act on a single one.</div>`);
 if(m.pcq==='none')
  notes.push(`<div class="note warn">Not enough carts or orders anywhere in the last 90 days to
   score post-click. Pre-click only — this group is too new.</div>`);
 if(!m.rankable)
  notes.push(`<div class="note warn">Too few creatives running to rank against each other. Scores
   are shown; positions are not.</div>`);
 if(m.cat_roas)
  notes.push(`<div class="note bench">Dynamic catalogue benchmark: <b>${m.cat_roas}x</b> on
   ${R(m.cat_spend)}. <b>${m.beat} of ${m.n}</b> creatives in this group beat it.</div>`);

 const maxsp = Math.max(...m.fstrip.map(f=>f.sp),1);
 const strip = m.fstrip.map(f=>`<div class="fs"><div class="fn">${esc(f.f)}</div>
   <div class="fm">${f.n} live · ${R(f.sp)}</div>
   <div class="fb"><span>Pre ${f.pre||'—'}</span><span class="bar2"><span style="width:${f.pre}%;background:var(--slate)"></span></span></div>
   <div class="fb"><span>Post ${f.post||'—'}</span><span class="bar2"><span style="width:${f.post}%;background:var(--amber)"></span></span></div>
  </div>`).join('');

 return ARCH+MSG+LEGEND+`
  <div class="chead"><div class="ctitle"><h3>${esc(m.cat)}</h3>
   <span class="role">${esc(m.role)}</span></div>
   <p class="cstats">${m.n} creatives<i>·</i>${R(m.spend)} spent<i>·</i>
    ${m.atc.toLocaleString('en-IN')} carts<i>·</i>${m.pur.toLocaleString('en-IN')} orders<i>·</i>
    attribution ${esc(m.attribution)}<i>·</i>${m.profile==='high'?'higher-volume':'testing'} scoring</p>
   <div class="notes">${notes.join('')}</div></div>
  <div class="brief"><h5>What changed in this group</h5><ul>${m.brief.map(b=>`<li>${b}</li>`).join('')}</ul></div>
  <div class="fstrip">${strip}</div>
  ${ads.length?`<div class="grid">${ads.map(a=>card(a)).join('')}</div>`
    :emptyState('No creatives match that filter in this group.','Clear the search or format filter to see everything running.')}
  ${insightsBlock()}`;
}

function viewConcepts(){
 const ads = filtered().filter(a=>a.ck===CK);
 const fam = {};
 ads.forEach(a=>{ (fam[a.vk] = fam[a.vk] || []).push(a); });
 const multi = Object.entries(fam).filter(([,v])=>v.length>1)
   .map(([k,v])=>[k,v.sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0))])
   .sort((a,b)=>((b[1][0].ov??b[1][0].pre??0)-(b[1].at(-1).ov??b[1].at(-1).pre??0))
              -((a[1][0].ov??a[1][0].pre??0)-(a[1].at(-1).ov??a[1].at(-1).pre??0)));
 const single = Object.entries(fam).filter(([,v])=>v.length===1).map(([,v])=>v[0])
   .sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0));
 if(!multi.length && !single.length)
  return ARCH+emptyState('Nothing to group in this window.','Try a wider window or a different group.');
 const blocks = multi.map(([k,v])=>{
  const best=v[0], worst=v.at(-1);
  const gap=Math.round((best.ov??best.pre??0)-(worst.ov??worst.pre??0));
  const cells=v.map((a,i)=>`<div class="vcell ${i===0?'best':''}">
    <div class="vthumb">${a.cid?`<img loading="lazy" src="images/${a.cid}.jpg" alt=""
      onerror="this.parentNode.classList.add('noimg');this.remove();">`:''}</div>
    <div class="vn">${esc(vlabel(a))}</div>
    <div class="vv" style="color:var(--${cls(a.ovB!=='Data Inadequate'?a.ovB:a.preB)})">${a.ov??a.pre??'—'}</div>
    <div class="vm">${esc(a.f)}${a.d?' · '+esc(a.d):''} · ${R(a.m.sp)} · ${a.m.pur} orders</div></div>`).join('');
  const same = v.every(a=>a.d===v[0].d), sameF = v.every(a=>a.f===v[0].f);
  let verdict;
  if(gap>=20) verdict = `<b>${gap} points</b> separate the best and worst version of this idea.
   ${sameF?'Same format':'Different formats'}${same&&v[0].d?`, same ${esc(v[0].d)} destination`:''},
   same product — so the gap is execution, not strategy. Whatever <b>${esc(vlabel(best))}</b>
   does differently is the cheapest win available to you this week.`;
  else if(gap>=8) verdict = `A <b>${gap}-point</b> spread across versions. Real but not dramatic —
   worth a look at the winner before the next round, not worth reshooting for.`;
  else verdict = `The versions score within <b>${gap} points</b> of each other. This concept performs
   consistently however it is executed, which usually means the product is doing the work rather than
   the treatment.`;
  return `<div class="concept"><h4>${esc(best.th)}</h4>
   <p class="csub">${v.length} versions · ${esc(best.c)} · ${esc(best.r)}</p>
   <div class="vrow">${cells}</div><div class="verdict">${verdict}</div></div>`;
 }).join('');
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Concepts</h3>
   <span class="role">${esc(CK)}</span></div>
  <p class="cstats">One card per idea. Where the same concept was shot more than once, the versions
   sit side by side so the gap between them is visible — that gap is execution, and it is the most
   directly useful number on this page.</p></div>
  ${blocks || emptyState('No concept in this group has more than one version.','Everything here was shot once, so there is nothing to compare against itself.')}
  ${single.length?`<div class="chead" style="margin-top:30px"><div class="ctitle">
   <h3>Shot once</h3><span class="role">${single.length} concepts with no sibling</span></div></div>
   <div class="grid">${single.map(a=>card(a)).join('')}</div>`:''}`;
}

function viewProducts(){
 const ads = filtered();
 const by = {};
 ads.forEach(a=>{ const k = a.col!=='Unnamed' ? a.col : a.pt; (by[k]=by[k]||[]).push(a); });
 const rows = Object.entries(by).filter(([,v])=>v.length>=2)
  .map(([k,v])=>({k,v,sp:v.reduce((s,a)=>s+a.m.sp,0),
    pur:v.reduce((s,a)=>s+a.m.pur,0), rev:v.reduce((s,a)=>s+a.m.rev,0),
    sc:Math.round(v.reduce((s,a)=>s+(a.ov??a.pre??0),0)/v.length)}))
  .sort((a,b)=>b.sp-a.sp);
 if(!rows.length) return ARCH+emptyState('Not enough to group by collection here.','Widen the window or clear the search.');
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Collections</h3>
   <span class="role">across every campaign group</span></div>
  <p class="cstats">The same view, pivoted the way the brand team actually thinks — by collection
   and product rather than by campaign. Scores are still calculated inside each creative's own
   group, so a collection spanning several groups is an average of fair comparisons.</p></div>
  ${rows.map(r=>`<div class="concept"><h4>${esc(r.k)}</h4>
   <p class="csub">${r.v.length} creatives · ${R(r.sp)} spent · ${r.pur} orders ·
    ${r.pur?R(r.rev/r.pur)+' average order':'no orders yet'} ·
    average score ${r.sc} · runs in ${[...new Set(r.v.map(a=>a.c))].join(', ')}</p>
   <div class="grid">${r.v.sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0)).map(a=>card(a)).join('')}</div>
  </div>`).join('')}`;
}

function viewWinners(){
 const out = [];
 Object.keys(win().cohorts).forEach(ck=>{
  const g = filtered().filter(a=>a.ck===ck).sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0));
  out.push(...g.slice(0, Math.max(1, Math.ceil(g.length/3))));
 });
 out.sort((x,y)=>(y.ov??y.pre??0)-(x.ov??x.pre??0));
 if(!out.length) return ARCH+emptyState('Nothing clears the bar in this window.','Try a wider window.');
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Winners</h3>
   <span class="role">top third of every group, ${out.length} creatives</span></div>
  <p class="cstats">No analysis, no filtering by group — just everything currently outperforming
   its peers, in one place. Use it when you want inspiration rather than diagnosis. Remember these
   are top-third <i>within their own group</i>, so a Jewellery winner and a Womenswear winner are
   not the same absolute standard.</p></div>
  <div class="grid">${out.map(a=>card(a)).join('')}</div>`;
}

/* ------------------------------------------------ compare */
function compare(){
 const [a,b] = [...SEL].map(id => win().ads.find(x=>x.id===id)).filter(Boolean);
 if(!a||!b) return;
 const rows = [
  ['Group', a.ck, b.ck, null],['Format', a.f, b.f, null],['Destination', a.d||'—', b.d||'—', null],
  ['Days live', a.dl, b.dl, null],
  ['Pre-Click', a.pre??'—', b.pre??'—', 'hi'],['Post-Click', a.post??'—', b.post??'—','hi'],
  ['Overall', a.ov??'—', b.ov??'—','hi'],
  ['Spend', R(a.m.sp), R(b.m.sp), null],['CPM', R(a.m.cpm), R(b.m.cpm), 'lo'],
  ['Outbound CTR', a.m.ctr+'%', b.m.ctr+'%','hi'],['Click to page', a.m.c2l+'%', b.m.c2l+'%','hi'],
  ['Page to cart', a.m.l2a+'%', b.m.l2a+'%','hi'],['Cost per cart', R(a.m.cpa), R(b.m.cpa),'lo'],
  ['Purchases', a.m.pur, b.m.pur,'hi'],['ROAS', a.m.roas??'—', b.m.roas??'—','hi'],
  ['AOV', R(a.m.aov), R(b.m.aov),'hi'],
 ];
 const num = v => parseFloat(String(v).replace(/[^\d.-]/g,''));
 const body = rows.map(([l,x,y,dir])=>{
  let cx='',cy='';
  if(dir && !isNaN(num(x)) && !isNaN(num(y))){
   const better = dir==='hi' ? (num(x)>num(y)) : (num(x)<num(y));
   if(num(x)!==num(y)){ better?cx='win2':cy='win2'; }
  }
  return `<div class="lbl">${esc(l)}</div><div class="${cx}">${esc(x)}</div><div class="${cy}">${esc(y)}</div>`;
 }).join('');
 document.getElementById('mbox').innerHTML = `
  <button class="closeb" onclick="document.getElementById('modal').classList.remove('on')">Close</button>
  <h3>Side by side</h3>
  <p class="msub">A learning view, not a scoring one. These two may sit in different groups, where
   scores are not strictly comparable — use this to understand <i>why</i> something works, not to
   decide which is better.</p>
  <div class="cmpimgs"><div></div>
   <div class="thumb">${a.cid?`<img src="images/${a.cid}.jpg" onerror="this.remove()">`:''}</div>
   <div class="thumb">${b.cid?`<img src="images/${b.cid}.jpg" onerror="this.remove()">`:''}</div></div>
  <div class="cmp"><div class="hd"></div><div class="hd">${esc(a.th)}</div><div class="hd">${esc(b.th)}</div>${body}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:22px">
   <div><h5 style="margin:0 0 5px;font-size:12px;letter-spacing:.8px;text-transform:uppercase;color:var(--mute)">${esc(a.th)}</h5>
    <p style="margin:0;font-size:13px;color:var(--dim);line-height:1.7">${esc(a.an)}</p></div>
   <div><h5 style="margin:0 0 5px;font-size:12px;letter-spacing:.8px;text-transform:uppercase;color:var(--mute)">${esc(b.th)}</h5>
    <p style="margin:0;font-size:13px;color:var(--dim);line-height:1.7">${esc(b.an)}</p></div></div>`;
 document.getElementById('modal').classList.add('on');
}

/* ------------------------------------------------ chrome */
function render(){
 document.getElementById('cksel').style.display = (V==='groups'||V==='concepts') ? '' : 'none';
 const v = {groups:viewGroups, concepts:viewConcepts, products:viewProducts, winners:viewWinners}[V];
 document.getElementById('app').innerHTML = v();
 const t = document.getElementById('tray');
 t.classList.toggle('on', SEL.size>0);
 document.getElementById('trayitems').textContent =
   SEL.size===1 ? '1 selected — pick one more' : SEL.size+' selected';
 document.getElementById('cmpgo').disabled = SEL.size!==2;
 document.getElementById('cmpgo').style.opacity = SEL.size===2 ? 1 : .45;
}

D.windows.forEach(w=>{
 const b=document.createElement('button'); b.dataset.w=w.k;
 b.innerHTML=`<b>${w.label}</b><i>${w.dates}</i>`;
 if(w.k===W) b.className='on';
 b.onclick=()=>{ W=w.k; document.querySelectorAll('#wtabs button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); render(); window.scrollTo({top:0,behavior:'smooth'}); };
 document.getElementById('wtabs').appendChild(b);
});
const sel=document.getElementById('cksel');
sel.innerHTML = D.cohortOrder.map(ck=>`<option value="${esc(ck)}">${esc(ck.replace(' | ',' — '))}</option>`).join('');
sel.value=CK; sel.onchange=()=>{CK=sel.value;render();window.scrollTo({top:0,behavior:'smooth'});};
const fmts=[...new Set(D.data.d90.ads.map(a=>a.f))].sort();
document.getElementById('fchips').innerHTML =
 ['All',...fmts].map(f=>`<button class="chip ${f==='All'?'on':''}" data-f="${esc(f)}">${esc(f)}</button>`).join('');
document.getElementById('fchips').onclick=e=>{const b=e.target.closest('[data-f]'); if(!b)return;
 document.querySelectorAll('#fchips .chip').forEach(x=>x.classList.remove('on'));
 b.classList.add('on'); F=b.dataset.f; render();};
document.getElementById('vtabs').onclick=e=>{const b=e.target.closest('[data-v]'); if(!b)return;
 document.querySelectorAll('#vtabs button').forEach(x=>x.classList.remove('on'));
 b.classList.add('on'); V=b.dataset.v; render(); window.scrollTo({top:0,behavior:'smooth'});};
let qt; document.getElementById('q').oninput=e=>{clearTimeout(qt);
 qt=setTimeout(()=>{Q=e.target.value.trim(); render();},220);};
function setMeeting(on){
 document.body.classList.toggle('meeting', on);
 const b=document.getElementById('meetb');
 b.classList.toggle('on', on);
 b.textContent = on ? 'Exit meeting mode' : 'Meeting mode';
 if(!on) window.scrollTo({top:0,behavior:'smooth'});
}
document.getElementById('meetb').onclick=()=>setMeeting(!document.body.classList.contains('meeting'));
document.getElementById('exitm').onclick=()=>setMeeting(false);
document.addEventListener('keydown',e=>{
 if(e.key==='Escape'){
  if(document.getElementById('modal').classList.contains('on'))
    document.getElementById('modal').classList.remove('on');
  else if(document.body.classList.contains('meeting')) setMeeting(false);
 }});
document.addEventListener('click',e=>{
 const c=e.target.closest('[data-cmp]');
 if(c){ const id=c.dataset.cmp;
  if(SEL.has(id)) SEL.delete(id); else { if(SEL.size>=2) SEL.delete([...SEL][0]); SEL.add(id); }
  render(); return; }
 const p=e.target.closest('.tabs2 button');
 if(p){ const card=p.closest('.card');
  card.querySelectorAll('.tabs2 button').forEach(x=>x.classList.remove('on')); p.classList.add('on');
  card.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  card.querySelector('.pane.'+p.dataset.p).classList.add('on'); }
});
document.getElementById('cmpgo').onclick=compare;
document.getElementById('cmpclr').onclick=()=>{SEL.clear();render();};
document.getElementById('modal').onclick=e=>{ if(e.target.id==='modal') e.target.classList.remove('on'); };
document.getElementById('pulled').textContent=D.pulled;
document.getElementById('acct').textContent=D.account;
render();
