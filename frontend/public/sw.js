/* EcoSignal Service Worker — notification click handling */

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/home'
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin)) {
          client.focus()
          client.postMessage({ type: 'NAVIGATE', url })
          return
        }
      }
      return clients.openWindow(url)
    })
  )
})
