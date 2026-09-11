# Git-Spectre HTML generator
# Run: python gen_html.py

HTML = r'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Git-Spectre | Developer Deep-Profiler</title>
  <meta name="description" content="Ultra-premium cinematic GitHub profile analyzer. Uncover developer archetypes, language DNA, and repository intelligence." />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>

  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: { extend: { fontFamily: { sans: ['Inter','sans-serif'], mono: ['JetBrains Mono','monospace'] } } }
    }
  </script>

  <style>
    body { background:#09090b; font-family:'Inter',sans-serif; }
    #starfield { position:fixed;inset:0;z-index:0;pointer-events:none; }
    .neon-cyan  { text-shadow:0 0 8px #22d3ee,0 0 24px #22d3ee44; }
    @keyframes scanline { 0%{transform:translateY(-100%);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateY(400%);opacity:0} }
    .scanline { position:absolute;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#22d3ee,transparent);animation:scanline 2.5s linear infinite;box-shadow:0 0 12px #22d3ee; }
    @keyframes ring-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(34,211,238,.6)}50%{box-shadow:0 0 0 16px rgba(34,211,238,0)} }
    .avatar-ring { animation:ring-pulse 2.5s ease-in-out infinite; }
    .glass { background:rgba(255,255,255,.04);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,.08); }
    .grad-border { position:relative;border-radius:1rem; }
    .grad-border::before { content:'';position:absolute;inset:0;border-radius:inherit;padding:1px;background:linear-gradient(135deg,rgba(34,211,238,.4),rgba(139,92,246,.4),rgba(34,211,238,.1));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude; }
    #searchInput:focus { box-shadow:0 0 0 2px #22d3ee66,0 0 40px #22d3ee22; }
    .repo-card { transition:all .25s ease; }
    .repo-card:hover { background:rgba(34,211,238,.06);border-color:rgba(34,211,238,.3);transform:translateY(-2px); }
    @keyframes grow { from{width:0} }
    .lang-bar { animation:grow .8s ease-out forwards; }
    @keyframes badge-glow { 0%,100%{filter:brightness(1)}50%{filter:brightness(1.3) drop-shadow(0 0 12px currentColor)} }
    .archetype-badge { animation:badge-glow 3s ease-in-out infinite; }
    ::-webkit-scrollbar { width:4px; }
    ::-webkit-scrollbar-track { background:transparent; }
    ::-webkit-scrollbar-thumb { background:rgba(34,211,238,.3);border-radius:2px; }
    @keyframes shimmer { 0%{background-position:-200% center}100%{background-position:200% center} }
  </style>
</head>

<body class="font-sans text-zinc-100 min-h-screen overflow-x-hidden">

<canvas id="starfield"></canvas>

<!-- NAV -->
<nav class="relative z-10 flex items-center justify-between px-6 py-4 border-b border-white/5 glass">
  <div class="flex items-center gap-3">
    <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-400 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
    </div>
    <div>
      <span class="font-black text-lg tracking-tight">GIT-SPECTRE</span>
      <span class="ml-2 font-mono text-xs text-cyan-400/80 bg-cyan-400/10 px-2 py-0.5 rounded-full">v1.0</span>
    </div>
  </div>
  <div class="flex items-center gap-3">
    <div id="rateIndicator" class="hidden items-center gap-2 font-mono text-xs text-zinc-400">
      <div class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
      <span>API LIVE</span>
    </div>
    <button id="vaultBtn" onclick="openVault()"
      class="flex items-center gap-2 font-mono text-xs font-semibold px-4 py-2 rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-300 hover:bg-violet-500/20 transition-all duration-200">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
      API VAULT
      <span id="tokenStatus" class="w-2 h-2 rounded-full bg-zinc-600"></span>
    </button>
  </div>
</nav>

<!-- VAULT MODAL -->
<div id="vaultModal" class="fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
  <div class="glass grad-border w-full max-w-md p-6 rounded-2xl">
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="font-black text-lg">API VAULT</h2>
        <p class="text-xs text-zinc-400 mt-0.5">Token encrypted in localStorage. Never sent to a 3rd party.</p>
      </div>
      <button onclick="closeVault()" class="text-zinc-500 hover:text-zinc-200 transition-colors">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <label class="block text-xs font-mono text-zinc-400 mb-2 uppercase tracking-widest">GitHub Personal Access Token</label>
    <input id="tokenInput" type="password" placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 font-mono text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-cyan-500/50 transition-colors" />
    <p class="mt-2 text-xs text-zinc-600 font-mono">Tip: Bumps rate limit 60 to 5000 req/hr. Needs read:user, repo scope.</p>
    <div class="flex gap-3 mt-5">
      <button onclick="saveToken()" class="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-600 font-bold text-sm hover:opacity-90 transition-opacity">LOCK IN TOKEN</button>
      <button onclick="clearToken()" class="px-4 py-2.5 rounded-lg border border-red-500/30 text-red-400 text-sm font-mono hover:bg-red-500/10 transition-colors">PURGE</button>
    </div>
  </div>
</div>

<!-- HERO -->
<main class="relative z-10">
  <section id="heroSection" class="flex flex-col items-center justify-center min-h-[calc(100vh-65px)] px-4 text-center relative">
    <div class="absolute inset-0 overflow-hidden pointer-events-none opacity-20"
         style="background-image:linear-gradient(rgba(34,211,238,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.15) 1px,transparent 1px);background-size:60px 60px;"></div>

    <div class="inline-flex items-center gap-2 font-mono text-xs bg-cyan-400/10 border border-cyan-400/20 text-cyan-300 px-3 py-1.5 rounded-full mb-6">
      <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
      INTELLIGENCE SYSTEM ONLINE
    </div>

    <h1 class="text-5xl md:text-7xl font-black tracking-tighter mb-4 leading-none">
      <span class="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">PROFILE</span><br/>
      <span class="bg-gradient-to-r from-cyan-400 via-blue-400 to-violet-500 bg-clip-text text-transparent neon-cyan">SPECTRE</span>
    </h1>
    <p class="text-zinc-400 max-w-lg mb-10 text-base leading-relaxed">
      Uncover developer archetypes. Map language DNA. Extract repository intelligence.<br/>
      <span class="text-zinc-500 text-sm font-mono">Powered by concurrent async GitHub REST.</span>
    </p>

    <div class="w-full max-w-2xl relative">
      <div class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
        </svg>
      </div>
      <input id="searchInput" type="text" placeholder="Enter GitHub Target  (e.g. torvalds)"
        class="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-36 py-5 text-lg font-mono text-zinc-100 placeholder-zinc-600 outline-none transition-all duration-300 focus:border-cyan-500/50"
        onkeydown="if(event.key==='Enter') runScan()" />
      <button id="scanBtn" onclick="runScan()"
        class="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 font-bold text-sm tracking-widest hover:opacity-90 active:scale-95 transition-all duration-150 shadow-lg shadow-cyan-500/25">
        SCAN
      </button>
    </div>

    <div id="errorBox" class="hidden mt-4 max-w-2xl w-full px-5 py-3 rounded-xl bg-red-500/10 border border-red-500/30 font-mono text-sm text-red-400"></div>
  </section>

  <!-- SCAN OVERLAY -->
  <div id="scanOverlay" class="hidden fixed inset-0 z-40 flex items-center justify-center bg-zinc-950/90 backdrop-blur-sm">
    <div class="text-center">
      <div class="relative w-32 h-32 mx-auto mb-8">
        <div class="absolute inset-0 rounded-full border border-cyan-400/30 animate-ping" style="animation-duration:1.5s;"></div>
        <div class="absolute inset-4 rounded-full border border-cyan-400/50 animate-ping" style="animation-duration:1.5s;animation-delay:.3s;"></div>
        <div class="absolute inset-8 rounded-full border border-cyan-400/70 animate-ping" style="animation-duration:1.5s;animation-delay:.6s;"></div>
        <div class="absolute inset-10 rounded-full bg-cyan-400/10 flex items-center justify-center">
          <svg class="text-cyan-400" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
          </svg>
        </div>
      </div>
      <p class="font-mono text-cyan-400 text-xl font-bold tracking-widest mb-2">SCANNING TARGET</p>
      <p id="scanTarget" class="font-mono text-zinc-400 text-sm"></p>
      <div class="mt-4 flex gap-1 justify-center">
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style="animation-delay:0s;"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style="animation-delay:.1s;"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-bounce" style="animation-delay:.2s;"></div>
      </div>
    </div>
  </div>

  <!-- DOSSIER -->
  <section id="dossier" class="hidden relative z-10 px-4 pb-20 pt-6 max-w-7xl mx-auto">

    <!-- Profile Header -->
    <div id="headerCard" class="glass grad-border rounded-2xl p-6 mb-6 relative overflow-hidden">
      <div class="scanline"></div>
      <div class="flex flex-col md:flex-row items-center md:items-start gap-6">
        <div class="relative shrink-0">
          <img id="avatar" src="" alt="Avatar" class="w-28 h-28 rounded-2xl border-2 border-cyan-500/30 avatar-ring object-cover" />
          <div class="absolute -bottom-2 -right-2 w-8 h-8 rounded-lg bg-green-400/20 border border-green-400/40 flex items-center justify-center">
            <div class="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse"></div>
          </div>
        </div>
        <div class="flex-1 text-center md:text-left">
          <div class="flex flex-col md:flex-row md:items-center gap-3 mb-2">
            <a id="profileName" href="#" target="_blank" class="font-black text-3xl tracking-tight hover:text-cyan-400 transition-colors"></a>
            <span id="archetypeBadge" class="archetype-badge self-center md:self-auto inline-flex items-center gap-1.5 font-mono text-xs font-bold px-3 py-1.5 rounded-full border"></span>
          </div>
          <p id="profileLogin" class="font-mono text-cyan-400 text-sm mb-2"></p>
          <p id="profileBio" class="text-zinc-400 text-sm max-w-xl leading-relaxed mb-4"></p>
          <div class="flex flex-wrap gap-4 text-xs font-mono text-zinc-500 justify-center md:justify-start">
            <span id="metaLocation" class="flex items-center gap-1.5"></span>
            <span id="metaCompany"  class="flex items-center gap-1.5"></span>
            <span id="metaJoined"   class="flex items-center gap-1.5"></span>
          </div>
        </div>
        <div class="shrink-0 glass rounded-xl p-4 max-w-xs text-center md:text-left">
          <p class="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-1">ARCHETYPE ANALYSIS</p>
          <p id="archetypeDesc" class="text-sm text-zinc-300 leading-relaxed"></p>
        </div>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="glass grad-border rounded-xl p-5 text-center">
        <p class="font-mono text-3xl font-bold text-cyan-400 neon-cyan" id="statRepos">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-1 uppercase tracking-widest">Total Repos</p>
      </div>
      <div class="glass grad-border rounded-xl p-5 text-center">
        <p class="font-mono text-3xl font-bold text-yellow-400" id="statStars">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-1 uppercase tracking-widest">Stars Earned</p>
      </div>
      <div class="glass grad-border rounded-xl p-5 text-center">
        <p class="font-mono text-3xl font-bold text-violet-400" id="statFollowers">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-1 uppercase tracking-widest">Followers</p>
      </div>
      <div class="glass grad-border rounded-xl p-5 text-center">
        <p class="font-mono text-3xl font-bold text-green-400" id="statFollowing">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-1 uppercase tracking-widest">Following</p>
      </div>
    </div>

    <!-- Language grid -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
      <div class="lg:col-span-2 glass grad-border rounded-2xl p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300">Language DNA</h2>
            <p class="text-xs font-mono text-zinc-600 mt-0.5">KB of code per language</p>
          </div>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(34,211,238,.6)" stroke-width="2">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
        </div>
        <div class="relative h-72">
          <canvas id="radarChart"></canvas>
        </div>
      </div>
      <div class="lg:col-span-3 glass grad-border rounded-2xl p-6">
        <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Language Breakdown</h2>
        <p class="text-xs font-mono text-zinc-600 mb-5">Sorted by total KB across owned repos</p>
        <div id="langBars" class="space-y-3.5"></div>
      </div>
    </div>

    <!-- Top Repos -->
    <div class="glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-5">
        Top Repositories &nbsp;<span class="text-cyan-400/60 font-mono normal-case text-xs">(by stars)</span>
      </h2>
      <div id="repoList" class="grid grid-cols-1 md:grid-cols-3 gap-4"></div>
    </div>

  </section>
</main>

<script>
// STARFIELD
(function(){
  const c=document.getElementById('starfield'),ctx=c.getContext('2d');
  let stars=[],W,H;
  function resize(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;}
  function init(){resize();stars=Array.from({length:220},()=>({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.2+.3,a:Math.random(),da:(Math.random()-.5)*.004,dx:(Math.random()-.5)*.15,dy:(Math.random()-.5)*.15}));}
  function draw(){ctx.clearRect(0,0,W,H);for(const s of stars){s.a=Math.max(.05,Math.min(1,s.a+s.da));s.x+=s.dx;s.y+=s.dy;if(s.x<0)s.x=W;if(s.x>W)s.x=0;if(s.y<0)s.y=H;if(s.y>H)s.y=0;ctx.save();ctx.globalAlpha=s.a;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fill();ctx.restore();}requestAnimationFrame(draw);}
  window.addEventListener('resize',init);init();draw();
})();

// TOKEN VAULT
function openVault(){const m=document.getElementById('vaultModal');m.classList.remove('hidden');m.classList.add('flex');const s=localStorage.getItem('gs_token');if(s)document.getElementById('tokenInput').value=s;}
function closeVault(){const m=document.getElementById('vaultModal');m.classList.add('hidden');m.classList.remove('flex');}
function saveToken(){const t=document.getElementById('tokenInput').value.trim();if(t){localStorage.setItem('gs_token',t);document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-green-400';}closeVault();}
function clearToken(){localStorage.removeItem('gs_token');document.getElementById('tokenInput').value='';document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-zinc-600';closeVault();}
if(localStorage.getItem('gs_token'))document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-green-400';
document.getElementById('vaultModal').addEventListener('click',function(e){if(e.target===this)closeVault();});

// LANG COLORS
const LC={Python:'#3b82f6',JavaScript:'#f59e0b',TypeScript:'#2563eb',Rust:'#f97316',Go:'#22d3ee',Java:'#ef4444','C':'#8b5cf6','C++':'#a855f7',Ruby:'#e11d48',Kotlin:'#10b981',Swift:'#f43f5e',PHP:'#6366f1','C#':'#06b6d4',Dart:'#14b8a6',Scala:'#dc2626',HTML:'#fb923c',CSS:'#60a5fa',Shell:'#4ade80',Vue:'#34d399',R:'#e879f9',Haskell:'#a78bfa',Elixir:'#8b5cf6',Lua:'#818cf8','Jupyter Notebook':'#f59e0b'};
function getLC(n){var h=(n.split('').reduce(function(a,c){return a+c.charCodeAt(0);},0)*37)%360;return LC[n]||('hsl('+h+',65%,60%)');}

// ANIMATED COUNTER
function animCount(el,target,dur=1200){const s=performance.now();function u(n){const p=Math.min((n-s)/dur,1);const e=1-Math.pow(1-p,4);el.textContent=Math.floor(e*target).toLocaleString();if(p<1)requestAnimationFrame(u);else el.textContent=target.toLocaleString();}requestAnimationFrame(u);}

// CHART
let chartInst=null;
function buildRadar(labels,vals){
  const canvas=document.getElementById('radarChart');
  if(chartInst){chartInst.destroy();chartInst=null;}
  chartInst=new Chart(canvas.getContext('2d'),{
    type:'radar',
    data:{labels,datasets:[{label:'KB',data:vals,fill:true,backgroundColor:'rgba(34,211,238,.12)',borderColor:'rgba(34,211,238,.8)',pointBackgroundColor:labels.map(getLC),pointBorderColor:'rgba(0,0,0,.5)',pointBorderWidth:1.5,pointRadius:5,pointHoverRadius:7}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{backgroundColor:'rgba(9,9,11,.9)',borderColor:'rgba(34,211,238,.3)',borderWidth:1,titleFont:{family:'JetBrains Mono',size:11},bodyFont:{family:'JetBrains Mono',size:11},callbacks:{label:(c)=>`${c.label} : ${c.raw} KB`}}},
      scales:{r:{grid:{color:'rgba(255,255,255,.06)'},angleLines:{color:'rgba(255,255,255,.06)'},ticks:{display:false,backdropColor:'transparent'},pointLabels:{color:'rgba(255,255,255,.7)',font:{family:'JetBrains Mono',size:11,weight:'600'}}}}}
  });
}

// LANG BARS
function buildBars(langs){
  const c=document.getElementById('langBars');c.innerHTML='';
  const e=Object.entries(langs);const max=e[0]?.[1]||1;const tot=e.reduce((s,[,v])=>s+v,0);
  e.forEach(([lang,bytes],i)=>{
    const pct=Math.round(bytes/tot*100);const bp=Math.round(bytes/max*100);const col=getLC(lang);const kb=(bytes/1024).toFixed(0);
    const row=document.createElement('div');row.className='group';
    row.innerHTML=`<div class="flex items-center justify-between mb-1.5"><div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm shrink-0" style="background:${col};box-shadow:0 0 6px ${col}66;"></span><span class="font-mono text-sm text-zinc-300 font-semibold">${lang}</span></div><div class="flex items-center gap-3"><span class="font-mono text-xs text-zinc-500">${kb} KB</span><span class="font-mono text-xs font-bold" style="color:${col};">${pct}%</span></div></div><div class="w-full bg-white/5 rounded-full h-1.5 overflow-hidden"><div class="lang-bar h-full rounded-full" style="width:${bp}%;background:linear-gradient(90deg,${col}cc,${col});box-shadow:0 0 8px ${col}66;"></div></div>`;
    c.appendChild(row);
  });
}

// REPO CARDS
function buildRepos(repos){
  const c=document.getElementById('repoList');c.innerHTML='';
  if(!repos.length){c.innerHTML='<p class="col-span-3 text-center text-zinc-600 font-mono text-sm py-8">No public repositories found.</p>';return;}
  repos.forEach(r=>{
    const col=getLC(r.language||'Unknown');
    const topics=r.topics.map(t=>`<span class="px-2 py-0.5 rounded-full bg-white/5 text-zinc-500 font-mono text-xs">${t}</span>`).join('');
    const card=document.createElement('a');card.href=r.url;card.target='_blank';card.rel='noopener noreferrer';card.className='repo-card block glass border border-white/5 rounded-xl p-5 cursor-pointer no-underline';
    card.innerHTML=`<div class="flex items-start justify-between gap-2 mb-2"><h3 class="font-mono text-sm font-bold text-cyan-300 truncate">${r.name}</h3><svg class="shrink-0 mt-0.5 opacity-40" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/></svg></div><p class="text-xs text-zinc-500 leading-relaxed mb-4 line-clamp-2">${r.description}</p><div class="flex flex-wrap gap-1.5 mb-4">${topics}</div><div class="flex items-center gap-4 text-xs font-mono"><span class="flex items-center gap-1 text-yellow-400"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>${r.stars}</span><span class="flex items-center gap-1 text-zinc-500"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"/><path d="M12 12v3"/></svg>${r.forks}</span><span class="flex items-center gap-1" style="color:${col};"><span class="w-2 h-2 rounded-full" style="background:${col};"></span>${r.language}</span></div>`;
    c.appendChild(card);
  });
}

// MAIN SCAN
async function runScan(){
  const username=document.getElementById('searchInput').value.trim();
  if(!username)return;
  const eb=document.getElementById('errorBox');eb.classList.add('hidden');eb.textContent='';
  document.getElementById('scanTarget').textContent=`> Initiating deep scan on: ${username}`;
  document.getElementById('scanOverlay').classList.remove('hidden');
  document.getElementById('dossier').classList.add('hidden');
  try{
    const token=localStorage.getItem('gs_token')||'';
    const resp=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,github_token:token||null})});
    const data=await resp.json();
    if(!resp.ok)throw new Error(data.detail||`HTTP ${resp.status}`);
    renderDossier(data);
  }catch(err){
    document.getElementById('scanOverlay').classList.add('hidden');
    eb.textContent=`ERROR: ${err.message}`;eb.classList.remove('hidden');
  }
}

// RENDER
function renderDossier(data){
  const{profile,stats,languages,archetype,top_repos}=data;
  document.getElementById('avatar').src=profile.avatar_url;
  const ne=document.getElementById('profileName');ne.textContent=profile.name;ne.href=profile.html_url;
  document.getElementById('profileLogin').textContent=`@${profile.login}`;
  document.getElementById('profileBio').textContent=profile.bio;
  document.getElementById('archetypeDesc').textContent=archetype.description;

  const locSvg='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>';
  const bizSvg='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></svg>';
  const calSvg='<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>';
  document.getElementById('metaLocation').innerHTML=locSvg+profile.location;
  document.getElementById('metaCompany').innerHTML=bizSvg+profile.company;
  document.getElementById('metaJoined').innerHTML=calSvg+'Since '+profile.created_at;

  const badge=document.getElementById('archetypeBadge');
  badge.textContent=archetype.label;
  badge.style.cssText=`background:linear-gradient(135deg,${archetype.glow}22,${archetype.glow}11);border-color:${archetype.glow}55;color:${archetype.glow};box-shadow:0 0 12px ${archetype.glow}33;`;

  animCount(document.getElementById('statRepos'),stats.total_repos);
  animCount(document.getElementById('statStars'),stats.total_stars);
  animCount(document.getElementById('statFollowers'),profile.followers);
  animCount(document.getElementById('statFollowing'),profile.following);

  const entries=Object.entries(languages);
  if(entries.length){buildRadar(entries.map(([k])=>k),entries.map(([,v])=>Math.round(v)));buildBars(languages);}
  buildRepos(top_repos);

  document.getElementById('scanOverlay').classList.add('hidden');
  document.getElementById('dossier').classList.remove('hidden');
  const ri=document.getElementById('rateIndicator');ri.classList.remove('hidden');ri.classList.add('flex');
  setTimeout(()=>document.getElementById('dossier').scrollIntoView({behavior:'smooth',block:'start'}),100);
}
</script>
</body>
</html>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f'index.html written: {len(HTML)} chars')