// Online play through the mock PeerJS relay: joining, moves syncing, the turn timer, quick messages and rejoining.
const { test, expect } = require('@playwright/test');
const mockNet = require('./helpers/mock-peer');

test.describe.configure({ timeout: 120_000 });

let net;
test.beforeEach(async ({ browser }) => { net = await mockNet(browser); });
test.afterEach(async () => {
  const errs = net.errors();
  await net.close();
  expect(errs, 'page errors').toEqual([]);
});

test('a guest joins, a move syncs to the host, and both see the turn timer', async () => {
  const h = await net.player('HOST'), g = await net.player('BOB');
  await net.startGame(h, [g], { size: 9, timer: 60 });
  // lobby to game: both are in, seated apart
  const seats = [await h.ev(() => [NET.host, MYSIDE, turnOrder.length]), await g.ev(() => [NET.client, MYSIDE, turnOrder.length])];
  expect(seats[0]).toEqual([true, 'P', 2]);
  expect(seats[1]).toEqual([true, 'A1', 2]);
  // the turn timer shows on both screens
  await expect(h.page.locator('#hudTimerBox')).toBeVisible();
  await expect(g.page.locator('#hudTimerBox')).toBeVisible();
  expect(await g.ev(() => typeof NET.turnEnds)).toBe('number');
  // the guest may not act on the host's turn
  const before = await h.ev(() => units.map(u => u.id + ':' + u.x + ',' + u.y).sort().join(' '));
  await g.ev(() => { const u = units.find(q => q.owner === MYSIDE); const t = [...reachable(u).values()][0]; if (t) act({ t: 'move', uid: u.id, x: t.x, y: t.y }); });
  await h.page.waitForTimeout(500);
  expect(await h.ev(() => units.map(u => u.id + ':' + u.x + ',' + u.y).sort().join(' '))).toBe(before);
  // host ends the turn, the guest moves, the host sees it
  await h.ev(() => act({ t: 'endturn' }));
  await g.page.waitForFunction(() => side === MYSIDE);
  await expect(g.page.locator('#hudTimer')).toHaveText(/\d:\d\d/);
  const mv = await g.ev(() => {
    const u = units.find(q => q.owner === MYSIDE && reachable(q).size);
    const t = [...reachable(u).values()][0];
    act({ t: 'move', uid: u.id, x: t.x, y: t.y });
    return { id: u.id, x: t.x, y: t.y };
  });
  await h.page.waitForFunction(m => { const u = units.find(q => q.id === m.id); return u && u.x === m.x && u.y === m.y; }, mv);
  // guest ends the turn, it comes back to the host
  await g.ev(() => act({ t: 'endturn' }));
  await h.page.waitForFunction(() => side === 'P');
  expect(await h.ev(() => turn)).toBe(2);
  expect(await g.ev(() => turn)).toBe(2);
});

test('quick messages reach every player, with a rate limit', async () => {
  const h = await net.player('HOST'), b = await net.player('BOB'), c = await net.player('CAT');
  await net.startGame(h, [b, c], { size: 9 });
  for (const p of [h, b, c]) await p.ev(() => { window.__n = []; const o = note; note = x => { if (x.icon === 'chat') __n.push(x.title + ': ' + x.text); return o(x); }; });
  await expect(b.page.locator('#emoteBtn')).toBeVisible();
  await b.ev(() => $('emoteBtn').click());
  await expect(b.page.locator('#emoteBar')).toBeVisible();
  const said = await b.ev(() => { const btn = [...$('emoteBar').querySelectorAll('button')][1]; btn.click(); return btn.textContent; });
  for (const p of [h, b, c]) await p.page.waitForFunction(t => __n.some(m => m.endsWith(t)), said);
  // the host relays at most a few messages from one player in a burst, and ignores unknown ones
  const shown = await h.ev(() => { const n0 = __n.length; for (let i = 0; i < 5; i++) NET.emote('A2', 2); NET.emote('A2', 42); return __n.length - n0; });
  expect(shown).toBeGreaterThanOrEqual(1);
  expect(shown).toBeLessThan(5);
});

test('a guest who reloads rejoins with the seat key; someone using their callsign without it is refused', async () => {
  const h = await net.player('HOST'), b = await net.player('BOB'), mal = await net.player('MAL');
  const code = await net.startGame(h, [b], { size: 9 });
  const tok = await b.ev(() => ({ mem: NET.tok, stored: (rejoinInfo() || {}).tok }));
  expect(tok.mem).toBeTruthy();
  expect(tok.stored).toBe(tok.mem);
  // MAL types BOB's callsign and presses Rejoin, with no seat key
  await mal.ev(c => { localStorage.setItem('foothold-rejoin', JSON.stringify({ code: c, name: 'BOB', t: Date.now() })); showSetup(); $('rejoinBtn').click(); }, code);
  await mal.page.waitForFunction(() => /in use/i.test($('mpStatus').textContent), null, { timeout: 30000 });
  expect(await mal.ev(() => NET.inGame)).toBe(false);
  expect(await h.ev(() => NET.humans.A1.name)).toBe('BOB');
  // BOB's tab reloads mid-game and he taps Rejoin online game
  await net.reload(b);
  await b.ev(() => showSetup());
  await expect(b.page.locator('#rejoinBtn')).toBeVisible();
  await b.ev(() => $('rejoinBtn').click());
  await b.page.waitForFunction(() => NET.inGame && map, null, { timeout: 30000 });
  await h.page.waitForFunction(() => NET.humans.A1.conn && NET.humans.A1.conn.open, null, { timeout: 30000 });
  expect(await b.ev(() => MYSIDE)).toBe('A1');
  // and play goes on: the host ends the turn and BOB gets his
  await h.ev(() => act({ t: 'endturn' }));
  await b.page.waitForFunction(() => side === MYSIDE, null, { timeout: 30000 });
  expect(await h.ev(() => isAI('A1'))).toBe(false);
  // BOB's connection drops; MAL tries again without the key, so the host is asked, and refuses
  net.cut(b, true);
  await h.page.waitForFunction(() => !(NET.humans.A1.conn && NET.humans.A1.conn.open), null, { timeout: 20000 });
  await mal.ev(c => { localStorage.setItem('foothold-rejoin', JSON.stringify({ code: c, name: 'BOB', t: Date.now() })); showSetup(); $('rejoinBtn').click(); }, code);
  await h.page.waitForFunction(() => /new device/.test($('netBar').textContent), null, { timeout: 15000 });
  await h.ev(() => [...$('netBar').querySelectorAll('button')].find(x => x.textContent === 'Refuse').click());
  await mal.page.waitForFunction(() => /did not let you in/i.test($('mpStatus').textContent), null, { timeout: 15000 });
  expect(await mal.ev(() => NET.inGame)).toBe(false);
});
