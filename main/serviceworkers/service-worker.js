// Evento de instalación
self.addEventListener('install', function(event) {
  console.log('[Service Worker] Instalando...');
  event.waitUntil(
    caches.open('v1').then(function(cache) {
      console.log('[Service Worker] Cache abierto');
      return cache.addAll([
        '/',
        '/static/css/dashboard.css',
        '/static/css/SeeleBot.css',
        '/static/images/SOULTRACK-ICON.png',
        '/static/images/SOULTRACK-ICON bb.png'
      ]);
    })
  );
});

// Evento de activación
self.addEventListener('activate', function(event) {
  console.log('[Service Worker] Activando...');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== 'v1') {
            console.log('[Service Worker] Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');

  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'Notificación', body: event.data.text() };
    }
  }

  const title = data.title || 'Notificación';
  const options = {
    body: data.body || 'Tienes una nueva notificación',
    icon: '/static/images/SOULTRACK-ICON.png',  // Usar icono existente
    badge: '/static/images/SOULTRACK-ICON bb.png', // Usar badge existente
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(windowClients => {
      // Si hay alguna ventana abierta, enfocarla
      for (const client of windowClients) {
        if (client.url === '/' && 'focus' in client) {
          return client.focus();
        }
      }
      // Si no, abrir una nueva ventana
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    })
  );
});
