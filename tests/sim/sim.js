// AI-vs-AI balance simulator. Not part of `npm test`.
//   npm run sim -- [seed] [--rounds N] [--games N] [--turns T] [--size S] [--diff D] [--pages P] [--game path] [--out file.jsonl]
// Every seat, including the player's, is played by the game's own AI. By default each faction meets every other
// faction once from each seat (a 1v1 round robin, 42 games), and the script prints each faction's win rate.
// Math.random in the page is replaced by a generator seeded from [seed] and the game number, so the same seed starts
// the same games. Results are close to repeatable but not exact, because some of the AI's turn handling runs on timers.
// --games N stops after the first N games, for a quick check.
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { chromium } = require('@playwright/test');

const args = process.argv.slice(2);
const opt = { seed: 1, rounds: 1, games: 0, turns: 70, size: 11, diff: 'hard', pages: 2, game: path.join(__dirname, '..', '..', 'gridline-command.html'), out: null };
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a.startsWith('--')) { const k = a.slice(2); opt[k] = typeof opt[k] === 'number' ? +args[++i] : args[++i]; }
  else opt.seed = +a;
}
if (!Number.isFinite(opt.seed)) { console.error('seed must be a number'); process.exit(2); }

(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const url = pathToFileURL(path.resolve(opt.game)).href;
  const open = async () => {
    const ctx = await browser.newContext({ viewport: { width: 400, height: 300 } });
    await ctx.route(/^https?:\/\//, r => r.abort());
    await ctx.addInitScript(() => { try { localStorage.setItem('foothold-tutorial-done', '1'); } catch (e) {} });
    const page = await ctx.newPage();
    await page.goto(url);
    await page.waitForFunction(() => typeof newGame === 'function');
    await page.evaluate(() => { window.loop = () => {}; });
    return { ctx, page, used: 0 };
  };
  const factions = await (async () => { const w = await open(); const f = await w.page.evaluate(() => Object.keys(FACTIONS)); await w.ctx.close(); return f; })();
  const jobs = [];
  for (let r = 0; r < opt.rounds; r++) for (const a of factions) for (const b of factions) if (a !== b) jobs.push({ a, b, n: jobs.length });
  if (opt.games > 0) jobs.length = Math.min(jobs.length, opt.games);   // a quick partial run
  console.log(`seed ${opt.seed}: ${jobs.length} games, ${opt.size}x${opt.size}, ${opt.diff} AI on every seat, up to ${opt.turns} turns`);

  const results = [];
  let next = 0, done = 0;
  const t0 = Date.now();
  const worker = async () => {
    let w = null;
    while (next < jobs.length) {
      const j = jobs[next++];
      if (!w || w.used >= 8) { if (w) await w.ctx.close(); w = await open(); }   // a fresh page now and then keeps memory flat
      w.used++;
      const r = await w.page.evaluate(async ({ j, o }) => {
        // seeded Math.random (mulberry32)
        let s = (o.seed * 1000003 + j.n * 7919) >>> 0;
        Math.random = () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
        const errs = []; window.onerror = m => { errs.push(String(m)); };
        aiSpeed = 0; followAI = false;
        cfg = { size: o.size, enemies: 1, faction: j.a, enemyFacs: [j.b], diff: o.diff, map: 'classic', mods: [] };
        $('setup').classList.remove('show'); newGame();
        const wait = ms => new Promise(r => setTimeout(r, ms));
        let guard = 0;
        while (!gameOver && turn <= o.turns && guard++ < 5000) {
          if (side === P && alive[P]) await aiTurn(P);
          await wait(2);
        }
        const fac = Object.fromEntries(turnOrder.map(x => [x, meta(x).faction.key]));
        const left = turnOrder.filter(x => alive[x]);
        const winner = gameOver && left.length === 1 ? fac[left[0]] : null;
        return { p: fac.P, a1: fac.A1, winner, turns: turn, over: gameOver, errs };
      }, { j, o: opt });
      results.push(r);
      if (opt.out) fs.appendFileSync(opt.out, JSON.stringify(r) + '\n');
      done++;
      process.stdout.write(done % 10 ? '.' : String(done));
    }
    if (w) await w.ctx.close();
  };
  await Promise.all(Array.from({ length: Math.max(1, opt.pages) }, worker));
  await browser.close();
  process.stdout.write('\n');

  // the faction spread
  const st = Object.fromEntries(factions.map(f => [f, { games: 0, wins: 0, losses: 0, open: 0 }]));
  let firstSeat = 0, decided = 0, turns = 0;
  const errors = [];
  for (const r of results) {
    for (const f of [r.p, r.a1]) {
      st[f].games++;
      if (!r.winner) st[f].open++; else if (r.winner === f) st[f].wins++; else st[f].losses++;
    }
    if (r.winner) { decided++; turns += r.turns; if (r.winner === r.p) firstSeat++; }
    errors.push(...r.errs);
  }
  const rows = factions.map(f => ({ f, ...st[f], rate: st[f].games ? st[f].wins / st[f].games : 0 })).sort((x, y) => y.rate - x.rate);
  const pad = (s, n) => String(s).padEnd(n);
  console.log('\n' + pad('faction', 10) + pad('games', 7) + pad('wins', 6) + pad('losses', 8) + pad('unfinished', 12) + 'win rate');
  for (const r of rows) console.log(pad(r.f, 10) + pad(r.games, 7) + pad(r.wins, 6) + pad(r.losses, 8) + pad(r.open, 12) + (100 * r.rate).toFixed(0) + '%');
  const rates = rows.map(r => r.rate);
  console.log(`\nspread (best minus worst win rate): ${(100 * (Math.max(...rates) - Math.min(...rates))).toFixed(0)} points`);
  console.log(`decided games: ${decided}/${results.length}, average length ${decided ? (turns / decided).toFixed(1) : '-'} turns`);
  console.log(`first seat won ${firstSeat} of ${decided} decided games`);
  console.log(`time: ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  if (errors.length) { console.log(`page errors (${errors.length}):`, [...new Set(errors)].slice(0, 5)); process.exitCode = 1; }
})().catch(e => { console.error(e); process.exit(1); });
