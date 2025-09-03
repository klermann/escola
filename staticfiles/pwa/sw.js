/* v1.0 – Service Worker para Sistema Escolar */
const APP_CACHE = 'app-cache-v1';
const STATIC_CACHE = 'static-cache-v1';
const OFFLINE_URL = '/offline/';

const STATIC_ASSETS = [
  '/static/pwa/icons/icon-192.png',
  '/static/pwa/icons/icon-512.png',
  '/static/pwa/pwa-register.js',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll([OFFLINE_URL, ...STATIC_ASSETS]))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => ![APP_CACHE, STATIC_CACHE].includes(k))
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

function isAdmin(url) {
  return url.pathname.startsWith('/admin/');
}

function isApi(url) {
  return url.pathname.startsWith('/api/');
}

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Ignora métodos não-GET e requisições de admin/API
  if (req.method !== 'GET' || isAdmin(url) || isApi(url)) {
    return;
  }

  // Recursos estáticos: cache first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then(cached => {
        const fetchPromise = fetch(req).then(resp => {
          const copy = resp.clone();
          caches.open(STATIC_CACHE).then(cache => cache.put(req, copy));
          return resp;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Páginas: network first com fallback para cache
  event.respondWith(
    fetch(req)
      .then(resp => {
        const copy = resp.clone();
        caches.open(APP_CACHE).then(cache => cache.put(req, copy));
        return resp;
      })
      .catch(async () => {
        const cached = await caches.match(req);
        return cached || caches.match(OFFLINE_URL);
      })
  );
});