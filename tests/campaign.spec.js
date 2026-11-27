// Campaign generator invariants over many seeds and map sizes, plus starting a campaign battle.
const { test, expect } = require('./helpers/game');

test('generated campaign maps are sound', async ({ game }) => {
  test.setTimeout(120_000);
  const r = await game.evaluate(() => {
    const bad = [];
    const fail = (c, msg) => { if (bad.length < 20) bad.push('seed ' + c.seed + ' n=' + c.regions.length + ': ' + msg); };
    const facs = Object.keys(FACTIONS);
    let checked = 0;
    for (const n of [10, 14, 20]) for (let k = 1; k <= 25; k++) {
      const seed = k * 7919 + n, fac = facs[k % facs.length];
      const c = genCampaign(seed, n, fac, 'normal');
      checked++;
      const R = c.regions;
      if (R.length !== n) fail(c, 'asked for ' + n + ' regions, got ' + R.length);
      if (JSON.stringify(genCampaign(seed, n, fac, 'normal')) !== JSON.stringify(c)) fail(c, 'not reproducible from its seed');
      R.forEach((r, i) => {
        if (r.id !== i) fail(c, 'region id ' + r.id + ' at ' + i);
        if (r.nb.includes(i)) fail(c, r.name + ' borders itself');
        for (const k2 of r.nb) if (!R[k2] || !R[k2].nb.includes(i)) fail(c, 'border ' + i + '-' + k2 + ' is one way');
        for (const k2 of r.lane) if (!r.nb.includes(k2)) fail(c, 'sea lane ' + i + '-' + k2 + ' is not a border');
        if (!c.sides.includes(r.owner)) fail(c, r.name + ' has no owner');
        if (!r.name) fail(c, 'region ' + i + ' has no name');
      });
      if (new Set(R.map(r => r.name)).size !== R.length) fail(c, 'duplicate region names');
      // one connected map
      const seen = new Set([0]), q = [0];
      while (q.length) { const i = q.shift(); for (const k2 of R[i].nb) if (!seen.has(k2)) { seen.add(k2); q.push(k2); } }
      if (seen.size !== R.length) fail(c, 'map is not connected');
      // four different factions, the player first, and no faction the player's clashes with
      if (c.sides.length !== 4 || new Set(c.sides).size !== 4) fail(c, 'sides ' + c.sides);
      if (c.sides[0] !== fac) fail(c, 'player is not the first side');
      for (const f of c.sides) if (!FACTIONS[f]) fail(c, 'unknown faction ' + f);
      for (const f of (FACTION_CLASH[fac] || [])) if (c.sides.includes(f)) fail(c, fac + ' meets ' + f);
      for (const f of c.sides) {
        const caps = R.filter(r => r.capital && r.owner === f);
        if (caps.length !== 1) fail(c, f + ' has ' + caps.length + ' capitals');
      }
      // the player can attack something on turn 1, and a capital still guarded by its own regions cannot be attacked
      // unless there is nothing else to attack
      const targets = R.filter(r => campCanAttack(c, r));
      if (!targets.length) fail(c, 'nothing to attack on turn 1');
      for (const r of targets) if (r.owner === fac) fail(c, 'can attack own region ' + r.name);
      const nonCap = targets.filter(r => !r.capital).length;
      for (const r of targets) if (r.capital && r.nb.some(k2 => R[k2].owner === r.owner) && nonCap) fail(c, 'guarded capital ' + r.name + ' is open');
      // every battle has an objective with card text
      for (const r of R) if (r.owner !== fac) {
        const o = campObjFor(c, r, 'attack', r.owner);
        if (!o || !CAMP_OBJ[o.k] || !campObjText(o, r.owner)) { fail(c, 'objective for ' + r.name); break; }
      }
      // winnable: winning every battle conquers the map in at most n battles, ending with a win
      const w = JSON.parse(JSON.stringify(c));
      let battles = 0;
      while (!w.over && battles <= n) {
        const t = w.regions.find(r => campCanAttack(w, r));
        if (!t) { fail(c, 'stuck after ' + battles + ' battles'); break; }
        const from = t.owner, wasCap = t.capital, guards = t.nb.filter(k2 => w.regions[k2].owner === from);
        campTake(w, t, w.fac); battles++;
        if (t.owner !== w.fac) fail(c, 'a won battle did not take the region');
        if (wasCap && t.capital) fail(c, 'a taken capital stays a capital');
        if (wasCap && guards.some(k2 => w.regions[k2].owner !== w.fac)) fail(c, 'regions next to a fallen capital did not surrender');
        campEliminations(w); campCheckEnd(w);
      }
      if (w.over !== 'won') fail(c, 'not won after ' + battles + ' battles: ' + w.over);
      if ((w.out || []).length !== 3) fail(c, 'rivals driven out: ' + (w.out || []).length);
      // and losing your capital loses the campaign
      const l = JSON.parse(JSON.stringify(c));
      const myCap = l.regions.find(r => r.capital && r.owner === fac);
      campTake(l, myCap, l.sides[1]);
      if (!campCheckEnd(l) || l.over !== 'lost') fail(c, 'losing the capital did not end the campaign');
    }
    return { bad, checked };
  });
  expect(r.checked).toBe(75);
  expect(r.bad).toEqual([]);
});

test('rival turns keep the campaign consistent', async ({ game }) => {
  const r = await game.evaluate(() => {
    const bad = [];
    for (let seed = 1; seed <= 10; seed++) {
      const c = genCampaign(seed * 104729, 14, 'AEGIS', 'normal');
      for (let t = 0; t < 25 && !c.over; t++) {
        const before = c.turn;
        campRivals(c);
        if (c.turn !== before + 1) bad.push(seed + ': turn did not advance');
        if (c.defend) {
          const d = c.regions[c.defend.region];
          if (!d || d.owner !== c.fac) bad.push(seed + ': defence of a region that is not yours');
          if (!c.sides.includes(c.defend.enemy) || c.defend.enemy === c.fac) bad.push(seed + ': defence against ' + c.defend.enemy);
          c.defend = null;   // the player holds
        }
        for (const f of c.sides) if (c.regions.filter(q => q.capital && q.owner === f).length > 1) bad.push(seed + ': ' + f + ' has two capitals');
        if (c.regions.some(q => !c.sides.includes(q.owner))) bad.push(seed + ': region with no owner');
        if (c.log.length > 40) bad.push(seed + ': log grows without bound');
        campCheckEnd(c);
      }
    }
    return bad.slice(0, 20);
  });
  expect(r).toEqual([]);
});

test('a campaign battle starts, keeps its objective through a save, and plays a round', async ({ game }) => {
  const r = await game.evaluate(async () => {
    const c = genCampaign(4242, 14, 'AEGIS', 'normal');
    campSave(c); setupView('camp');
    const t = c.regions.find(q => campCanAttack(c, q));
    campSel = t.id; renderCampaign();
    const card = $('campCard').textContent;
    const o = campObjFor(c, t, 'attack', t.owner);
    campBattle('attack', t.id, t.owner, o); gen++;
    const got = { card: card.length, map: !!map, setupHidden: !$('setup').classList.contains('show'), enemies: enemySides.length, obj: gcfg.campaign && gcfg.campaign.obj && gcfg.campaign.obj.k, wantObj: o.k, foe: meta(enemySides[0]).faction.key, wantFoe: t.owner };
    const sv = JSON.parse(serializeGame());
    restoreGame(sv); gen++;
    got.objAfterRestore = gcfg.campaign && gcfg.campaign.obj && gcfg.campaign.obj.k;
    got.played = await __t.round(30000);
    return got;
  });
  expect(r.card).toBeGreaterThan(0);
  expect(r.map && r.setupHidden).toBe(true);
  expect(r.enemies).toBeGreaterThanOrEqual(1);
  expect(r.foe).toBe(r.wantFoe);
  expect(r.obj).toBe(r.wantObj);
  expect(r.objAfterRestore).toBe(r.wantObj);
  expect(r.played).toBe(true);
});
