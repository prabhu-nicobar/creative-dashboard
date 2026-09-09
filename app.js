const D = JSON.parse(document.getElementById('payload').textContent);
let W='l7', V='groups', CK=D.cohortOrder[0], Q='', SORT='rank', SHOWF=false;
const F = {};                       // active filter values, key -> value
const SEL = new Set();

const TIP={
 'CPM':'What it costs to show this creative to 1,000 people. Lower is cheaper reach.',
 'Outbound CTR':'Of everyone who saw it, the share who clicked through to the site.',
 'Click to page':'Of everyone who clicked, the share who actually reached the page. Below 70% means people drop before the page loads.',
 'Page to cart':'Of everyone who reached the page, the share who added something to the basket.',
 'Cost per cart':'What you paid, on average, for each item added to a basket.',
 'ROAS':'Revenue divided by spend. 2.00x means two rupees back for every rupee in.',
 'AOV':'Average order value — what a single order from this creative is worth.',
 'Frequency':'How many times the average person saw this creative.',
 'Landing page views':'Times someone actually arrived on the site from this creative.',
 'Impressions':'Times the creative was shown.','Spend':'Spent on this creative in this window.',
 'Add to carts':'Items added to basket, attributed to this creative.',
 'Purchases':'Orders attributed to this creative.','Revenue':'Order value attributed to this creative.'};

const R=v=>'₹'+(v==null?'—':Math.round(v).toLocaleString('en-IN'));
const cls=b=>({'Strong':'strong','Above par':'above','At par':'par','Below par':'below','Weak':'weak'}[b]||'na');
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const win=()=>D.data[W];
const wlabel=k=>D.windows.find(x=>x.k===k).label;
const uniq=(arr,k)=>[...new Set(arr.map(a=>a[k]).filter(Boolean))].sort();

/* ---------------------------------------------------- filters */
const FDEFS=[
 {k:'sort',  label:'Sort by', opts:['Rank','Amount spent','ROAS','Pre-Click','Post-Click','Biggest drop','Newest','Cost per cart'], single:true},
 {k:'fn',    label:'Funnel',  opts:()=>['TOF','MOF','BOF']},
 {k:'c',     label:'Category',opts:a=>uniq(a,'c')},
 {k:'st',    label:'Status',  opts:()=>['Active','Paused']},
 {k:'pship', label:'Asset type', opts:()=>['Partnership','Non-Partnership']},
 {k:'f',     label:'Creative type', opts:a=>uniq(a,'f')},
 {k:'col',   label:'Collection', opts:a=>uniq(a,'col')},
 {k:'d',     label:'Destination', opts:()=>['PDP','PLP']},
 {k:'ovB',   label:'Score band', opts:()=>['Strong','Above par','At par','Below par','Weak']},
 {k:'conf',  label:'Confidence', opts:()=>['solid','moderate','thin'], pretty:{solid:'Solid',moderate:'Moderate',thin:'Thin'}},
 {k:'dlband',label:'Days live', opts:()=>['<7','7–14','14–30','30+']},
 {k:'ranked',label:'Ranking',  opts:()=>['Ranked','Below spend floor']},
 {k:'angle', label:'Angle',    opts:a=>uniq(a,'angle')},
 {k:'sil',   label:'Silhouette',opts:a=>uniq(a,'sil')},
 {k:'vo',    label:'Voiceover', opts:a=>uniq(a,'vo')},
 {k:'ai',    label:'Origin',    opts:a=>uniq(a,'ai')},
];
function dlband(d){return d<7?'<7':d<14?'7–14':d<30?'14–30':'30+';}

function renderFilters(){
 const all=win().ads;
 let h='';
 for(const f of FDEFS){
  const opts=typeof f.opts==='function'?f.opts(all):f.opts;
  if(!opts.length) continue;
  const cur=f.k==='sort'?SORT:(F[f.k]||'All');
  h+=`<div class="frow"><span>${esc(f.label)}</span>`;
  if(f.k!=='sort') h+=`<button class="chip ${cur==='All'?'on':''}" data-fk="${f.k}" data-fv="All">All</button>`;
  h+=opts.map(o=>`<button class="chip ${cur===o?'on':''}" data-fk="${f.k}" data-fv="${esc(o)}">${esc((f.pretty&&f.pretty[o])||o)}</button>`).join('');
  h+='</div>';
 }
 document.getElementById('frows').innerHTML=h;
 const n=Object.values(F).filter(v=>v&&v!=='All').length;
 const c=document.getElementById('fcnt');
 c.style.display=n?'':'none'; c.textContent=n;
}

function match(a){
 const q=Q.toLowerCase();
 if(q && !(a.n+' '+a.th+' '+a.col+' '+a.pt+' '+a.c+' '+a.r+' '+a.camp).toLowerCase().includes(q)) return false;
 for(const [k,v] of Object.entries(F)){
  if(!v||v==='All') continue;
  if(k==='dlband'){ if(dlband(a.dl)!==v) return false; continue; }
  if(k==='ranked'){ if((v==='Ranked')!==a.ranked) return false; continue; }
  if(a[k]!==v) return false;
 }
 return true;
}
function sorted(list){
 const s=[...list];
 const by={'Rank':(x,y)=>y.ov-x.ov,'Amount spent':(x,y)=>y.m.sp-x.m.sp,
  'ROAS':(x,y)=>(y.m.roas||0)-(x.m.roas||0),'Pre-Click':(x,y)=>y.pre-x.pre,
  'Post-Click':(x,y)=>y.post-x.post,'Newest':(x,y)=>x.dl-y.dl,
  'Cost per cart':(x,y)=>(x.m.cpa||1e9)-(y.m.cpa||1e9),
  'Biggest drop':(x,y)=>((x.dec?Math.min(x.dec.ctr??0,x.dec.roas??0):0)-(y.dec?Math.min(y.dec.ctr??0,y.dec.roas??0):0))};
 return s.sort(by[SORT]||by['Rank']);
}
const filtered=()=>sorted(win().ads.filter(match));

/* ---------------------------------------------------- card */
function img(name,cid,c){
 return `<div class="thumb ${c||''}"><img loading="lazy" src="images/${encodeURIComponent(name)}.png"
  onerror="if(this.dataset.t){const t=this.parentNode;t.classList.add('noimg');
    t.closest('.card')&&t.closest('.card').classList.add('noimg');this.remove();}
   else{this.dataset.t=1;this.src='images/${cid}.jpg';}">
  <span>no preview</span></div>`;
}
function sc(label,val,b,w,extra,base,scope,bn){
 let bar='';
 if(base!=null){
  const d=val-base;
  const tone=d>=3?'up':d<=-3?'dn':'fl';
  const where=scope==='cohort'?'in this group':'account-wide — too few in this group';
  bar=`<span class="vsb ${tone}${scope==='account'?' wide':''}" title="Median for this format ${where}, across ${esc(D.baselineLabel)}, from ${bn} creatives. This one is ${d>0?'+':''}${d} against it.">
   fmt ${base}${scope==='account'?'*':''} <b>${d>0?'+':''}${d}</b></span>`;
 }
 return `<div class="sc ${cls(b)}${extra||''}"><span class="wt">${w}</span>
  <span class="sl">${label}</span><span class="sv">${val}</span>
  <span class="sb">${esc(b)}</span>${bar}</div>`;
}
function metricRows(m){
 const rows=[['Spend',R(m.sp)],['Impressions',(m.im||0).toLocaleString('en-IN')],['CPM',R(m.cpm)],
  ['Outbound CTR',(m.ctr??0)+'%'],['Click to page',(m.c2l??0)+'%'],
  ['Landing page views',(m.lpv||0).toLocaleString('en-IN')],['Page to cart',(m.l2a??0)+'%'],
  ['Add to carts',(m.atc||0).toLocaleString('en-IN')],['Cost per cart',R(m.cpa)],
  ['Purchases',(m.pur||0).toLocaleString('en-IN')],['Revenue',R(m.rev)],
  ['ROAS',m.roas?m.roas+'x':'—'],['AOV',R(m.aov)],['Frequency',m.fq??'—']];
 return rows.map(([k,v])=>`<div class="m"><span class="tt" title="${esc(TIP[k]||'')}">${k}</span><b>${v}</b></div>`).join('');
}
function card(a){
 const meta=win().cohorts[a.ck]||{wPre:20,wPost:80};
 const top=a.ranked&&a.rk<=Math.max(1,Math.ceil(a.of/3));
 const rk=a.ranked?`<span class="rk ${top?'top':''}">#${a.rk} of ${a.of}</span>`
   :`<span class="rk none">under ${R(a.floor)} — unranked</span>`;
 const fb=a.fb?`<div class="fb"><h5>Creative feedback</h5><p>${esc(a.fb)}</p></div>`
   :`<div class="fb thin"><h5>Creative feedback</h5><p>${esc(a.fbBlock)}</p></div>`;
 let flags='';
 if(a.small) flags+=`<p class="flag small">This sales score rests on ${a.m.pur} order${a.m.pur===1?'':'s'}. One more or one fewer would move it substantially.</p>`;
 if(a.dec) flags+=`<p class="flag dec">${a.dec.pre_down?'Losing attention':'Converting worse'} against ${esc(a.decP)}.${a.dec.pre_down&&a.dec.ctr!=null&&a.dec.ctr<=-15?` Clicks down ${Math.abs(a.dec.ctr).toFixed(0)}%.`:''}${a.dec.post_down&&a.dec.roas!=null&&a.dec.roas<=-15?` Return down ${Math.abs(a.dec.roas).toFixed(0)}%.`:''}</p>`;
 if(a.dead) flags+=`<p class="flag dead">Too close to call — this sits in the inconclusive band. Read it again next week.</p>`;
 return `<article class="card ${SEL.has(a.id)?'sel':''}" data-id="${a.id}">
  <div class="chd"><div>
   <div class="tags">${rk}<span class="tag">${esc(a.f)}</span>
    ${a.d?`<span class="tag dest">${esc(a.d)}</span>`:''}
    ${a.st==='Paused'?'<span class="tag paused">Paused</span>':''}
    ${a.tagged?'':'<span class="tag untag">not tagged</span>'}</div>
   <h4>${esc(a.th)}</h4><p class="fn2">${esc(a.n)}</p></div>
   <div class="cbox ${SEL.has(a.id)?'on':''}" data-cmp="${a.id}" title="Add to comparison">✓</div></div>
  ${img(a.img,a.cid)}
  <div class="scores">
   ${sc('Pre-Click',a.pre,a.preB,meta.wPre+'%','',a.base?a.base.pre:null,a.base&&a.base.scope,a.base&&a.base.n)}
   ${sc('Post-Click',a.post,a.postB,meta.wPost+'%','',a.base?a.base.post:null,a.base&&a.base.scope,a.base&&a.base.n)}
   ${sc('Overall',a.ov,a.ovB,'',' ov',a.base?a.base.ov:null,a.base&&a.base.scope,a.base&&a.base.n)}</div>
  ${a.base?`<p class="basenote">Format medians are for <b>${a.base.scope==='cohort'?esc(a.f)+' in this group':esc(a.f)+' account-wide'}</b>${a.base.scope==='account'?' — too few in this group to read separately':''}, from ${a.base.n} creatives scored over ${esc(D.baselineLabel)}.</p>`:''}
  ${a.tagged?`<div class="attrs">
   ${a.pov?`<span class="at" title="POV — what the picture argues">${esc(a.pov)}</span>`:''}
   ${a.structure?`<span class="at" title="Structure — how the message is built">${esc(a.structure)}</span>`:''}
   ${a.sil?`<span class="at" title="Silhouette">${esc(a.sil)}</span>`:''}
   ${a.persona?`<span class="at soft" title="Persona this was written for">${esc(a.persona)}</span>`:''}
   ${a.angleTxt?`<p class="angtxt">“${esc(a.angleTxt)}”</p>`:''}
  </div>`:''}
  <div class="meta"><span class="conf ${a.conf}" title="${esc(a.confN)}"><i class="dot"></i>${esc(a.confL)}</span>
   <span>·</span><span>${a.dl} days live</span><span>·</span><span>${esc(a.camp)}</span></div>
  ${flags}
  <div><div class="tabs2"><button class="on" data-p="a">What this means</button><button data-p="m">Numbers</button></div>
   <div class="pane a on" style="margin-top:9px"><p>${esc(a.an)}</p></div>
   <div class="pane m" style="margin-top:9px"><div class="mgrid">${metricRows(a.m)}</div>
    ${a.vid?`<div class="vidbox"><h6>Video plays <i>reported, not scored</i></h6>
     <div class="vrowm"><span class="tt" title="Times the video started playing, divided by impressions. Excludes replays.">Video plays / impressions</span><b>${a.vid.rate}%</b></div>
     <div class="vbars">
      ${[['25%',a.vid.p25,a.vid.n25],['50%',a.vid.p50,a.vid.n50],['100%',a.vid.p100,a.vid.n100]].map(([l,v,n])=>
       `<div class="vb"><span>${l}</span><span class="vbar"><span style="width:${v}%"></span></span><b title="${n.toLocaleString('en-IN')} plays reached ${l}">${v}%</b></div>`).join('')}
     </div>
     <p class="vnote">${a.vid.plays.toLocaleString('en-IN')} plays from ${a.m.im.toLocaleString('en-IN')} impressions · ${a.vid.thru.toLocaleString('en-IN')} thruplays. Completion percentages are a share of plays, not impressions.</p>
    </div>`:''}
    <a class="cta" target="_blank" rel="noopener"
     href="https://adsmanager.facebook.com/adsmanager/manage/ads?act=${D.account}&selected_ad_ids=${a.id}">Open in Ads Manager ↗</a></div></div>
  ${fb}</article>`;
}

/* ---------------------------------------------------- shared blocks */
const ARCH=`<div class="arch"><h4>Archive<span class="tbd">TBD</span></h4>
 <p>Completed months collect here — August is live above; September joins once the month closes,
 then October and onward. Current-month performance is covered by the Last 7, 14 and 30 day views.</p></div>`;
const MSG=`<div class="msg">
 <p><b>Pick one group and stay in it.</b> Scores compare a creative only to others in its own
  category and audience. A 62 here and a 62 elsewhere are not the same ad.</p>
 <p><b>Read Pre-Click against Post-Click before the Overall.</b> When they disagree, that
  disagreement is the brief.</p>
 <p><b>Every number comes from the window named at the top.</b> No borrowing from longer periods.</p>
 <p><a href="#" onclick="go('howto');return false;">How to read this dashboard →</a></p></div>`;

function insBlock(items){
 return `<div class="igrid">${items.map(i=>`<div class="ins"><h5>${esc(i.t)}</h5><p>${i.b}</p>
  <p class="idet">${esc(i.d)}</p></div>`).join('')}</div>`;
}
const empty=(a,b)=>`<div class="empty"><b>${esc(a)}</b>${esc(b)}</div>`;

/* ---------------------------------------------------- views */
function viewGroups(){
 const m=win().cohorts[CK];
 if(!m) return ARCH+MSG+empty('Nothing ran in this group during '+wlabel(W)+'.',
   'The campaign may not have launched yet, or had no spend in this window. Try a wider window.');
 const inCK=a=>(m.subs&&m.subs.length?m.subs.includes(a.ck):a.ck===CK);
 const ads=filtered().filter(inCK);
 const notes=[];
 if(m.agg) notes.push(`<div class="note bench"><b>This is a combined view.</b> Each creative keeps
  the score it earned inside its own campaign group, because that is the only comparison that is
  fair. So the ranking here is a merge of several separate rankings, useful for spotting patterns
  across the category but not for declaring one creative better than another.</div>`);
 if(m.zero) notes.push(`<div class="note alarm"><b>No orders at all in this group during this
  window.</b> ROAS and purchase scores are zero for every creative here, so Overall reflects reach
  and cart behaviour only. That is usually a funding or recency issue rather than a creative
  failure — check spend and days live before concluding anything.</div>`);
 if(m.n>m.ranked) notes.push(`<div class="note warn">${m.n-m.ranked} of ${m.n} creatives sit below
  this group's ${R(m.floor)} spend floor. They are shown and scored, but carry no rank position and
  do not set the benchmark others are measured against.</div>`);
 if(m.cat_roas) notes.push(`<div class="note bench">Dynamic catalogue benchmark:
  <b>${m.cat_roas}x</b> on ${R(m.cat_spend)}. <b>${m.beat} of ${m.n}</b> creatives here beat it.</div>`);
 const strip=m.fstrip.map(f=>`<div class="fs"><div class="fn">${esc(f.f)}</div>
   <div class="fm">${f.n} live · ${R(f.sp)}</div>
   <div class="fb"><span>Pre ${f.pre||'—'}</span><span class="bar2"><span style="width:${f.pre}%;background:var(--slate)"></span></span></div>
   <div class="fb"><span>Post ${f.post||'—'}</span><span class="bar2"><span style="width:${f.post}%;background:var(--amber)"></span></span></div></div>`).join('');
 return ARCH+MSG+`<div class="chead"><div class="ctitle"><h3>${esc(m.cat)}</h3>
   <span class="stg${m.agg?' agg':''}">${esc(m.agg?'COMBINED':m.funnel)}</span><span class="role">${esc(m.role)}</span></div>
   <p class="cstats">${m.n} creatives<i>·</i>${m.ranked} ranked<i>·</i>${R(m.spend)}<i>·</i>
    ${m.atc.toLocaleString('en-IN')} carts<i>·</i>${m.pur.toLocaleString('en-IN')} orders<i>·</i>
    ${m.agg?'mixed weighting':m.wPre+'/'+m.wPost+' pre/post weighting'}<i>·</i>attribution ${esc(m.attribution)}</p>
   <div class="notes">${notes.join('')}</div></div>
  <div class="brief"><h5>What changed in this group</h5><ul>${m.brief.map(b=>`<li>${b}</li>`).join('')}</ul></div>
  <div class="fstrip">${strip}</div>
  ${ads.length?`<div class="grid">${ads.map(card).join('')}</div>`
    :empty('No creatives match those filters in this group.','Clear a filter or widen the window.')}
  ${(m.insB&&m.insB.length)?`<div class="secins"><h4>For the brand team</h4>
   <p class="ssub">Design-first read of ${esc(m.cat)} ${esc(m.role)} — what the work looks like
    and what to make next. Computed from this group only.</p>${insBlock(m.insB)}</div>`:''}
  ${(m.insG&&m.insG.length)?`<div class="secins"><h4>For growth</h4>
   <p class="ssub">Performance read of the same group — efficiency, spend distribution and
    structure.</p>${insBlock(m.insG)}</div>`:''}`;
}

function viewCollections(){
 const cm=win().cohorts[CK];
 const inCK=a=>(cm&&cm.subs&&cm.subs.length?cm.subs.includes(a.ck):a.ck===CK);
 const ads=filtered().filter(inCK);
 const by={}; ads.forEach(a=>{const k=a.col!=='Other'?a.col:a.pt;(by[k]=by[k]||[]).push(a);});
 const rows=Object.entries(by).map(([k,v])=>({k,v:v.sort((x,y)=>y.ov-x.ov),
   sp:v.reduce((s,a)=>s+a.m.sp,0),pur:v.reduce((s,a)=>s+a.m.pur,0),
   rev:v.reduce((s,a)=>s+a.m.rev,0),
   sc:Math.round(v.reduce((s,a)=>s+a.ov,0)/v.length)})).sort((a,b)=>b.sp-a.sp);
 if(!rows.length) return ARCH+empty('Nothing to group by collection here.','Widen the window or clear the filters.');
 const best=rows[0], worst=rows[rows.length-1];
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Collections</h3>
   <span class="role">${esc(CK.replace(' | ',' — '))}</span></div>
  <p class="cstats">The same creatives grouped the way the brand team thinks — by collection and
   product rather than by ad. Within each collection, versions of the same concept sit together so
   the gap between executions is visible.</p></div>
  ${rows.length>1?`<div class="brief"><h5>Across collections here</h5><ul>
   <li><b>${esc(best.k)}</b> carries the most spend (${R(best.sp)}, ${best.v.length} creatives,
    average score ${best.sc}).</li>
   <li>Strongest average is <b>${esc(rows.slice().sort((a,b)=>b.sc-a.sc)[0].k)}</b>, weakest is
    <b>${esc(rows.slice().sort((a,b)=>a.sc-b.sc)[0].k)}</b>. A collection performing badly across
    several creatives is usually a product signal, not a creative one.</li></ul></div>`:''}
  ${rows.map(r=>{
   const fam={}; r.v.forEach(a=>{(fam[a.vk]=fam[a.vk]||[]).push(a);});
   const multi=Object.values(fam).filter(v=>v.length>1);
   let note='';
   if(multi.length){
    const g=multi.map(v=>({v,gap:Math.round(v[0].ov-v[v.length-1].ov)})).sort((a,b)=>b.gap-a.gap)[0];
    note=`<div class="verdict" style="margin-bottom:12px">${g.gap>=20
     ?`<b>${g.gap} points</b> separate the best and worst version of <i>${esc(g.v[0].th)}</i> in
       this collection. Same product, same audience — the gap is execution, and it is the cheapest
       lesson available because the shoot already happened.`
     :`Versions of <i>${esc(g.v[0].th)}</i> land within <b>${g.gap} points</b> of each other, so
       this concept performs consistently however it is cut.`}</div>`;
   }
   return `<div class="concept"><h4>${esc(r.k)}</h4>
    <p class="csub">${r.v.length} creatives · ${R(r.sp)} · ${r.pur} orders ·
     ${r.pur?R(r.rev/r.pur)+' average order':'no orders yet'} · average score ${r.sc}</p>
    ${note}<div class="grid">${r.v.map(card).join('')}</div></div>`;}).join('')}`;
}

function viewConceptsOld(){
 const ads=filtered().filter(a=>a.ck===CK);
 const fam={}; ads.forEach(a=>{(fam[a.vk]=fam[a.vk]||[]).push(a);});
 const multi=Object.entries(fam).filter(([,v])=>v.length>1)
   .map(([k,v])=>v.sort((x,y)=>y.ov-x.ov))
   .sort((a,b)=>(b[0].ov-b.at(-1).ov)-(a[0].ov-a.at(-1).ov));
 const single=Object.values(fam).filter(v=>v.length===1).map(v=>v[0]).sort((x,y)=>y.ov-x.ov);
 const vlabel=a=>{const m=a.n.match(/\b(V\d)\b/i); if(m) return 'Version '+m[1].toUpperCase();
   const stop=/^(PDP|PLP|COPY|SNG|GIF|VIDEO|CAROUSEL|A\d\d|\d+)$/i;
   return a.n.split(/[-\s]+/).filter(x=>x&&!stop.test(x)).slice(-2).join(' ')||a.f;};
 const blocks=multi.map(v=>{
  const best=v[0],worst=v.at(-1),gap=Math.round(best.ov-worst.ov);
  const cells=v.map((a,i)=>`<div class="vcell ${i===0?'best':''}">
    ${img(a.img,a.cid).replace('class="thumb ','class="vthumb ').replace('<span>preview not added yet</span>','')}
    <div class="vn">${esc(vlabel(a))}</div>
    <div class="vv" style="color:var(--${cls(a.ovB)})">${a.ov}</div>
    <div class="vm">${esc(a.f)}${a.d?' · '+esc(a.d):''} · ${R(a.m.sp)} · ${a.m.pur} orders</div></div>`).join('');
  const sameF=v.every(a=>a.f===v[0].f), sameD=v.every(a=>a.d===v[0].d);
  let verdict;
  if(gap>=20) verdict=`<b>${gap} points</b> separate the best and worst version of this idea.
   ${sameF?'Same format':'Different formats'}${sameD&&v[0].d?`, same ${esc(v[0].d)} destination`:''},
   same product — the gap is execution, not strategy. Whatever <b>${esc(vlabel(best))}</b> does
   differently is the cheapest win available this week, because the shoot already happened.`;
  else if(gap>=8) verdict=`A <b>${gap}-point</b> spread. Real but not dramatic — look at the winner
   before the next round rather than reshooting.`;
  else verdict=`Versions score within <b>${gap} points</b> of each other. This concept performs
   consistently however it is executed, which usually means the product is doing the work.`;
  return `<div class="concept"><h4>${esc(best.th)}</h4>
   <p class="csub">${v.length} versions · ${esc(best.c)} · ${esc(best.r)}</p>
   <div class="vrow">${cells}</div><div class="verdict">${verdict}</div></div>`;
 }).join('');
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Concepts</h3>
   <span class="role">${esc(CK.replace(' | ',' — '))}</span></div>
  <p class="cstats">One card per idea. Where a concept was shot more than once, the versions sit
   side by side so the gap between them is visible — that gap is execution, and it is the most
   directly usable number here.</p></div>
  ${blocks||empty('No concept in this group has more than one version.','Everything here was shot once, so there is nothing to compare against itself.')}
  ${single.length?`<div class="chead" style="margin-top:28px"><div class="ctitle"><h3>Shot once</h3>
   <span class="role">${single.length} concepts with no sibling</span></div></div>
   <div class="grid">${single.map(card).join('')}</div>`:''}`;
}

function viewWinners(){
 const out=[];
 Object.keys(win().cohorts).forEach(ck=>{
  const g=filtered().filter(a=>a.ck===ck&&a.ranked);
  out.push(...g.slice(0,Math.max(1,Math.ceil(g.length/3))));
 });
 out.sort((x,y)=>y.ov-x.ov);
 if(!out.length) return ARCH+empty('Nothing clears the bar in this window.','Try a wider window or clear the filters.');
 return ARCH+`<div class="chead"><div class="ctitle"><h3>Winners</h3>
   <span class="role">top third of every group · ${out.length} creatives</span></div>
  <p class="cstats">No diagnosis, no group filtering — everything currently outperforming its peers,
   in one place. Use it for inspiration rather than analysis. These are top third <i>within their own
   group</i>, so a Jewellery winner and a Womenswear winner are not the same absolute standard.</p></div>
  <div class="grid">${out.map(card).join('')}</div>`;
}

function viewBrand(){
 const d=win();
 return `<div class="insh"><h3>Insights for the brand team</h3>
  <p class="isub">Category and funnel-stage patterns across everything running in ${wlabel(W).toLowerCase()}.
   Written for someone commissioning creative: what is working visually and thematically, which
   collections carry their weight, and what to brief next.</p>
  ${insBlock(d.brand)}
  ${!d.totals.tagged?`<div class="caveat"><p><b>The attribute layer is not connected yet.</b>
   None of the ${d.totals.n} creatives in this window are matched to the Ad Nomenclature sheet, so
   angle, silhouette and VO/AI analysis is absent. Those are the fields that explain <i>why</i>
   something worked rather than just that it did — once the sheet is joined, this section starts
   answering craft questions instead of format questions.</p></div>`:''}</div>`;
}
function viewGrowth(){
 return `<div class="insh"><h3>Insights for growth</h3>
  <p class="isub">Campaign structure, budget distribution, attribution effects and testing
   throughput for ${wlabel(W).toLowerCase()}. Written for someone running the account rather than
   commissioning the work.</p>${insBlock(win().growth)}</div>`;
}

function viewPatterns(){
 const p=win().patterns||[];
 const t=win().totals;
 return `<div class="insh"><h3>Summary and patterns</h3>
  <p class="isub">What is repeating across groups, windows and variables in
   ${wlabel(W).toLowerCase()}. A single group preferring something is noise; several arriving at it
   separately is worth knowing.</p>
  <div class="brief" style="margin-bottom:22px"><h5>Where things stand</h5><ul>
   <li><b>${t.n} creatives</b> carried spend — ${t.active} active, ${t.n-t.active} paused.
    <b>${t.ranked}</b> cleared their spend floor and are ranked.</li>
   <li><b>${R(t.sp)}</b> produced ${t.pur.toLocaleString('en-IN')} orders worth ${R(t.rev)},
    from ${t.atc.toLocaleString('en-IN')} carts.</li>
   <li><b>${t.tagged} of ${t.n}</b> creatives are matched to the nomenclature sheet, which is what
    the angle and silhouette patterns below rest on.</li></ul></div>
  ${p.length?insBlock(p):empty('Not enough repetition to call a pattern yet.','Patterns need several groups behaving the same way. Try a wider window.')}</div>`;
}

function viewDupes(){
 const dups=(win().dups||[]).filter(d=>{
  if(!Q) return true; const q=Q.toLowerCase();
  return (d.th+' '+d.camps.join(' ')+' '+d.f).toLowerCase().includes(q);});
 if(!dups.length) return ARCH+empty('No creative is running in more than one campaign right now.',
   'This view only lists assets that appear in two or more campaigns during this window.');
 const tot=dups.reduce((s,d)=>s+d.spend,0);
 const legs=dups.reduce((s,d)=>s+d.n,0);
 return `<div class="insh"><h3>Duplication</h3>
  <p class="isub">Where the same asset is running in more than one campaign, and what it has done
   in total. Meta scores each placement separately because each sits in a different audience — this
   view adds them back together so you can see the creative rather than the ad.</p>
  <div class="brief" style="margin-bottom:22px"><h5>What this covers</h5><ul>
   <li><b>${dups.length} creatives</b> are running in more than one campaign, across
    <b>${legs} placements</b> in total.</li>
   <li>They account for <b>${R(tot)}</b> of spend in ${wlabel(W).toLowerCase()}.</li>
   <li>Combined figures are a plain sum of what each placement reported. Where the campaigns use
    different attribution windows, that difference is carried through untouched and named on each
    block — nothing has been reconciled or adjusted.</li></ul></div>
  ${dups.map(d=>{
   const mixed=d.attributions.length>1;
   const best=d.legs.reduce((a,b)=>a.ov>b.ov?a:b);
   const worst=d.legs.reduce((a,b)=>a.ov<b.ov?a:b);
   const gap=best.ov-worst.ov;
   return `<div class="concept dupe">
    <div class="duphead">
     ${img(d.img,d.cid,'dupimg')}
     <div>
      <h4>${esc(d.th)}</h4>
      <p class="csub">${esc(d.f)} · running in ${d.camps.length} campaigns · ${d.n} placements</p>
      <div class="dupstats">
       <div><span>Combined spend</span><b>${R(d.spend)}</b></div>
       <div><span>Impressions</span><b>${d.imps.toLocaleString('en-IN')}</b></div>
       <div><span>Carts</span><b>${d.atc.toLocaleString('en-IN')}</b></div>
       <div><span>Orders</span><b>${d.pur.toLocaleString('en-IN')}</b></div>
       <div><span>Revenue</span><b>${R(d.rev)}</b></div>
       <div><span>Blended ROAS</span><b>${d.roas}x</b></div>
       <div><span>CPM</span><b>${R(d.cpm)}</b></div>
       <div><span>Page to cart</span><b>${d.l2a}%</b></div>
      </div>
     </div>
    </div>
    ${mixed?`<div class="note warn" style="margin:10px 0">These placements run
     <b>different attribution windows</b> (${d.attributions.map(esc).join(' and ')}). The combined
     ROAS above simply adds them together, so part of it counts view-through purchases and part
     does not. Shown as-is rather than reconciled — read it as an order of magnitude.</div>`:''}
    <table class="duptable"><thead><tr>
     <th>Campaign</th><th>Group</th><th>Spend</th><th>Orders</th><th>ROAS</th>
     <th>Pre</th><th>Post</th><th>Overall</th><th>Status</th></tr></thead><tbody>
     ${d.legs.map(l=>`<tr>
      <td><b>${esc(l.camp)}</b></td><td class="mut">${esc(l.ck.replace(' | ',' — '))}</td>
      <td>${R(l.sp)}</td><td>${l.pur}</td><td>${l.roas?l.roas+'x':'—'}</td>
      <td>${l.pre}</td><td>${l.post}</td><td><b>${l.ov}</b></td>
      <td class="mut">${l.ranked?esc(l.st):'unranked'}</td></tr>`).join('')}
     </tbody></table>
    <div class="verdict" style="margin-top:11px">${gap>=15
     ?`The same asset scores <b>${best.ov} in ${esc(best.camp)}</b> and <b>${worst.ov} in
       ${esc(worst.camp)}</b> — a ${gap}-point spread on identical creative. Nothing about the
       picture changed, so the difference is audience and competition, not the work. Useful as a
       reminder that a low score in one group is not a verdict on the asset.`
     :`It performs consistently across all ${d.n} placements (${worst.ov} to ${best.ov}), which
       suggests the creative rather than the audience is driving the result.`}</div>
   </div>`;}).join('')}</div>`;
}

function viewHowto(){
 const w=D.weights, f=D.floors;
 const rowsP=w.pre.map(([m,x])=>`<tr><td>${({cpm:'CPM (lower is better)',octr:'Outbound CTR',clk2lpv:'Click → landing page'})[m]}</td><td>${x}</td></tr>`).join('');
 const rowsQ=w.post.map(([m,x])=>`<tr><td>${({roas:'ROAS',cpatc:'Cost per add-to-cart (lower is better)',pur:'Purchases',lpv2atc:'Landing page → cart'})[m]}</td><td>${x}</td></tr>`).join('');
 return `<div class="howto"><h2>How to read this dashboard</h2>
 <p>Everything explanatory lives here so the working views stay clean. Nothing below changes week
 to week; the numbers in the other tabs do.</p>

 <h3>What the three scores mean</h3>
 <p><b>Pre-Click</b> is how well a creative earns attention — how cheaply it reaches people, how
 many click, and how many of those clicks actually land on the page.</p>
 <p><b>Post-Click</b> is what happens after: carts, cost per cart, orders and return on spend.</p>
 <p><b>Overall</b> combines the two. The useful part is usually the <i>gap</i> between them. High
 attention with low conversion means the picture promised something the page did not keep. Low
 attention with high conversion means a good idea nobody is seeing. Those need different fixes.</p>

 <h3>The scale</h3>
 <p><b>50 is the middle of the group.</b> Each metric is compared to the median creative in the
 same category and audience, then mapped so the median scores 50 and twice-median scores 100.
 Nothing here is an absolute grade — it is always relative to what runs alongside it.</p>
 <div class="bands">
  <span class="bd" style="color:var(--strong)">Strong 65+</span>
  <span class="bd" style="color:var(--above)">Above par 55–64</span>
  <span class="bd" style="color:var(--par)">At par 45–54</span>
  <span class="bd" style="color:var(--below)">Below par 35–44</span>
  <span class="bd" style="color:var(--weak)">Weak under 35</span>
  <span class="bd" style="border-color:var(--amber);background:#fffdf6">Amber rank = top third</span></div>
 <p>Scores between 52–58 and 42–48 are marked <b>too close to call</b>. The difference between 53
 and 47 is not reliably a difference in quality.</p>

 <h3>Exact weights</h3>
 <p>Same metrics, same weights, every group. Only the split between the two halves changes.</p>
 <table><thead><tr><th>Pre-Click metric</th><th>Weight</th></tr></thead><tbody>${rowsP}</tbody></table>
 <table><thead><tr><th>Post-Click metric</th><th>Weight</th></tr></thead><tbody>${rowsQ}</tbody></table>
 <table><thead><tr><th>Group type</th><th>Pre-Click</th><th>Post-Click</th></tr></thead><tbody>
  <tr><td>Prospecting — Testing</td><td>40%</td><td>60%</td></tr>
  <tr><td>Scaling · Engaged · Existing</td><td>20%</td><td>80%</td></tr></tbody></table>
 <p>CPC and cost per landing page view are shown but never scored — both are arithmetic products of
 metrics already counted, so scoring them would count the same signal twice.</p>

 <h3>Spend floors and what "unranked" means</h3>
 <p>An ad must clear a spend floor before it gets a rank position. Below the floor it still appears
 and still scores — it just carries no position, and it does not help set the benchmark others are
 measured against.</p>
 <table><thead><tr><th>Group</th><th>Floor</th></tr></thead><tbody>
  ${Object.entries(f).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${R(v)}</td></tr>`).join('')}</tbody></table>

 <h3>Zeros are real</h3>
 <p>An ad that sold nothing scores zero on ROAS and purchases. It is not hidden or marked
 unavailable, and the weight is not moved elsewhere — so Overall falls, which is the honest reading.
 If a whole group sold nothing, every creative in it scores zero on that half and the group header
 says so plainly.</p>
 <p>The reverse is flagged too: a strong sales score built on a handful of orders carries a warning
 on the card, because one order either way would move it substantially.</p>

 <h3>Format median — the second number on each score</h3>
 <p>Under each score you will see something like <b>fmt 46 +7</b>. That is the median score for
 this creative's format <b>inside this same category and audience group</b>, measured across
 <b>${esc(D.baselineLabel)}</b>, and how far this creative sits from it.</p>
 <p>It answers a question the ranking alone cannot: is a Video-Partnership ad weak, or is it simply
 a Video-Partnership ad? Formats have different natural ceilings, and those ceilings differ by
 category and audience — a Carousel in Existing Customers is not the same proposition as a Carousel
 in cold prospecting. So the median is cohort-specific rather than one house-wide figure.</p>
 <p>Where a group has fewer than three creatives of that format, there is nothing reliable to
 compare against, so the account-wide median for the format is shown instead and marked with an
 <b>asterisk</b>. The note under each card always states which one you are looking at and how many
 creatives it rests on.</p>
 <p><b>These medians recompute on every refresh.</b> As the baseline window grows past
 ${esc(D.baselineLabel)}, the reference moves with it. The window start stays 1 August unless that
 is deliberately changed.</p>

 <h3>Video plays</h3>
 <p>Video and Video-Partnership creatives show a play rate and completion curve in the Numbers tab.
 <b>None of it is scored</b> — it is there for the brand team to read alongside the score, never to
 change it.</p>
 <p><b>Video plays / impressions</b> is the share of people shown the ad who started watching it.
 Plays exclude replays. The <b>25 / 50 / 100</b> bars are the share of those plays that reached each
 point, so they measure holding power once someone has started, not reach.</p>
 <p>Read the two together. A high play rate with a low 50% figure means the opening frame is pulling
 people in and the middle is losing them. A low play rate with a high 100% figure means few people
 start but the ones who do watch it through — usually a thumbnail or first-frame problem rather than
 an edit problem.</p>

 <h3>Creative attributes</h3>
 <p>Tagged creatives show their <b>POV</b> (what the picture argues), <b>Structure</b> (how the
 message is built — Feel-seen, Desire, Proof, Curiosity, Social proof), <b>Silhouette</b>, and the
 <b>persona</b> it was written for, with the one-line audience insight underneath. These come from
 the Ad Nomenclature sheet and are the only fields in this dashboard that describe the work rather
 than its results.</p>

 <h3>Combined views</h3>
 <p>Menu entries marked ▸ (<b>Prospecting (All)</b>, <b>All audiences</b>) merge several groups
 into one screen. Every creative keeps the score it earned inside its own group, because that is
 the only fair comparison. So a combined ranking is a merge of separate rankings — good for
 spotting patterns across a category, not for declaring one creative better than another.</p>

 <h3>Duplication</h3>
 <p>Where one asset runs in several campaigns, Meta reports it separately in each. The Duplication
 tab adds those placements back together so you can see the creative rather than the ad. Combined
 figures are a plain sum of what each placement reported — where campaigns use different
 attribution windows, that is named on the block and left unreconciled.</p>

 <h3>Confidence</h3>
 <p><b>Solid</b> — 20+ orders, 14+ days, 50,000+ impressions. Act on it.<br>
 <b>Moderate</b> — 5+ orders over a week. Directional.<br>
 <b>Thin</b> — below that. An early signal, not a verdict.</p>

 <h3>Fatigue</h3>
 <p>There is no separate fatigue view. Decline shows up on the card, measured against the same ad's
 own earlier performance — the 7-day view compares to the 7 days before it, the 14-day view to the
 fortnight before. The card names which half fell: losing attention (clicks down, or cost to serve
 up) is the creative wearing out and no change after the click fixes it. Holding attention but
 converting worse means something after the click changed.</p>

 <h3>Why groups never mix</h3>
 <p>A House &amp; Home ad and a Womenswear ad do not compete for the same impression and do not
 carry the same order value, so their numbers are not comparable. Legacy and current scaling
 campaigns are also kept apart: NB-008, NB-009, NB-010 and FE-104 still count 7-day click plus
 1-day view, while NB-012, NB-014 and NB-016 count 7-day click only. Comparing ROAS across those
 would credit the older campaigns for purchases the newer ones simply do not count.</p>

 <h3>The catalogue benchmark</h3>
 <p>Dynamic catalogue ads are never scored — there is no creative to brief. They appear as a
 benchmark line instead, with a count of how many hand-made creatives beat them. Catalogue costs
 nothing to produce, so anything below it is effort better spent elsewhere.</p>

 <h3>What this dashboard cannot tell you</h3>
 <div class="caveat">
  <p><b>Creative quality and audience quality are tangled together.</b> Meta sends impressions
  toward people likely to convert, so a well-funded creative gets a better audience and a better
  ROAS partly for reasons the creative team did not control. ROAS and purchases carry most of the
  Overall score in scaling groups, so a card can read Weak for something that was not the work's
  fault. Read the Pre-Click score when you want the cleanest signal about the creative itself.</p>
  <p><b>Product demand is confounded with creative quality.</b> A good creative for a slow-selling
  product will score badly. Read these alongside what you already know about the range.</p>
  <p><b>Nothing here is causal.</b> These are observed patterns, not experiments.</p>
  <p><b>It will not tell you where to move budget.</b> That is a media decision and it lives
  elsewhere. This exists so the next thing you brief is better than the last thing you shipped.</p>
 </div></div>`;
}

/* ---------------------------------------------------- compare */
function compare(){
 const [a,b]=[...SEL].map(id=>win().ads.find(x=>x.id===id)).filter(Boolean);
 if(!a||!b) return;
 const rows=[['Group',a.ck,b.ck,null],['Funnel',a.fn,b.fn,null],['Format',a.f,b.f,null],
  ['Destination',a.d||'—',b.d||'—',null],['Days live',a.dl,b.dl,null],
  ['Pre-Click',a.pre,b.pre,'hi'],['Post-Click',a.post,b.post,'hi'],['Overall',a.ov,b.ov,'hi'],
  ['Spend',R(a.m.sp),R(b.m.sp),null],['CPM',R(a.m.cpm),R(b.m.cpm),'lo'],
  ['Outbound CTR',a.m.ctr+'%',b.m.ctr+'%','hi'],['Click to page',a.m.c2l+'%',b.m.c2l+'%','hi'],
  ['Page to cart',a.m.l2a+'%',b.m.l2a+'%','hi'],['Cost per cart',R(a.m.cpa),R(b.m.cpa),'lo'],
  ['Purchases',a.m.pur,b.m.pur,'hi'],['ROAS',a.m.roas??'—',b.m.roas??'—','hi'],
  ['AOV',R(a.m.aov),R(b.m.aov),'hi']];
 const num=v=>parseFloat(String(v).replace(/[^\d.-]/g,''));
 const body=rows.map(([l,x,y,dir])=>{let cx='',cy='';
  if(dir&&!isNaN(num(x))&&!isNaN(num(y))&&num(x)!==num(y)){
   ((dir==='hi')?(num(x)>num(y)):(num(x)<num(y)))?cx='win2':cy='win2';}
  return `<div class="lbl">${esc(l)}</div><div class="${cx}">${esc(x)}</div><div class="${cy}">${esc(y)}</div>`;}).join('');
 document.getElementById('mbox').innerHTML=`
  <button class="closeb" onclick="document.getElementById('modal').classList.remove('on')">Close</button>
  <h3>Side by side</h3>
  <p style="font-size:12.5px;color:var(--slate);margin:0 0 18px">A learning view, not a scoring one.
   These may sit in different groups where scores are not strictly comparable — use it to understand
   <i>why</i> something works, not to decide which is better.</p>
  <div class="cmpimgs"><div></div>${img(a.img,a.cid)}${img(b.img,b.cid)}</div>
  <div class="cmp"><div class="hd"></div><div class="hd">${esc(a.th)}</div><div class="hd">${esc(b.th)}</div>${body}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px">
   <div><p style="margin:0;font-size:13px;color:var(--dim);line-height:1.7">${esc(a.an)}</p></div>
   <div><p style="margin:0;font-size:13px;color:var(--dim);line-height:1.7">${esc(b.an)}</p></div></div>`;
 document.getElementById('modal').classList.add('on');
}

/* ---------------------------------------------------- chrome */
function go(v){V=v;document.querySelectorAll('#vtabs button').forEach(x=>x.classList.toggle('on',x.dataset.v===v));render();window.scrollTo({top:0,behavior:'smooth'});}
function render(){
 if(document.body.classList.contains('meeting')){
  document.getElementById('app').innerHTML=meetingView();
  return;
 }
 const needsCk=(V==='groups'||V==='collections');
 document.getElementById('cksel').style.display=needsCk?'':'none';
 document.getElementById('fbtn').style.display=(V==='howto')?'none':'';
 document.getElementById('app').innerHTML=
  ({groups:viewGroups,collections:viewCollections,winners:viewWinners,patterns:viewPatterns,
    dupes:viewDupes,brand:viewBrand,growth:viewGrowth,howto:viewHowto})[V]();
 renderFilters();
 const t=win().totals;
 document.getElementById('foot').innerHTML=
  `${t.n} creatives with spend in ${wlabel(W).toLowerCase()} · ${t.ranked} ranked · `+
  `${R(t.sp)} · ${t.pur.toLocaleString('en-IN')} orders · ${t.tagged} matched to the nomenclature sheet. `+
  `Catalogue ads are excluded from scoring and shown as a benchmark only. `+
  `Scores are relative within a group and never across groups.`;
 const tr=document.getElementById('tray');
 tr.classList.toggle('on',SEL.size>0);
 document.getElementById('trayitems').textContent=SEL.size===1?'1 selected — pick one more':SEL.size+' selected';
 document.getElementById('cmpgo').style.opacity=SEL.size===2?1:.45;
}
D.windows.forEach(w=>{const b=document.createElement('button');b.dataset.w=w.k;
 b.innerHTML=`<b>${w.label}</b><i>${w.dates}</i>`;if(w.k===W)b.className='on';
 b.onclick=()=>{W=w.k;document.querySelectorAll('#wtabs button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');render();window.scrollTo({top:0,behavior:'smooth'});};
 document.getElementById('wtabs').appendChild(b);});
const sel=document.getElementById('cksel');
(function(){
 const byCat={};
 D.cohortOrder.forEach(ck=>{const c=ck.split(' | ')[0];(byCat[c]=byCat[c]||[]).push(ck);});
 sel.innerHTML=Object.entries(byCat).map(([c,list])=>
  `<optgroup label="${esc(c)}">`+list.map(ck=>{
   const r=ck.split(' | ')[1];
   const isAgg=(r==='Prospecting (All)'||r==='All audiences');
   return `<option value="${esc(ck)}">${isAgg?'▸ ':''}${esc(r)}</option>`;}).join('')+'</optgroup>').join('');
})();
sel.value=CK; sel.onchange=()=>{CK=sel.value;render();window.scrollTo({top:0,behavior:'smooth'});};
document.getElementById('vtabs').onclick=e=>{const b=e.target.closest('[data-v]');if(b)go(b.dataset.v);};
document.getElementById('fbtn').onclick=function(){SHOWF=!SHOWF;
 document.getElementById('filters').classList.toggle('on',SHOWF);this.classList.toggle('on',SHOWF);};
document.getElementById('frows').onclick=e=>{const b=e.target.closest('[data-fk]');if(!b)return;
 if(b.dataset.fk==='sort') SORT=b.dataset.fv; else F[b.dataset.fk]=b.dataset.fv;
 render();};
let qt;document.getElementById('q').oninput=e=>{clearTimeout(qt);qt=setTimeout(()=>{Q=e.target.value.trim();render();},220);};
function meetingView(){
 const m=win().cohorts[CK];
 if(!m) return empty('Pick a group first.','Meeting mode condenses whichever group is in focus.');
 const inCK=a=>(m.subs&&m.subs.length?m.subs.includes(a.ck):a.ck===CK);
 const ads=filtered().filter(inCK).sort((x,y)=>y.ov-x.ov);
 if(!ads.length) return empty('Nothing running in this group.','Try another group or window.');
 const t=(f)=>ads.reduce((s,a)=>s+(f(a)||0),0);
 const spend=t(a=>a.m.sp), pur=t(a=>a.m.pur), rev=t(a=>a.m.rev), atc=t(a=>a.m.atc);
 const top=ads.slice(0,3), bottom=ads.slice(-3).reverse();
 const declining=ads.filter(a=>a.dec);
 const lopsided=ads.filter(a=>Math.abs(a.post-a.pre)>=20);
 const thin=ads.filter(a=>!a.ranked);
 const acts=[];
 if(top.length) acts.push(`<b>Make more like ${esc(top[0].th)}</b> — top of this group at
  ${top[0].ov}${top[0].base?`, ${top[0].ov-top[0].base.ov>0?'+':''}${top[0].ov-top[0].base.ov} against the ${esc(top[0].f)} norm`:''}.`);
 if(declining.length) acts.push(`<b>${declining.length} creative${declining.length>1?'s are':' is'} declining</b>
  against ${esc(declining[0].decP||'the prior period')} — ${declining.slice(0,2).map(a=>esc(a.th)).join(', ')}${declining.length>2?' and others':''}.
  ${declining.filter(a=>a.dec.pre_down).length?'Mostly losing attention, which is wear.':'Mostly converting worse, which sits after the click.'}`);
 if(lopsided.length) acts.push(`<b>${lopsided.length} ${lopsided.length>1?'are':'is'} lopsided</b> — 20+ points apart on
  attention versus conversion. Half of each already works, so these are the cheapest to fix.`);
 if(thin.length) acts.push(`<b>${thin.length} of ${ads.length} sit below the ${R(m.floor)} floor</b>
  and carry no rank. Either fund fewer creatives properly or accept these stay unreadable.`);
 if(bottom.length && bottom[0].ov<40) acts.push(`<b>Stop iterating on ${esc(bottom[0].th)}</b> —
  bottom of the group at ${bottom[0].ov}. The concept is not the problem worth solving here.`);
 const line=(a)=>`<tr><td><b>${esc(a.th)}</b><span class="mut"> ${esc(a.f)}${a.pov?' · '+esc(a.pov):''}</span></td>
  <td>${R(a.m.sp)}</td><td>${a.m.pur}</td><td>${a.m.roas?a.m.roas+'x':'—'}</td>
  <td>${a.pre}</td><td>${a.post}</td><td class="big ${cls(a.ovB)}">${a.ov}</td></tr>`;
 return `<div class="meet">
  <div class="mhead"><h2>${esc(m.cat)} <span>${esc(m.role)}</span></h2>
   <p>${wlabel(W)} · ${esc(D.windows.find(x=>x.k===W).dates)}</p></div>
  <div class="bigrow">
   <div><span>Spend</span><b>${R(spend)}</b></div>
   <div><span>Orders</span><b>${pur.toLocaleString('en-IN')}</b></div>
   <div><span>Revenue</span><b>${R(rev)}</b></div>
   <div><span>Blended ROAS</span><b>${spend?(rev/spend).toFixed(2):'0.00'}x</b></div>
   <div><span>Carts</span><b>${atc.toLocaleString('en-IN')}</b></div>
   <div><span>Creatives</span><b>${ads.length}</b></div>
  </div>
  <div class="mcols">
   <div><h3>Working</h3><table class="mtab"><thead><tr><th>Creative</th><th>Spend</th><th>Orders</th>
    <th>ROAS</th><th>Pre</th><th>Post</th><th>Ov</th></tr></thead>
    <tbody>${top.map(line).join('')}</tbody></table></div>
   <div><h3>Not working</h3><table class="mtab"><thead><tr><th>Creative</th><th>Spend</th><th>Orders</th>
    <th>ROAS</th><th>Pre</th><th>Post</th><th>Ov</th></tr></thead>
    <tbody>${bottom.map(line).join('')}</tbody></table></div>
  </div>
  <div class="acts"><h3>What to do</h3><ol>${acts.map(a=>`<li>${a}</li>`).join('')}</ol></div>
  <p class="mfoot">Scores are relative to this group only. ${m.agg?'This is a combined view of several groups, each scored separately.':''}
   ${win().totals.tagged} of ${win().totals.n} creatives account-wide carry creative attributes.</p>
 </div>`;
}

function setMeeting(on){document.body.classList.toggle('meeting',on);
 const b=document.getElementById('meetb');b.classList.toggle('on',on);
 b.textContent=on?'Exit meeting mode':'Meeting mode';if(!on)window.scrollTo({top:0,behavior:'smooth'});}
document.getElementById('meetb').onclick=()=>setMeeting(!document.body.classList.contains('meeting'));
document.getElementById('exitm').onclick=()=>setMeeting(false);
document.addEventListener('keydown',e=>{if(e.key!=='Escape')return;
 const m=document.getElementById('modal');
 if(m.classList.contains('on'))m.classList.remove('on');
 else if(document.body.classList.contains('meeting'))setMeeting(false);});
document.addEventListener('click',e=>{
 const c=e.target.closest('[data-cmp]');
 if(c){const id=c.dataset.cmp;
  if(SEL.has(id))SEL.delete(id);else{if(SEL.size>=2)SEL.delete([...SEL][0]);SEL.add(id);}
  render();return;}
 const p=e.target.closest('.tabs2 button');
 if(p){const card=p.closest('.card');
  card.querySelectorAll('.tabs2 button').forEach(x=>x.classList.remove('on'));p.classList.add('on');
  card.querySelectorAll('.pane').forEach(x=>x.classList.remove('on'));
  card.querySelector('.pane.'+p.dataset.p).classList.add('on');}});
document.getElementById('cmpgo').onclick=compare;
document.getElementById('cmpclr').onclick=()=>{SEL.clear();render();};
document.getElementById('modal').onclick=e=>{if(e.target.id==='modal')e.target.classList.remove('on');};
document.getElementById('pulled').textContent=D.pulled;
document.getElementById('acct').textContent=D.account;
render();
