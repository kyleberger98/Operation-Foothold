// Write a save file made by a given copy of the game, for the save compatibility tests.
//   node tests/tools/make-save.js <game.html> <out.json> [rounds]
// The current fixture comes from gridline-command.html. The legacy ones came from the game as of commits 6e50341
// (2026-11-06) and bc1b529 (2026-11-22): `git show 6e50341:gridline-command.html > /tmp/old.html`, then run this on it.
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { chromium } = require('@playwright/test');

const [game, out, rounds = '4'] = process.argv.slice(2);
if (!game || !out) { console.error('usage: node tests/tools/make-save.js <game.html> <out.json> [rounds]'); process.exit(2); }

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const context = await browser.newContext({ viewport: { width: 400, height: 300 } });
  await context.route(/^https?:\/\//, r => r.abort());
  await context.addInitScript(() => { try { localStorage.setItem('foothold-tutorial-done', '1'); } catch (e) {} });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(pathToFileURL(path.resolve(game)).href);
  await page.waitForFunction(() => typeof newGame === 'function' && typeof serializeGame === 'function');
  const json = await page.evaluate(async n => {
    window.loop = () => {};
    if (typeof aiSpeed !== 'undefined') aiSpeed = 0;
    cfg = Object.assign({}, cfg, { size: 9, enemies: 2, faction: 'VERDANT' in FACTIONS ? 'VERDANT' : 'AEGIS', diff: 'normal' });
    $('setup').classList.remove('show'); newGame();
    const wait = ms => new Promise(r => setTimeout(r, ms));
    for (let i = 0; i < n && !gameOver; i++) {
      // move every unit one step toward the middle so the save has some history in it
      for (const u of units.filter(q => q.owner === MYSIDE)) {
        const t = [...reachable(u).values()].sort((a, b) => Math.hypot(a.x - W / 2, a.y - W / 2) - Math.hypot(b.x - W / 2, b.y - W / 2))[0];
        if (t) act({ t: 'move', uid: u.id, x: t.x, y: t.y });
      }
      act({ t: 'endturn' });
      const t0 = Date.now();
      while (side !== MYSIDE && !gameOver && Date.now() - t0 < 30000) await wait(20);
    }
    return serializeGame();
  }, +rounds);
  fs.writeFileSync(out, JSON.stringify(JSON.parse(json)) + '\n');
  console.log('wrote', out, json.length, 'bytes', errors.length ? 'page errors: ' + errors.join(' | ') : '');
  await browser.close();
})();
