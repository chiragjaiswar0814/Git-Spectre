/**
 * Git-Spectre Application Controller
 * Bootstraps modules, coordinates view transitions, scans, comparisons, and keyboard shortcuts.
 */

import {
	analyzeProfile,
	compareProfiles,
	clearLeaderboardClientCache,
} from "./api.js";
import {
	appState,
	getToken,
	getTheme,
	applyTheme,
	toggleTheme,
} from "./state.js";
import { showToast, parseTarget } from "./utils.js";

import { initNav, updateThemeIcon } from "./components/nav.js";
import { initHero } from "./components/hero.js";
import { showScan, hideScan } from "./components/scanOverlay.js";
import { renderIdentity } from "./components/identity.js";
import { renderExplorer } from "./components/explorer.js";
import { renderGamification } from "./components/gamification.js";
import { renderActivity } from "./components/activity.js";
import { renderRadarDna } from "./components/radarDna.js";
import { renderCodeQuality } from "./components/codeQuality.js";
import { renderRepos } from "./components/repos.js";
import { renderCompareView } from "./components/compare.js";
import {
	initModals,
	openModal,
	closeModal,
	openWrappedModal,
} from "./components/modals.js";
import { renderLeaderboardView } from "./components/leaderboard.js";
import { exportPdf, exportShareCard, copyBadgeSnippet, openBadgeModal } from "./export.js";

import { initBackground } from "./components/background.js";

// View Transition Helper
function setView(view) {
	appState.currentView = view;
	const heroSection = document.getElementById("heroSection");
	const dossierSection = document.getElementById("dossierSection");
	const compareSection = document.getElementById("compareSection");
	const leaderboardSection = document.getElementById("leaderboardSection");
	const actionDock = document.getElementById("actionDock");

	if (heroSection) heroSection.classList.toggle("hidden", view !== "hero");
	if (dossierSection)
		dossierSection.classList.toggle("hidden", view !== "dossier");
	if (compareSection)
		compareSection.classList.toggle("hidden", view !== "compare");
	if (leaderboardSection)
		leaderboardSection.classList.toggle("hidden", view !== "leaderboard");
	if (actionDock) actionDock.classList.toggle("hidden", view !== "dossier");

	// Smooth scroll to top on view changes
	window.scrollTo({ top: 0, behavior: "smooth" });

	// URL state management
	if (view === "hero") {
		if (window.location.search) {
			history.pushState(null, "", window.location.pathname);
		}
	} else if (view === "leaderboard") {
		history.pushState(null, "", "/?view=leaderboard");
	}
}

// Dedicated Leaderboard Page Controller
export function showLeaderboardPage() {
	renderLeaderboardView({
		onOpenDossier: (login) => runScan(login),
		onBackHome: () => setView("hero"),
	});
	setView("leaderboard");
}

// Main Scan Action
export async function runScan(rawUsername) {
	const username = parseTarget(rawUsername);
	if (!username) return;

	showScan(username);

	try {
		const token = getToken();
		const data = await analyzeProfile(username, token);
		appState.activeDossier = data;
		clearLeaderboardClientCache();

		// Render all modular dossier components
		renderIdentity(data);
		renderExplorer(data);
		renderGamification(data);
		renderActivity(data);
		renderRadarDna(data);
		renderCodeQuality(data);
		renderRepos(data);

		// Update browser URL
		history.pushState(null, "", `/?u=${encodeURIComponent(username)}`);

		// Switch view to dossier
		setView("dossier");
	} catch (err) {
		showToast(`Scan failed: ${err.message}`, "alert-triangle");
	} finally {
		hideScan();
	}
}

// Dual Compare Action
export async function runCompare(userA, userB) {
	showScan(`${userA} vs ${userB}`);

	try {
		const token = getToken();
		const data = await compareProfiles(userA, userB, token);
		appState.activeCompare = data;

		renderCompareView(data, {
			onBack: () => setView("hero"),
			onOpenDossier: (login) => runScan(login),
		});

		setView("compare");
	} catch (err) {
		showToast(`Comparison failed: ${err.message}`, "alert-triangle");
	} finally {
		hideScan();
	}
}

// Global Keyboard Shortcuts
function initShortcuts() {
	window.addEventListener("keydown", (e) => {
		// Escape closes any open modal
		if (e.key === "Escape") {
			document
				.querySelectorAll(".modal-backdrop")
				.forEach((m) => m.classList.add("hidden"));
			return;
		}

		// Don't trigger shortcuts if user is typing in an input or textarea
		const active = document.activeElement;
		const isTyping =
			active &&
			(active.tagName === "INPUT" || active.tagName === "TEXTAREA");

		if (e.ctrlKey || e.metaKey) {
			const key = e.key.toLowerCase();
			if (key === "k") {
				e.preventDefault();
				const searchInput = document.getElementById("searchInput");
				if (searchInput) searchInput.focus();
			} else if (key === "e") {
				e.preventDefault();
				if (appState.activeDossier) exportPdf(appState.activeDossier);
			} else if (key === "d") {
				e.preventDefault();
				openModal("compareModal");
			} else if (key === "b") {
				e.preventDefault();
				openModal("batchModal");
			} else if (key === "l") {
				e.preventDefault();
				showLeaderboardPage();
			} else if (key === "t") {
				e.preventDefault();
				toggleTheme();
				updateThemeIcon();
			}
		}
	});
}

// Initialize Application
window.addEventListener("DOMContentLoaded", () => {
	// Apply saved theme & initialize telemetry grid canvas background
	applyTheme(getTheme());
	initBackground();

	// Initialize Nav
	initNav({
		onHome: () => {
			const searchInput = document.getElementById("searchInput");
			if (searchInput) searchInput.value = "";
			setView("hero");
		},
		onLeaderboard: () => showLeaderboardPage(),
		onCompare: () => openModal("compareModal"),
		onBatch: () => openModal("batchModal"),
		onVault: () => openModal("vaultModal"),
	});

	// Global delegation for data-nav-leaderboard and data-open-leaderboard elements
	document.addEventListener("click", (e) => {
		const trigger = e.target.closest(
			"[data-nav-leaderboard], [data-open-leaderboard]",
		);
		if (trigger) {
			e.preventDefault();
			showLeaderboardPage();
		}
	});

	// Initialize Hero
	initHero({
		onScan: (login) => runScan(login),
	});

	// Initialize Modals
	initModals({
		onRunCompare: (a, b) => runCompare(a, b),
		onOpenDossier: (login) => runScan(login),
		onExportPdf: () => {
			if (appState.activeDossier) exportPdf(appState.activeDossier);
			else showToast("Scan a profile first", "alert-triangle");
		},
		onShareCard: () => {
			if (appState.activeDossier) exportShareCard(appState.activeDossier);
			else showToast("Scan a profile first", "alert-triangle");
		},
		onCopyBadge: () => {
			if (appState.activeDossier?.profile?.login) {
				openBadgeModal(appState.activeDossier);
			} else {
				showToast("Scan a profile first", "alert-triangle");
			}
		},
		onOpenWrapped: () => {
			if (appState.activeDossier)
				openWrappedModal(appState.activeDossier);
			else showToast("Scan a profile first", "alert-triangle");
		},
	});

	// Initialize Global Shortcuts
	initShortcuts();

	// Handle browser Back/Forward navigation
	window.addEventListener("popstate", () => {
		const params = new URLSearchParams(window.location.search);
		const u = params.get("u");
		const view = params.get("view");
		if (view === "leaderboard") {
			showLeaderboardPage();
		} else if (u) {
			runScan(u);
		} else {
			setView("hero");
		}
	});

	// Initial URL query parameter check: ?u=username or ?view=leaderboard
	const params = new URLSearchParams(window.location.search);
	const u = params.get("u");
	const view = params.get("view");
	if (view === "leaderboard") {
		showLeaderboardPage();
	} else if (u) {
		runScan(u);
	}
});
