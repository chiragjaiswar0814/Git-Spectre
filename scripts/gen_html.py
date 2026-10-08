# Git-Spectre v2 HTML Generator
# Run: python gen_html.py

HTML = r'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Git-Spectre | Developer Deep-Profiler</title>
  <meta name="description" content="Ultra-premium cinematic GitHub profile analyzer. Uncover developer archetypes, language DNA, contribution heatmaps, and repository intelligence." />

  <!-- OpenGraph / Twitter -->
  <meta property="og:type"        content="website" />
  <meta property="og:title"       content="Git-Spectre | Developer Deep-Profiler" />
  <meta property="og:description" content="Uncover developer archetypes, language DNA, and repository intelligence from any GitHub profile." />
  <meta property="og:url"         content="https://git-spectre.vercel.app/" />
  <meta name="twitter:card"       content="summary_large_image" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>

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
    ::-webkit-scrollbar { width:4px;height:4px; }
    ::-webkit-scrollbar-track { background:transparent; }
    ::-webkit-scrollbar-thumb { background:rgba(34,211,238,.3);border-radius:2px; }
    .heatmap-cell:hover { transform:scale(1.4);z-index:10; }
    .heatmap-cell { transition:transform .15s ease;border-radius:2px;cursor:default; }
    .tag-chip:hover { color:#22d3ee!important;border-color:rgba(34,211,238,.4)!important; }
    .tag-chip { transition:all .2s ease; }
    @keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
    .fade-up { animation:fadeUp .5s ease forwards; }
    #exportBtn { position:fixed;bottom:2rem;right:2rem;z-index:30; }
  </style>
</head>

<body class="font-sans text-zinc-100 min-h-screen overflow-x-hidden">
<canvas id="starfield"></canvas>

<!-- =========================================================
     NAV
     ========================================================= -->
<nav class="relative z-10 flex items-center justify-between px-4 md:px-6 py-3 border-b border-white/5 glass">
  <div class="flex items-center gap-3.5 select-none">

    <!-- ── Logo mark: glass card + precision reticle ── -->
    <div class="relative flex-shrink-0 flex items-center justify-center"
         style="width:42px;height:42px">
      <!-- glass background -->
      <div class="absolute inset-0 rounded-xl"
           style="background:linear-gradient(145deg,rgba(34,211,238,0.10),rgba(109,40,217,0.16));
                  border:1px solid rgba(34,211,238,0.28);
                  box-shadow:0 0 22px rgba(34,211,238,0.13),inset 0 1px 0 rgba(255,255,255,0.08)"></div>
      <!-- reticle icon -->
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="position:relative;z-index:1">
        <!-- outer ring -->
        <circle cx="12" cy="12" r="9"   stroke="rgba(34,211,238,0.22)" stroke-width="1"/>
        <!-- mid ring -->
        <circle cx="12" cy="12" r="5.5" stroke="rgba(34,211,238,0.55)" stroke-width="1.2"/>
        <!-- core dot -->
        <circle cx="12" cy="12" r="2"   fill="#22d3ee" style="filter:drop-shadow(0 0 4px #22d3ee)"/>
        <!-- crosshairs -->
        <line x1="12" y1="2"    x2="12" y2="5.5"  stroke="#22d3ee" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
        <line x1="12" y1="18.5" x2="12" y2="22"   stroke="#22d3ee" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
        <line x1="2"  y1="12"   x2="5.5" y2="12"  stroke="#22d3ee" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
        <line x1="18.5" y1="12" x2="22"  y2="12"  stroke="#22d3ee" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
      </svg>
    </div>

    <!-- ── Wordmark ── -->
    <div>
      <!-- top row: GIT | SPECTRE -->
      <div class="flex items-baseline gap-0">
        <span style="font-family:Inter,sans-serif;font-weight:300;font-size:10px;
                     letter-spacing:0.22em;color:#52525b;text-transform:uppercase;
                     padding-right:7px">GIT</span>
        <!-- vertical divider -->
        <div style="width:1px;height:13px;margin-right:7px;flex-shrink:0;
                    background:linear-gradient(180deg,transparent,rgba(34,211,238,0.55),transparent)"></div>
        <span style="font-family:Inter,sans-serif;font-weight:900;font-size:17px;
                     letter-spacing:-0.03em;text-transform:uppercase;
                     background:linear-gradient(135deg,#f4f4f5 30%,#a1a1aa);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     background-clip:text">SPECTRE</span>
      </div>
      <!-- bottom row: gradient rule + v2.0 -->
      <div class="flex items-center gap-1.5" style="margin-top:3px">
        <div style="height:1px;width:44px;
                    background:linear-gradient(90deg,rgba(34,211,238,0.7),transparent)"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:600;
                     color:rgba(34,211,238,0.60);letter-spacing:0.14em">v2.0</span>
      </div>
    </div>

  </div>

  <!-- Rate Limit Gauge -->
  <div id="rlGauge" class="hidden md:flex flex-col items-center gap-0.5 mx-4">
    <div class="flex items-center gap-2">
      <span class="font-mono text-xs text-zinc-500">API</span>
      <div class="w-24 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div id="rlBar" class="h-full rounded-full transition-all duration-500" style="width:100%;background:#22d3ee"></div>
      </div>
      <span id="rlText" class="font-mono text-xs text-zinc-600">—</span>
    </div>
  </div>

  <div class="flex items-center gap-2">
    <button onclick="openCompareModal()"
      class="hidden md:flex items-center gap-2 font-mono text-xs font-semibold px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition-all">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
      COMPARE
    </button>
    <button id="exportBtn2" onclick="exportPDF()"
      class="hidden items-center gap-2 font-mono text-xs font-semibold px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/30 text-green-300 hover:bg-green-500/20 transition-all">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
      PDF
    </button>
    <button id="vaultBtn" onclick="openVault()"
      class="flex items-center gap-2 font-mono text-xs font-semibold px-3 py-2 rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-300 hover:bg-violet-500/20 transition-all">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
      VAULT
      <span id="tokenStatus" class="w-2 h-2 rounded-full bg-zinc-600"></span>
    </button>
  </div>
</nav>

<!-- =========================================================
     API VAULT MODAL
     ========================================================= -->
<div id="vaultModal" class="fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
  <div class="glass grad-border w-full max-w-md p-6 rounded-2xl">
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="font-black text-lg">API VAULT</h2>
        <p class="text-xs text-zinc-400 mt-0.5">Token stored in localStorage. Never sent to a 3rd party.</p>
      </div>
      <button onclick="closeVault()" class="text-zinc-500 hover:text-zinc-200 transition-colors">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <label class="block text-xs font-mono text-zinc-400 mb-2 uppercase tracking-widest">GitHub Personal Access Token</label>
    <input id="tokenInput" type="password" placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 font-mono text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-cyan-500/50 transition-colors" />
    <p class="mt-2 text-xs text-zinc-600 font-mono">Bumps rate limit: 60 → 5000 req/hr. Needs read:user, repo scope.</p>
    <div class="flex gap-3 mt-5">
      <button onclick="saveToken()" class="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-violet-600 font-bold text-sm hover:opacity-90 transition-opacity">LOCK IN TOKEN</button>
      <button onclick="clearToken()" class="px-4 py-2.5 rounded-lg border border-red-500/30 text-red-400 text-sm font-mono hover:bg-red-500/10 transition-colors">PURGE</button>
    </div>
  </div>
</div>

<!-- =========================================================
     COMPARE MODAL
     ========================================================= -->
<div id="compareModal" class="fixed inset-0 z-50 hidden items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
  <div class="glass grad-border w-full max-w-lg p-6 rounded-2xl">
    <div class="flex items-center justify-between mb-5">
      <div>
        <h2 class="font-black text-lg">DUAL TARGET SCAN</h2>
        <p class="text-xs text-zinc-400 mt-0.5">Compare two GitHub profiles side-by-side.</p>
      </div>
      <button onclick="closeCompareModal()" class="text-zinc-500 hover:text-zinc-200 transition-colors">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="grid grid-cols-2 gap-3 mb-5">
      <div>
        <label class="block font-mono text-xs text-zinc-500 uppercase tracking-widest mb-1.5">Target Alpha</label>
        <input id="compareInputA" type="text" placeholder="e.g. torvalds"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 font-mono text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-cyan-500/50 transition-colors" />
      </div>
      <div>
        <label class="block font-mono text-xs text-zinc-500 uppercase tracking-widest mb-1.5">Target Beta</label>
        <input id="compareInputB" type="text" placeholder="e.g. gvanrossum"
          class="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2.5 font-mono text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-cyan-500/50 transition-colors" />
      </div>
    </div>
    <button onclick="runCompare()" class="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 font-bold tracking-widest hover:opacity-90 transition-opacity">
      INITIATE DUAL SCAN
    </button>
  </div>
</div>

<!-- =========================================================
     HERO
     ========================================================= -->
<main class="relative z-10">
<section id="heroSection" class="flex flex-col items-center justify-center min-h-[calc(100vh-57px)] px-4 text-center relative">
  <div class="absolute inset-0 overflow-hidden pointer-events-none opacity-20"
       style="background-image:linear-gradient(rgba(34,211,238,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.15) 1px,transparent 1px);background-size:60px 60px;"></div>

  <div class="inline-flex items-center gap-2 font-mono text-xs bg-cyan-400/10 border border-cyan-400/20 text-cyan-300 px-3 py-1.5 rounded-full mb-6">
    <div class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></div>
    INTELLIGENCE SYSTEM v2 ONLINE
  </div>

  <h1 class="text-5xl md:text-7xl font-black tracking-tighter mb-4 leading-none">
    <span class="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">PROFILE</span><br/>
    <span class="bg-gradient-to-r from-cyan-400 via-blue-400 to-violet-500 bg-clip-text text-transparent neon-cyan">SPECTRE</span>
  </h1>
  <p class="text-zinc-400 max-w-lg mb-10 text-base leading-relaxed">
    Uncover developer archetypes. Map language DNA. Extract repository intelligence.<br/>
    <span class="text-zinc-500 text-sm font-mono">Heatmaps · Streaks · Scores · Compare · Export</span>
  </p>

  <div class="w-full max-w-2xl relative">
    <div class="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
      </svg>
    </div>
    <input id="searchInput" type="text" placeholder="Enter GitHub Target  (e.g. chiragjaiswar0814)"
      class="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-36 py-5 text-lg font-mono text-zinc-100 placeholder-zinc-600 outline-none transition-all duration-300 focus:border-cyan-500/50"
      onkeydown="if(event.key==='Enter') runScan()" />
    <button id="scanBtn" onclick="runScan()"
      class="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 font-bold text-sm tracking-widest hover:opacity-90 active:scale-95 transition-all shadow-lg shadow-cyan-500/25">
      SCAN
    </button>
  </div>

  <div id="errorBox" class="hidden mt-4 max-w-2xl w-full px-5 py-3 rounded-xl bg-red-500/10 border border-red-500/30 font-mono text-sm text-red-400"></div>
</section>

<!-- =========================================================
     SCAN OVERLAY
     ========================================================= -->
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

<!-- =========================================================
     DOSSIER
     ========================================================= -->
<section id="dossier" class="hidden relative z-10 px-4 pb-20 pt-6 max-w-7xl mx-auto">

  <!-- Cached badge -->
  <div id="cachedBadge" class="hidden mb-3 inline-flex items-center gap-2 font-mono text-xs text-zinc-500 bg-white/5 border border-white/10 px-3 py-1 rounded-full">
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
    Served from cache · <span id="cachedTime"></span>
  </div>

  <!-- 1. PROFILE HEADER -->
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
        <div class="flex flex-col md:flex-row md:items-center gap-3 mb-1">
          <a id="profileName" href="#" target="_blank" class="font-black text-3xl tracking-tight hover:text-cyan-400 transition-colors"></a>
          <span id="archetypeBadge" class="archetype-badge self-center inline-flex items-center gap-1.5 font-mono text-xs font-bold px-3 py-1.5 rounded-full border"></span>
        </div>
        <p id="profileLogin" class="font-mono text-cyan-400 text-sm mb-2"></p>
        <p id="profileBio" class="text-zinc-400 text-sm max-w-xl leading-relaxed mb-3"></p>
        <div class="flex flex-wrap gap-4 text-xs font-mono text-zinc-500 justify-center md:justify-start mb-1">
          <span id="metaLocation" class="flex items-center gap-1.5"></span>
          <span id="metaCompany"  class="flex items-center gap-1.5"></span>
          <span id="metaJoined"   class="flex items-center gap-1.5"></span>
          <span id="metaBlog"     class="flex items-center gap-1.5"></span>
        </div>
        <!-- Org Chips -->
        <div id="orgChips"></div>
        <!-- Streak Badges -->
        <div id="streakBadges"></div>
      </div>
      <div class="shrink-0 glass rounded-xl p-4 max-w-xs text-center md:text-left">
        <p class="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-1">ARCHETYPE ANALYSIS</p>
        <p id="archetypeDesc" class="text-sm text-zinc-300 leading-relaxed"></p>
        <!-- Share Button -->
        <button id="shareBtn" onclick="copyShareLink()"
          class="mt-3 w-full flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/10 font-mono text-xs text-zinc-400 hover:text-zinc-200 hover:border-white/20 transition-all">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/></svg>
          COPY PROFILE LINK
        </button>
      </div>
    </div>
  </div>

  <!-- 2. SCORE + STATS ROW -->
  <div class="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
    <!-- Score Ring -->
    <div class="col-span-2 glass grad-border rounded-2xl p-5 flex flex-col items-center justify-center">
      <div id="scoreRingContainer"></div>
    </div>
    <!-- Stats -->
    <div class="glass grad-border rounded-xl p-4 flex flex-col">
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-cyan-400 neon-cyan" id="statRepos">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-0.5 uppercase tracking-widest">Repos</p>
      </div>
      <div class="border-t border-white/5 mt-3 pt-2 space-y-1.5 overflow-y-auto" style="max-height:110px" id="reposMiniList"></div>
    </div>
    <div class="glass grad-border rounded-xl p-4 flex flex-col">
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-yellow-400" id="statStars">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-0.5 uppercase tracking-widest">Stars</p>
      </div>
      <div class="border-t border-white/5 mt-3 pt-2 space-y-1.5 overflow-y-auto" style="max-height:110px" id="starsMiniList"></div>
    </div>
    <div class="glass grad-border rounded-xl p-4 flex flex-col">
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-violet-400" id="statFollowers">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-0.5 uppercase tracking-widest">Followers</p>
      </div>
      <div class="border-t border-white/5 mt-3 pt-2 space-y-1.5 overflow-y-auto" style="max-height:110px" id="followersMiniList"></div>
    </div>
    <div class="glass grad-border rounded-xl p-4 flex flex-col">
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-green-400" id="statFollowing">0</p>
        <p class="text-xs font-mono text-zinc-500 mt-0.5 uppercase tracking-widest">Following</p>
      </div>
      <div class="border-t border-white/5 mt-3 pt-2 space-y-1.5 overflow-y-auto" style="max-height:110px" id="followingMiniList"></div>
    </div>
  </div>

  <!-- 3. CONTRIBUTION HEATMAP -->
  <div class="glass grad-border rounded-2xl p-6 mb-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300">Contribution Heatmap</h2>
        <p class="text-xs font-mono text-zinc-600 mt-0.5">Last 91 days of push activity</p>
      </div>
      <div class="flex items-center gap-2 text-xs font-mono text-zinc-600">
        <span>Less</span>
        <div class="flex gap-0.5">
          <div class="w-2.5 h-2.5 rounded-sm" style="background:rgba(255,255,255,0.05)"></div>
          <div class="w-2.5 h-2.5 rounded-sm" style="background:rgba(34,211,238,0.2)"></div>
          <div class="w-2.5 h-2.5 rounded-sm" style="background:rgba(34,211,238,0.45)"></div>
          <div class="w-2.5 h-2.5 rounded-sm" style="background:rgba(34,211,238,0.7)"></div>
          <div class="w-2.5 h-2.5 rounded-sm" style="background:rgba(34,211,238,0.95)"></div>
        </div>
        <span>More</span>
      </div>
    </div>
    <div id="heatmapGrid" class="overflow-x-auto"></div>
  </div>

  <!-- 4. LANGUAGE INTELLIGENCE + TAG CLOUD -->
  <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
    <div class="lg:col-span-2 glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Language DNA</h2>
      <p class="text-xs font-mono text-zinc-600 mb-4">KB of code per language</p>
      <div class="relative h-64"><canvas id="radarChart"></canvas></div>
    </div>
    <div class="lg:col-span-2 glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Language Breakdown</h2>
      <p class="text-xs font-mono text-zinc-600 mb-5">Sorted by total KB across owned repos</p>
      <div id="langBars" class="space-y-3.5"></div>
    </div>
    <div id="tagCloudSection" class="lg:col-span-1 glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Tech Tags</h2>
      <p class="text-xs font-mono text-zinc-600 mb-4">From repo topics</p>
      <div id="tagCloud" class="flex flex-wrap gap-1.5"></div>
    </div>
  </div>

  <!-- 5. DEEP ANALYTICS: Activity Hours + Language Evolution -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
    <div class="glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Activity Hours</h2>
      <p class="text-xs font-mono text-zinc-600 mb-4">Events by day × hour (UTC)</p>
      <div id="activityHoursGrid"></div>
    </div>
    <div id="langEvoSection" class="glass grad-border rounded-2xl p-6">
      <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-1">Stack Evolution</h2>
      <p class="text-xs font-mono text-zinc-600 mb-4">Language KB per year of creation</p>
      <div class="relative h-52"><canvas id="langEvoChart"></canvas></div>
    </div>
  </div>

  <!-- 6. GIST INTELLIGENCE -->
  <div id="gistCard" class="hidden glass grad-border rounded-2xl p-6 mb-6">
    <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-4">Gist Intelligence</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-cyan-400" id="gistTotal">0</p>
        <p class="font-mono text-xs text-zinc-500 mt-1">Total Gists</p>
      </div>
      <div class="text-center">
        <p class="font-mono text-2xl font-bold text-violet-400" id="gistComments">0</p>
        <p class="font-mono text-xs text-zinc-500 mt-1">Comments</p>
      </div>
      <div class="text-center">
        <p class="font-mono text-sm font-bold text-yellow-400 truncate" id="gistLang">—</p>
        <p class="font-mono text-xs text-zinc-500 mt-1">Top Language</p>
      </div>
      <div class="text-center col-span-2 md:col-span-1">
        <p class="font-mono text-xs text-zinc-500 mb-1">Most Forked</p>
        <div id="gistMostForked" class="font-mono text-xs text-zinc-300 truncate"></div>
      </div>
    </div>
  </div>

  <!-- 7. TOP REPOSITORIES (6 repos) -->
  <div class="glass grad-border rounded-2xl p-6">
    <h2 class="font-bold text-sm tracking-widest uppercase text-zinc-300 mb-5">
      Top Repositories &nbsp;<span class="text-cyan-400/60 font-mono normal-case text-xs">(by stars)</span>
    </h2>
    <div id="repoList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
  </div>

</section>

<!-- =========================================================
     COMPARE SECTION
     ========================================================= -->
<section id="compareSection" class="hidden relative z-10 px-4 pb-20 max-w-7xl mx-auto">
  <div class="glass grad-border rounded-2xl p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="font-black text-xl tracking-tight">DUAL TARGET ANALYSIS</h2>
        <p class="text-xs font-mono text-zinc-500 mt-0.5">Side-by-side developer comparison</p>
      </div>
      <button onclick="document.getElementById('compareSection').classList.add('hidden')"
        class="text-zinc-500 hover:text-zinc-200 transition-colors">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div id="compareSectionContent"></div>
  </div>
</section>

</main>

<!-- Floating Export Button -->
<button id="exportBtn" onclick="exportPDF()"
  class="hidden items-center gap-2 font-mono text-xs font-bold px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500/20 to-violet-600/20 border border-cyan-500/30 text-cyan-300 hover:opacity-90 active:scale-95 transition-all shadow-xl shadow-cyan-500/10 backdrop-blur">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>
  EXPORT PDF
</button>

<script>
// ============================================================
// STARFIELD
// ============================================================
(function(){
  const c=document.getElementById('starfield'),ctx=c.getContext('2d');
  let stars=[],W,H;
  function resize(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;}
  function init(){resize();stars=Array.from({length:220},()=>({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.2+.3,a:Math.random(),da:(Math.random()-.5)*.004,dx:(Math.random()-.5)*.15,dy:(Math.random()-.5)*.15}));}
  function draw(){ctx.clearRect(0,0,W,H);for(const s of stars){s.a=Math.max(.05,Math.min(1,s.a+s.da));s.x+=s.dx;s.y+=s.dy;if(s.x<0)s.x=W;if(s.x>W)s.x=0;if(s.y<0)s.y=H;if(s.y>H)s.y=0;ctx.save();ctx.globalAlpha=s.a;ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fill();ctx.restore();}requestAnimationFrame(draw);}
  window.addEventListener('resize',init);init();draw();
})();

// ============================================================
// TOKEN VAULT
// ============================================================
function openVault(){const m=document.getElementById('vaultModal');m.classList.remove('hidden');m.classList.add('flex');const s=localStorage.getItem('gs_token');if(s)document.getElementById('tokenInput').value=s;}
function closeVault(){const m=document.getElementById('vaultModal');m.classList.add('hidden');m.classList.remove('flex');}
function saveToken(){const t=document.getElementById('tokenInput').value.trim();if(t){localStorage.setItem('gs_token',t);document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-green-400';}closeVault();refreshRateLimit();}
function clearToken(){localStorage.removeItem('gs_token');document.getElementById('tokenInput').value='';document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-zinc-600';closeVault();}
if(localStorage.getItem('gs_token'))document.getElementById('tokenStatus').className='w-2 h-2 rounded-full bg-green-400';
document.getElementById('vaultModal').addEventListener('click',function(e){if(e.target===this)closeVault();});
document.getElementById('compareModal').addEventListener('click',function(e){if(e.target===this)closeCompareModal();});

// ============================================================
// RATE LIMIT GAUGE
// ============================================================
async function refreshRateLimit(){
  try{
    const r=await fetch('/api/rate-limit');
    if(!r.ok)return;
    const d=await r.json();
    const pct=d.remaining/d.limit*100;
    const bar=document.getElementById('rlBar');
    const txt=document.getElementById('rlText');
    const gauge=document.getElementById('rlGauge');
    gauge.classList.remove('hidden');
    gauge.classList.add('flex');
    bar.style.width=pct+'%';
    bar.style.background=pct>50?'#22d3ee':pct>20?'#f59e0b':'#ef4444';
    const reset=new Date(d.reset*1000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
    txt.textContent=`${d.remaining}/${d.limit}`;
    bar.title=`${d.remaining} remaining. Resets at ${reset}`;
  }catch(e){}
}
// Auto-refresh every 60 seconds
setInterval(refreshRateLimit,60000);

// ============================================================
// LANG COLORS
// ============================================================
const LC={Python:'#3b82f6',JavaScript:'#f59e0b',TypeScript:'#2563eb',Rust:'#f97316',Go:'#22d3ee',Java:'#ef4444','C':'#8b5cf6','C++':'#a855f7',Ruby:'#e11d48',Kotlin:'#10b981',Swift:'#f43f5e',PHP:'#6366f1','C#':'#06b6d4',Dart:'#14b8a6',Scala:'#dc2626',HTML:'#fb923c',CSS:'#60a5fa',Shell:'#4ade80',Vue:'#34d399',R:'#e879f9',Haskell:'#a78bfa',Elixir:'#8b5cf6',Lua:'#818cf8','Jupyter Notebook':'#f59e0b'};
function getLC(n){if(LC[n])return LC[n];var h=(n.split('').reduce(function(a,c){return a+c.charCodeAt(0);},0)*37)%360;return'hsl('+h+',65%,60%)';}

// ============================================================
// ANIMATED COUNTER
// ============================================================
function animCount(el,target,dur=1200){if(!el)return;const s=performance.now();function u(n){const p=Math.min((n-s)/dur,1);const e=1-Math.pow(1-p,4);el.textContent=Math.floor(e*target).toLocaleString();if(p<1)requestAnimationFrame(u);else el.textContent=target.toLocaleString();}requestAnimationFrame(u);}

// ============================================================
// SCORE RING
// ============================================================
function buildScoreRing(score){
  const{total,grade,breakdown}=score;
  const r=54,circ=2*Math.PI*r;
  const offset=circ*(1-Math.min(total,1000)/1000);
  const gradeColors={'S+':'#f59e0b','S':'#10b981','A':'#06b6d4','B':'#8b5cf6','C':'#f97316','D':'#ef4444','E':'#6b7280'};
  const col=gradeColors[grade]||'#22d3ee';
  // Max possible points per component
  const maxScore={stars:300,followers:200,diversity:150,repos:100,age:80,activity:70};
  // Human-readable labels (rename 'age' -> 'Tenure' to avoid confusion)
  const labelMap={stars:'Stars',followers:'Social',diversity:'Diversity',repos:'Repos',age:'Tenure',activity:'Activity'};
  const barsHtml=Object.entries(breakdown).map(([k,v])=>`
    <div class="flex items-center gap-2">
      <span class="font-mono text-xs text-zinc-600 w-16 shrink-0">${labelMap[k]||k}</span>
      <div class="flex-1 bg-white/5 rounded-full h-1 overflow-hidden">
        <div class="h-full rounded-full transition-all duration-700" style="width:${Math.round(v/(maxScore[k]||100)*100)}%;background:${col};opacity:0.7"></div>
      </div>
      <span class="font-mono text-xs text-zinc-600 w-6 text-right">${v}</span>
    </div>`).join('');

  // Use relative wrapper + absolute SVG so the center text never overlaps or floats away
  document.getElementById('scoreRingContainer').innerHTML=`
    <div class="flex flex-col items-center w-full">
      <div class="relative flex items-center justify-center" style="width:130px;height:130px;flex-shrink:0">
        <svg width="130" height="130" class="-rotate-90" style="position:absolute;top:0;left:0;overflow:visible">
          <circle cx="65" cy="65" r="${r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="10"/>
          <circle id="scoreArc" cx="65" cy="65" r="${r}" fill="none" stroke="${col}" stroke-width="10"
            stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ}"
            style="transition:stroke-dashoffset 1.6s cubic-bezier(0.4,0,0.2,1);filter:drop-shadow(0 0 10px ${col}66)"/>
        </svg>
        <div class="relative z-10 flex flex-col items-center leading-none gap-0.5">
          <span id="scoreNum" class="font-black text-3xl text-white">0</span>
          <span class="font-mono text-xs text-zinc-600">/1000</span>
          <span class="font-black text-base" style="color:${col}">${grade}</span>
        </div>
      </div>
      <p class="font-mono text-xs text-zinc-500 uppercase tracking-widest mt-2 mb-3 text-center">Dev Score™</p>
      <div class="space-y-1.5 w-full">${barsHtml}</div>
    </div>`;

  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const arc=document.getElementById('scoreArc');
    if(arc)arc.style.strokeDashoffset=offset;
    animCount(document.getElementById('scoreNum'),total,1500);
  }));
}

// ============================================================
// ORG CHIPS
// ============================================================
function buildOrgs(orgs){
  const el=document.getElementById('orgChips');
  if(!orgs||!orgs.length){el.innerHTML='';return;}
  el.innerHTML=`<div class="flex flex-wrap gap-2 mt-3">
    ${orgs.map(o=>`<a href="${o.url}" target="_blank" rel="noopener" title="@${o.login}"
      class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/10 hover:border-cyan-500/30 hover:text-zinc-200 transition-all text-xs font-mono text-zinc-400">
      <img src="${o.avatar_url}" class="w-4 h-4 rounded-sm" alt="${o.login}" loading="lazy"/>
      ${o.login}
    </a>`).join('')}
  </div>`;
}

// ============================================================
// STREAKS
// ============================================================
function buildStreaks(streaks){
  const el=document.getElementById('streakBadges');
  if(!streaks||streaks.total_active_days===0){el.innerHTML='';return;}
  el.innerHTML=`<div class="flex flex-wrap gap-2 mt-3">
    ${streaks.current>0?`<div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-orange-500/10 border border-orange-500/20">
      <span class="text-base">🔥</span>
      <div><p class="font-black text-sm text-orange-400 leading-none">${streaks.current}d</p><p class="font-mono text-xs text-zinc-600">Current</p></div>
    </div>`:''}
    <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
      <span class="text-base">⚡</span>
      <div><p class="font-black text-sm text-yellow-400 leading-none">${streaks.longest}d</p><p class="font-mono text-xs text-zinc-600">Best</p></div>
    </div>
    <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
      <span class="text-base">📅</span>
      <div><p class="font-black text-sm text-cyan-400 leading-none">${streaks.total_active_days}</p><p class="font-mono text-xs text-zinc-600">Active Days</p></div>
    </div>
  </div>`;
}

// ============================================================
// CONTRIBUTION HEATMAP
// ============================================================
function buildHeatmap(data){
  const today=new Date();
  const cells=[];
  for(let i=90;i>=0;i--){
    const d=new Date(today);d.setDate(d.getDate()-i);
    const ds=d.toISOString().split('T')[0];
    cells.push({date:ds,count:data[ds]||0,dow:d.getDay()});
  }
  // Pad so grid starts on Monday
  const firstMon=(cells[0].dow===0?6:cells[0].dow-1);
  const padded=[...Array(firstMon).fill(null),...cells];
  const maxC=Math.max(...cells.map(c=>c.count),1);

  function cellColor(n){
    if(!n)return'rgba(255,255,255,0.04)';
    const p=n/maxC;
    if(p>.75)return'rgba(34,211,238,0.95)';
    if(p>.5)return'rgba(34,211,238,0.65)';
    if(p>.25)return'rgba(34,211,238,0.4)';
    return'rgba(34,211,238,0.2)';
  }

  const dayLabels=['Mon','','Wed','','Fri','','Sun'];
  const cellsHtml=padded.map(cell=>{
    if(!cell)return`<div style="width:10px;height:10px;background:transparent"></div>`;
    const shadow=cell.count?`box-shadow:0 0 4px rgba(34,211,238,0.4)`:'';
    return`<div class="heatmap-cell" style="width:10px;height:10px;background:${cellColor(cell.count)};${shadow}" title="${cell.date}: ${cell.count} commit${cell.count!==1?'s':''}"></div>`;
  }).join('');

  document.getElementById('heatmapGrid').innerHTML=`
    <div class="flex gap-1.5 items-start">
      <div class="flex flex-col gap-0.5 mt-0.5 shrink-0">
        ${dayLabels.map(l=>`<div class="font-mono text-zinc-700 text-right" style="font-size:9px;line-height:10px;height:10px;margin-bottom:2px">${l}</div>`).join('')}
      </div>
      <div style="display:grid;grid-template-rows:repeat(7,10px);grid-auto-flow:column;gap:2px;overflow-x:auto;padding-bottom:4px">
        ${cellsHtml}
      </div>
    </div>`;
}

// ============================================================
// STAT MINI-LISTS (repos / stars / followers / following)
// ============================================================
const _repoSvg=`<svg class="shrink-0" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>`;

function _emptyMsg(text){
  return `<p class="font-mono text-center" style="font-size:9px;color:#3f3f46;padding-top:4px">${text}</p>`;
}

function buildStatLists(topRepos,followers,following){
  // --- Repos ---
  const rl=document.getElementById('reposMiniList');
  if(topRepos&&topRepos.length){
    rl.innerHTML=topRepos.slice(0,7).map(r=>`
      <a href="${r.url}" target="_blank" rel="noopener" class="flex items-center gap-1.5 group min-w-0" title="${r.name}">
        <span class="text-zinc-700 group-hover:text-cyan-500 transition-colors shrink-0">${_repoSvg}</span>
        <span class="font-mono text-zinc-500 group-hover:text-zinc-200 transition-colors truncate" style="font-size:10px">${r.name}</span>
      </a>`).join('');
  }else{rl.innerHTML=_emptyMsg('No repos yet');}

  // --- Stars (repos that have stars) ---
  const sl=document.getElementById('starsMiniList');
  const starredRepos=(topRepos||[]).filter(r=>r.stars>0).slice(0,7);
  if(starredRepos.length){
    sl.innerHTML=starredRepos.map(r=>`
      <a href="${r.url}" target="_blank" rel="noopener" class="flex items-center gap-1.5 group min-w-0" title="${r.name} — ${r.stars} stars">
        <span class="shrink-0" style="color:#ca8a04;font-size:10px">★</span>
        <span class="font-mono text-zinc-500 group-hover:text-zinc-200 transition-colors truncate flex-1" style="font-size:10px">${r.name}</span>
        <span class="font-mono shrink-0" style="font-size:9px;color:#713f12">${r.stars}</span>
      </a>`).join('');
  }else{sl.innerHTML=_emptyMsg('No starred repos');}

  // --- Followers ---
  const fl=document.getElementById('followersMiniList');
  if(followers&&followers.length){
    fl.innerHTML=followers.slice(0,8).map(f=>`
      <a href="${f.url}" target="_blank" rel="noopener" class="flex items-center gap-1.5 group min-w-0" title="@${f.login}">
        <img src="${f.avatar_url}" class="shrink-0 rounded-full" style="width:14px;height:14px" alt="${f.login}" loading="lazy"/>
        <span class="font-mono text-zinc-500 group-hover:text-zinc-200 transition-colors truncate" style="font-size:10px">@${f.login}</span>
      </a>`).join('');
  }else{fl.innerHTML=_emptyMsg('No followers yet');}

  // --- Following ---
  const fwl=document.getElementById('followingMiniList');
  if(following&&following.length){
    fwl.innerHTML=following.slice(0,8).map(f=>`
      <a href="${f.url}" target="_blank" rel="noopener" class="flex items-center gap-1.5 group min-w-0" title="@${f.login}">
        <img src="${f.avatar_url}" class="shrink-0 rounded-full" style="width:14px;height:14px" alt="${f.login}" loading="lazy"/>
        <span class="font-mono text-zinc-500 group-hover:text-zinc-200 transition-colors truncate" style="font-size:10px">@${f.login}</span>
      </a>`).join('');
  }else{fwl.innerHTML=_emptyMsg('Not following anyone');}
}

// ============================================================
// ACTIVITY HOURS (7x24)
// ============================================================
function buildActivityHours(grid){
  const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const maxVal=Math.max(...grid.flat(),1);
  function cellBg(v){
    const p=v/maxVal;
    if(p>.75)return'rgba(139,92,246,0.9)';
    if(p>.5)return'rgba(139,92,246,0.6)';
    if(p>.2)return'rgba(139,92,246,0.3)';
    if(p>0)return'rgba(139,92,246,0.12)';
    return'rgba(255,255,255,0.03)';
  }
  let html='<div class="overflow-x-auto">';
  html+='<div class="flex mb-1 ml-8">';
  for(let h=0;h<24;h+=6)html+=`<div style="flex:6 0 0;text-align:center;font-size:9px;font-family:\'JetBrains Mono\',monospace;color:#52525b">${h}h</div>`;
  html+='</div>';
  grid.forEach((row,di)=>{
    html+=`<div class="flex items-center gap-0.5 mb-0.5">`;
    html+=`<span style="font-size:9px;font-family:\'JetBrains Mono\',monospace;color:#52525b;width:2rem;text-align:right;padding-right:4px;flex-shrink:0">${days[di]}</span>`;
    row.forEach(v=>{
      html+=`<div style="flex:1;height:14px;border-radius:2px;background:${cellBg(v)}" title="${v} events"></div>`;
    });
    html+='</div>';
  });
  html+='</div>';
  document.getElementById('activityHoursGrid').innerHTML=html;
}

// ============================================================
// TECH TAG CLOUD
// ============================================================
function buildTagCloud(topics){
  const el=document.getElementById('tagCloud');
  const sec=document.getElementById('tagCloudSection');
  const entries=Object.entries(topics);
  if(!entries.length){sec.classList.add('hidden');return;}
  sec.classList.remove('hidden');
  const maxC=entries[0][1];
  el.innerHTML=entries.map(([tag,count])=>{
    const size=0.6+(count/maxC)*0.55;
    const op=0.45+(count/maxC)*0.55;
    return`<span class="tag-chip px-1.5 py-0.5 rounded border border-white/10 cursor-default"
      style="font-size:${size}rem;opacity:${op};font-family:'JetBrains Mono',monospace;color:#a1a1aa"
      title="${count} repo${count!==1?'s':''}">#${tag}</span>`;
  }).join('');
}

// ============================================================
// LANGUAGE EVOLUTION CHART
// ============================================================
let langEvoInst=null;
function buildLangEvolution(data){
  const years=Object.keys(data);
  const sec=document.getElementById('langEvoSection');
  if(!years.length){sec.classList.add('hidden');return;}
  sec.classList.remove('hidden');
  const allLangs=[...new Set(years.flatMap(y=>Object.keys(data[y])))];
  const datasets=allLangs.map(lang=>({
    label:lang,
    data:years.map(y=>data[y][lang]||0),
    backgroundColor:getLC(lang)+'99',
    borderColor:getLC(lang),
    borderWidth:1,
  }));
  const canvas=document.getElementById('langEvoChart');
  if(langEvoInst){langEvoInst.destroy();langEvoInst=null;}
  langEvoInst=new Chart(canvas.getContext('2d'),{
    type:'bar',
    data:{labels:years,datasets},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'rgba(255,255,255,0.5)',font:{family:'JetBrains Mono',size:9},boxWidth:8,padding:8}},
        tooltip:{backgroundColor:'rgba(9,9,11,0.92)',borderColor:'rgba(34,211,238,0.3)',borderWidth:1,
          titleFont:{family:'JetBrains Mono',size:11},bodyFont:{family:'JetBrains Mono',size:11}}},
      scales:{
        x:{stacked:true,grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'rgba(255,255,255,0.45)',font:{family:'JetBrains Mono',size:10}}},
        y:{stacked:true,grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'rgba(255,255,255,0.45)',font:{family:'JetBrains Mono',size:10}}}
      }}
  });
}

// ============================================================
// GIST SECTION
// ============================================================
function buildGistSection(gists){
  const el=document.getElementById('gistCard');
  if(!gists||gists.total===0){el.classList.add('hidden');return;}
  el.classList.remove('hidden');
  animCount(document.getElementById('gistTotal'),gists.total);
  animCount(document.getElementById('gistComments'),gists.total_comments);
  document.getElementById('gistLang').textContent=gists.top_language||'—';
  if(gists.most_forked){
    document.getElementById('gistMostForked').innerHTML=
      `<a href="${gists.most_forked.url}" target="_blank" rel="noopener" class="text-cyan-400 hover:underline">${gists.most_forked.description}</a>
       <span class="text-zinc-600 ml-1">(${gists.most_forked.forks} forks)</span>`;
  }
}

// ============================================================
// RADAR CHART
// ============================================================
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

// ============================================================
// LANG BARS
// ============================================================
function buildBars(langs){
  const c=document.getElementById('langBars');c.innerHTML='';
  const e=Object.entries(langs);const max=e[0]?.[1]||1;const tot=e.reduce((s,[,v])=>s+v,0);
  e.forEach(([lang,bytes])=>{
    const pct=Math.round(bytes/tot*100);const bp=Math.round(bytes/max*100);const col=getLC(lang);const kb=(bytes/1024).toFixed(0);
    const row=document.createElement('div');row.className='group';
    row.innerHTML=`<div class="flex items-center justify-between mb-1.5"><div class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm shrink-0" style="background:${col};box-shadow:0 0 6px ${col}66;"></span><span class="font-mono text-sm text-zinc-300 font-semibold">${lang}</span></div><div class="flex items-center gap-3"><span class="font-mono text-xs text-zinc-500">${kb} KB</span><span class="font-mono text-xs font-bold" style="color:${col};">${pct}%</span></div></div><div class="w-full bg-white/5 rounded-full h-1.5 overflow-hidden"><div class="lang-bar h-full rounded-full" style="width:${bp}%;background:linear-gradient(90deg,${col}cc,${col});box-shadow:0 0 8px ${col}66;"></div></div>`;
    c.appendChild(row);
  });
}

// ============================================================
// REPO CARDS (v2 — richer info)
// ============================================================
function buildRepos(repos){
  const c=document.getElementById('repoList');c.innerHTML='';
  if(!repos.length){c.innerHTML='<p class="col-span-3 text-center text-zinc-600 font-mono text-sm py-8">No public repositories found.</p>';return;}
  repos.forEach(r=>{
    const col=getLC(r.language||'Unknown');
    const topics=r.topics.map(t=>`<span class="px-1.5 py-0.5 rounded-full bg-white/5 text-zinc-500 font-mono text-xs">${t}</span>`).join('');
    const sizeStr=r.size>1024?`${(r.size/1024).toFixed(1)}MB`:`${r.size}KB`;
    const updated=r.updated_at?r.updated_at.slice(0,7):'';
    const card=document.createElement('a');
    card.href=r.url;card.target='_blank';card.rel='noopener noreferrer';
    card.className='repo-card block glass border border-white/5 rounded-xl p-4 cursor-pointer no-underline';
    card.innerHTML=`
      <div class="flex items-start justify-between gap-2 mb-2">
        <h3 class="font-mono text-sm font-bold text-cyan-300 truncate">${r.name}</h3>
        <svg class="shrink-0 mt-0.5 opacity-40" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x2="21" y1="14" y2="3"/></svg>
      </div>
      <p class="text-xs text-zinc-500 leading-relaxed mb-3 line-clamp-2">${r.description}</p>
      <div class="flex flex-wrap gap-1 mb-3">${topics}</div>
      <div class="grid grid-cols-3 gap-1.5 text-xs font-mono mb-2">
        <span class="flex items-center gap-1 text-yellow-400"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>${r.stars}</span>
        <span class="flex items-center gap-1 text-zinc-500"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><path d="M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9"/><path d="M12 12v3"/></svg>${r.forks}</span>
        <span class="flex items-center gap-1 text-zinc-600"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>${r.open_issues}</span>
      </div>
      <div class="flex items-center justify-between pt-2 border-t border-white/5">
        <span class="flex items-center gap-1 text-xs" style="color:${col}"><span class="w-2 h-2 rounded-full" style="background:${col}"></span>${r.language}</span>
        <span class="font-mono text-xs text-zinc-600">${sizeStr} · ${updated}</span>
      </div>`;
    c.appendChild(card);
  });
}

// ============================================================
// COMPARE MODE
// ============================================================
function openCompareModal(){
  document.getElementById('compareModal').classList.remove('hidden');
  document.getElementById('compareModal').classList.add('flex');
  document.getElementById('compareInputA').value='';
  document.getElementById('compareInputB').value='';
}
function closeCompareModal(){
  document.getElementById('compareModal').classList.add('hidden');
  document.getElementById('compareModal').classList.remove('flex');
}

async function runCompare(){
  const ua=document.getElementById('compareInputA').value.trim();
  const ub=document.getElementById('compareInputB').value.trim();
  if(!ua||!ub)return;
  closeCompareModal();
  const token=localStorage.getItem('gs_token')||'';
  const cSec=document.getElementById('compareSection');
  const cContent=document.getElementById('compareSectionContent');
  cSec.classList.remove('hidden');
  cContent.innerHTML='<div class="text-center py-20 font-mono text-cyan-400 animate-pulse text-lg tracking-widest">DUAL SCAN IN PROGRESS...</div>';
  cSec.scrollIntoView({behavior:'smooth',block:'start'});
  try{
    const resp=await fetch('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username_a:ua,username_b:ub,github_token:token||null})});
    const data=await resp.json();
    if(!resp.ok)throw new Error(data.detail||`HTTP ${resp.status}`);
    renderCompare(data);
  }catch(err){
    cContent.innerHTML=`<p class="text-red-400 font-mono text-center py-10 text-sm">ERROR: ${err.message}</p>`;
  }
}

function renderCompare(data){
  const{user_a,user_b}=data;
  const cContent=document.getElementById('compareSectionContent');

  function miniCard(u){
    const{profile,stats,score,archetype,languages,streaks}=u;
    const langE=Object.entries(languages).slice(0,5);
    const tot=langE.reduce((s,[,v])=>s+v,0)||1;
    const gradeColors={'S+':'#f59e0b','S':'#10b981','A':'#06b6d4','B':'#8b5cf6','C':'#f97316','D':'#ef4444','E':'#6b7280'};
    const scoreCol=gradeColors[score.grade]||'#22d3ee';
    const r=36,circ=2*Math.PI*r;
    return`<div class="glass grad-border rounded-2xl p-6">
      <div class="flex items-center gap-4 mb-5">
        <img src="${profile.avatar_url}" class="w-16 h-16 rounded-xl border-2 border-cyan-500/30 object-cover" alt="${profile.login}"/>
        <div class="min-w-0">
          <h3 class="font-black text-lg truncate">${profile.name}</h3>
          <p class="font-mono text-cyan-400 text-sm">@${profile.login}</p>
          <span class="inline-flex mt-1 font-mono text-xs font-bold px-2 py-0.5 rounded-full border"
            style="background:${archetype.glow}22;border-color:${archetype.glow}55;color:${archetype.glow}">${archetype.label}</span>
        </div>
      </div>
      <div class="flex items-center gap-4 mb-5">
        <div class="relative shrink-0" style="width:80px;height:80px">
          <svg width="80" height="80" class="-rotate-90">
            <circle cx="40" cy="40" r="${r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8"/>
            <circle cx="40" cy="40" r="${r}" fill="none" stroke="${scoreCol}" stroke-width="8"
              stroke-dasharray="${circ}" stroke-dashoffset="${circ*(1-score.total/1000)}"
              stroke-linecap="round" style="filter:drop-shadow(0 0 6px ${scoreCol}66)"/>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <span class="font-black text-sm leading-none">${score.total}</span>
            <span class="font-black text-xs" style="color:${scoreCol}">${score.grade}</span>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 flex-1">
          <div class="text-center"><p class="font-black text-base text-cyan-400">${stats.own_repos}</p><p class="font-mono text-xs text-zinc-600">Repos</p></div>
          <div class="text-center"><p class="font-black text-base text-yellow-400">${stats.total_stars}</p><p class="font-mono text-xs text-zinc-600">Stars</p></div>
          <div class="text-center"><p class="font-black text-base text-violet-400">${profile.followers}</p><p class="font-mono text-xs text-zinc-600">Followers</p></div>
          <div class="text-center"><p class="font-black text-base text-orange-400">${streaks.current||0}d</p><p class="font-mono text-xs text-zinc-600">Streak</p></div>
        </div>
      </div>
      <div class="space-y-2">
        ${langE.map(([l,b])=>{const p=Math.round(b/tot*100);const col=getLC(l);return`<div><div class="flex justify-between mb-0.5"><span class="font-mono text-xs text-zinc-400">${l}</span><span class="font-mono text-xs text-zinc-600">${p}%</span></div><div class="bg-white/5 rounded-full h-1 overflow-hidden"><div class="h-full rounded-full" style="width:${p}%;background:${col}"></div></div></div>`;}).join('')}
      </div>
    </div>`;
  }

  const metrics=[
    {label:'Dev Score',a:user_a.score.total,b:user_b.score.total},
    {label:'Stars',a:user_a.stats.total_stars,b:user_b.stats.total_stars},
    {label:'Followers',a:user_a.profile.followers,b:user_b.profile.followers},
    {label:'Repos',a:user_a.stats.own_repos,b:user_b.stats.own_repos},
    {label:'Languages',a:Object.keys(user_a.languages).length,b:Object.keys(user_b.languages).length},
    {label:'Streak',a:user_a.streaks.current||0,b:user_b.streaks.current||0},
  ];

  cContent.innerHTML=`
    <div class="grid grid-cols-1 lg:grid-cols-[1fr_180px_1fr] gap-6 items-start">
      <div class="fade-up" style="animation-delay:0s">${miniCard(user_a)}</div>
      <div class="flex flex-col items-center py-4 lg:py-8">
        <div class="font-black text-4xl text-zinc-700 mb-6">VS</div>
        <div class="space-y-2 w-full">
          ${metrics.map(m=>{
            const aW=m.a>m.b,bW=m.b>m.a;
            return`<div class="glass rounded-lg py-2 px-3 text-center">
              <p class="font-mono text-xs text-zinc-600 mb-1">${m.label}</p>
              <div class="flex items-center justify-between">
                <span class="font-black text-sm ${aW?'text-cyan-400':'text-zinc-600'}">${m.a.toLocaleString()}</span>
                <span class="font-mono text-xs text-zinc-700">${aW?'←':bW?'→':'='}</span>
                <span class="font-black text-sm ${bW?'text-cyan-400':'text-zinc-600'}">${m.b.toLocaleString()}</span>
              </div>
            </div>`;
          }).join('')}
        </div>
      </div>
      <div class="fade-up" style="animation-delay:0.1s">${miniCard(user_b)}</div>
    </div>`;
}

// ============================================================
// EXPORT PDF
// ============================================================
let currentUsername='';
async function exportPDF(){
  const btn=document.getElementById('exportBtn');
  const btn2=document.getElementById('exportBtn2');
  [btn,btn2].forEach(b=>{if(b){b.textContent='GENERATING...';b.disabled=true;}});
  try{
    const el=document.getElementById('dossier');
    const canvas=await html2canvas(el,{backgroundColor:'#09090b',scale:1.5,useCORS:true,allowTaint:true,logging:false});
    const{jsPDF}=window.jspdf;
    const w=canvas.width/1.5,h=canvas.height/1.5;
    const pdf=new jsPDF({orientation:w>h?'landscape':'portrait',unit:'px',format:[w,h]});
    pdf.addImage(canvas.toDataURL('image/png'),'PNG',0,0,w,h);
    pdf.save(`git-spectre-${currentUsername||'report'}.pdf`);
  }catch(e){
    console.error('PDF export error:',e);
    alert('PDF export failed. Please try on a modern Chromium browser.');
  }finally{
    [btn,btn2].forEach(b=>{if(b){b.textContent='EXPORT PDF';b.disabled=false;}});
  }
}

// ============================================================
// SHAREABLE URL
// ============================================================
function updateShareURL(username){
  currentUsername=username;
  const url=new URL(window.location.href);
  url.searchParams.set('u',username);
  window.history.pushState({},'',url.toString());
}

function copyShareLink(){
  const url=window.location.href;
  navigator.clipboard.writeText(url).then(()=>{
    const btn=document.getElementById('shareBtn');
    const orig=btn.innerHTML;
    btn.innerHTML='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> COPIED!';
    btn.style.color='#22d3ee';
    setTimeout(()=>{btn.innerHTML=orig;btn.style.color='';},2000);
  }).catch(()=>alert('Copy: '+url));
}

function initFromURL(){
  const params=new URLSearchParams(window.location.search);
  const u=params.get('u')||params.get('username');
  if(u){document.getElementById('searchInput').value=u;runScan();}
}

// ============================================================
// MAIN SCAN
// ============================================================
async function runScan(){
  const username=document.getElementById('searchInput').value.trim();
  if(!username)return;
  const eb=document.getElementById('errorBox');eb.classList.add('hidden');eb.textContent='';
  document.getElementById('scanTarget').textContent=`> Initiating deep scan on: ${username}`;
  document.getElementById('scanOverlay').classList.remove('hidden');
  document.getElementById('dossier').classList.add('hidden');
  document.getElementById('compareSection').classList.add('hidden');
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

// ============================================================
// RENDER DOSSIER (v2)
// ============================================================
function renderDossier(data){
  const{profile,stats,languages,archetype,top_repos,score,heatmap,activity_hours,streaks,topics,lang_evolution,gists,orgs,cached,followers_list,following_list}=data;

  // Cached badge
  const cb=document.getElementById('cachedBadge');
  if(cached){cb.classList.remove('hidden');document.getElementById('cachedTime').textContent='last 5 min';}
  else{cb.classList.add('hidden');}

  // Profile
  document.getElementById('avatar').src=profile.avatar_url;
  const ne=document.getElementById('profileName');ne.textContent=profile.name;ne.href=profile.html_url;
  document.getElementById('profileLogin').textContent=`@${profile.login}`;
  document.getElementById('profileBio').textContent=profile.bio;
  document.getElementById('archetypeDesc').textContent=archetype.description;

  const locSvg='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>';
  const bizSvg='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>';
  const calSvg='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>';
  const lnkSvg='<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';

  document.getElementById('metaLocation').innerHTML=locSvg+profile.location;
  document.getElementById('metaCompany').innerHTML=bizSvg+profile.company;
  document.getElementById('metaJoined').innerHTML=calSvg+'Since '+profile.created_at;
  const blogEl=document.getElementById('metaBlog');
  if(profile.blog){blogEl.innerHTML=`${lnkSvg}<a href="${profile.blog.startsWith('http')?profile.blog:'https://'+profile.blog}" target="_blank" rel="noopener" class="hover:text-cyan-400 transition-colors">${profile.blog.replace(/^https?:\/\//,'').slice(0,28)}</a>`;}
  else{blogEl.innerHTML='';}

  const badge=document.getElementById('archetypeBadge');
  badge.textContent=archetype.label;
  badge.style.cssText=`background:linear-gradient(135deg,${archetype.glow}22,${archetype.glow}11);border-color:${archetype.glow}55;color:${archetype.glow};box-shadow:0 0 12px ${archetype.glow}33;`;

  // Stats
  animCount(document.getElementById('statRepos'),stats.total_repos);
  animCount(document.getElementById('statStars'),stats.total_stars);
  animCount(document.getElementById('statFollowers'),profile.followers);
  animCount(document.getElementById('statFollowing'),profile.following);

  // v2 sections
  buildScoreRing(score);
  buildOrgs(orgs);
  buildStreaks(streaks);
  buildHeatmap(heatmap);
  buildActivityHours(activity_hours);
  buildTagCloud(topics);
  buildLangEvolution(lang_evolution);
  buildGistSection(gists);
  buildStatLists(top_repos,followers_list||[],following_list||[]);

  // Charts
  const entries=Object.entries(languages);
  if(entries.length){buildRadar(entries.map(([k])=>k),entries.map(([,v])=>Math.round(v)));buildBars(languages);}
  buildRepos(top_repos);

  // Share URL
  updateShareURL(profile.login);

  // Show dossier + export buttons
  document.getElementById('scanOverlay').classList.add('hidden');
  document.getElementById('dossier').classList.remove('hidden');
  document.getElementById('exportBtn').classList.remove('hidden');
  document.getElementById('exportBtn').classList.add('flex');
  document.getElementById('exportBtn2').classList.remove('hidden');
  document.getElementById('exportBtn2').classList.add('flex');
  document.getElementById('heroSection').classList.add('hidden');

  setTimeout(()=>document.getElementById('dossier').scrollIntoView({behavior:'smooth',block:'start'}),100);
  refreshRateLimit();
}

// ============================================================
// INIT
// ============================================================
window.addEventListener('load',()=>{
  refreshRateLimit();
  initFromURL();
});
</script>
</body>
</html>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f'index.html written — {len(HTML):,} chars')