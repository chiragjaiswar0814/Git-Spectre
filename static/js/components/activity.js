/**
 * Activity & Temporal Component
 * Full 52-week contribution heatmap calendar with streaks, 7x24 activity grid, and stack evolution.
 */

import { full, compact, getLangColor, icon } from '../utils.js';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function renderActivity(dossier) {
  const container = document.getElementById('activityContainer');
  if (!container) return;

  const streaks = dossier.streaks || { current: 0, longest: 0, total_active_days: 0 };
  const rawHeatmap = dossier.heatmap || {};
  const activityHours = dossier.activity_hours || [];
  const langEvo = dossier.lang_evolution || {};

  // Build 52-week calendar array (today backwards 364 days)
  const today = new Date();
  const daysList = [];
  let totalCommitsYear = 0;

  for (let i = 363; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const count = Number(rawHeatmap[key]) || 0;
    totalCommitsYear += count;
    daysList.push({ date: d, key, count });
  }

  // Group into weeks of 7 days (aligning Monday-Sunday)
  const weeks = [];
  let curWeek = [];
  // Pad beginning so days align with day of week (Monday=0 ... Sunday=6)
  const firstDayOfWeek = (daysList[0].date.getDay() + 6) % 7;
  for (let p = 0; p < firstDayOfWeek; p++) {
    curWeek.push(null);
  }

  daysList.forEach(item => {
    curWeek.push(item);
    if (curWeek.length === 7) {
      weeks.push(curWeek);
      curWeek = [];
    }
  });
  if (curWeek.length) {
    while (curWeek.length < 7) curWeek.push(null);
    weeks.push(curWeek);
  }

  // Heatmap level color
  function getHeatClass(count) {
    if (!count || count <= 0) return 'bg-raised';
    if (count <= 2) return 'bg-accent/40';
    if (count <= 5) return 'bg-accent/70';
    if (count <= 9) return 'bg-accent';
    return 'bg-lime';
  }

  // Month labels
  const monthLabels = [];
  let lastMonth = -1;
  weeks.forEach((w, wIdx) => {
    const valid = w.find(d => d !== null);
    if (valid) {
      const m = valid.date.getMonth();
      if (m !== lastMonth) {
        lastMonth = m;
        const name = valid.date.toLocaleDateString('en-US', { month: 'short' });
        monthLabels.push({ wIdx, name });
      }
    }
  });

  // Heatmap HTML
  const heatmapHtml = `
    <div class="scroll-thin overflow-x-auto pb-3">
      <div class="relative min-w-[700px] select-none" id="heatmapGridContainer">
        <!-- Month headers -->
        <div class="flex pl-7 text-[10px] text-muted font-mono mb-2 h-4 relative">
          ${monthLabels.map(m => `
            <span class="absolute" style="left: ${28 + m.wIdx * 14}px">${m.name}</span>
          `).join('')}
        </div>

        <div class="flex gap-1">
          <!-- Day of week column -->
          <div class="flex flex-col justify-between text-[9px] text-muted font-mono pr-2 py-0.5">
            <span>Mon</span>
            <span>Wed</span>
            <span>Fri</span>
          </div>

          <!-- Week columns -->
          <div class="flex gap-[3px]">
            ${weeks.map(week => `
              <div class="flex flex-col gap-[3px]">
                ${week.map(day => {
                  if (!day) {
                    return '<span class="h-2.5 w-2.5 rounded-[2px] opacity-0"></span>';
                  }
                  const title = `${day.count} commits on ${day.key}`;
                  return `
                    <span data-heatmap-cell title="${title}"
                      data-count="${day.count}" data-date="${day.key}"
                      class="h-2.5 w-2.5 rounded-[2px] cursor-pointer transition-transform hover:scale-125 ${getHeatClass(day.count)}">
                    </span>
                  `;
                }).join('')}
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  // Activity hours grid & peak hour
  let peakDay = 0;
  let peakHour = 0;
  let maxHourVal = 1;

  if (activityHours.length) {
    activityHours.forEach((row, d) => {
      row.forEach((val, h) => {
        if (val > (activityHours[peakDay]?.[peakHour] || 0)) {
          peakDay = d;
          peakHour = h;
        }
        if (val > maxHourVal) maxHourVal = val;
      });
    });
  }

  function getHourClass(val, isPeak) {
    if (isPeak) return 'bg-lime';
    if (!val || val <= 0) return 'bg-raised';
    const r = val / maxHourVal;
    if (r > 0.66) return 'bg-accent';
    if (r > 0.33) return 'bg-accent/65';
    return 'bg-accent/35';
  }

  const activityGridHtml = activityHours.length ? `
    <div class="overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden min-w-0">
      <div class="grid grid-cols-[28px_repeat(24,minmax(0,1fr))] gap-[2px] mt-4 min-w-[280px]">
        <span></span>
        ${Array.from({ length: 24 }, (_, h) => `
          <span class="text-center font-mono text-[9px] text-muted">
            ${h % 6 === 0 ? String(h).padStart(2, '0') : ''}
          </span>
        `).join('')}

        ${activityHours.map((row, d) => `
          <span class="self-center text-[10px] text-muted font-mono">${DAYS[d]}</span>
          ${row.map((val, h) => {
            const isPeak = d === peakDay && h === peakHour && val > 0;
            return `
              <span title="${DAYS[d]} ${String(h).padStart(2, '0')}:00 UTC · ${val} commits"
                class="aspect-square rounded-[2px] transition-transform hover:scale-125 ${getHourClass(val, isPeak)}"></span>
            `;
          }).join('')}
        `).join('')}
      </div>
    </div>
  ` : '<p class="text-xs text-muted font-mono py-4">No event timestamps recorded</p>';

  // Stack Evolution horizontal multi-segment bars
  const years = Object.keys(langEvo).sort();
  const allEvoLangs = new Set();
  const evoRows = years.map(yr => {
    const langs = langEvo[yr] || {};
    const yrTotal = Object.values(langs).reduce((a, b) => a + b, 0) || 1;
    const parts = Object.entries(langs)
      .map(([name, bytes]) => {
        allEvoLangs.add(name);
        return { name, pct: (bytes / yrTotal) * 100 };
      })
      .sort((a, b) => b.pct - a.pct);
    return { year: yr, parts };
  });

  const evoHtml = evoRows.length ? `
    <ul class="space-y-2 mt-4">
      ${evoRows.map(r => `
        <li class="grid grid-cols-[38px_minmax(0,1fr)] items-center gap-3">
          <span class="font-mono text-[11px] tabular-nums text-muted">${r.year}</span>
          <div class="flex h-3 overflow-hidden rounded-full bg-line" title="${r.parts.map(p => `${p.name} ${Math.round(p.pct)}%`).join(', ')}">
            ${r.parts.map(p => `
              <span class="h-full border-r border-surface last:border-r-0"
                style="width:${p.pct}%; background:${getLangColor(p.name)}"></span>
            `).join('')}
          </div>
        </li>
      `).join('')}
    </ul>
    <ul class="mt-4 flex flex-wrap gap-x-3.5 gap-y-1.5">
      ${Array.from(allEvoLangs).slice(0, 8).map(name => `
        <li class="flex items-center gap-1.5 text-[11px] text-muted">
          <span class="h-2 w-2 rounded-full" style="background:${getLangColor(name)}"></span>
          ${name}
        </li>
      `).join('')}
    </ul>
  ` : '<p class="text-xs text-muted font-mono py-4">No repo history available</p>';

  container.innerHTML = `
    <div class="space-y-4">
      <!-- Heatmap Panel -->
      <section class="rounded-2xl border border-line bg-surface p-3.5 sm:p-7 min-w-0 overflow-hidden">
        <header class="flex flex-wrap items-baseline justify-between gap-3 mb-6">
          <div>
            <h3 class="text-base font-semibold tracking-tight text-ink">Contributions & Streaks</h3>
            <p class="mt-0.5 text-xs text-muted">${full(totalCommitsYear)} public contributions in the last year</p>
          </div>
          <div class="flex items-center gap-1.5 text-[11px] text-muted font-mono">
            <span>Less</span>
            <span class="h-2.5 w-2.5 rounded-[2px] bg-raised"></span>
            <span class="h-2.5 w-2.5 rounded-[2px] bg-accent/40"></span>
            <span class="h-2.5 w-2.5 rounded-[2px] bg-accent/70"></span>
            <span class="h-2.5 w-2.5 rounded-[2px] bg-accent"></span>
            <span class="h-2.5 w-2.5 rounded-[2px] bg-lime"></span>
            <span>More</span>
          </div>
        </header>

        <!-- Streaks 3-stat block -->
        <dl class="grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3 mb-6">
          <div class="flex items-center gap-3 sm:gap-4 bg-surface px-3.5 sm:px-5 py-3 sm:py-3.5 min-w-0">
            <span class="grid h-9 w-9 sm:h-10 sm:w-10 shrink-0 place-items-center rounded-xl bg-danger/10 text-danger">${icon('flame', 'w-4 h-4 sm:w-5 sm:h-5')}</span>
            <div class="min-w-0">
              <dt class="text-[11px] sm:text-xs text-muted truncate">Current streak</dt>
              <dd class="font-mono text-lg sm:text-xl font-semibold tabular-nums text-limeink">
                ${streaks.current || 0} <span class="text-xs font-normal text-muted">days</span>
              </dd>
            </div>
          </div>
          <div class="flex items-center gap-3 sm:gap-4 bg-surface px-3.5 sm:px-5 py-3 sm:py-3.5 min-w-0">
            <span class="grid h-9 w-9 sm:h-10 sm:w-10 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent">${icon('zap', 'w-4 h-4 sm:w-5 sm:h-5')}</span>
            <div class="min-w-0">
              <dt class="text-[11px] sm:text-xs text-muted truncate">Longest streak</dt>
              <dd class="font-mono text-lg sm:text-xl font-semibold tabular-nums text-accent">
                ${streaks.longest || 0} <span class="text-xs font-normal text-muted">days</span>
              </dd>
            </div>
          </div>
          <div class="flex items-center gap-3 sm:gap-4 bg-surface px-3.5 sm:px-5 py-3 sm:py-3.5 min-w-0">
            <span class="grid h-9 w-9 sm:h-10 sm:w-10 shrink-0 place-items-center rounded-xl bg-lime/10 text-lime">${icon('calendar', 'w-4 h-4 sm:w-5 sm:h-5')}</span>
            <div class="min-w-0">
              <dt class="text-[11px] sm:text-xs text-muted truncate">Active push days</dt>
              <dd class="font-mono text-lg sm:text-xl font-semibold tabular-nums text-ink">
                ${streaks.total_active_days || 0} <span class="text-xs font-normal text-muted">days</span>
              </dd>
            </div>
          </div>
        </dl>

        ${heatmapHtml}
      </section>

      <!-- Temporal Analytics Panel -->
      <section class="rounded-2xl border border-line bg-surface p-3.5 sm:p-7 min-w-0 overflow-hidden">
        <header class="mb-5">
          <h3 class="text-base font-semibold tracking-tight text-ink">Temporal Analytics</h3>
          <p class="mt-0.5 text-xs text-muted">When they code, and how their stack has shifted over time</p>
        </header>

        <div class="grid gap-8 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <!-- Activity hours -->
          <div>
            <div class="flex items-baseline justify-between">
              <h4 class="text-xs font-medium text-ink uppercase tracking-wider font-mono">Activity hours</h4>
              <span class="font-mono text-[11px] text-muted">
                Peak <span class="text-limeink font-bold">${DAYS[peakDay]} ${String(peakHour).padStart(2, '0')}:00</span> UTC
              </span>
            </div>
            ${activityGridHtml}
          </div>

          <!-- Stack Evolution -->
          <div>
            <h4 class="text-xs font-medium text-ink uppercase tracking-wider font-mono">Stack evolution</h4>
            ${evoHtml}
          </div>
        </div>
      </section>
    </div>
  `;
}
