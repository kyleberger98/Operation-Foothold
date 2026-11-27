// Save compatibility: saves made by the current game, by the first PWA release (commit 6e50341, 2026-11-06) and by the
// last version before diplomacy (commit bc1b529, 2026-11-22) all load from the home screen and play on.
// Regenerate the current fixture with tests/tools/make-save.js when the format changes on purpose, but keep the legacy
// ones: returning players still have saves like them.
const fs = require('fs');
const path = require('path');
const { test, expect, openGame } = require('./helpers/game');

const FIX = path.join(__dirname, 'fixtures');
const SAVES = {
  current: 'save-current.json',
  'legacy (2026-11-06)': 'save-legacy-2026-11-06.json',
  'legacy (2026-11-22)': 'save-legacy-2026-11-22.json',
};

for (const [label, file] of Object.entries(SAVES)) {
  test(`${label} save loads from Continue and plays on`, async ({ context }) => {
    const json = fs.readFileSync(path.join(FIX, file), 'utf8');
    const data = JSON.parse(json);
    await context.addInitScript(s => { try { localStorage.setItem('foothold-save-v1', s); } catch (e) {} }, json);
    const page = await openGame(context, { render: false });
    await expect(page.locator('#continueBtn')).toBeVisible();
    await expect(page.locator('#continueInfo')).toContainText('turn ' + data.turn);
    await page.click('#continueBtn');
    await page.waitForFunction(() => map && !$('setup').classList.contains('show'));
    const r = await page.evaluate(async () => {
      const got = { turn, W, side, me: MYSIDE, units: units.length, sides: Object.fromEntries(turnOrder.map(s => [s, meta(s).faction.key])), stars: { ...stars } };
      got.played = await __t.round(30000);
      got.turnAfter = turn;
      const before = __t.sig();
      const fresh = JSON.parse(serializeGame());
      got.restored = restoreGame(fresh); gen++;
      got.same = __t.sig() === before;
      got.keys = Object.keys(fresh);
      return got;
    });
    expect(r.turn).toBe(data.turn);
    expect(r.W).toBe(data.W);
    expect(r.side).toBe('P');
    expect(r.me).toBe('P');
    expect(r.units).toBe(data.units.length);
    expect(r.sides).toEqual(data.sides);
    expect(r.stars).toEqual(data.stars);
    expect(r.played).toBe(true);
    expect(r.turnAfter).toBeGreaterThan(data.turn);
    expect(r.restored).toBe(true);
    expect(r.same, 'a re-save of the loaded game restores to the same state').toBe(true);
    for (const k of ['v', 'cfg', 'W', 'sides', 'units', 'map', 'turn']) expect(r.keys).toContain(k);
    expect(page.errors).toEqual([]);
  });
}

test('a save file loads through Import Save', async ({ context }) => {
  const page = await openGame(context, { render: false });
  await page.evaluate(() => setupView('solo'));
  const [chooser] = await Promise.all([page.waitForEvent('filechooser'), page.click('#importBtn')]);
  await chooser.setFiles(path.join(FIX, SAVES.current));
  await page.waitForFunction(() => map && !$('setup').classList.contains('show'));
  const data = JSON.parse(fs.readFileSync(path.join(FIX, SAVES.current), 'utf8'));
  expect(await page.evaluate(() => [turn, units.length])).toEqual([data.turn, data.units.length]);
  expect(page.errors).toEqual([]);
});

test('broken saves are refused and leave the menu up', async ({ game }) => {
  const r = await game.evaluate(() => {
    aiSpeed = 0; cfg = { size: 11, enemies: 2, faction: 'AEGIS', diff: 'normal' }; $('setup').classList.remove('show'); newGame(); gen++;
    const save = serializeGame();
    showSetup();
    const cases = {
      missingFaction: d => { delete d.sides.A2; },
      badOwner: d => { d.units[0].owner = 'A3'; },
      shortMap: d => { d.map.pop(); },
      notASave: () => ({ hello: 1 }),
      dupSeat: d => { d.enemySides = ['A1', 'A1']; },
      badUnitType: d => { d.units[0].type = 'NOPE'; },
    };
    const out = [];
    for (const k in cases) {
      const d = JSON.parse(save); const bad = cases[k](d) || d;
      const W0 = W, u0 = units.length;
      const ok = restoreGame(bad);
      out.push({ k, ok, menu: $('setup').classList.contains('show'), sameBoard: W === W0 && units.length === u0 });
    }
    return out;
  });
  for (const c of r) expect(c, c.k).toEqual({ k: c.k, ok: false, menu: true, sameBoard: true });
});

test('an online guest\'s exported save puts the guest in the solo seat', async ({ game }) => {
  const r = await game.evaluate(() => {
    aiSpeed = 0; cfg = { size: 11, enemies: 2, faction: 'AEGIS', diff: 'normal' }; $('setup').classList.remove('show'); newGame(); gen++;
    const a1Units = units.filter(u => u.owner === 'A1').length, a1Fac = meta('A1').faction.key, a1Stars = stars.A1;
    MYSIDE = 'A1';
    const json = serializeGame();
    MYSIDE = 'P';
    const ok = restoreGame(JSON.parse(json));
    return { ok, me: MYSIDE, side, pFac: meta('P').faction.key, a1Fac, pUnits: units.filter(u => u.owner === 'P').length, a1Units, pStars: stars.P, a1Stars, order: [...turnOrder] };
  });
  expect(r.ok).toBe(true);
  expect(r.me).toBe('P');
  expect(r.pFac).toBe(r.a1Fac);
  expect(r.pUnits).toBe(r.a1Units);
  expect(r.pStars).toBe(r.a1Stars);
  expect(r.order).toEqual(['P', 'A1', 'A2']);
});
