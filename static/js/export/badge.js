/**
 * static/js/export/badge.js
 * =========================
 * Interactive GitHub Profile Badge Studio.
 * Live SVG preview rendering, customizer controls, and markdown/HTML snippet generation.
 */

import { showToast } from '../utils.js';

let _activeLogin = '';
let _activeFormat = 'card';
let _activeMetric = 'score';
let _activeTheme = 'spectre';
let _isInitialized = false;

function _getBaseUrl() {
  // Use current window origin if available (or fallback to production)
  return window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? window.location.origin
    : 'https://git-spectre.vercel.app';
}

function _buildBadgeUrl(login, format, metric, theme) {
  const base = _getBaseUrl();
  const params = new URLSearchParams();
  if (format && format !== 'pill') params.set('style', format);
  if (metric && metric !== 'score' && format !== 'card') params.set('metric', metric);
  if (theme && theme !== 'spectre') params.set('theme', theme);

  const qs = params.toString() ? `?${params.toString()}` : '';
  return `${base}/api/badge/${encodeURIComponent(login)}${qs}`;
}

function _buildProfileUrl(login) {
  const base = _getBaseUrl();
  return `${base}/?u=${encodeURIComponent(login)}`;
}

function _updateStudio() {
  if (!_activeLogin) return;

  const badgeUrl = _buildBadgeUrl(_activeLogin, _activeFormat, _activeMetric, _activeTheme);
  const profileUrl = _buildProfileUrl(_activeLogin);

  // Update Snippet text input (defaulting to markdown)
  const snippetInput = document.getElementById('badgeSnippetInput');
  if (snippetInput) {
    snippetInput.value = `[![Git-Spectre](${badgeUrl})](${profileUrl})`;
  }

  // Update Metric select visibility (disabled when format is "card" because card shows full stats)
  const metricGroup = document.getElementById('badgeMetricGroup');
  if (metricGroup) {
    metricGroup.style.opacity = _activeFormat === 'card' ? '0.4' : '1';
    metricGroup.style.pointerEvents = _activeFormat === 'card' ? 'none' : 'auto';
  }

  // Update Live Preview Container
  const container = document.getElementById('badgePreviewContainer');
  if (container) {
    container.innerHTML = '';
    const img = document.createElement('img');
    const bustUrl = `${badgeUrl}${badgeUrl.includes('?') ? '&' : '?'}_t=${Date.now()}`;
    img.src = bustUrl;
    img.alt = `Git-Spectre Badge - ${_activeLogin}`;
    img.className = 'max-w-full h-auto drop-shadow-md rounded-lg transition-transform duration-200 hover:scale-[1.02]';
    img.onerror = () => {
      container.innerHTML = '<span class="text-xs font-mono text-muted">Preview unavailable</span>';
    };
    container.appendChild(img);
  }
}

function _initEventListeners() {
  if (_isInitialized) return;

  const formatSelect = document.getElementById('badgeFormatSelect');
  const metricSelect = document.getElementById('badgeMetricSelect');
  const themeSelect = document.getElementById('badgeThemeSelect');

  if (formatSelect) {
    formatSelect.addEventListener('change', (e) => {
      _activeFormat = e.target.value;
      _updateStudio();
    });
  }

  if (metricSelect) {
    metricSelect.addEventListener('change', (e) => {
      _activeMetric = e.target.value;
      _updateStudio();
    });
  }

  if (themeSelect) {
    themeSelect.addEventListener('change', (e) => {
      _activeTheme = e.target.value;
      _updateStudio();
    });
  }

  // Copy buttons
  const copyMdBtn = document.getElementById('badgeCopyMdBtn');
  if (copyMdBtn) {
    copyMdBtn.addEventListener('click', () => {
      const badgeUrl = _buildBadgeUrl(_activeLogin, _activeFormat, _activeMetric, _activeTheme);
      const profileUrl = _buildProfileUrl(_activeLogin);
      const text = `[![Git-Spectre](${badgeUrl})](${profileUrl})`;
      navigator.clipboard.writeText(text)
        .then(() => showToast('Markdown snippet copied!', 'copy'))
        .catch(() => showToast('Could not copy markdown', 'alert-triangle'));
    });
  }

  const copyHtmlBtn = document.getElementById('badgeCopyHtmlBtn');
  if (copyHtmlBtn) {
    copyHtmlBtn.addEventListener('click', () => {
      const badgeUrl = _buildBadgeUrl(_activeLogin, _activeFormat, _activeMetric, _activeTheme);
      const profileUrl = _buildProfileUrl(_activeLogin);
      const text = `<a href="${profileUrl}"><img src="${badgeUrl}" alt="Git-Spectre" /></a>`;
      navigator.clipboard.writeText(text)
        .then(() => showToast('HTML snippet copied!', 'copy'))
        .catch(() => showToast('Could not copy HTML', 'alert-triangle'));
    });
  }

  const copyUrlBtn = document.getElementById('badgeCopyUrlBtn');
  if (copyUrlBtn) {
    copyUrlBtn.addEventListener('click', () => {
      const badgeUrl = _buildBadgeUrl(_activeLogin, _activeFormat, _activeMetric, _activeTheme);
      navigator.clipboard.writeText(badgeUrl)
        .then(() => showToast('Badge URL copied!', 'copy'))
        .catch(() => showToast('Could not copy URL', 'alert-triangle'));
    });
  }

  _isInitialized = true;
}

export function openBadgeModal(dossierOrLogin) {
  const login = typeof dossierOrLogin === 'string'
    ? dossierOrLogin
    : dossierOrLogin?.profile?.login;

  if (!login) {
    showToast('Scan a profile first to generate a badge', 'alert-triangle');
    return;
  }

  _activeLogin = login;
  _initEventListeners();

  // Reset controls to defaults
  const formatSelect = document.getElementById('badgeFormatSelect');
  if (formatSelect) {
    formatSelect.value = _activeFormat;
  }
  const metricSelect = document.getElementById('badgeMetricSelect');
  if (metricSelect) {
    metricSelect.value = _activeMetric;
  }
  const themeSelect = document.getElementById('badgeThemeSelect');
  if (themeSelect) {
    themeSelect.value = _activeTheme;
  }

  _updateStudio();

  // Open modal
  const modal = document.getElementById('badgeModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }
}

export function copyBadgeSnippet(login) {
  if (!login) return;
  const badgeUrl = `${_getBaseUrl()}/api/badge/${encodeURIComponent(login)}`;
  const profileUrl = _buildProfileUrl(login);
  const snippet = `[![Git-Spectre](${badgeUrl})](${profileUrl})`;
  navigator.clipboard
    .writeText(snippet)
    .then(() => showToast('Badge markdown copied to clipboard!', 'copy'))
    .catch(() => showToast('Could not copy badge', 'alert-triangle'));
}
