// FaceMortgage Service Worker
// Handles caching, offline support, and push notifications

const CACHE_NAME = 'facemortgage-v1';
const OFFLINE_URL = '/offline.html';

// Assets to precache on install
const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/favicon.ico',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');

  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      console.log('[ServiceWorker] Pre-caching critical assets');

      // Cache assets individually to handle failures gracefully
      for (const asset of PRECACHE_ASSETS) {
        try {
          await cache.add(asset);
          console.log(`[ServiceWorker] Cached: ${asset}`);
        } catch (error) {
          console.warn(`[ServiceWorker] Failed to cache: ${asset}`, error);
        }
      }

      // Skip waiting to activate immediately
      await self.skipWaiting();
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');

  event.waitUntil(
    (async () => {
      // Clean up old caches
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log(`[ServiceWorker] Deleting old cache: ${name}`);
            return caches.delete(name);
          })
      );

      // Take control of all clients immediately
      await self.clients.claim();
      console.log('[ServiceWorker] Now controlling all clients');
    })()
  );
});

// Fetch event - network-first with cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip WebSocket connections
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }

  // Skip API requests (don't cache them)
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    return;
  }

  // Skip browser extensions
  if (url.protocol === 'chrome-extension:' || url.protocol === 'moz-extension:') {
    return;
  }

  event.respondWith(
    (async () => {
      try {
        // Network-first strategy
        const networkResponse = await fetch(request);

        // Cache successful responses
        if (networkResponse.ok) {
          const cache = await caches.open(CACHE_NAME);
          // Clone the response since it can only be consumed once
          cache.put(request, networkResponse.clone());
        }

        return networkResponse;
      } catch (error) {
        console.log('[ServiceWorker] Network request failed, trying cache:', request.url);

        // Try to get from cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
          console.log('[ServiceWorker] Serving from cache:', request.url);
          return cachedResponse;
        }

        // For navigation requests, return offline page
        if (request.mode === 'navigate') {
          console.log('[ServiceWorker] Serving offline page');
          const offlineResponse = await caches.match(OFFLINE_URL);
          if (offlineResponse) {
            return offlineResponse;
          }
        }

        // For other requests, return a simple error response
        return new Response('Network error', {
          status: 503,
          statusText: 'Service Unavailable',
          headers: new Headers({
            'Content-Type': 'text/plain',
          }),
        });
      }
    })()
  );
});

// Push notification handler
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');

  let data = {
    title: 'FaceMortgage',
    body: 'You have a new notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: 'default',
    requireInteraction: false,
    data: {},
  };

  // Parse push data if available
  if (event.data) {
    try {
      const pushData = event.data.json();
      data = {
        title: pushData.title || data.title,
        body: pushData.body || data.body,
        icon: pushData.icon || data.icon,
        badge: pushData.badge || data.badge,
        tag: pushData.tag || data.tag,
        requireInteraction: pushData.requireInteraction || data.requireInteraction,
        data: pushData.data || data.data,
      };
    } catch (error) {
      console.warn('[ServiceWorker] Failed to parse push data:', error);
      data.body = event.data.text();
    }
  }

  // Show notification
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: data.icon,
      badge: data.badge,
      tag: data.tag,
      requireInteraction: data.requireInteraction,
      data: data.data,
      vibrate: [200, 100, 200],
      actions: getNotificationActions(data.data),
    })
  );
});

// Get notification actions based on notification type
function getNotificationActions(data) {
  if (!data || !data.type) {
    return [];
  }

  switch (data.type) {
    case 'incoming_call':
      return [
        { action: 'answer', title: 'Answer', icon: '/icons/call-answer.png' },
        { action: 'decline', title: 'Decline', icon: '/icons/call-decline.png' },
      ];
    case 'new_lead':
      return [
        { action: 'view', title: 'View Lead', icon: '/icons/view.png' },
        { action: 'dismiss', title: 'Dismiss', icon: '/icons/dismiss.png' },
      ];
    case 'scheduled_call':
      return [
        { action: 'view', title: 'View Details', icon: '/icons/view.png' },
      ];
    default:
      return [];
  }
}

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification click:', event.action);

  const notification = event.notification;
  const data = notification.data || {};
  const action = event.action;

  // Close the notification
  notification.close();

  event.waitUntil(
    (async () => {
      // Get all window clients
      const clientList = await self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
      });

      let targetUrl = '/';

      // Determine target URL based on action and notification type
      switch (data.type) {
        case 'incoming_call':
          if (action === 'answer') {
            targetUrl = `/dashboard?answer_call=${data.call_id}`;
          } else if (action === 'decline') {
            // Just close notification, maybe send decline to server
            return;
          }
          break;
        case 'new_lead':
          if (action === 'view' || !action) {
            targetUrl = `/dashboard/leads?lead_id=${data.lead_id}`;
          } else if (action === 'dismiss') {
            return;
          }
          break;
        case 'scheduled_call':
          targetUrl = `/dashboard?scheduled_call=${data.scheduled_call_id}`;
          break;
        default:
          targetUrl = data.url || '/dashboard';
      }

      // Try to focus an existing window
      for (const client of clientList) {
        const clientUrl = new URL(client.url);
        if (clientUrl.origin === self.location.origin && 'focus' in client) {
          await client.focus();
          // Navigate to the target URL
          await client.navigate(targetUrl);
          return;
        }
      }

      // Open a new window if none exists
      if (self.clients.openWindow) {
        await self.clients.openWindow(targetUrl);
      }
    })()
  );
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
  console.log('[ServiceWorker] Notification closed:', event.notification.tag);

  // Could track notification dismissals here for analytics
  const data = event.notification.data || {};
  if (data.tracking_id) {
    // Fire and forget tracking
    fetch('/api/v1/analytics/notification-dismissed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tracking_id: data.tracking_id }),
    }).catch(() => {
      // Ignore errors for analytics
    });
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);

  if (event.tag === 'sync-pending-actions') {
    event.waitUntil(syncPendingActions());
  }
});

// Sync pending actions when back online
async function syncPendingActions() {
  try {
    // Get pending actions from IndexedDB (if implemented)
    // For now, just log that sync was triggered
    console.log('[ServiceWorker] Syncing pending actions...');

    // Could implement IndexedDB storage for offline actions
    // and sync them here when back online
  } catch (error) {
    console.error('[ServiceWorker] Sync failed:', error);
  }
}

// Message handler for client communication
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);

  const { type, payload } = event.data || {};

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    case 'CACHE_URLS':
      if (payload && Array.isArray(payload.urls)) {
        event.waitUntil(cacheUrls(payload.urls));
      }
      break;
    case 'CLEAR_CACHE':
      event.waitUntil(clearCache());
      break;
    default:
      console.log('[ServiceWorker] Unknown message type:', type);
  }
});

// Cache specific URLs
async function cacheUrls(urls) {
  const cache = await caches.open(CACHE_NAME);
  for (const url of urls) {
    try {
      await cache.add(url);
      console.log(`[ServiceWorker] Cached: ${url}`);
    } catch (error) {
      console.warn(`[ServiceWorker] Failed to cache: ${url}`, error);
    }
  }
}

// Clear all caches
async function clearCache() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((name) => caches.delete(name)));
  console.log('[ServiceWorker] All caches cleared');
}
