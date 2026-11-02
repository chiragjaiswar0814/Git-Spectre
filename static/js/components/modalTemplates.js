/**
 * Modal Templates Component
 * Markup definitions and DOM mounting for Vault, Compare, Batch, and Wrapped modals.
 */

export function mountModalTemplates() {
	if (document.getElementById("vaultModal")) return;

	const container = document.createElement("div");
	container.id = "modalsContainer";
	container.innerHTML = `
    <!-- API Vault Modal -->
    <div id="vaultModal" class="hidden modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div class="relative w-full max-w-md max-h-[calc(100vh-2rem)] overflow-y-auto rounded-2xl border border-line bg-surface shadow-2xl p-5 sm:p-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div class="flex items-start justify-between border-b border-line pb-4 mb-5">
          <div>
            <h2 class="font-mono text-sm font-semibold tracking-wider text-ink uppercase">API Vault</h2>
            <p class="text-xs text-muted mt-0.5">Store a GitHub Personal Access Token in localStorage.</p>
          </div>
          <button type="button" data-close-modal="vaultModal" class="text-muted hover:text-ink text-lg font-bold">×</button>
        </div>
        <div class="flex items-center justify-between rounded-xl border border-line bg-raised/50 px-4 py-2.5 mb-4 text-xs">
          <span class="flex items-center gap-2 text-ink font-medium">
            <span class="h-2 w-2 rounded-full bg-lime"></span>
            <span id="vaultStatusText">Checking token...</span>
          </span>
          <span id="vaultStatusLimit" class="font-mono text-muted">60 req/hr</span>
        </div>
        <label class="block text-xs font-mono text-muted mb-1.5 uppercase tracking-wider">GitHub Personal Access Token</label>
        <div class="flex items-center rounded-xl border border-line bg-canvas pr-1 mb-2">
          <input id="vaultTokenInput" type="password" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" class="w-full bg-transparent px-3 py-2.5 font-mono text-sm text-ink outline-none" />
          <button type="button" id="vaultTokenToggle" class="px-2 text-muted hover:text-ink text-sm flex items-center justify-center" aria-label="Toggle password visibility">
            <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
        </div>
        <p id="vaultError" class="text-xs text-danger font-mono mb-2"></p>
        <p class="text-[12px] text-muted leading-relaxed mb-5">Stored strictly in your browser. Bumps the API limit from 60 to 5,000 requests/hour.</p>
        <div class="flex gap-3">
          <button type="button" id="vaultSaveBtn" class="flex-1 py-2.5 rounded-xl bg-lime font-mono text-xs font-bold text-onlime hover:brightness-105 active:scale-95 transition-all">LOCK IN TOKEN</button>
          <button type="button" id="vaultPurgeBtn" class="px-4 py-2.5 rounded-xl border border-danger/40 font-mono text-xs text-danger hover:bg-danger/10 active:scale-95 transition-colors">PURGE</button>
        </div>
      </div>
    </div>

    <!-- Compare Modal -->
    <div id="compareModal" class="hidden modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div class="relative w-full max-w-lg max-h-[calc(100vh-2rem)] overflow-y-auto rounded-2xl border border-line bg-surface shadow-2xl p-5 sm:p-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div class="flex items-start justify-between border-b border-line pb-4 mb-5">
          <div>
            <h2 class="font-mono text-sm font-semibold tracking-wider text-ink uppercase">Dual Target Scan</h2>
            <p class="text-xs text-muted mt-0.5">Compare two developers side by side.</p>
          </div>
          <button type="button" data-close-modal="compareModal" class="text-muted hover:text-ink text-lg font-bold">×</button>
        </div>
        <form id="compareForm" class="space-y-4">
          <div>
            <label class="block font-mono text-xs text-muted mb-1 uppercase tracking-wider">Target Alpha (User A)</label>
            <input id="compareInputA" type="text" placeholder="e.g. torvalds" class="w-full rounded-xl border border-line bg-canvas px-3.5 py-2.5 font-mono text-sm text-ink outline-none focus:border-accent" />
          </div>
          <div>
            <label class="block font-mono text-xs text-muted mb-1 uppercase tracking-wider">Target Beta (User B)</label>
            <input id="compareInputB" type="text" placeholder="e.g. gvanrossum" class="w-full rounded-xl border border-line bg-canvas px-3.5 py-2.5 font-mono text-sm text-ink outline-none focus:border-accent" />
          </div>
          <p id="compareError" class="text-xs text-danger font-mono"></p>
          <button type="submit" class="w-full py-3 rounded-xl bg-lime font-mono text-xs font-bold text-onlime hover:brightness-105 active:scale-95 transition-all">INITIATE DUAL SCAN</button>
        </form>
      </div>
    </div>

    <!-- Batch Screener Modal -->
    <div id="batchModal" class="hidden modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm">
      <div class="relative w-full max-w-2xl sm:max-w-3xl lg:max-w-4xl max-h-[calc(100vh-2rem)] overflow-y-auto rounded-2xl border border-line bg-surface shadow-2xl p-5 sm:p-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div class="flex items-start justify-between border-b border-line pb-4 mb-4">
          <div>
            <h2 class="font-mono text-sm font-semibold tracking-wider text-ink uppercase">Batch Screener</h2>
            <p class="text-xs text-muted mt-0.5">Rank up to 10 profiles by Developer Score™. One target per line.</p>
          </div>
          <button type="button" data-close-modal="batchModal" class="text-muted hover:text-ink text-lg font-bold">×</button>
        </div>
        <div id="batchFormView">
          <form id="batchForm" class="space-y-4">
            <textarea id="batchTextarea" rows="6" placeholder="torvalds&#10;gvanrossum&#10;antirez&#10;https://github.com/karpathy" class="w-full resize-none rounded-xl border border-line bg-canvas px-3.5 py-3 font-mono text-sm text-ink outline-none focus:border-accent"></textarea>
            <p id="batchError" class="text-xs text-danger font-mono"></p>
            <button type="submit" id="batchRunBtn" class="w-full py-3 rounded-xl bg-lime font-mono text-xs font-bold text-onlime hover:brightness-105 active:scale-95 transition-all">INITIATE BATCH SCAN</button>
          </form>
        </div>
        <div id="batchResultsView" class="hidden">
          <div class="flex items-center justify-between pb-3">
            <button type="button" id="batchBackBtn" class="text-xs text-muted hover:text-ink font-mono">&larr; Edit targets</button>
            <span class="text-xs text-muted font-mono">Click a row to inspect</span>
          </div>
          <div class="scroll-thin overflow-x-auto max-h-96">
            <table class="w-full min-w-[620px] text-left text-xs font-mono">
              <thead>
                <tr class="border-y border-line text-muted">
                  <th class="px-4 py-2.5 w-10 text-center">#</th>
                  <th class="px-4 py-2.5 min-w-[170px]">Developer</th>
                  <th class="px-4 py-2.5 whitespace-nowrap min-w-[110px]">Score</th>
                  <th class="px-4 py-2.5 whitespace-nowrap min-w-[140px]">Archetype</th>
                  <th class="px-4 py-2.5 whitespace-nowrap">Top Lang</th>
                  <th class="px-4 py-2.5 text-right whitespace-nowrap">Stars</th>
                  <th class="px-4 py-2.5 text-right whitespace-nowrap">Followers</th>
                </tr>
              </thead>
              <tbody id="batchTableBody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- GitHub Wrapped Modal -->
    <div id="wrappedModal" class="hidden modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md">
      <div class="relative w-full max-w-2xl max-h-[calc(100vh-2rem)] overflow-y-auto rounded-3xl p-5 sm:p-10 text-white shadow-2xl [scrollbar-width:none] [&::-webkit-scrollbar]:hidden" style="background: linear-gradient(140deg, #2a1572 0%, #5b3be8 45%, #8b6cff 70%, #c6f432 130%);">
        <div id="wrappedConfetti" class="absolute inset-0 overflow-hidden pointer-events-none"></div>
        <button type="button" data-close-modal="wrappedModal" class="absolute right-4 top-4 sm:right-5 sm:top-5 z-20 grid h-8 w-8 place-items-center rounded-full bg-white/10 text-white hover:bg-white/20 active:scale-95 transition-all">×</button>
        <div class="relative z-10">
          <div class="flex items-center gap-3">
            <img id="wrappedAvatar" src="" alt="" class="h-10 w-10 rounded-full ring-2 ring-white/40 object-cover" />
            <span id="wrappedLogin" class="font-mono text-xs tracking-widest text-white/80"></span>
          </div>
          <h2 class="mt-4 sm:mt-5 text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">Your Year,<br />Unwrapped.</h2>
          <div class="mt-6 sm:mt-8 grid gap-3 sm:grid-cols-4">
            <div class="rounded-2xl bg-lime p-4 sm:p-5 text-onlime flex flex-col justify-between sm:col-span-2 sm:row-span-2">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wider opacity-75">Contributions This Year</p>
                <p id="wrappedCommits" class="mt-2 font-mono text-4xl sm:text-5xl font-black tabular-nums">0</p>
              </div>
              <div class="mt-3 sm:mt-4">
                <p class="text-xs font-semibold uppercase tracking-wider opacity-75">Biggest Repository</p>
                <p id="wrappedBiggestRepo" class="font-mono text-base sm:text-lg font-bold truncate">—</p>
              </div>
            </div>
            <div id="wrappedTilesContainer" class="contents"></div>
          </div>
          <div class="mt-6 sm:mt-8 flex items-center justify-between border-t border-white/15 pt-4">
            <span class="font-mono text-[11px] tracking-widest text-white/70">GIT-SPECTRE // 2026</span>
            <button type="button" id="wrappedShareBtn" class="rounded-full bg-white px-5 py-2 font-mono text-xs font-bold text-[#2A1572] hover:bg-white/90 active:scale-95 transition-all">Share Card</button>
          </div>
        </div>
      </div>
    </div>

    <!-- GitHub Profile Badge Studio Modal -->
    <div id="badgeModal" class="hidden modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-sm">
      <div class="relative w-full max-w-2xl max-h-[calc(100vh-2rem)] overflow-y-auto rounded-2xl border border-line bg-surface shadow-2xl p-4 sm:p-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div class="flex items-start justify-between border-b border-line pb-4 mb-5">
          <div>
            <div class="flex items-center gap-2">
              <h2 class="font-mono text-xs sm:text-sm font-semibold tracking-wider text-ink uppercase">GitHub Badge</h2>
            </div>
            <p class="text-xs text-muted mt-0.5">Embed stats directly in your GitHub Profile README.</p>
          </div>
          <button type="button" data-close-modal="badgeModal" class="text-muted hover:text-ink text-lg font-bold">×</button>
        </div>

        <!-- Live Preview Stage -->
        <div class="relative flex min-h-[140px] sm:min-h-[160px] items-center justify-center rounded-xl border border-line bg-canvas/80 p-3 sm:p-5 overflow-hidden mb-5">
          <div id="badgePreviewContainer" class="flex items-center justify-center w-full max-w-lg transition-all overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <div class="text-xs font-mono text-muted animate-pulse">Rendering preview...</div>
          </div>
        </div>

        <!-- Options Configuration -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
          <!-- Format / Style -->
          <div>
            <label class="block font-mono text-[11px] text-muted mb-1.5 uppercase tracking-wider">Format</label>
            <select id="badgeFormatSelect" class="w-full rounded-xl border border-line bg-canvas px-3 py-2 font-mono text-xs text-ink outline-none focus:border-accent">
              <option value="card" selected>Profile Badge (README)</option>
              <option value="pill">Compact Pill (Shields)</option>
              <option value="cyber">Cyber Pill (Tactical)</option>
              <option value="for-the-badge">Chunky (For-The-Badge)</option>
            </select>
          </div>

          <!-- Metric (for pills) -->
          <div id="badgeMetricGroup">
            <label class="block font-mono text-[11px] text-muted mb-1.5 uppercase tracking-wider">Metric</label>
            <select id="badgeMetricSelect" class="w-full rounded-xl border border-line bg-canvas px-3 py-2 font-mono text-xs text-ink outline-none focus:border-accent">
              <option value="score" selected>Dev Score &amp; Tier</option>
              <option value="rank">Global Rank</option>
              <option value="archetype">Archetype</option>
              <option value="streak">Active Streak</option>
              <option value="level">Dev Level</option>
            </select>
          </div>

          <!-- Theme -->
          <div>
            <label class="block font-mono text-[11px] text-muted mb-1.5 uppercase tracking-wider">Theme</label>
            <select id="badgeThemeSelect" class="w-full rounded-xl border border-line bg-canvas px-3 py-2 font-mono text-xs text-ink outline-none focus:border-accent">
              <option value="spectre" selected>Spectre (Dark Neon)</option>
              <option value="dark">GitHub Dark</option>
              <option value="tokyo">Tokyo Night</option>
              <option value="matrix">Hacker Matrix</option>
              <option value="light">Clean Light</option>
            </select>
          </div>
        </div>

        <!-- Embed Snippet Box -->
        <div class="space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="font-mono text-[11px] text-muted uppercase tracking-wider">Snippet Output</span>
            <div class="flex flex-wrap gap-1.5 sm:gap-2">
              <button type="button" id="badgeCopyMdBtn" class="inline-flex items-center gap-1.5 rounded-lg bg-lime px-2.5 sm:px-3 py-1.5 font-mono text-xs font-bold text-onlime hover:brightness-105 active:scale-95 transition-all">
                Copy Markdown
              </button>
              <button type="button" id="badgeCopyHtmlBtn" class="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 sm:px-3 py-1.5 font-mono text-xs font-medium text-ink hover:bg-raised active:scale-95 transition-colors">
                HTML
              </button>
              <button type="button" id="badgeCopyUrlBtn" class="inline-flex items-center gap-1.5 rounded-lg border border-line px-2.5 sm:px-3 py-1.5 font-mono text-xs font-medium text-ink hover:bg-raised active:scale-95 transition-colors">
                Raw URL
              </button>
            </div>
          </div>
          <div class="relative">
            <input id="badgeSnippetInput" readonly type="text" class="w-full rounded-xl border border-line bg-canvas px-3.5 py-2.5 font-mono text-xs text-ink select-all outline-none" />
          </div>
        </div>

      </div>
    </div>
  `;

	document.body.appendChild(container);
}
