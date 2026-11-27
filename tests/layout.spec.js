// Phone layout at 360x740: nothing on screen overlaps a control, runs off the side, or gets its text cut off.
const { test, expect, openGame } = require('./helpers/game');

const PHONE = { viewport: { width: 360, height: 740 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true };

// Runs in the page; returns a list of problems on the current screen.
const CHECK = () => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity !== 0; };
  const R = e => e.getBoundingClientRect();
  const ov = (a, b) => { const x = Math.min(a.right, b.right) - Math.max(a.left, b.left), y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top); return x > 0.5 && y > 0.5 ? Math.round(x) + 'x' + Math.round(y) : null; };
  const name = e => '#' + (e.id || e.className || e.tagName);
  const out = [];
  const q = s => [...document.querySelectorAll(s)].filter(vis);
  // a control hidden under an open panel cannot be tapped anyway, so it does not count
  const PANELS = '#techPanel, #dipPanel, #armyPanel, #overlay, #setup, #rewardBox';
  const onTop = e => {
    const r = R(e), h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!h || e.contains(h)) return true;
    const p = h.closest(PANELS);
    return !(p && !p.contains(e));
  };
  // corner and rail buttons never sit on each other or on the HUD
  const btns = q('#helpBtn, #muteBtn, #menuBtn, #fitBtn, .rb');
  const uniq = [...new Set(btns)].filter(onTop);
  for (let i = 0; i < uniq.length; i++) for (let j = i + 1; j < uniq.length; j++) {
    if (uniq[i].contains(uniq[j]) || uniq[j].contains(uniq[i])) continue;
    const o = ov(R(uniq[i]), R(uniq[j])); if (o) out.push('BUTTONS ' + name(uniq[i]) + ' on ' + name(uniq[j]) + ' ' + o);
  }
  for (const b of q('#hud .hud-box')) for (const t of uniq) { const o = ov(R(b), R(t)); if (o) out.push('HUD ' + b.className + ' under ' + name(t) + ' ' + o); }
  // the bottom dock buttons stay clear of each other and of the rail
  const dock = q('#endTurn, #nextBtn, #techBtn, #undoBtn').filter(onTop);
  for (let i = 0; i < dock.length; i++) for (let j = i + 1; j < dock.length; j++) { const o = ov(R(dock[i]), R(dock[j])); if (o) out.push('DOCK ' + name(dock[i]) + ' on ' + name(dock[j]) + ' ' + o); }
  for (const d of dock) for (const t of uniq) { const o = ov(R(d), R(t)); if (o) out.push('DOCK ' + name(d) + ' under ' + name(t) + ' ' + o); }
  // the selection card must not cover the dock
  const cmd = document.querySelector('#command');
  if (cmd && document.body.classList.contains('selOpen')) for (const d of dock) { const o = ov(R(cmd), R(d)); if (o) out.push('CARD over ' + name(d) + ' ' + o); }
  // nothing visible runs off the side of the screen, and no text is cut off without an ellipsis
  const roots = ['#command', '#toasts', '.apInner', '#techPanel.show', '#setup.show', '#overlay.show', '#rewardBox:not([hidden])', '#hud', '#turnBanner', '#dipPanel:not([hidden])', '#armyPanel:not([hidden])'];
  for (const sel of roots) for (const root of document.querySelectorAll(sel)) {
    if (!vis(root)) continue;
    if (sel === '#command' && !document.body.classList.contains('selOpen')) continue;
    for (const e of [root, ...root.querySelectorAll('*')]) {
      if (!vis(e)) continue;
      const r = R(e);
      if (r.right > innerWidth + 1 || r.left < -1) out.push('OFFSCREEN ' + sel + ' ' + name(e) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
      const s = getComputedStyle(e);
      if (e.children.length === 0 && e.textContent.trim() && (s.overflow === 'hidden' || s.overflowX === 'hidden') && e.scrollWidth > e.clientWidth + 1 && s.textOverflow !== 'ellipsis' && !s.webkitLineClamp)
        out.push('CLIP ' + name(e) + ' "' + e.textContent.trim().slice(0, 20) + '"');
    }
  }
  return out;
};

test('phone layout at 360x740 has no overlaps', async ({ browser }) => {
  test.setTimeout(120_000);
  const context = await browser.newContext(PHONE);
  const page = await openGame(context, { gfx: 'low' });
  await page.evaluate(() => document.fonts.ready);
  const res = {};
  // let slide-ins and fades finish first (looping animations are left alone)
  const settle = () => page.waitForFunction(() => document.getAnimations().every(a => a.playState !== 'running' || a.effect.getComputedTiming().iterations === Infinity), null, { timeout: 10000 });
  const look = async n => { await page.waitForTimeout(150); await settle(); res[n] = await page.evaluate(CHECK); };
  await look('home');
  await page.evaluate(() => { aiSpeed = 0; cfg = { size: 11, enemies: 2, faction: 'AEGIS', diff: 'normal', mods: ['nofog'] }; $('setup').classList.remove('show'); newGame(); gen++; });
  // long numbers in the HUD
  await page.evaluate(() => { $('hudStars').textContent = '124'; $('hudIncome').textContent = '+18'; $('hudCities').textContent = '12'; $('hudTurn').textContent = '27'; });
  await look('game');
  await page.evaluate(() => { document.querySelectorAll('.toast').forEach(t => t.remove()); const u = units.find(q => q.owner === MYSIDE); sel = { kind: 'unit', id: u.id }; refresh(); });
  await look('unit');
  await page.evaluate(() => { const h = __t.hq(MYSIDE); sel = { kind: 'city', x: h.x, y: h.y }; refresh(); });
  await look('city');
  await page.evaluate(() => { sel = null; refresh(); window.__tt = NET.timerTick; NET.timerTick = () => {}; $('hudTimerBox').hidden = false; $('hudTimer').textContent = '1:30'; });
  await look('timer');
  await page.evaluate(() => { $('hudTimerBox').hidden = true; NET.timerTick = window.__tt; $('techBtn').click(); });
  await look('tech');
  await page.evaluate(() => { $('techPanel').classList.remove('show'); openDip(); });
  await look('diplomacy');
  await page.evaluate(() => { $('dipPanel').hidden = true; openArmy(); });
  await look('army');
  await page.evaluate(() => { $('armyPanel').hidden = true; toast('Your Infantry captured a city near the river crossing', 'var(--amber)'); });
  await look('toast');
  await page.evaluate(() => { document.querySelectorAll('.toast').forEach(t => t.remove()); $('helpBtn').click(); });
  await look('manual');
  const problems = Object.entries(res).flatMap(([k, v]) => v.map(p => k + ': ' + p));
  expect(problems).toEqual([]);
  expect(page.errors).toEqual([]);
  await context.close();
});
