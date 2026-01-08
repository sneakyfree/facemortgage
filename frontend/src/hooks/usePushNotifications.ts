'use client';

import { useCallback, useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api/client';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// VAPID public key should be set in environment variables
const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';

export type PermissionState = 'default' | 'granted' | 'denied' | 'unsupported';

interface PushNotificationState {
  permission: PermissionState;
  isSubscribed: boolean;
  isLoading: boolean;
  error: string | null;
  subscription: PushSubscription | null;
}

interface UsePushNotificationsOptions {
  onPermissionChange?: (permission: PermissionState) => void;
  onSubscriptionChange?: (subscription: PushSubscription | null) => void;
  onError?: (error: string) => void;
}

interface UsePushNotificationsReturn extends PushNotificationState {
  requestPermission: () => Promise<PermissionState>;
  subscribeToNotifications: () => Promise<PushSubscription | null>;
  unsubscribe: () => Promise<boolean>;
  checkSubscription: () => Promise<PushSubscription | null>;
}

// Convert VAPID key from base64 to Uint8Array
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }

  return outputArray;
}

export function usePushNotifications(
  options: UsePushNotificationsOptions = {}
): UsePushNotificationsReturn {
  const { onPermissionChange, onSubscriptionChange, onError } = options;
  const { user, isAuthenticated } = useAuthStore();

  const [state, setState] = useState<PushNotificationState>({
    permission: 'default',
    isSubscribed: false,
    isLoading: true,
    error: null,
    subscription: null,
  });

  // Check if push notifications are supported
  const isSupported = useCallback((): boolean => {
    if (typeof window === 'undefined') return false;
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  }, []);

  // Get current permission state
  const getPermissionState = useCallback((): PermissionState => {
    if (!isSupported()) return 'unsupported';
    return Notification.permission as PermissionState;
  }, [isSupported]);

  // Check existing subscription
  const checkSubscription = useCallback(async (): Promise<PushSubscription | null> => {
    if (!isSupported()) return null;

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      setState((prev) => ({
        ...prev,
        isSubscribed: !!subscription,
        subscription,
        isLoading: false,
      }));

      return subscription;
    } catch (error) {
      console.error('Error checking push subscription:', error);
      setState((prev) => ({ ...prev, isLoading: false }));
      return null;
    }
  }, [isSupported]);

  // Request notification permission
  const requestPermission = useCallback(async (): Promise<PermissionState> => {
    if (!isSupported()) {
      const errorMsg = 'Push notifications are not supported in this browser';
      setState((prev) => ({ ...prev, error: errorMsg, permission: 'unsupported' }));
      onError?.(errorMsg);
      return 'unsupported';
    }

    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      const permission = await Notification.requestPermission();
      const permissionState = permission as PermissionState;

      setState((prev) => ({
        ...prev,
        permission: permissionState,
        isLoading: false,
      }));

      onPermissionChange?.(permissionState);
      return permissionState;
    } catch (error) {
      const errorMsg = 'Failed to request notification permission';
      console.error(errorMsg, error);
      setState((prev) => ({ ...prev, error: errorMsg, isLoading: false }));
      onError?.(errorMsg);
      return 'denied';
    }
  }, [isSupported, onPermissionChange, onError]);

  // Subscribe to push notifications
  const subscribeToNotifications = useCallback(async (): Promise<PushSubscription | null> => {
    if (!isSupported()) {
      onError?.('Push notifications are not supported');
      return null;
    }

    if (!VAPID_PUBLIC_KEY) {
      const errorMsg = 'VAPID public key is not configured';
      console.error(errorMsg);
      setState((prev) => ({ ...prev, error: errorMsg }));
      onError?.(errorMsg);
      return null;
    }

    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Ensure permission is granted
      let permission = getPermissionState();
      if (permission === 'default') {
        permission = await requestPermission();
      }

      if (permission !== 'granted') {
        const errorMsg = 'Notification permission not granted';
        setState((prev) => ({ ...prev, error: errorMsg, isLoading: false }));
        onError?.(errorMsg);
        return null;
      }

      // Get service worker registration
      const registration = await navigator.serviceWorker.ready;

      // Check for existing subscription
      let subscription = await registration.pushManager.getSubscription();

      // If no subscription exists, create one
      if (!subscription) {
        const applicationServerKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY);

        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: applicationServerKey as BufferSource,
        });
      }

      // Send subscription to server (uses httpOnly cookie auth)
      if (isAuthenticated && user) {
        try {
          await apiClient.post('/devices/push-subscription', {
            subscription: subscription.toJSON(),
            user_agent: navigator.userAgent,
          });
        } catch (error) {
          console.warn('Failed to save subscription to server:', error);
        }
      }

      setState((prev) => ({
        ...prev,
        isSubscribed: true,
        subscription,
        isLoading: false,
      }));

      onSubscriptionChange?.(subscription);
      return subscription;
    } catch (error) {
      const errorMsg = 'Failed to subscribe to push notifications';
      console.error(errorMsg, error);
      setState((prev) => ({ ...prev, error: errorMsg, isLoading: false }));
      onError?.(errorMsg);
      return null;
    }
  }, [isSupported, getPermissionState, requestPermission, isAuthenticated, user, onSubscriptionChange, onError]);

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async (): Promise<boolean> => {
    if (!isSupported()) return false;

    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        // Notify server about unsubscription (uses httpOnly cookie auth)
        if (isAuthenticated) {
          try {
            await apiClient.delete('/devices/push-subscription', {
              data: { endpoint: subscription.endpoint },
            });
          } catch (error) {
            console.warn('Failed to notify server about unsubscription:', error);
          }
        }

        // Unsubscribe locally
        await subscription.unsubscribe();
      }

      setState((prev) => ({
        ...prev,
        isSubscribed: false,
        subscription: null,
        isLoading: false,
      }));

      onSubscriptionChange?.(null);
      return true;
    } catch (error) {
      const errorMsg = 'Failed to unsubscribe from push notifications';
      console.error(errorMsg, error);
      setState((prev) => ({ ...prev, error: errorMsg, isLoading: false }));
      onError?.(errorMsg);
      return false;
    }
  }, [isSupported, isAuthenticated, onSubscriptionChange, onError]);

  // Initialize on mount
  useEffect(() => {
    if (!isSupported()) {
      setState((prev) => ({
        ...prev,
        permission: 'unsupported',
        isLoading: false,
      }));
      return;
    }

    // Get initial permission state
    const permission = getPermissionState();
    setState((prev) => ({ ...prev, permission }));

    // Check for existing subscription
    checkSubscription();
  }, [isSupported, getPermissionState, checkSubscription]);

  // Listen for permission changes (some browsers support this)
  useEffect(() => {
    if (!isSupported() || !('permissions' in navigator)) return;

    let permissionStatus: PermissionStatus | null = null;

    navigator.permissions
      .query({ name: 'notifications' })
      .then((status) => {
        permissionStatus = status;

        const handleChange = () => {
          const newPermission = status.state as PermissionState;
          setState((prev) => ({ ...prev, permission: newPermission }));
          onPermissionChange?.(newPermission);
        };

        status.addEventListener('change', handleChange);
      })
      .catch(() => {
        // Permissions API not fully supported
      });

    return () => {
      if (permissionStatus) {
        // Clean up would go here, but the API doesn't provide a clean way
      }
    };
  }, [isSupported, onPermissionChange]);

  return {
    ...state,
    requestPermission,
    subscribeToNotifications,
    unsubscribe,
    checkSubscription,
  };
}
