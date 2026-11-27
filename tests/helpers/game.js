// Shared helpers: open the game from disk, start a solo game, collect page errors.
const path = require('path');
const { pathToFileURL } = require('url');
const base = require('@playwright/test');

const GAME = path.resolve(process.env.GAME || path.join(__dirname, '..', '..', 'gridline-command.html'));
const GAME_URL = pathToFileURL(GAME).href;
// Messages that are not game bugs: blocked network requests (fonts) and SwiftShader performance notes.
const IGNORED = /Failed to load resource|net::ERR_|GL Driver Message/;

// Small in-page toolkit, installed before the game script runs. Everything it touches is looked up at call time.
function pageKit() {
  window.__t = {
    hq(s) { for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const c = tileAt(x, y).city; if (c && c.owner === s && c.capital) return { x, y }; } return null; },
    cities(s) { const out = []; for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const c = tileAt(x, y).city; if (c && (s === undefined || c.owner === s)) out.push({ x, y, c }); } return out; },
    seen() { return explored.reduce((n, r) => n + r.filter(Boolean).length, 0); },
    // spawn and return the new unit, clearing whatever stood on the tile
    put(owner, type, x, y) { units = units.filter(u => !(u.x === x && u.y === y)); spawn(owner, type, x, y); const u = units[units.length - 1]; u.moved = false; u.attacked = false; return u; },
    // clear a 4-tile strip of plains away from cities, with no units on it, and return its left end
    strip() {
      for (let y = 2; y < H - 2; y++) for (let x = 2; x < W - 4; x++) {
        let ok = true;
        for (let dx = 0; dx < 4 && ok; dx++) if (tileAt(x + dx, y).city) ok = false;
        if (!ok) continue;
        for (let dx = 0; dx < 4; dx++) __t.plains(x + dx, y);
        units = units.filter(u => !(u.y === y && u.x >= x && u.x < x + 4));
        return { x, y };
      }
      throw new Error('no open strip');
    },
    plains(x, y) { const t = tileAt(x, y); t.terrain = 'plains'; t.resource = null; t.ruin = false; t.b = null; },
    sig() { return JSON.stringify({ turn, side, stars, units: units.map(u => [u.id, u.type, u.owner, u.x, u.y, u.hp]).sort(), map: map.map(r => r.map(t => [t.terrain, t.city && [t.city.owner, t.city.level, t.city.pop], t.resource || 0, t.b || 0])) }); },
    wait: ms => new Promise(r => setTimeout(r, ms)),
    // end the turn and wait until it is this side's turn again (or the game ends)
    async round(maxMs = 30000) {
      const me = MYSIDE, t0 = Date.now();
      if (side === me) act({ t: 'endturn' });
      await __t.wait(20);
      while (side !== me && !gameOver && Date.now() - t0 < maxMs) await __t.wait(20);
      return side === me || gameOver;
    },
  };
}

// Open the game in a fresh page. opts.render=false stops the WebGL draw loop, which makes rule tests much faster.
async function openGame(context, opts = {}) {
  await context.route(/^https?:\/\//, r => r.abort());   // no fonts or other network: the suite runs offline
  await context.addInitScript(({ tut, gfx }) => {
    try {
      if (tut) localStorage.setItem('foothold-tutorial-done', '1');
      if (gfx) localStorage.setItem('foothold-gfx', gfx);
    } catch (e) {}
  }, { tut: opts.tutorialDone !== false, gfx: opts.gfx || null });
  await context.addInitScript(pageKit);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !IGNORED.test(m.text())) errors.push('console: ' + m.text()); });
  await page.goto(GAME_URL);
  await page.waitForFunction(() => typeof newGame === 'function' && typeof NET !== 'undefined' && !!document.getElementById('setup'));
  if (opts.render === false) await page.evaluate(() => { window.loop = () => {}; });
  page.errors = errors;
  return page;
}

// Start a solo game with the AI playing instantly. Returns basic facts about the new game.
async function newSolo(page, cfg = {}) {
  return page.evaluate(c => {
    aiSpeed = 0; followAI = false;
    cfg = Object.assign({ size: 11, enemies: 1, faction: 'AEGIS', diff: 'normal', map: 'classic', mods: [] }, c);
    $('setup').classList.remove('show'); newGame(); gen++;
    return { W, side, me: MYSIDE, enemies: [...enemySides] };
  }, cfg);
}

// `game` fixture: a page with the draw loop stopped; the test fails if the page threw any error.
const test = base.test.extend({
  game: async ({ context }, use) => {
    const page = await openGame(context, { render: false });
    await use(page);
    base.expect(page.errors, 'page errors').toEqual([]);
  },
});

module.exports = { test, expect: base.expect, openGame, newSolo, GAME, GAME_URL, IGNORED };
