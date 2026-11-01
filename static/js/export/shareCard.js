/**
 * Share Card Generator
 * Native Canvas 2D pixel-perfect PNG card generation with custom vector icons.
 */

import { showToast, compact, full, getLangColor } from '../utils.js';
import { fetchAvatarImage, fetchGhostImage, fetchTextLogoImage } from './imageHelpers.js';

// Vector SVG Paths for Metric Icons (Lucide-based 24x24 paths, zero emojis)
const METRIC_ICONS = {
  stars: new Path2D('M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'),
  repos: new Path2D('M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 8 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z'),
  followers: new Path2D('M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75'),
  streak: new Path2D('M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z'),
};

function drawMetricIcon(ctx, key, x, y, color, fill = false) {
  const p = METRIC_ICONS[key];
  if (!p) return;
  ctx.save();
  ctx.translate(x, y - 6.5);
  ctx.scale(13 / 24, 13 / 24);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  if (fill) {
    ctx.fill(p);
  } else {
    ctx.stroke(p);
  }
  ctx.restore();
}

function roundRect(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function drawTrackedText(ctx, text, x, y, tracking = 0, align = 'left') {
  const chars = Array.from(String(text));
  if (!tracking || chars.length <= 1) {
    const prevAlign = ctx.textAlign;
    ctx.textAlign = align;
    ctx.fillText(text, x, y);
    ctx.textAlign = prevAlign;
    return ctx.measureText(text).width;
  }
  const widths = chars.map((c) => ctx.measureText(c).width);
  const totalWidth = widths.reduce((a, b) => a + b, 0) + tracking * (chars.length - 1);
  let curX = align === 'right' ? x - totalWidth : align === 'center' ? x - totalWidth / 2 : x;
  const prevAlign = ctx.textAlign;
  ctx.textAlign = 'left';
  chars.forEach((ch, idx) => {
    ctx.fillText(ch, curX, y);
    curX += widths[idx] + tracking;
  });
  ctx.textAlign = prevAlign;
  return totalWidth;
}

export async function exportShareCard(dossier) {
  if (!dossier || !dossier.profile) {
    showToast('No profile scanned yet', 'alert-triangle');
    return;
  }

  showToast('Generating shareable card…', 'image');

  try {
    const profile = dossier.profile || {};
    const score = dossier.score || {};
    const arch = dossier.archetype || {};
    const stats = dossier.stats || {};
    const streaks = dossier.streaks || {};
    const langs = Object.entries(dossier.languages || {}).slice(0, 4);

    const rawName = profile.name || profile.login || 'Developer';
    const name = rawName.length > 22 ? rawName.slice(0, 21) + '…' : rawName;
    const login = profile.login || '';
    const totalScore = String(Math.max(0, Math.min(1000, Number(score.total) || 0)));
    const grade = String(score.grade || 'E');
    const archLabel = String(arch.label || 'Code Craftsman').toUpperCase();
    const archGlow = arch.glow || '#06b6d4';

    if (document.fonts && document.fonts.ready) {
      try { await document.fonts.ready; } catch (_) {}
    }

    const [avatarImg, ghostImg, textLogoImg] = await Promise.all([
      fetchAvatarImage(login, profile.avatar_url),
      fetchGhostImage(),
      fetchTextLogoImage(),
    ]);

    const W = 680, H = 380, SCALE = 2;
    const canvas = document.createElement('canvas');
    canvas.width = W * SCALE;
    canvas.height = H * SCALE;
    const ctx = canvas.getContext('2d');
    ctx.scale(SCALE, SCALE);

    const sans = `'Inter', system-ui, -apple-system, sans-serif`;
    const mono = `'JetBrains Mono', monospace`;

    // 1. Card Base & Radial Ambient Glows
    roundRect(ctx, 0, 0, W, H, 24);
    ctx.fillStyle = '#0c0c11';
    ctx.fill();
    ctx.save();
    ctx.clip();

    const gradTR = ctx.createRadialGradient(W * 0.88, H * 0.12, 10, W * 0.88, H * 0.12, 260);
    gradTR.addColorStop(0, 'rgba(124, 58, 237, 0.28)');
    gradTR.addColorStop(1, 'rgba(12, 12, 17, 0)');
    ctx.fillStyle = gradTR;
    ctx.fillRect(0, 0, W, H);

    const gradBL = ctx.createRadialGradient(W * 0.12, H * 0.92, 10, W * 0.12, H * 0.92, 230);
    gradBL.addColorStop(0, 'rgba(196, 248, 42, 0.15)');
    gradBL.addColorStop(1, 'rgba(12, 12, 17, 0)');
    ctx.fillStyle = gradBL;
    ctx.fillRect(0, 0, W, H);

    roundRect(ctx, 0.75, 0.75, W - 1.5, H - 1.5, 23.25);
    ctx.strokeStyle = 'rgba(139, 108, 255, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // 2. Avatar Squircle
    const avX = 30, avY = 30, avS = 76;
    ctx.save();
    ctx.shadowColor = 'rgba(139, 108, 255, 0.45)';
    ctx.shadowBlur = 18;
    roundRect(ctx, avX, avY, avS, avS, 18);
    ctx.fillStyle = '#1e1b4b';
    ctx.fill();
    ctx.restore();

    ctx.save();
    roundRect(ctx, avX, avY, avS, avS, 18);
    ctx.clip();
    if (avatarImg) {
      ctx.drawImage(avatarImg, avX, avY, avS, avS);
    } else {
      ctx.fillStyle = '#c4b5fd';
      ctx.font = `800 30px ${sans}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(name.charAt(0).toUpperCase(), avX + avS / 2, avY + avS / 2);
    }
    ctx.restore();

    roundRect(ctx, avX, avY, avS, avS, 18);
    ctx.strokeStyle = '#8b6cff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 3. Identity Text & Archetype Pill
    const idX = 124;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = '#ffffff';
    ctx.font = `800 24px ${sans}`;
    ctx.fillText(name, idX, 44);

    ctx.fillStyle = '#a78bfa';
    ctx.font = `600 13px ${mono}`;
    ctx.fillText(`@${login}`, idX, 68);

    ctx.font = `700 10px ${mono}`;
    const pillTracking = 1.2;
    const archChars = Array.from(archLabel);
    const archTextW = archChars.reduce((sum, c) => sum + ctx.measureText(c).width, 0) + pillTracking * Math.max(0, archChars.length - 1);
    const pillPadX = 12, dotSize = 6, dotGap = 8;
    const pillW = pillPadX * 2 + dotSize + dotGap + archTextW;
    const pillH = 24, pillX = idX, pillY = 82;
    const pillMidY = pillY + pillH / 2;

    roundRect(ctx, pillX, pillY, pillW, pillH, 12);
    ctx.fillStyle = `${archGlow}1f`;
    ctx.fill();
    ctx.strokeStyle = archGlow;
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(pillX + pillPadX + dotSize / 2, pillMidY, dotSize / 2, 0, Math.PI * 2);
    ctx.fillStyle = archGlow;
    ctx.fill();

    ctx.fillStyle = archGlow;
    drawTrackedText(ctx, archLabel, pillX + pillPadX + dotSize + dotGap, pillMidY + 0.5, pillTracking, 'left');

    // 4. Developer Score Box
    const sbW = 152, sbH = 78, sbX = W - 30 - sbW, sbY = 30;
    roundRect(ctx, sbX, sbY, sbW, sbH, 16);
    ctx.fillStyle = '#14141d';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#9ca3af';
    ctx.font = `700 9px ${mono}`;
    drawTrackedText(ctx, 'DEVELOPER SCORE™', sbX + sbW - 16, sbY + 20, 1.5, 'right');

    const rowMidY = sbY + 52;
    ctx.font = `900 14px ${mono}`;
    const gradeW = Math.max(26, ctx.measureText(grade).width + 14);
    const gradeH = 24;
    const gradeX = sbX + sbW - 16 - gradeW;
    const gradeY = rowMidY - gradeH / 2;

    roundRect(ctx, gradeX, gradeY, gradeW, gradeH, 6);
    ctx.fillStyle = '#c6f432';
    ctx.fill();

    ctx.fillStyle = '#0f1206';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(grade, gradeX + gradeW / 2, rowMidY + 0.5);

    ctx.fillStyle = '#ffffff';
    ctx.font = `900 36px ${mono}`;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillText(totalScore, gradeX - 10, rowMidY + 1);

    // 5. TOP STACK & DNA
    const stackLabelY = 142;
    ctx.fillStyle = '#71717a';
    ctx.font = `700 9.5px ${mono}`;
    ctx.textBaseline = 'middle';
    drawTrackedText(ctx, 'TOP STACK & DNA', 30, stackLabelY, 1.5, 'left');

    const chipsY = 156, chipH = 30;
    const chipMidY = chipsY + chipH / 2;
    let curChipX = 30;

    if (langs.length) {
      langs.forEach(([lang]) => {
        ctx.font = `600 11.5px ${mono}`;
        const textW = ctx.measureText(lang).width;
        const cPadX = 12, cDot = 7, cGap = 8;
        const chipW = cPadX * 2 + cDot + cGap + textW;

        roundRect(ctx, curChipX, chipsY, chipW, chipH, 10);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.045)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(curChipX + cPadX + cDot / 2, chipMidY, cDot / 2, 0, Math.PI * 2);
        ctx.fillStyle = getLangColor(lang);
        ctx.fill();

        ctx.fillStyle = '#e4e4e7';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(lang, curChipX + cPadX + cDot + cGap, chipMidY + 0.5);

        curChipX += chipW + 8;
      });
    } else {
      ctx.fillStyle = '#71717a';
      ctx.font = `500 11px ${mono}`;
      ctx.textAlign = 'left';
      ctx.fillText('Polyglot Developer', 30, chipMidY);
    }

    // 6. Key Metrics (4 Glass Tiles with Vector Icons — NO Emojis)
    const tilesY = 210, tileH = 74, tileGap = 12;
    const tileW = (W - 60 - tileGap * 3) / 4;

    const metrics = [
      { key: 'stars', iconColor: '#facc15', label: 'Total Stars', value: compact(stats.total_stars ?? 0), valColor: '#ffffff', suffix: '', fill: true },
      { key: 'repos', iconColor: '#4ade80', label: 'Repositories', value: full(stats.own_repos ?? stats.total_repos ?? 0), valColor: '#ffffff', suffix: '', fill: false },
      { key: 'followers', iconColor: '#a78bfa', label: 'Followers', value: compact(profile.followers ?? 0), valColor: '#ffffff', suffix: '', fill: false },
      { key: 'streak', iconColor: '#f43f5e', label: 'Best Streak', value: String(streaks.longest ?? streaks.current ?? 0), valColor: '#c6f432', suffix: 'days', fill: false },
    ];

    metrics.forEach((m, idx) => {
      const tx = 30 + idx * (tileW + tileGap);
      roundRect(ctx, tx, tilesY, tileW, tileH, 14);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.035)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Tile Header Row (Vector Path Icon + Label)
      const labelY = tilesY + 23;
      drawMetricIcon(ctx, m.key, tx + 14, labelY, m.iconColor, m.fill);

      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#9ca3af';
      ctx.font = `500 11.5px ${sans}`;
      ctx.fillText(m.label, tx + 14 + 19, labelY);

      // Tile Value Row
      const valY = tilesY + 51;
      ctx.fillStyle = m.valColor;
      ctx.font = `800 19px ${mono}`;
      ctx.fillText(String(m.value), tx + 14, valY);

      if (m.suffix) {
        const valW = ctx.measureText(String(m.value)).width;
        ctx.fillStyle = '#9ca3af';
        ctx.font = `500 12px ${mono}`;
        ctx.fillText(m.suffix, tx + 14 + valW + 6, valY + 1);
      }
    });

    // 7. Footer Divider & Branding
    const divY = 314;
    ctx.beginPath();
    ctx.moveTo(30, divY);
    ctx.lineTo(W - 30, divY);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.stroke();

    const footMidY = 342;
    let footX = 30;

    if (ghostImg) {
      ctx.drawImage(ghostImg, footX, footMidY - 9, 18, 18);
      footX += 26;
    }

    if (textLogoImg) {
      const textH = 16;
      const textW = Math.round(textH * (248.35 / 46.30));
      ctx.drawImage(textLogoImg, footX, footMidY - textH / 2, textW, textH);
      footX += textW + 12;
    } else {
      ctx.textBaseline = 'middle';
      ctx.font = `900 12px ${mono}`;
      ctx.fillStyle = '#ffffff';
      const gitW = drawTrackedText(ctx, 'GIT', footX, footMidY, 1.8, 'left');
      footX += gitW + 3;

      ctx.fillStyle = '#8b5cf6';
      const dotW = drawTrackedText(ctx, '·', footX, footMidY, 0, 'left');
      footX += dotW + 3;

      ctx.fillStyle = '#ffffff';
      const specW = drawTrackedText(ctx, 'SPECTRE', footX, footMidY, 1.8, 'left');
      footX += specW + 12;
    }

    ctx.font = `500 10px ${mono}`;
    ctx.fillStyle = '#71717a';
    ctx.textBaseline = 'middle';
    drawTrackedText(ctx, '', footX, footMidY, 1.0, 'left');

    drawTrackedText(ctx, 'git-spectre.vercel.app', W - 30, footMidY, 0.8, 'right');
    ctx.restore();

    // Trigger PNG download
    const link = document.createElement('a');
    link.download = `git-spectre-${login}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    showToast('Share card downloaded!', 'check');
  } catch (err) {
    showToast(`Card creation failed: ${err.message}`, 'alert-triangle');
  }
}
