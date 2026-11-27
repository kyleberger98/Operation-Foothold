// Smoke test: every theme draws a game, the AI plays a few turns, the game saves and restores, Low graphics works.
// The WebGL draw loop stays on here, so these are the slowest tests; the board is kept small.
const { test, expect, openGame } = require('./helpers/game');

const THEMES = ['temperate', 'autumn', 'desert', 'winter', 'tropical', 'dusk', 'ash'];

test('the theme list matches the game', async ({ game }) => {
  const names = await game.evaluate(() => Object.keys(THEMES));
  // a new theme should get its own smoke run: add it to THEMES above
  expect(names.sort()).toEqual([...THEMES].sort());
});

for (const theme of THEMES) {
  test(`theme ${theme}: AI turns, save and restore`, async ({ browser }) => {
    const context = await browser.newContext({ viewport: { width: 480, height: 360 } });
    const page = await openGame(context, { gfx: 'high' });
    const r = await page.evaluate(async th => {
      // a high rank unlocks every theme and cosmetic
      const pr = { xp: 0 }; for (let n = 1; n < 30; n++) pr.xp += rankNeed(n); localStorage.setItem('foothold-progress', JSON.stringify(pr));
      setCosmetic('theme', th); aiSpeed = 0; followAI = false;
      cfg = { size: 11, enemies: 2, faction: 'TIDE', diff: 'hard', map: th === 'desert' ? 'sea' : 'classic', mods: [] };
      $('setup').classList.remove('show'); newGame();
      await __t.wait(500);
      const drew = renderer.info.render.frame > 0;
      // the AI rounds run with drawing paused to save time; the long game test below keeps it on
      const realLoop = loop; window.loop = () => {};
      const rounds = [];
      for (let i = 0; i < 2 && !gameOver; i++) rounds.push(await __t.round(25000));
      window.loop = realLoop; requestAnimationFrame(loop);
      setCosmetic('finish', 'gold'); refreshUnitFinish(); setCosmetic('emblem', 'laurel'); syncCities();
      const before = __t.sig();
      const ok = restoreGame(JSON.parse(serializeGame())); gen++;
      const frames1 = renderer.info.render.frame;
      await __t.wait(400);
      const fx = THEMES[th].fx;
      return {
        rounds, turn, over: gameOver, ok, same: __t.sig() === before,
        drew, drewAfterRestore: renderer.info.render.frame > frames1,
        weatherOk: fx ? !!weather && weather.d === WX[fx] : true,
        units: units.length,
      };
    }, theme);
    expect(r.rounds.every(Boolean), 'each AI round finished').toBe(true);
    expect(r.over || r.turn >= 3).toBe(true);
    expect(r.drew, 'the board was drawn').toBe(true);
    expect(r.drewAfterRestore, 'the restored board was drawn').toBe(true);
    expect(r.ok).toBe(true);
    expect(r.same, 'restored game equals the saved one').toBe(true);
    expect(r.weatherOk, 'theme weather').toBe(true);
    expect(r.units).toBeGreaterThan(0);
    expect(page.errors).toEqual([]);
    await context.close();
  });
}

test('the AI plays several rounds while the board draws every frame', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 480, height: 360 } });
  const page = await openGame(context, { gfx: 'high' });
  const r = await page.evaluate(async () => {
    aiSpeed = 0; followAI = false;
    cfg = { size: 11, enemies: 2, faction: 'GHOST', diff: 'hard', map: 'classic', mods: [] };
    $('setup').classList.remove('show'); newGame();
    await __t.wait(300);
    const frames0 = renderer.info.render.frame, rounds = [];
    for (let i = 0; i < 2 && !gameOver; i++) rounds.push(await __t.round(30000));
    return { rounds, turn, over: gameOver, frames0, frames: renderer.info.render.frame };
  });
  expect(r.rounds.every(Boolean)).toBe(true);
  expect(r.over || r.turn >= 3).toBe(true);
  expect(r.frames, 'frames drawn during the AI turns').toBeGreaterThan(r.frames0);
  expect(page.errors).toEqual([]);
  await context.close();
});

test('Quick play from the home screen, then Low graphics and back', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 480, height: 360 } });
  const page = await openGame(context, { gfx: 'high' });
  await page.evaluate(() => {
    const pr = { xp: 0 }; for (let n = 1; n < 30; n++) pr.xp += rankNeed(n); localStorage.setItem('foothold-progress', JSON.stringify(pr));
    aiSpeed = 0; setCosmetic('theme', 'winter');
  });
  await page.click('#quickBtn');
  await page.waitForFunction(() => map && !$('setup').classList.contains('show'));
  const before = await page.evaluate(() => ({ low: gfxLow, weather: !!weather }));
  await page.evaluate(() => $('gfxMenuBtn').click());
  const low = await page.evaluate(() => ({ low: gfxLow, weather: !!weather, saved: localStorage.getItem('foothold-gfx'), label: $('gfxMenuBtn').textContent }));
  // a turn on Low graphics
  const played = await page.evaluate(() => __t.round(25000));
  await page.evaluate(() => $('gfxMenuBtn').click());
  const back = await page.evaluate(() => ({ low: gfxLow, weather: !!weather, saved: localStorage.getItem('foothold-gfx') }));
  expect(before).toEqual({ low: false, weather: true });
  expect(low.low).toBe(true);
  expect(low.weather, 'Low graphics turns the weather off').toBe(false);
  expect(low.saved).toBe('low');
  expect(low.label).toMatch(/Low/);
  expect(played).toBe(true);
  expect(back).toEqual({ low: false, weather: true, saved: 'high' });
  expect(page.errors).toEqual([]);
  await context.close();
});
