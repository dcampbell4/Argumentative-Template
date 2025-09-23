/* service-worker.js */
const CACHE_NAME = 'awc-cache-v2';
const ENTRY_HTML = '/index.html';

const PRECACHE_ASSETS = [
  '/',
  ENTRY_HTML,
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon-180.png'
];

// Install: pre-cache the core assets (app shell)
self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_ASSETS))
  );
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => (k !== CACHE_NAME ? caches.delete(k) : null)));
    await self.clients.claim();
  })());
});

// Fetch strategy:
// - Navigations (HTML pages): network-first (fresh if online), fallback to cached entry or minimal offline
// - CSS/JS: stale-while-revalidate
// - Images: cache-first
// - Others: network, fallback to cache
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  if (req.method !== 'GET') return;

  // Page navigations
  if (req.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(req));
    return;
  }

  // Same-origin optimizations
  if (url.origin === self.origin) {
    if (/\.(?:css|js)$/.test(url.pathname)) {
      event.respondWith(staleWhileRevalidate(req));
      return;
    }
    if (/\.(?:png|jpg|jpeg|gif|webp|svg|ico)$/.test(url.pathname)) {
      event.respondWith(cacheFirst(req));
      return;
    }
  }

  // Default
  event.respondWith(fetch(req).catch(() => caches.match(req)));
});

async function networkFirstNavigation(request) {
  try {
    const fresh = await fetch(request);
    const cache = await caches.open(CACHE_NAME);
    cache.put(ENTRY_HTML, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = (await caches.match(ENTRY_HTML)) || (await caches.match('/'));
    return (
      cached ||
      new Response(
        `<!doctype html><html><head><meta charset="utf-8"><title>Offline</title><meta name="viewport" content="width=device-width, initial-scale=1"/></head><body><h1>Offline</h1><p>The app is unavailable offline for this page.</p></body></html>`,
        { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
      )
    );
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then(res => { cache.put(request, res.clone()); return res; })
    .catch(() => undefined);
  return cached || networkPromise || fetch(request);
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;
  const res = await fetch(request);
  cache.put(request, res.clone());
  return res;
}
