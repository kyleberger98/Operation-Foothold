/* Service worker that makes Gridline Command installable and playable offline.
   Pages go to the network so updates arrive on the next online visit. If the network is slow (3 s) or offline,
   the cached page is served instead and the download finishes in the background for next time.
   Icons and other files are cache first. Google Fonts are cached at install, then served from cache and refreshed in the background.
   Online multiplayer traffic is never touched. Bump VERSION with each release so icons and the manifest refresh. */
const VERSION = 'gc-v2';
const SHELL = [
  './', './index.html', './gridline-command.html', './operation-foothold-final.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/maskable-192.png', './icons/maskable-512.png',
  './icons/apple-touch-icon.png', './icons/favicon-64.png'
];
const FONTS = 'gc-fonts';
const FONT_CSS = 'https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;700&family=Nunito:wght@500;600;700;800&display=swap';
const SLOW = 3000;

// the page asks for the fonts before this worker exists, so fetch them here once (latin subsets only)
function cacheFonts() {
  return caches.open(FONTS).then(async c => {
    if (await c.match(FONT_CSS, {ignoreVary: true})) return;
    const r = await fetch(FONT_CSS);
    if (!r.ok) return;
    const css = await r.clone().text();
    const urls = new Set();
    for (const block of css.split('/* ')) {
      if (!/^latin(-ext)? \*\//.test(block)) continue;
      for (const m of block.matchAll(/url\((https:\/\/fonts\.gstatic\.com\/[^)]+)\)/g)) urls.add(m[1]);
    }
    await Promise.all([...urls].map(u => fetch(u).then(f => { if (f.ok) return c.put(u, f); })));
    await c.put(FONT_CSS, r);
  }).catch(() => {});
}
self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL))
    .then(() => Promise.race([cacheFonts(), new Promise(r => setTimeout(r, 10000))]))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== FONTS).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
const cachedPage = req => caches.match(req, {ignoreSearch: true}).then(hit => hit || caches.match('./gridline-command.html'));
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(caches.open(FONTS).then(async c => {
      const hit = await c.match(req, {ignoreVary: true});
      const net = fetch(req).then(r => { if (r.ok || r.type === 'opaque') c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    }));
    return;
  }
  if (url.origin !== location.origin) return;
  if (req.mode === 'navigate' || url.pathname.endsWith('.html')) {
    const net = fetch(req, {cache: 'no-cache'}).then(r => {
      if (!r.ok) return r;
      const copy = r.clone();
      return caches.open(VERSION).then(c => c.put(req, copy)).then(() => r, () => r);
    });
    e.waitUntil(net.catch(() => {}));   // keep the worker alive until the cache is updated
    e.respondWith(new Promise(done => {
      const t = setTimeout(() => cachedPage(req).then(hit => { if (hit) done(hit); }), SLOW);
      net.then(r => { clearTimeout(t); done(r); },
        () => { clearTimeout(t); cachedPage(req).then(hit => done(hit || Response.error())); });
    }));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
    return r;
  })));
});
