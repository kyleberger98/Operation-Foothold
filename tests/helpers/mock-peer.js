// Mock PeerJS relay for multiplayer tests. Each player is its own browser context, and a fake `Peer` class in every
// page routes connections and messages through Node instead of the PeerJS cloud, so no network is used.
//   const net = await mockNet(browser); const host = await net.player('HOST'); ... await net.startGame(host, [guest]);
const { openGame } = require('./game');

// Runs in every page before the game script: replaces window.Peer.
const MOCK = () => {
  const peers = {}, conns = {};
  class Em {
    constructor() { this._h = {}; }
    on(e, f) { (this._h[e] = this._h[e] || []).push(f); return this; }
    emit(e, ...a) { (this._h[e] || []).slice().forEach(f => { try { f(...a); } catch (x) { console.error('mock handler', x); } }); }
  }
  class MockConn extends Em {
    constructor(id, peer) { super(); this.id = id; this.peer = peer; this.open = false; this._closed = false; conns[id] = this; }
    send(m) { if (!this.open) return; window.__netSend(this.id, JSON.stringify(m)); }
    close() { if (this._closed) return; this.open = false; this._closed = true; window.__netClose(this.id); this.emit('close'); }
  }
  class MockPeer extends Em {
    constructor(id) {
      super(); this.destroyed = false; this.lid = Math.random().toString(36).slice(2); peers[this.lid] = this;
      window.__netPeer(this.lid, id || null).then(r => {
        if (this.destroyed) return;
        if (r.err) { this.emit('error', { type: r.err }); return; }
        this.id = r.id; this.emit('open', r.id);
      });
    }
    connect(id) { const c = new MockConn('c' + Math.random().toString(36).slice(2), this); window.__netConnect(this.lid, c.id, id); return c; }
    destroy() {
      if (this.destroyed) return; this.destroyed = true;
      for (const k in conns) if (conns[k].peer === this && !conns[k]._closed) { conns[k].open = false; conns[k]._closed = true; }
      window.__netDestroy(this.lid);
    }
    reconnect() {}
  }
  window.__netIn = {
    conn(lid, cid) { const p = peers[lid]; if (!p || p.destroyed) return; const c = new MockConn(cid, p); p.emit('connection', c); },
    open(cid) { const c = conns[cid]; if (c && !c._closed) { c.open = true; c.emit('open'); } },
    data(cid, s) { const c = conns[cid]; if (c && c.open) c.emit('data', JSON.parse(s)); },
    close(cid) { const c = conns[cid]; if (c && !c._closed) { c.open = false; c._closed = true; c.emit('close'); } },
    err(lid, type) { const p = peers[lid]; if (p && !p.destroyed) p.emit('error', { type }); },
  };
  Object.defineProperty(window, 'Peer', { get: () => MockPeer, set() {}, configurable: true });
};

module.exports = async function mockNet(browser) {
  const ids = {};     // peer id -> {page, lid}
  const byLid = {};   // lid -> {page, id}
  const link = {};    // conn id -> {page, cid} at the other end
  const owner = {};   // conn id -> {page, lid}
  const offline = new Set();
  const q = new Map();
  // deliver in order per page
  const deliver = (page, fn, arg) => {
    const prev = q.get(page) || Promise.resolve();
    const next = prev.then(() => page.isClosed() ? null : page.evaluate(fn, arg)).catch(() => {});
    q.set(page, next); return next;
  };
  const closeEnd = cid => { const o = link[cid]; delete link[cid]; if (o) { delete link[o.cid]; deliver(o.page, c => window.__netIn.close(c), o.cid); } };
  const dropPage = page => {
    for (const cid in owner) if (owner[cid].page === page) { closeEnd(cid); delete owner[cid]; }
    for (const lid in byLid) if (byLid[lid].page === page) { delete ids[byLid[lid].id]; delete byLid[lid]; }
  };
  const players = [];

  async function player(name, o = {}) {
    const ctx = await browser.newContext({ viewport: o.viewport || { width: 560, height: 420 } });
    await ctx.addInitScript(MOCK);
    await ctx.exposeBinding('__netPeer', ({ page }, lid, id) => {
      if (offline.has(page)) return { err: 'network' };
      id = id || 'p' + Math.random().toString(36).slice(2);
      if (ids[id]) return { err: 'unavailable-id' };
      ids[id] = { page, lid }; byLid[lid] = { page, id }; return { id };
    });
    await ctx.exposeBinding('__netConnect', ({ page }, lid, cid, target) => {
      owner[cid] = { page, lid };
      const t = ids[target];
      if (!t || offline.has(page) || offline.has(t.page)) { setTimeout(() => deliver(page, ([l, ty]) => window.__netIn.err(l, ty), [lid, 'peer-unavailable']), 30); return; }
      const rc = cid + 'r';
      owner[rc] = { page: t.page, lid: t.lid };
      link[cid] = { page: t.page, cid: rc }; link[rc] = { page, cid };
      deliver(t.page, ([l, c]) => window.__netIn.conn(l, c), [t.lid, rc]);
      setTimeout(() => { deliver(t.page, c => window.__netIn.open(c), rc); deliver(page, c => window.__netIn.open(c), cid); }, 20);
    });
    await ctx.exposeBinding('__netSend', (src, cid, s) => { const o = link[cid]; if (o) deliver(o.page, ([c, m]) => window.__netIn.data(c, m), [o.cid, s]); });
    await ctx.exposeBinding('__netClose', (src, cid) => { closeEnd(cid); });
    await ctx.exposeBinding('__netDestroy', (src, lid) => {
      const p = byLid[lid]; if (p) { delete ids[p.id]; delete byLid[lid]; }
      for (const cid in owner) if (owner[cid].lid === lid) { closeEnd(cid); delete owner[cid]; }
    });
    const page = await openGame(ctx, { render: false });
    page.on('close', () => dropPage(page));
    await page.evaluate(() => { aiSpeed = 0; });
    const p = { name, ctx, page, ev: (f, a) => page.evaluate(f, a) };
    players.push(p);
    return p;
  }
  async function reload(p) {
    dropPage(p.page);
    await p.page.reload();
    await p.page.waitForFunction(() => typeof NET !== 'undefined' && typeof newGame === 'function');
    await p.page.evaluate(() => { window.loop = () => {}; aiSpeed = 0; });
  }
  // cut every live connection of a player, as a network drop would; optionally keep them offline
  function cut(p, stayOffline) {
    for (const cid in owner) if (owner[cid].page === p.page) { closeEnd(cid); deliver(p.page, c => window.__netIn.close(c), cid); }
    if (stayOffline) offline.add(p.page);
  }
  function online(p) { offline.delete(p.page); }
  // host opens a room, guests join, host launches
  async function startGame(host, guests, o = {}) {
    await host.ev(n => { $('mpName').value = n; setupView('mp'); NET.startHost(); }, host.name);
    await host.page.waitForFunction(() => NET.code && $('mpLobby').style.display !== 'none');
    const code = await host.ev(() => NET.code);
    if (o.size || o.timer != null) await host.ev(([s, t]) => { if (s) NET.size = s; if (t != null) NET.timer = t; NET.renderLobby(); NET.lobbySync(); }, [o.size, o.timer]);
    if (guests.length > 1) await host.ev(n => { for (let i = 2; i <= n; i++) NET.slots[i].kind = 'open'; NET.renderLobby(); }, guests.length);
    for (const g of guests) {
      await g.ev(([n, c]) => { $('mpName').value = n; $('mpCode').value = c; setupView('mp'); NET.join(); }, [g.name, code]);
      await g.page.waitForFunction(() => NET.mySlot);
    }
    await host.ev(() => NET.launch());
    for (const g of guests) await g.page.waitForFunction(() => NET.inGame && map);
    return code;
  }
  async function close() { for (const p of players) await p.ctx.close().catch(() => {}); }
  const errors = () => players.flatMap(p => p.page.errors.map(e => p.name + ': ' + e));
  return { player, reload, cut, online, startGame, close, errors };
};
