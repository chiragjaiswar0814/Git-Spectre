/**
 * Language DNA & Radar Component
 * Interactive SVG Language Radar with dual metric toggle (KB vs repo count), language bars, and topic cloud.
 */

import { esc, getLangColor } from '../utils.js';
import { appState } from '../state.js';

const SIZE = 280;
const CENTER = SIZE / 2;
const RADIUS = 96;

function getPoint(index, total, ratio) {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / total;
  return {
    x: CENTER + Math.cos(angle) * RADIUS * ratio,
    y: CENTER + Math.sin(angle) * RADIUS * ratio
  };
}

export function renderRadarDna(dossier) {
  const container = document.getElementById('radarDnaContainer');
  if (!container) return;

  const rawLangs = dossier.languages || {};
  const rawCounts = dossier.lang_repo_counts || {};
  const rawTopics = dossier.topics || {};
  const topics = Array.isArray(rawTopics)
    ? rawTopics.map(t => (typeof t === 'string' ? { tag: t, count: 1 } : t))
    : Object.entries(rawTopics).map(([tag, count]) => ({ tag, count }));

  const langEntries = Object.entries(rawLangs);
  const totalKb = langEntries.reduce((sum, [, bytes]) => sum + bytes, 0) || 1;

  const languages = langEntries.map(([name, bytes]) => ({
    name,
    kb: Math.round(bytes),
    repos: rawCounts[name] || 1,
    color: getLangColor(name)
  }));

  const maxTopic = Math.max(1, ...topics.map(t => t.count || 1));

  function renderRadarSvg(mode) {
    const n = Math.max(3, languages.length);
    if (!languages.length) {
      return '<div class="h-64 grid place-items-center text-xs text-muted font-mono">No language data</div>';
    }

    const values = languages.map(l => (mode === 'kb' ? Math.sqrt(l.kb) : l.repos));
    const maxVal = Math.max(1, ...values);
    const points = values.map((v, i) => getPoint(i, n, Math.max(0.08, v / maxVal)));
    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ' Z';

    // Ring webs
    const ringWebs = [0.25, 0.5, 0.75, 1.0].map(ratio => {
      const ringPts = Array.from({ length: n }, (_, i) => getPoint(i, n, ratio))
        .map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
      return `<polygon points="${ringPts}" class="fill-none stroke-line" stroke-width="1" />`;
    }).join('');

    // Spokes
    const spokes = languages.map((_, i) => {
      const p = getPoint(i, n, 1);
      return `<line x1="${CENTER}" y1="${CENTER}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" class="stroke-line" stroke-width="1" />`;
    }).join('');

    // Dots
    const dots = points.map((p, i) =>
      `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="3.5" class="fill-lime stroke-surface transition-all duration-300" stroke-width="1.5" />`
    ).join('');

    // Labels
    const labels = languages.map((l, i) => {
      const p = getPoint(i, n, 1.22);
      const anchor = Math.abs(p.x - CENTER) < 10 ? 'middle' : p.x > CENTER ? 'start' : 'end';
      return `
        <text x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" text-anchor="${anchor}" dominant-baseline="middle"
          class="fill-muted font-mono text-[10px]">
          ${esc(l.name)}
        </text>
      `;
    }).join('');

    return `
      <svg viewBox="0 0 ${SIZE} ${SIZE}" class="mx-auto w-full max-w-[280px]" role="img" aria-label="Language radar">
        ${ringWebs}
        ${spokes}
        <path d="${pathD}" class="fill-accent/20 stroke-accent transition-all duration-300" stroke-width="2" stroke-linejoin="round" />
        ${dots}
        ${labels}
      </svg>
    `;
  }

  container.innerHTML = `
    <section class="rounded-2xl border border-line bg-surface p-3.5 sm:p-7 min-w-0 overflow-hidden">
      <header class="flex flex-wrap items-baseline justify-between gap-3 mb-6">
        <div>
          <h3 class="text-base font-semibold tracking-tight text-ink">Language DNA</h3>
          <p class="mt-0.5 text-xs text-muted">
            ${languages.length} languages · ${(totalKb / 1024).toFixed(1)} MB of authored code
          </p>
        </div>

        <!-- Metric toggle button -->
        <div role="radiogroup" aria-label="Radar metric" class="inline-flex rounded-lg border border-line bg-raised p-0.5 font-mono text-xs">
          <button type="button" id="radarModeKb"
            class="rounded-md px-2.5 py-1 transition-colors duration-150 ${appState.radarMode === 'kb' ? 'bg-surface text-ink shadow-sm font-bold' : 'text-muted hover:text-ink'}">
            KB
          </button>
          <button type="button" id="radarModeCount"
            class="rounded-md px-2.5 py-1 transition-colors duration-150 ${appState.radarMode === 'count' ? 'bg-surface text-ink shadow-sm font-bold' : 'text-muted hover:text-ink'}">
            #
          </button>
        </div>
      </header>

      <div class="grid items-center gap-8 md:grid-cols-2">
        <div id="radarSvgContainer">
          ${renderRadarSvg(appState.radarMode)}
        </div>

        <ul class="space-y-3.5">
          ${languages.map(l => {
            const pct = (l.kb / totalKb) * 100;
            return `
              <li>
                <div class="flex items-baseline justify-between gap-3 text-xs">
                  <span class="flex items-center gap-2 text-ink font-medium">
                    <span class="h-2 w-2 rounded-full" style="background:${l.color}"></span>
                    ${esc(l.name)}
                  </span>
                  <span class="font-mono text-[11px] tabular-nums text-muted">
                    ${l.kb.toLocaleString()} KB · <span class="text-ink font-bold">${pct.toFixed(1)}%</span>
                  </span>
                </div>
                <div class="mt-1.5 h-1 overflow-hidden rounded-full bg-line">
                  <div class="h-full rounded-full transition-all duration-500" style="width:${Math.max(pct, 2)}%; background:${l.color}"></div>
                </div>
              </li>
            `;
          }).join('')}
        </ul>
      </div>

      <!-- Topic Cloud -->
      ${topics.length ? `
        <div class="mt-7 border-t border-line pt-5">
          <h4 class="text-xs text-muted uppercase font-mono tracking-wider">Topic Cloud</h4>
          <ul class="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-2">
            ${topics.map(t => {
              const weight = (t.count || 1) / maxTopic;
              const size = 11 + Math.round(weight * 8);
              return `
                <li class="font-mono ${weight > 0.6 ? 'text-ink font-semibold' : weight > 0.3 ? 'text-ink/80' : 'text-muted'}"
                  style="font-size:${size}px">
                  #${esc(t.tag || t)}
                </li>
              `;
            }).join('')}
          </ul>
        </div>
      ` : ''}
    </section>
  `;

  // Attach toggle listeners
  const btnKb = document.getElementById('radarModeKb');
  const btnCount = document.getElementById('radarModeCount');
  const svgCont = document.getElementById('radarSvgContainer');

  if (btnKb && btnCount && svgCont) {
    btnKb.addEventListener('click', () => {
      appState.radarMode = 'kb';
      btnKb.className = 'rounded-md px-2.5 py-1 transition-colors duration-150 bg-surface text-ink shadow-sm font-bold';
      btnCount.className = 'rounded-md px-2.5 py-1 transition-colors duration-150 text-muted hover:text-ink';
      svgCont.innerHTML = renderRadarSvg('kb');
    });

    btnCount.addEventListener('click', () => {
      appState.radarMode = 'count';
      btnCount.className = 'rounded-md px-2.5 py-1 transition-colors duration-150 bg-surface text-ink shadow-sm font-bold';
      btnKb.className = 'rounded-md px-2.5 py-1 transition-colors duration-150 text-muted hover:text-ink';
      svgCont.innerHTML = renderRadarSvg('count');
    });
  }
}
