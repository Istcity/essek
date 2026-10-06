self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.map((k) => caches.delete(k))
    )).then(() => self.registration.unregister())
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Always network-first, no stale caching
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
