// First launch: the guided tutorial starts from Quick play and can be skipped; the Field Manual opens and every tab has text.
const { test, expect, openGame, newSolo } = require('./helpers/game');

test('first Quick play starts the guided tutorial, which advances and can be skipped', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 640, height: 480 } });
  // the coach bubble is updated by the draw loop, so drawing stays on here
  const page = await openGame(context, { tutorialDone: false, gfx: 'low' });
  expect(await page.evaluate(() => tutDone())).toBe(false);
  await page.evaluate(() => { aiSpeed = 0; });
  await page.click('#quickBtn');
  await page.waitForFunction(() => map && coach.on && !$('coach').hidden);
  const first = await page.evaluate(() => ({ i: coach.i, step: $('coachStep').textContent, text: $('coachText').textContent, enemies: enemySides.length }));
  expect(first.i).toBe(0);
  expect(first.text.length).toBeGreaterThan(10);
  expect(first.enemies).toBe(1);
  // do what the first step asks: select your unit
  await page.evaluate(() => { const u = units.find(q => q.owner === MYSIDE); sel = { kind: 'unit', id: u.id }; refresh(); });
  await page.waitForFunction(() => coach.i > 0);
  const second = await page.evaluate(() => $('coachText').textContent);
  expect(second).not.toBe(first.text);
  // Skip ends it for good
  await page.click('#coachSkip');
  await page.waitForFunction(() => !coach.on);
  expect(await page.evaluate(() => localStorage.getItem('foothold-tutorial-done'))).toBe('1');
  expect(page.errors).toEqual([]);
  await context.close();
});

test('How to play replays the tutorial for a returning player', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 640, height: 480 } });
  const page = await openGame(context, { gfx: 'low' });
  await page.evaluate(() => { aiSpeed = 0; });
  await page.click('#tutBtn');
  await page.waitForFunction(() => map && coach.on && !$('coach').hidden);
  expect(await page.evaluate(() => coach.i)).toBe(0);
  expect(page.errors).toEqual([]);
  await context.close();
});

test('the Field Manual opens, every tab has entries, and Escape closes it', async ({ game }) => {
  await newSolo(game, {});
  await game.click('#helpBtn');
  await expect(game.locator('#overlay')).toHaveClass(/manual/);
  await expect(game.locator('#ovTitle')).toHaveText('Field Manual');
  const tabs = game.locator('#overlay .mTabs button');
  const n = await tabs.count();
  expect(n).toBe(await game.evaluate(() => MANUAL.length));
  for (let i = 0; i < n; i++) {
    await tabs.nth(i).click();
    await expect(tabs.nth(i)).toHaveAttribute('aria-selected', 'true');
    const entries = await game.evaluate(() => [...document.querySelectorAll('#overlay .mEnt')].map(e => e.textContent.trim()));
    expect(entries.length, 'tab ' + i).toBeGreaterThan(0);
    for (const e of entries) expect(e.length).toBeGreaterThan(3);
  }
  await game.keyboard.press('Escape');
  await expect(game.locator('#overlay')).not.toHaveClass(/show/);
  // H opens it from the board too
  await game.keyboard.press('h');
  await expect(game.locator('#overlay')).toHaveClass(/manual/);
});
