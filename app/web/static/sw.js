// Service worker del Centro de Analitica del Mundial 2026.
// Autor: Jeshua Romero Guadarrama
//
// Estrategia: cacheamos el "esqueleto" de la app (HTML/CSS/JS/icono) para que
// cargue al instante y funcione sin conexion. Las llamadas a la API van siempre
// a la red (datos frescos); si la red falla, no se sirve cache de la API para
// no mostrar datos antiguos como si fueran en vivo.

const CACHE = "mundial2026-v6";
const SHELL = [
  "/",
  "/static/style.css",
  "/static/app.js",
  "/static/icon.svg",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // La API siempre desde la red.
  if (url.pathname.startsWith("/api/")) return;
  // El resto: primero cache, luego red (app shell).
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((resp) => {
      const copy = resp.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      return resp;
    }).catch(() => caches.match("/")))
  );
});
