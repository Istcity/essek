const CACHE_NAME = 'tjk-ai-cache-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/css/mobile.css',
  '/js/app.js',
  '/js/race-simulator.js',
  '/js/coupon-builder.js',
  '/js/h2h-compare.js',
  '/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.map((k) => k !== CACHE_NAME && caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) {
    // Network first for dynamic race APIs
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
  } else {
    // Cache first for static assets
    e.respondWith(
      caches.match(e.request).then((res) => res || fetch(e.request))
    );
  }
});
