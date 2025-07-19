self.addEventListener('push', function(event) {
  let data = {};
  if (event.data) {
    data = event.data.json();
  }
  const options = {
    body: data.body || 'Notificación SoulTrack',
    icon: '/static/images/SOULTRACK-ICON-FONDO.png',
    badge: '/static/images/SOULTRACK-ICON-FONDO.png',
  };
  event.waitUntil(
    self.registration.showNotification(data.title || 'SoulTrack', options)
  );
});
