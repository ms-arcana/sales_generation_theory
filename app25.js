(function(){
var slides=[].slice.call(document.querySelectorAll('.slide'));
var dots=document.getElementById('dots'),counter=document.getElementById('counter'),idx=0;
slides.forEach(function(s,i){var b=document.createElement('button');b.type='button';
  b.setAttribute('aria-label',(i+1)+'枚目へ');b.addEventListener('click',function(){go(i);});dots.appendChild(b);});
function go(n){idx=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach(function(s,i){s.classList.toggle('is-active',i===idx);});
  [].forEach.call(dots.children,function(d,i){d.setAttribute('aria-current',i===idx?'true':'false');});
  counter.textContent=String(idx+1).padStart(2,'0')+' / '+String(slides.length).padStart(2,'0');
  window.scrollTo(0,0);}
document.getElementById('prev').addEventListener('click',function(){go(idx-1);});
document.getElementById('next').addEventListener('click',function(){go(idx+1);});
document.addEventListener('keydown',function(ev){
  if(ev.target.tagName==='BUTTON'&&(ev.key===' '||ev.key==='Enter'))return;
  if(ev.key==='ArrowRight'||ev.key==='PageDown'){ev.preventDefault();go(idx+1);}
  if(ev.key==='ArrowLeft'||ev.key==='PageUp'){ev.preventDefault();go(idx-1);}});
go(0);

var PK=['IT','AD','CONSUL','HR','OFFICE'];
var PNM={IT:'ITソリューション',AD:'広告',CONSUL:'コンサルティング',HR:'人材サービス',OFFICE:'オフィス用品'};
function vc(v){return v==='妥当'?'ok':(v==='不成立'?'fail':'cond');}

/* 分布バー */
var bars=document.getElementById('bars');
PK.forEach(function(k){
  var o=0,c=0,f=0;
  DATA.inds.forEach(function(r){r.p.forEach(function(p){if(p.k!==k)return;
    if(p.v==='妥当')o++;else if(p.v==='不成立')f++;else c++;});});
  var row=document.createElement('div');row.className='barrow';
  row.innerHTML='<div class="barlab">'+PNM[k]+'</div>'+
    '<div class="bar"><i class="ok" style="width:'+(o/25*100)+'%"></i>'+
    '<i class="cond" style="width:'+(c/25*100)+'%"></i>'+
    '<i class="fail" style="width:'+(f/25*100)+'%"></i></div>'+
    '<div class="barnum">'+o+' / '+c+' / '+f+'</div>';
  bars.appendChild(row);
});
var lg=document.createElement('div');lg.className='legend';
lg.innerHTML='<span><i class="ok" style="background:var(--accent)"></i>妥当</span>'+
  '<span><i style="background:var(--ochre-line)"></i>条件付き</span>'+
  '<span><i style="background:var(--crim)"></i>不成立</span>'+
  '<span style="margin-left:auto">各25業種中</span>';
bars.appendChild(lg);

/* 商材タブ */
var pt=document.getElementById('ptabs'),pl=[].slice.call(document.querySelectorAll('.pf')),pc=0;
PK.forEach(function(k,i){var b=document.createElement('button');b.type='button';b.textContent=PNM[k];
  b.addEventListener('click',function(){pc=i;pr();});pt.appendChild(b);});
function pr(){[].forEach.call(pt.children,function(c,i){c.setAttribute('aria-pressed',i===pc?'true':'false');});
  pl.forEach(function(a,i){a.style.display=i===pc?'block':'none';});}
pr();

/* 穴フィルタ */
var ga=[].slice.call(document.querySelectorAll('.gap')),gc=document.getElementById('gchips'),gf=null;
[['すべて',null],['致命のみ','致命'],['重大のみ','重大']].forEach(function(f){
  var b=document.createElement('button');b.type='button';b.textContent=f[0];b.dataset.v=f[1]||'';
  if(f[1]==='致命')b.className='sev-f';
  b.addEventListener('click',function(){gf=f[1];gp();});gc.appendChild(b);});
function gp(){[].forEach.call(gc.children,function(c){c.setAttribute('aria-pressed',(c.dataset.v||null)===gf?'true':'false');});
  ga.forEach(function(a){a.style.display=(!gf||a.dataset.sev===gf)?'block':'none';});}
gp();

/* 業種グリッド */
var ig=document.getElementById('indgrid'),idt=document.getElementById('inddetail'),ic=0;
DATA.inds.forEach(function(r,i){
  var b=document.createElement('button');b.type='button';b.className='indbtn';
  var vv=r.p.map(function(p){return '<i class="v'+vc(p.v)+'"></i>';}).join('');
  b.innerHTML=r.id+'<span class="vv">'+vv+'</span>';
  b.addEventListener('click',function(){ic=i;ir();});
  ig.appendChild(b);
});
function ir(){
  [].forEach.call(ig.children,function(c,i){c.setAttribute('aria-pressed',i===ic?'true':'false');});
  var r=DATA.inds[ic];
  var strip=r.t.map(function(t){return '<span class="'+(t.e?'on':'')+'" title="'+(t.src||'').replace(/"/g,'')+'">'+t.f+' '+(t.e?t.s:'なし')+'</span>';}).join('');
  var body=r.p.map(function(p){
    return '<div class="prow"><div class="ph2"><span class="pk">'+PNM[p.k]+'</span>'+
      '<span class="vtag '+vc(p.v)+'">'+p.v+'</span>'+
      '<span class="mono">T: '+p.t.slice(0,60)+'</span><span class="mono">D: '+p.dd.slice(0,40)+'</span></div>'+
      '<div class="line"><span class="lb">生成される④</span>'+p.l4+'</div>'+
      '<div class="line"><span class="lb">生成される⑤</span>'+p.l5+'</div>'+
      '<p class="kv"><b>判定理由</b>'+p.w+'</p>'+
      (p.f&&p.f!=='―'?'<p class="kv" style="margin-bottom:0;color:var(--crim)"><b style="color:var(--crim)">壊れ方</b>'+p.f+'</p>':'')+
      '</div>';
  }).join('');
  idt.innerHTML='<div class="mono" style="margin-bottom:8px">'+r.id+' 　/　 D既定：'+r.dp+' ／ 従：'+r.ds+'</div>'+
    '<div class="tstrip">'+strip+'</div>'+
    '<p class="kv"><b>D既定の理由</b>'+r.dr+'</p>'+body;
}
ir();
})();
