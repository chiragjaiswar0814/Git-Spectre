/**
 * Gamification Component
 * Developer Level XP progression, animated rank ladder, and 15 unlockable achievement badges.
 */

import { esc, full, icon } from '../utils.js';

const TITLES = ['Intern', 'Junior', 'Mid', 'Senior', 'Staff', 'Principal', 'Legend'];
const TITLE_COLORS = ['#94A3B8', '#60A5FA', '#22D3EE', '#4ADE80', '#FACC15', '#A78BFA', '#C6F432'];

const TIER_COLORS = {
  common: '#94A3B8',
  rare: '#60A5FA',
  epic: '#A78BFA',
  legendary: '#F43F5E'
};

export function renderGamification(dossier) {
  const container = document.getElementById('gamificationContainer');
  if (!container) return;

  const level = dossier.dev_level || {
    level: 1,
    title: 'Junior',
    xp: 250,
    next: 500,
    description: 'Steadily expanding codebase impact and language proficiency.',
    index: 1
  };

  const achievements = dossier.achievements || [];
  const unlockedCount = achievements.filter(a => a.unlocked).length;

  const rankTitle = level.title || level.rank || 'Junior';
  let rankIdx = TITLES.indexOf(rankTitle);
  if (rankIdx === -1) rankIdx = level.index ?? (level.level ? level.level - 1 : 1);
  const rankColor = TITLE_COLORS[rankIdx] || '#C6F432';

  const xpCurrent = level.xp || 0;
  const xpNext = level.xp_next || level.next || 1000;
  const pct = level.xp_pct ?? Math.max(0, Math.min(100, Math.round((xpCurrent / xpNext) * 100)));

  // SVG XP ring
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - pct / 100);

  container.innerHTML = `
    <section class="rounded-2xl border border-line bg-surface p-3.5 sm:p-7 min-w-0 overflow-hidden">
      <header class="flex flex-wrap items-baseline justify-between gap-3 mb-6">
        <div>
          <h3 class="text-base font-semibold tracking-tight text-ink">Level & Achievements</h3>
          <p class="mt-0.5 text-xs text-muted">${unlockedCount} of ${achievements.length || 15} badges unlocked</p>
        </div>
      </header>

      <div class="grid gap-6 sm:gap-8 lg:grid-cols-[280px_minmax(0,1fr)] min-w-0">
        <!-- XP & Level Rank Box -->
        <div class="flex flex-col lg:border-r lg:border-line lg:pr-8 min-w-0">
          <div class="flex items-center gap-4 sm:gap-5 min-w-0">
            <!-- XP Circle -->
            <div class="relative h-[100px] w-[100px] sm:h-[116px] sm:w-[116px] shrink-0">
              <svg viewBox="0 0 116 116" class="-rotate-90 w-full h-full">
                <circle cx="58" cy="58" r="${r}" stroke-width="8" class="fill-none stroke-line" />
                <circle cx="58" cy="58" r="${r}" stroke-width="8" stroke-linecap="round"
                  stroke-dasharray="${c}" stroke-dashoffset="${offset}"
                  class="fill-none transition-all duration-1000 ease-out" style="stroke:${rankColor}" />
              </svg>
              <div class="absolute inset-0 grid place-items-center text-center">
                <div>
                  <div class="font-mono text-xl sm:text-2xl font-bold tabular-nums text-ink">${pct}%</div>
                  <div class="text-[9px] sm:text-[10px] text-muted">to ${TITLES[rankIdx + 1] || 'max'}</div>
                </div>
              </div>
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-xs text-muted">Current rank</p>
              <p class="mt-0.5 text-xl sm:text-2xl font-bold tracking-tight truncate" style="color:${rankColor}">
                ${esc(level.title || TITLES[rankIdx])}
              </p>
            </div>
          </div>

          <p class="mt-3 sm:mt-4 text-xs leading-relaxed text-muted break-words">${esc(level.description || '')}</p>

          <div class="mt-4 sm:mt-5">
            <div class="flex justify-between font-mono text-[11px] tabular-nums text-muted">
              <span>${full(xpCurrent)} XP</span>
              <span>${full(xpNext)} XP</span>
            </div>
            <div class="mt-1.5 h-1.5 overflow-hidden rounded-full bg-line">
              <div class="h-full rounded-full transition-all duration-700" style="width:${pct}%; background:${rankColor}"></div>
            </div>
          </div>

          <!-- Rank ladder dots -->
          <ol class="mt-5 sm:mt-6 flex items-center justify-between" aria-label="Rank ladder">
            ${TITLES.map((t, i) => `
              <li class="flex flex-col items-center gap-1.5" title="${t}">
                <span class="h-2 w-2 rounded-full ${i <= rankIdx ? '' : 'bg-line'}"
                  style="${i <= rankIdx ? `background:${TITLE_COLORS[i]}` : ''}"></span>
                <span class="text-[9px] ${i === rankIdx ? 'font-bold text-ink' : 'hidden xs:inline text-muted'}">${t}</span>
              </li>
            `).join('')}
          </ol>
        </div>

        <!-- 15 Achievement Badges Grid -->
        <ul class="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-5 gap-2 sm:gap-2.5 min-w-0">
          ${achievements.map(a => {
            const badgeSvg = icon(a.icon || 'star', 'w-5 h-5');
            const tier = (a.rarity || a.tier || 'common').toLowerCase();
            const color = TIER_COLORS[tier] || '#94A3B8';
            const isUnlocked = Boolean(a.unlocked);
            const name = a.label || a.name || 'Achievement';
            const desc = a.desc || a.description || '';

            return `
              <li title="${esc(desc || name)}"
                class="relative flex flex-col items-center rounded-xl p-2.5 sm:p-3 text-center border border-line bg-raised transition-transform duration-200 hover:scale-105 min-w-0 ${
                  isUnlocked ? 'ring-1 ring-white/10' : 'opacity-35 grayscale'
                }">
                <span class="grid h-9 w-9 sm:h-10 sm:w-10 place-items-center rounded-full text-base sm:text-lg"
                  style="background:${color}18; color:${color}; ${isUnlocked ? `box-shadow:inset 0 0 0 1px ${color}55` : ''}">
                  ${badgeSvg}
                </span>
                <span class="mt-2 text-[11px] sm:text-[12px] font-medium leading-tight text-ink line-clamp-1 w-full truncate">${esc(name)}</span>
                <span class="mt-1 font-mono text-[9px] uppercase tracking-wider font-semibold" style="color:${color}">
                  ${esc(a.rarity || a.tier || 'Common')}
                </span>
                ${!isUnlocked ? `<span class="absolute right-1.5 top-1.5 sm:right-2 sm:top-2 text-muted/60">${icon('lock', 'w-3 h-3')}</span>` : ''}
              </li>
            `;
          }).join('')}
        </ul>
      </div>
    </section>
  `;
}
