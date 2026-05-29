'use client';

import { useEffect } from 'react';
import { logger } from '@/lib/utils';

export default function ServiceWorkerRegistration() {
  useEffect(() => {
    // Only register service worker in production or if explicitly enabled
    if (typeof window === 'undefined') return;
    // Skip SW in dev mode — HMR churn breaks the SW lifecycle
    if (process.env.NODE_ENV !== 'production' && !process.env.NEXT_PUBLIC_ENABLE_SW_IN_DEV) return;

    // Check if service workers are supported
    if (!('serviceWorker' in navigator)) {
      logger.log('[SW] Service workers are not supported');
      return;
    }

    // Register service worker
    const registerServiceWorker = async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/',
          updateViaCache: 'none',
        });

        logger.log('[SW] Service worker registered successfully:', registration.scope);

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            logger.log('[SW] New service worker installing...');

            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // New service worker available
                logger.log('[SW] New service worker available');

                // Optionally show update prompt to user
                if (window.confirm('A new version of FaceMortgage is available. Reload to update?')) {
                  // Tell the new service worker to skip waiting
                  newWorker.postMessage({ type: 'SKIP_WAITING' });
                  window.location.reload();
                }
              }
            });
          }
        });

        // Handle controller change (new SW took over)
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          logger.log('[SW] Controller changed, reloading...');
        });

        // Periodic update check (every hour)
        setInterval(() => {
          registration.update().catch((error) => {
            logger.warn('[SW] Update check failed:', error);
          });
        }, 60 * 60 * 1000);
      } catch (error) {
        logger.error('[SW] Service worker registration failed:', error);
      }
    };

    // Register on load
    if (document.readyState === 'complete') {
      registerServiceWorker();
    } else {
      window.addEventListener('load', registerServiceWorker);
      return () => window.removeEventListener('load', registerServiceWorker);
    }
  }, []);

  // This component doesn't render anything
  return null;
}
