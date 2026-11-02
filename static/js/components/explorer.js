/**
 * Quick Explorer Component
 * 4-panel grid: Top repos, Starred repos, Followers, and Following.
 */

import { esc, safeUrl, compact, avatarUrl, icon } from '../utils.js';

export function renderExplorer(dossier) {
  const container = document.getElementById('explorerPanelsContainer');
  if (!container) return;

  const topRepos = dossier.top_repos || [];
  const starred = dossier.starred_repos || [];
  const followers = dossier.followers_list || [];
  const following = dossier.following_list || [];
  const summary = dossier.profile || {};

  function renderRepoList(title, repos, totalCount) {
    return `
      <div class="bg-surface p-3.5 sm:p-5 flex flex-col min-h-0 min-w-0 overflow-hidden">
        <h3 class="flex items-baseline justify-between text-sm font-semibold text-ink">
          ${title}
          <span class="font-mono text-[11px] font-normal text-muted">${totalCount}</span>
        </h3>
        <ul class="scroll-thin mt-3 max-h-52 space-y-1 overflow-y-auto pr-1">
          ${repos.length ? repos.map(r => `
            <li>
              <a href="${safeUrl(r.html_url || r.url || `https://github.com/${summary.login}/${r.name}`)}"
                target="_blank" rel="noreferrer"
                class="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-xs transition-colors duration-150 hover:bg-raised min-w-0">
                <span class="truncate font-mono text-ink min-w-0 flex-1">${esc(r.name)}</span>
                <span class="flex shrink-0 items-center gap-1 font-mono text-[11px] tabular-nums text-muted">
                  ${icon('star', 'w-3 h-3 text-yellow-400/80')} ${compact(r.stargazers_count ?? r.stars ?? 0)}
                </span>
              </a>
            </li>
          `).join('') : '<p class="text-xs text-muted py-4 text-center font-mono">None found</p>'}
        </ul>
      </div>
    `;
  }

  function renderPeopleGrid(title, people, totalCount) {
    return `
      <div class="bg-surface p-3.5 sm:p-5 min-w-0 overflow-hidden">
        <h3 class="flex items-baseline justify-between text-sm font-semibold text-ink">
          ${title}
          <span class="font-mono text-[11px] font-normal text-muted">${totalCount}</span>
        </h3>
        <ul class="mt-3 grid grid-cols-1 xs:grid-cols-2 gap-x-2.5 gap-y-2">
          ${people.length ? people.slice(0, 8).map(p => `
            <li>
              <a href="${safeUrl(p.url || `https://github.com/${p.login}`)}"
                target="_blank" rel="noreferrer"
                class="flex items-center gap-2 rounded-md px-1.5 py-1 transition-colors duration-150 hover:bg-raised min-w-0">
                <img src="${avatarUrl(p.login, 44)}" alt="" class="h-5 w-5 rounded-full object-cover shrink-0" />
                <span class="truncate font-mono text-xs text-ink min-w-0 flex-1">@${esc(p.login)}</span>
              </a>
            </li>
          `).join('') : '<p class="col-span-1 xs:col-span-2 text-xs text-muted py-4 text-center font-mono">None listed</p>'}
        </ul>
      </div>
    `;
  }

  container.innerHTML = `
    <section aria-label="Quick explorer" class="grid gap-px overflow-hidden rounded-2xl border border-line bg-line md:grid-cols-2 xl:grid-cols-4">
      ${renderRepoList('Top repositories', topRepos, topRepos.length)}
      ${renderRepoList('Starred repos', starred, starred.length)}
      ${renderPeopleGrid('Followers', followers, compact(summary.followers || followers.length))}
      ${renderPeopleGrid('Following', following, compact(summary.following || following.length))}
    </section>
  `;
}
