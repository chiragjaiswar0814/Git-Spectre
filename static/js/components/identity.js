/**
 * Identity Card Component
 * Profile identity, archetype badge, persona badge, roast, score ring with breakdown, and stat strip.
 */

import {
	esc,
	safeUrl,
	compact,
	full,
	animCount,
	avatarUrl,
	icon,
} from "../utils.js";

export function renderIdentity(dossier) {
	const {
		profile = {},
		stats = {},
		archetype = {},
		score = {},
		peak_hour = {},
		star_velocity = 0,
		roast = "",
		orgs = [],
		cached = false,
	} = dossier;

	const container = document.getElementById("identityCardContainer");
	if (!container) return;

	const totalScore = Math.max(0, Math.min(1000, Number(score.total) || 0));
	const grade = score.grade || "E";
	const archColor = archetype.glow || "#8B6CFF";

	// SVG Score ring geometry
	const radius = 72;
	const circumference = 2 * Math.PI * radius;
	const strokeOffset = circumference * (1 - totalScore / 1000);

	// Score breakdown bars (handles both dict and array formats)
	let breakdown = [];
	if (Array.isArray(score.breakdown)) {
		breakdown = score.breakdown;
	} else if (score.breakdown && typeof score.breakdown === "object") {
		const limits = {
			stars: 300,
			followers: 200,
			diversity: 150,
			repos: 100,
			age: 80,
			activity: 70,
		};
		const labels = {
			stars: "Stars Impact",
			followers: "Followers",
			diversity: "Language Diversity",
			repos: "Repositories",
			age: "Account Age",
			activity: "Active Days",
		};
		breakdown = Object.entries(score.breakdown).map(([k, v]) => ({
			label: labels[k] || k,
			value: Number(v) || 0,
			max: limits[k] || 100,
		}));
	} else {
		breakdown = [
			{
				label: "Volume & Scope",
				value: Math.round(totalScore * 0.25),
				max: 250,
			},
			{
				label: "Impact & Stars",
				value: Math.round(totalScore * 0.25),
				max: 250,
			},
			{
				label: "Consistency",
				value: Math.round(totalScore * 0.25),
				max: 250,
			},
			{
				label: "Diversity",
				value: Math.round(totalScore * 0.25),
				max: 250,
			},
		];
	}

	// Persona
	const personaText =
		peak_hour && peak_hour.persona && peak_hour.persona !== "Ghost Coder"
			? `<span class="inline-flex items-center gap-2 rounded-full border border-line bg-raised px-3 py-1.5 text-xs text-ink">
        <span class="font-medium text-accent">${esc(peak_hour.persona)}</span>
        <span class="text-muted">· peaks ${esc(peak_hour.hour || "00:00")} · ${esc(peak_hour.day || "weekdays")}s</span>
      </span>`
			: "";

	// Leaderboard Rank Badge
	const lb = dossier.leaderboard;
	let leaderboardBadge = "";
	if (lb && lb.eligible) {
		if (lb.daily && lb.daily.rank) {
			leaderboardBadge = `
        <button type="button" data-nav-leaderboard class="inline-flex items-center gap-1.5 rounded-full border border-lime/40 bg-lime/10 px-3 py-1 font-mono text-[11px] font-semibold text-limeink transition-all hover:bg-lime/20 hover:scale-105 active:scale-95" title="Ranked #${lb.daily.rank} Today (${lb.daily.checks} check${lb.daily.checks === 1 ? "" : "s"}). Click to view rankings.">
          ${icon("flame", "w-3 h-3 text-limeink shrink-0")}
          <span>Ranked #${lb.daily.rank} Today (${full(lb.daily.checks)} check${lb.daily.checks === 1 ? "" : "s"})</span>
        </button>
      `;
		} else if (lb.monthly && lb.monthly.rank) {
			leaderboardBadge = `
        <button type="button" data-nav-leaderboard class="inline-flex items-center gap-1.5 rounded-full border border-lime/40 bg-lime/10 px-3 py-1 font-mono text-[11px] font-semibold text-limeink transition-all hover:bg-lime/20 hover:scale-105 active:scale-95" title="Ranked #${lb.monthly.rank} This Month. Click to view rankings.">
          ${icon("award", "w-3 h-3 text-limeink shrink-0")}
          <span>Ranked #${lb.monthly.rank} This Month</span>
        </button>
      `;
		} else if (lb.all_time && lb.all_time.rank) {
			leaderboardBadge = `
        <button type="button" data-nav-leaderboard class="inline-flex items-center gap-1.5 rounded-full border border-line bg-raised px-3 py-1 font-mono text-[11px] font-semibold text-ink transition-all hover:border-accent hover:scale-105 active:scale-95" title="Ranked #${lb.all_time.rank} All-Time. Click to view rankings.">
          ${icon("star", "w-3 h-3 text-ink shrink-0")}
          <span>Ranked #${lb.all_time.rank} All-Time</span>
        </button>
      `;
		}
	}

	// Organizations
	const orgsHtml = orgs.length
		? `<div class="mt-5 flex flex-wrap items-center gap-2">
        <span class="mr-1 text-xs text-muted">Organizations</span>
        ${orgs
			.map(
				(o) => `
          <a href="${safeUrl(o.url || `https://github.com/${o.login}`)}" target="_blank" rel="noreferrer"
            class="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface py-0.5 pl-0.5 pr-2.5 text-xs text-ink transition-colors duration-150 hover:border-accent/60">
            <img src="${avatarUrl(o.login, 40)}" class="h-5 w-5 rounded-md object-cover" alt="" />
            ${esc(o.login)}
          </a>
        `,
			)
			.join("")}
      </div>`
		: "";

	// Roast
	const roastHtml = roast
		? `<figure class="mt-6 overflow-hidden rounded-xl border border-line bg-raised">
        <figcaption class="flex items-center justify-between border-b border-line px-4 py-2 font-mono text-[11px] text-muted">
          <span>// roast.exe</span>
          <span class="flex gap-1.5" aria-hidden="true">
            <span class="h-2 w-2 rounded-full bg-faint"></span>
            <span class="h-2 w-2 rounded-full bg-faint"></span>
            <span class="h-2 w-2 rounded-full bg-lime"></span>
          </span>
        </figcaption>
        <blockquote class="px-4 py-3 font-mono text-xs leading-relaxed text-ink/90 italic">
          <span class="text-limeink font-bold">&gt; </span>${esc(roast)}
        </blockquote>
      </figure>`
		: "";

	container.innerHTML = `
    <section class="overflow-hidden rounded-2xl border border-line bg-surface">
      <div class="grid lg:grid-cols-[minmax(0,1fr)_340px]">
        <!-- Left details column -->
        <div class="p-4 sm:p-8 min-w-0">
          <div class="flex flex-col gap-5 sm:gap-6 sm:flex-row sm:items-start min-w-0">
            <div class="relative h-20 w-20 sm:h-24 sm:w-24 shrink-0 mx-auto sm:mx-0">
              <span class="absolute inset-0 rounded-full border-2 border-accent animate-ring-pulse" aria-hidden="true"></span>
              <span class="absolute -inset-1 rounded-full border border-accent/40" aria-hidden="true"></span>
              <img src="${avatarUrl(profile.login, 200)}" alt="${esc(profile.name || profile.login)}"
                class="relative h-20 w-20 sm:h-24 sm:w-24 rounded-full bg-raised object-cover" />
            </div>
            <div class="min-w-0 flex-1 text-center sm:text-left">
              <div class="flex flex-wrap items-center justify-center sm:justify-start gap-2.5 sm:gap-3">
                <h1 class="text-2xl sm:text-3xl font-semibold tracking-tight text-ink truncate max-w-full">
                  <a href="${safeUrl(profile.html_url || `https://github.com/${profile.login}`)}"
                    target="_blank" rel="noreferrer" class="transition-colors duration-150 hover:text-accent">
                    ${esc(profile.name || profile.login)}
                  </a>
                </h1>
                ${
					cached
						? `
                  <span class="inline-flex items-center gap-1.5 rounded-full bg-lime/15 px-2.5 py-0.5 font-mono text-[11px] font-medium text-limeink">
                    ${icon("zap", "w-3 h-3 text-limeink")} Cached · last 5 min
                  </span>
                `
						: ""
				}
              </div>
              <p class="mt-1 font-mono text-xs sm:text-sm text-muted truncate">@${esc(profile.login)}</p>
              ${profile.bio ? `<p class="mt-3 max-w-2xl text-[13px] sm:text-[14px] leading-relaxed text-ink/80 break-words">${esc(profile.bio)}</p>` : ""}
            </div>
          </div>

          <div class="mt-5 sm:mt-6 flex flex-wrap items-center justify-center sm:justify-start gap-2.5 sm:gap-3">
            <span class="inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[11px] font-bold tracking-[0.14em] text-ink"
              style="border-color:${archColor}; box-shadow:0 0 0 3px ${archColor}1f, 0 0 20px -6px ${archColor}">
              <span class="h-2 w-2 rounded-full" style="background:${archColor}" aria-hidden="true"></span>
              ${esc(archetype.label || "Code Craftsman")}
            </span>
            ${personaText}
            ${leaderboardBadge}
          </div>
          ${archetype.description ? `<p class="mt-2.5 max-w-2xl text-xs text-muted leading-relaxed break-words">${esc(archetype.description)}</p>` : ""}

          <!-- Metadata list -->
          <ul class="mt-5 flex flex-wrap justify-center sm:justify-start gap-x-4 sm:gap-x-5 gap-y-2 text-xs text-muted">
            ${profile.location ? `<li class="flex items-center gap-1.5 truncate max-w-[200px]">${icon("map-pin", "w-3.5 h-3.5 text-muted shrink-0")} <span class="truncate">${esc(profile.location)}</span></li>` : ""}
            ${profile.company ? `<li class="flex items-center gap-1.5 truncate max-w-[200px]">${icon("building", "w-3.5 h-3.5 text-muted shrink-0")} <span class="truncate">${esc(profile.company)}</span></li>` : ""}
            ${profile.created_at ? `<li class="flex items-center gap-1.5 shrink-0">${icon("calendar", "w-3.5 h-3.5 text-muted shrink-0")} Joined ${esc(profile.created_at)}</li>` : ""}
            ${
				profile.blog
					? `
              <li class="truncate max-w-[200px]">
                <a href="${safeUrl(profile.blog.startsWith("http") ? profile.blog : "https://" + profile.blog)}"
                  target="_blank" rel="noreferrer" class="flex items-center gap-1.5 text-accent hover:underline truncate">
                  ${icon("link", "w-3.5 h-3.5 text-accent shrink-0")} <span class="truncate">${esc(profile.blog.replace(/^https?:\/\//, ""))}</span>
                </a>
              </li>
            `
					: ""
			}
          </ul>

          ${orgsHtml}
          ${roastHtml}
        </div>

        <!-- Right Score column -->
        <aside class="border-t border-line bg-raised p-4 sm:p-8 lg:border-l lg:border-t-0 flex flex-col justify-between min-w-0">
          <div>
            <div class="flex items-baseline justify-between">
              <h2 class="text-sm font-semibold text-ink">
                Developer Score<span class="align-super text-[9px] text-muted">™</span>
              </h2>
              <span class="font-mono text-[11px] text-muted">0 – 1000</span>
            </div>

            <!-- SVG Score Ring -->
            <div class="relative mx-auto mt-5 h-[164px] w-[164px]">
              <svg viewBox="0 0 164 164" class="-rotate-90 w-full h-full">
                <circle cx="82" cy="82" r="${radius}" stroke-width="10" class="fill-none stroke-line" />
                <circle cx="82" cy="82" r="${radius}" stroke-width="10" stroke-linecap="round"
                  stroke-dasharray="${circumference}" stroke-dashoffset="${strokeOffset}"
                  class="fill-none stroke-accent transition-all duration-1000 ease-out" />
              </svg>
              <div class="absolute inset-0 grid place-items-center text-center">
                <div>
                  <div id="scoreRingNumber" class="font-mono text-4xl font-bold leading-none tracking-tight text-ink tabular-nums">0</div>
                  <div class="mt-2 inline-flex rounded-md bg-lime px-2 py-0.5 font-mono text-xs font-bold text-onlime">${esc(grade)}</div>
                </div>
              </div>
            </div>

            <!-- Breakdown -->
            <ul class="mt-6 space-y-3">
              ${breakdown
					.map(
						(b) => `
                <li>
                  <div class="flex items-baseline justify-between text-xs">
                    <span class="text-muted">${esc(b.label)}</span>
                    <span class="font-mono tabular-nums text-ink">${b.value}<span class="text-muted">/${b.max}</span></span>
                  </div>
                  <div class="mt-1 h-1 overflow-hidden rounded-full bg-line">
                    <div class="h-full rounded-full bg-accent" style="width:${Math.round((b.value / b.max) * 100)}%"></div>
                  </div>
                </li>
              `,
					)
					.join("")}
            </ul>
          </div>
        </aside>
      </div>

      <!-- Metric Strip -->
      <dl class="grid grid-cols-2 gap-px border-t border-line bg-line md:grid-cols-4 min-w-0">
        <div class="bg-surface px-3.5 sm:px-6 py-3 sm:py-4 min-w-0">
          <dt class="text-[11px] sm:text-xs text-muted truncate">Own repositories</dt>
          <dd class="mt-1 font-mono text-xl sm:text-2xl font-semibold tabular-nums text-ink" id="statOwnRepos">0</dd>
        </div>
        <div class="bg-surface px-3.5 sm:px-6 py-3 sm:py-4 min-w-0">
          <dt class="text-[11px] sm:text-xs text-muted truncate">Total stars</dt>
          <dd class="mt-1 flex flex-wrap items-baseline gap-1.5 sm:gap-2">
            <span class="font-mono text-xl sm:text-2xl font-semibold tabular-nums text-ink" id="statTotalStars">0</span>
            ${star_velocity > 0 ? `<span class="inline-flex items-center gap-1 rounded-md bg-lime/15 px-1.5 py-0.5 font-mono text-[10px] sm:text-[11px] font-medium text-limeink">${icon("zap", "w-3 h-3 text-limeink")} ${star_velocity}/yr</span>` : ""}
          </dd>
        </div>
        <div class="bg-surface px-3.5 sm:px-6 py-3 sm:py-4 min-w-0">
          <dt class="text-[11px] sm:text-xs text-muted truncate">Followers</dt>
          <dd class="mt-1 font-mono text-xl sm:text-2xl font-semibold tabular-nums text-ink" id="statFollowers">0</dd>
        </div>
        <div class="bg-surface px-3.5 sm:px-6 py-3 sm:py-4 min-w-0">
          <dt class="text-[11px] sm:text-xs text-muted truncate">Following</dt>
          <dd class="mt-1 font-mono text-xl sm:text-2xl font-semibold tabular-nums text-ink" id="statFollowing">0</dd>
        </div>
      </dl>
    </section>
  `;

	// Animate stats
	animCount(document.getElementById("scoreRingNumber"), totalScore);
	animCount(
		document.getElementById("statOwnRepos"),
		stats.own_repos ?? stats.total_repos ?? 0,
	);
	animCount(
		document.getElementById("statTotalStars"),
		stats.total_stars ?? 0,
	);
	animCount(document.getElementById("statFollowers"), profile.followers ?? 0);
	animCount(document.getElementById("statFollowing"), profile.following ?? 0);
}
