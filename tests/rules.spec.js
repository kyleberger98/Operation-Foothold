// Core rule regressions. These check rules and invariants, not tuned numbers, so balance changes should not break them.
const { test, expect, newSolo } = require('./helpers/game');

// Two factions whose perks are purely economic, so unit stats are the plain ones.
const PLAIN = { faction: 'SOLARIS', enemyFacs: ['CRIMSON'], mods: ['nofog'] };

test.describe('combat', () => {
  test('forecast matches the damage dealt and the return fire taken', async ({ game }) => {
    await newSolo(game, PLAIN);
    const rows = await game.evaluate(() => {
      const s = __t.strip();
      const pairs = [['INF', 'INF'], ['TNK', 'INF'], ['INF', 'TNK'], ['HEL', 'TNK'], ['TNK', 'HEL'], ['SNP', 'INF'], ['AA', 'HEL'], ['TNK', 'TNK']];
      const out = [];
      for (const [A, B] of pairs) {
        units = units.filter(u => !(u.y === s.y && u.x >= s.x && u.x < s.x + 4));
        side = 'P';
        const a = __t.put('P', A, s.x, s.y), d = __t.put('A1', B, s.x + 1, s.y);
        const f = forecast(a, d), ahp = a.hp, dhp = d.hp;
        attack(a, d);
        out.push({ pair: A + '>' + B, f, dealt: dhp - d.hp, taken: ahp - a.hp, killed: !units.includes(d) });
      }
      return out;
    });
    for (const r of rows) {
      expect(r.dealt, r.pair + ' damage dealt').toBe(r.f.dmg);
      expect(r.f.dmg, r.pair + ' always does damage').toBeGreaterThanOrEqual(1);
      expect(r.killed, r.pair + ' kill flag').toBe(r.f.kills);
      if (!r.killed) expect(r.taken, r.pair + ' return fire').toBe(r.f.rdmg);
    }
  });

  test('a Tank does not one-shot full-HP Infantry with Combat Drills', async ({ game }) => {
    await newSolo(game, PLAIN);
    const r = await game.evaluate(() => {
      const s = __t.strip();
      tech.P.add('MECH'); tech.A1.add('MARKS'); tech.A1.add('DRILLS');
      side = 'P';
      const t = __t.put('P', 'TNK', s.x, s.y), i = __t.put('A1', 'INF', s.x + 1, s.y);
      const f = forecast(t, i);
      return { dmg: f.dmg, hp: i.hp, max: i.maxHp, kills: f.kills };
    });
    expect(r.hp).toBe(r.max);
    expect(r.kills).toBe(false);
    expect(r.dmg).toBeLessThan(r.hp);
  });

  test('counters, range and terrain behave as the rules say', async ({ game }) => {
    await newSolo(game, PLAIN);
    const r = await game.evaluate(() => {
      const s = __t.strip();
      const reset = () => { units = units.filter(u => !(u.y === s.y && u.x >= s.x && u.x < s.x + 4)); side = 'P'; for (let dx = 0; dx < 4; dx++) __t.plains(s.x + dx, s.y); };
      const duel = (A, B, gap = 1, setup) => { reset(); const a = __t.put('P', A, s.x, s.y), d = __t.put('A1', B, s.x + gap, s.y); if (setup) setup(a, d); return forecast(a, d); };
      const out = {};
      out.helVsTank = duel('HEL', 'TNK'); out.tankVsHel = duel('TNK', 'HEL');
      out.aaVsHel = duel('AA', 'HEL'); out.helVsAa = duel('HEL', 'AA');
      out.snpVsTank = duel('SNP', 'TNK');
      // a ranged attack from beyond the target's reach draws no return fire, and siege guns never return fire
      out.artFar = duel('ART', 'INF', 2);
      out.snpFar = duel('SNP', 'INF', 2);
      out.infVsArt = duel('INF', 'ART', 1);
      // a hurt attacker hits softer
      out.full = duel('INF', 'INF');
      out.hurt = duel('INF', 'INF', 1, a => { a.hp = Math.ceil(a.maxHp / 2); });
      // forest gives the defender cover
      out.open = duel('TNK', 'INF');
      out.forest = duel('TNK', 'INF', 1, (a, d) => { tileAt(d.x, d.y).terrain = 'forest'; });
      // a melee kill advances into the tile; a ranged kill does not
      out.meleeKill = duel('TNK', 'INF', 1, (a, d) => { d.hp = 1; });
      out.rangedKill = duel('SNP', 'INF', 2, (a, d) => { d.hp = 1; });
      return out;
    });
    expect(r.helVsTank.cAtk, 'Helicopters are strong vs Tanks').toBe(true);
    expect(r.helVsTank.dmg).toBeGreaterThan(r.tankVsHel.dmg);
    expect(r.aaVsHel.cAtk, 'Flak is strong vs Helicopters').toBe(true);
    expect(r.aaVsHel.dmg).toBeGreaterThan(r.helVsAa.dmg);
    expect(r.snpVsTank.cDef, 'Tanks shrug off Sniper fire').toBe(true);
    expect(r.artFar.rdmg).toBe(0);
    expect(r.snpFar.rdmg).toBe(0);
    expect(r.infVsArt.rdmg, 'siege guns do not return fire').toBe(0);
    expect(r.hurt.dmg).toBeLessThan(r.full.dmg);
    expect(r.forest.dmg).toBeLessThan(r.open.dmg);
    expect(r.meleeKill.kills && r.meleeKill.advances).toBe(true);
    expect(r.rangedKill.kills).toBe(true);
    expect(r.rangedKill.advances).toBe(false);
  });
});

test('Titans: one per city of the Titan level, never past the cap', async ({ game }) => {
  await newSolo(game, { mods: ['nofog'] });
  const r = await game.evaluate(() => {
    const me = MYSIDE, L = titanLevel(), out = { L };
    const all = __t.cities();
    const mine = all.filter(q => q.c.owner === me), rest = all.filter(q => q.c.owner !== me && !q.c.capital);
    const [A, B, C] = mine.concat(rest);
    for (const q of [A, B, C]) { q.c.owner = me; q.c.rw = []; units = units.filter(u => !(u.x === q.x && u.y === q.y)); }
    // every other city of mine stays below the Titan level
    for (const q of __t.cities(me)) if (q !== A && q !== B) q.c.level = Math.min(q.c.level, L - 1);
    A.c.level = L; B.c.level = L; C.c.level = L - 1;
    stars[me] = 500; refresh();
    out.cap = titanCap(me);
    out.lowCity = canFieldTitan(me, C.c);
    act({ t: 'train', k: 'TTN', x: C.x, y: C.y }); out.afterLow = titanCount(me);
    act({ t: 'train', k: 'TTN', x: A.x, y: A.y }); act({ t: 'train', k: 'TTN', x: B.x, y: B.y });
    out.afterTwo = titanCount(me);
    // clear city A and try again: the cap is reached
    const t = units.find(u => u.owner === me && u.type === 'TTN' && u.x === A.x && u.y === A.y);
    t.x = -99; t.y = -99;   // off the board but still counted
    units = units.filter(u => u === t || !(u.x === A.x && u.y === A.y));
    out.canMore = canFieldTitan(me, A.c);
    const st = stars[me]; act({ t: 'train', k: 'TTN', x: A.x, y: A.y });
    out.afterExtra = titanCount(me); out.paidForExtra = st - stars[me];
    // lose one and the city can train again
    units = units.filter(u => u !== t);
    out.canAfterLoss = canFieldTitan(me, A.c);
    act({ t: 'train', k: 'TTN', x: A.x, y: A.y }); out.afterRetrain = titanCount(me);
    return out;
  });
  expect(r.cap).toBe(2);
  expect(r.lowCity).toBe(false);
  expect(r.afterLow).toBe(0);
  expect(r.afterTwo).toBe(2);
  expect(r.canMore).toBe(false);
  expect(r.afterExtra).toBe(2);
  expect(r.paidForExtra).toBe(0);
  expect(r.canAfterLoss).toBe(true);
  expect(r.afterRetrain).toBe(2);
});

test('tribute demands have a cooldown', async ({ game }) => {
  await newSolo(game, { mods: ['nofog'] });
  const r = await game.evaluate(() => {
    const foe = enemySides[0], out = {};
    turn = 10; stars[foe] = 60;
    const demand = () => act({ t: 'dip', op: 'demand', to: foe, n: 5 });
    const snap = () => [stars.P, stars[foe], dip.last['P>' + foe + '$'], dip.good[foe + '>P'] || 0, dip.offers.length];
    out.wait0 = demandWait('P', foe);
    demand(); out.first = snap(); out.wait1 = demandWait('P', foe);
    demand(); out.again = snap();
    openDip(); renderDip();
    out.buttons = [...document.querySelectorAll('#dipList button')].filter(b => /Demand|Asked/i.test(b.textContent)).map(b => ({ t: b.textContent, off: b.disabled }));
    $('dipPanel').hidden = true;
    turn += out.wait1; out.wait2 = demandWait('P', foe);
    demand(); out.later = snap(); out.turn = turn;
    return out;
  });
  expect(r.wait0).toBe(0);
  expect(r.first[2], 'the first demand is recorded').toBe(10);
  expect(r.wait1).toBeGreaterThan(0);
  expect(r.again, 'a second demand during the cooldown does nothing').toEqual(r.first);
  expect(r.buttons.length).toBeGreaterThan(0);
  expect(r.buttons.every(b => b.off), 'Demand is disabled during the cooldown').toBe(true);
  expect(r.wait2).toBe(0);
  expect(r.later[2], 'after the cooldown a new demand goes through').toBe(r.turn);
});

test('a nuclear missile needs a confirming second click', async ({ game }) => {
  await newSolo(game, { mods: ['nofog'] });
  const r = await game.evaluate(() => {
    const me = MYSIDE, hq = __t.hq(me), out = {};
    units = units.filter(u => u.owner !== me);
    tech[me].add('NUKE');
    const n = __t.put(me, 'NUKE', hq.x, hq.y);
    // two open tiles in range, away from the HQ
    const spots = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const d = cheb(n, { x, y });
      if (d >= 3 && d <= uRange(n) && !tileAt(x, y).city && tileAt(x, y).terrain !== 'water' && !unitAt(x, y)) spots.push({ x, y });
    }
    const [a, b] = spots;
    const foe = __t.put(enemySides[0], 'INF', a.x, a.y);
    const live = () => units.includes(n) && !n.attacked;
    sel = { kind: 'unit', id: n.id }; refresh();
    onTileClick(a.x, a.y);
    out.afterAim = { live: live(), pending: !!pendingAtk, fc: $('forecast').textContent, foeHp: foe.hp };
    onTileClick(b.x, b.y);   // aiming elsewhere moves the aim, it does not fire
    out.afterReaim = { live: live(), pending: pendingAtk && [pendingAtk.tx, pendingAtk.ty], b: [b.x, b.y] };
    if (typeof quickOrder === 'function') { sel = { kind: 'unit', id: n.id }; pendingAtk = null; quickOrder(a.x, a.y); out.rightClickOnce = live(); }
    sel = { kind: 'unit', id: n.id }; pendingAtk = null; refresh();
    onTileClick(a.x, a.y); onTileClick(a.x, a.y);
    out.afterConfirm = { live: live(), foe: units.includes(foe) && foe.hp === foe.maxHp ? 'untouched' : 'hit' };
    return out;
  });
  expect(r.afterAim.live).toBe(true);
  expect(r.afterAim.pending).toBe(true);
  expect(r.afterAim.fc).toMatch(/again to launch/i);
  expect(r.afterReaim.live).toBe(true);
  expect(r.afterReaim.pending).toEqual(r.afterReaim.b);
  if (r.rightClickOnce !== undefined) expect(r.rightClickOnce, 'one right click does not launch').toBe(true);
  expect(r.afterConfirm.live).toBe(false);
  expect(r.afterConfirm.foe).toBe('hit');
});

test.describe('undo', () => {
  test('a move that reveals nothing can be undone; a move that scouts new ground is final', async ({ game }) => {
    await newSolo(game, {});
    const r = await game.evaluate(() => {
      const me = MYSIDE, out = {};
      const u = units.find(q => q.owner === me && reachable(q).size > 0);
      const tiles = [...reachable(u).values()].filter(p => !tileAt(p.x, p.y).ruin && !tileAt(p.x, p.y).city);
      // everything already explored: nothing new to see
      explored = explored.map(r => r.map(() => true));
      undoStack.length = 0; syncUndo();
      const from = { x: u.x, y: u.y }, to = tiles[0];
      act({ t: 'move', uid: u.id, x: to.x, y: to.y });
      out.moved = [u.x, u.y].join(',') === [to.x, to.y].join(',');
      out.stack1 = undoStack.length; out.btn1 = !$('undoBtn').hidden;
      undo();
      const u2 = byId(u.id);
      out.back = u2.x === from.x && u2.y === from.y && !u2.moved;
      // hide the ground around the destination: the move reveals it, so it cannot be taken back
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const x = to.x + dx, y = to.y + dy; if ((dx || dy) && inb(x, y)) explored[y][x] = false; }
      const s0 = __t.seen();
      act({ t: 'move', uid: u2.id, x: to.x, y: to.y });
      out.revealed = __t.seen() > s0;
      out.stack2 = undoStack.length; out.btn2 = !$('undoBtn').hidden;
      undo();
      out.stayed = byId(u.id).x === to.x && byId(u.id).y === to.y;
      return out;
    });
    expect(r.moved).toBe(true);
    expect(r.stack1).toBe(1);
    expect(r.btn1).toBe(true);
    expect(r.back).toBe(true);
    expect(r.revealed).toBe(true);
    expect(r.stack2).toBe(0);
    expect(r.btn2).toBe(false);
    expect(r.stayed).toBe(true);
  });

  test('training that reveals nothing is refunded by undo; a supply drop is final', async ({ game }) => {
    await newSolo(game, { mods: ['nofog'] });
    const r = await game.evaluate(() => {
      const me = MYSIDE, hq = __t.hq(me), out = {};
      units = units.filter(u => !(u.x === hq.x && u.y === hq.y));
      stars[me] = 30; undoStack.length = 0; refresh();
      const s0 = stars[me], n0 = units.length;
      act({ t: 'train', k: 'INF', x: hq.x, y: hq.y });
      out.trained = units.length === n0 + 1 && stars[me] < s0;
      undo();
      out.refunded = stars[me] === s0 && units.length === n0;
      // walking onto a supply drop cannot be undone
      const s = __t.strip();
      const u = __t.put(me, 'INF', s.x, s.y), t = { x: s.x + 1, y: s.y };
      tileAt(t.x, t.y).ruin = true; addDropDecor(t.x, t.y);
      undoStack.length = 0;
      act({ t: 'move', uid: u.id, x: t.x, y: t.y });
      out.dropStack = undoStack.length; out.dropTaken = !tileAt(t.x, t.y).ruin;
      return out;
    });
    expect(r.trained).toBe(true);
    expect(r.refunded).toBe(true);
    expect(r.dropTaken).toBe(true);
    expect(r.dropStack).toBe(0);
  });
});

test('treaty borders: units cannot enter a peace partner\'s land', async ({ game }) => {
  await newSolo(game, { enemies: 2, mods: ['nofog'] });
  const r = await game.evaluate(() => {
    const me = MYSIDE, [A1, A2] = enemySides, out = {};
    units = units.filter(u => u.owner !== me);
    const c = __t.hq(A1), tg = terrGrid();
    let pick = null;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const ix = c.x + dx, iy = c.y + dy, ox = c.x + 2 * dx, oy = c.y + 2 * dy;
      if (inb(ix, iy) && inb(ox, oy) && tg[iy][ix] === A1 && tg[oy][ox] !== A1 && !tileAt(ix, iy).city && !tileAt(ox, oy).city) { pick = { ix, iy, ox, oy }; break; }
    }
    __t.plains(pick.ix, pick.iy); __t.plains(pick.ox, pick.oy);
    units = units.filter(u => cheb(u, { x: pick.ix, y: pick.iy }) > 2);
    const inA1 = p => terrGrid()[p.y][p.x] === A1;
    // at war the border is open
    setRel(me, A1, 'war');
    let u = __t.put(me, 'TNK', pick.ox, pick.oy);
    out.warEnters = [...reachable(u).values()].some(inA1);
    // at peace it is closed
    setRel(me, A1, 'peace');
    out.peaceEnters = [...reachable(u).values()].some(inA1);
    out.peaceReach = reachable(u).size;
    // a unit that is already inside may walk out
    units = units.filter(q => q !== u);
    u = __t.put(me, 'INF', pick.ix, pick.iy);
    out.insideCanLeave = [...reachable(u).values()].some(p => !inA1(p));
    // a melee kill does not advance into the partner's land
    units = units.filter(q => q !== u);
    const v = __t.put(A2, 'INF', pick.ix, pick.iy); v.hp = 1;
    const a = __t.put(me, 'INF', pick.ox, pick.oy);
    side = me;
    out.fc = forecast(a, v);
    attack(a, v);
    out.victimDead = !units.includes(v);
    out.attackerStayed = a.x === pick.ox && a.y === pick.oy;
    // a landing craft cannot unload into it either
    units = units.filter(q => q !== a);
    tileAt(pick.ox, pick.oy).terrain = 'water';
    const craft = __t.put(me, 'LND', pick.ox, pick.oy);
    craft.cargo = { id: uid++, owner: me, type: 'INF', x: craft.x, y: craft.y, hp: 10, maxHp: 10, moved: true, attacked: true };
    out.unloadIntoPeace = unloadSpots(craft).some(inA1);
    setRel(me, A1, 'war');
    out.unloadAtWar = unloadSpots(craft).some(inA1);
    return out;
  });
  expect(r.warEnters).toBe(true);
  expect(r.peaceEnters).toBe(false);
  expect(r.peaceReach).toBeGreaterThan(0);
  expect(r.insideCanLeave).toBe(true);
  expect(r.fc.kills).toBe(true);
  expect(r.fc.advances).toBe(false);
  expect(r.victimDead).toBe(true);
  expect(r.attackerStayed).toBe(true);
  expect(r.unloadIntoPeace).toBe(false);
  expect(r.unloadAtWar).toBe(true);
});

// Movement basics that hold with or without zones of control: the board is cleared of every other unit.
test('movement basics on an empty board', async ({ game }) => {
  await newSolo(game, { mods: ['nofog'] });
  const r = await game.evaluate(() => {
    const me = MYSIDE, out = {};
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) if (!tileAt(x, y).city) __t.plains(x, y);
    units = [];
    const cx = Math.floor(W / 2), cy = Math.floor(H / 2);
    const check = type => {
      units = [];
      const u = __t.put(me, type, cx, cy), mv = uMove(u), got = reachable(u);
      let want = 0, missing = 0, extra = 0;
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        const d = cheb(u, { x, y }), inR = d >= 1 && d <= mv;
        if (inR) { want++; if (!got.has(key(x, y))) missing++; }
        else if (got.has(key(x, y))) extra++;
      }
      return { mv, want, missing, extra };
    };
    out.inf = check('INF'); out.tnk = check('TNK');
    // blocked tiles: water, mountain, any unit
    units = [];
    const u = __t.put(me, 'INF', cx, cy);
    tileAt(cx + 1, cy).terrain = 'water'; tileAt(cx - 1, cy).terrain = 'mountain';
    __t.put(me, 'INF', cx, cy + 1); __t.put(enemySides[0], 'INF', cx, cy - 1);
    const g = reachable(u);
    out.water = g.has(key(cx + 1, cy)); out.mountain = g.has(key(cx - 1, cy));
    out.own = g.has(key(cx, cy + 1)); out.enemy = g.has(key(cx, cy - 1));
    // flyers cross water and mountains; ships keep to water
    units = [];
    const h = __t.put(me, 'HEL', cx, cy); const hg = reachable(h);
    out.helWater = hg.has(key(cx + 1, cy)); out.helMountain = hg.has(key(cx - 1, cy));
    units = [];
    tileAt(cx + 1, cy).terrain = 'water';
    tech[me].add('NAVAL');
    const boat = __t.put(me, 'PTB', cx + 1, cy);
    out.boatLand = [...reachable(boat).values()].some(p => tileAt(p.x, p.y).terrain !== 'water');
    // one move per turn
    units = [];
    tileAt(cx + 1, cy).terrain = 'plains'; tileAt(cx - 1, cy).terrain = 'plains';
    const w = __t.put(me, 'INF', cx, cy);
    side = me;
    act({ t: 'move', uid: w.id, x: cx + 1, y: cy });
    out.walked = w.x === cx + 1 && w.y === cy && !!w.moved;
    out.secondMove = reachable(w).size;
    act({ t: 'move', uid: w.id, x: cx + 2, y: cy });
    out.stillThere = w.x === cx + 1;
    return out;
  });
  for (const k of ['inf', 'tnk']) {
    expect(r[k].want, k + ' has room to move').toBeGreaterThan(0);
    expect(r[k].missing, k + ' reaches every tile within its move').toBe(0);
    expect(r[k].extra, k + ' never goes past its move').toBe(0);
  }
  expect(r.water).toBe(false);
  expect(r.mountain).toBe(false);
  expect(r.own).toBe(false);
  expect(r.enemy).toBe(false);
  expect(r.helWater).toBe(true);
  expect(r.helMountain).toBe(true);
  expect(r.boatLand).toBe(false);
  expect(r.walked).toBe(true);
  expect(r.secondMove).toBe(0);
  expect(r.stillThere).toBe(true);
});
