/**
 * usePushNotifications hook tests.
 *
 * Tests cover:
 * - isSupported detection (SSR, service worker, PushManager)
 * - Permission request flow (granted, denied)
 * - Subscription management (subscribe, unsubscribe)
 * - Error handling
 * - VAPID key handling
 */
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

// Mock modules BEFORE importing the hook
// vi.mock calls are hoisted, so we use factory functions that reference vi.fn()

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { id: 'test-user-id', email: 'test@example.com' },
    isAuthenticated: true,
  })),
}));

vi.mock('@/lib/api/client', () => ({
  apiClient: {
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
  },
}));

// Import after mocking
import { usePushNotifications } from './usePushNotifications';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api/client';

// Type for our mock subscription
interface MockPushSubscription {
  endpoint: string;
  unsubscribe: Mock;
  toJSON: () => {
    endpoint: string;
    keys: { p256dh: string; auth: string };
  };
}

// Mock service worker registration
const createMockSubscription = (): MockPushSubscription => ({
  endpoint: 'https://fcm.googleapis.com/fcm/send/test-endpoint',
  unsubscribe: vi.fn().mockResolvedValue(true),
  toJSON: () => ({
    endpoint: 'https://fcm.googleapis.com/fcm/send/test-endpoint',
    keys: {
      p256dh: 'test-p256dh-key',
      auth: 'test-auth-key',
    },
  }),
});

let mockSubscription = createMockSubscription();

const mockPushManager = {
  getSubscription: vi.fn().mockResolvedValue(null),
  subscribe: vi.fn().mockResolvedValue(mockSubscription),
};

const mockServiceWorkerRegistration = {
  pushManager: mockPushManager,
};

// Setup browser API mocks
function setupBrowserMocks(options: {
  serviceWorkerSupported?: boolean;
  pushManagerSupported?: boolean;
  notificationSupported?: boolean;
  notificationPermission?: NotificationPermission;
} = {}) {
  const {
    serviceWorkerSupported = true,
    pushManagerSupported = true,
    notificationSupported = true,
    notificationPermission = 'default',
  } = options;

  // Mock navigator.serviceWorker
  // The hook checks 'serviceWorker' in navigator, so we need to delete the property
  // rather than set it to undefined
  if (serviceWorkerSupported) {
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        ready: Promise.resolve(mockServiceWorkerRegistration),
      },
      writable: true,
      configurable: true,
    });
  } else {
    // Delete the property entirely so 'serviceWorker' in navigator returns false
    // @ts-expect-error - navigator.serviceWorker is read-only; deleting for test
    delete navigator.serviceWorker;
  }

  // Mock PushManager
  // The hook checks 'PushManager' in window
  if (pushManagerSupported) {
    Object.defineProperty(window, 'PushManager', {
      value: class MockPushManager {},
      writable: true,
      configurable: true,
    });
  } else {
    // Delete the property entirely so 'PushManager' in window returns false
    delete (window as { PushManager?: unknown }).PushManager;
  }

  // Mock Notification
  // The hook checks 'Notification' in window
  if (notificationSupported) {
    Object.defineProperty(window, 'Notification', {
      value: {
        permission: notificationPermission,
        requestPermission: vi.fn().mockResolvedValue(notificationPermission),
      },
      writable: true,
      configurable: true,
    });
  } else {
    // Delete the property entirely so 'Notification' in window returns false
    delete (window as { Notification?: unknown }).Notification;
  }

  // Mock navigator.permissions
  Object.defineProperty(navigator, 'permissions', {
    value: {
      query: vi.fn().mockResolvedValue({
        state: notificationPermission,
        addEventListener: vi.fn(),
      }),
    },
    writable: true,
    configurable: true,
  });
}

describe('usePushNotifications', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSubscription = createMockSubscription();
    mockPushManager.getSubscription.mockResolvedValue(null);
    mockPushManager.subscribe.mockResolvedValue(mockSubscription);

    // Reset API client mocks
    vi.mocked(apiClient.post).mockResolvedValue({ data: { success: true } });
    vi.mocked(apiClient.delete).mockResolvedValue({ data: { success: true } });

    // Reset auth store mock
    vi.mocked(useAuthStore).mockReturnValue({
      user: { id: 'test-user-id', email: 'test@example.com' },
      isAuthenticated: true,
    } as ReturnType<typeof useAuthStore>);

    // Reset browser APIs to default supported state before each test
    setupBrowserMocks({ notificationPermission: 'default' });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('isSupported detection', () => {
    it('returns unsupported when service worker is not available', async () => {
      setupBrowserMocks({ serviceWorkerSupported: false });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('unsupported');
    });

    it('returns unsupported when PushManager is not available', async () => {
      setupBrowserMocks({ pushManagerSupported: false });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('unsupported');
    });

    it('returns unsupported when Notification API is not available', async () => {
      setupBrowserMocks({ notificationSupported: false });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('unsupported');
    });

    it('returns current permission state when all APIs are supported', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('granted');
    });
  });

  describe('requestPermission', () => {
    it('requests permission and updates state on granted', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });

      // Update mock to return granted after request
      (window.Notification.requestPermission as Mock).mockResolvedValue('granted');

      const onPermissionChange = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onPermissionChange })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let permission: string;
      await act(async () => {
        permission = await result.current.requestPermission();
      });

      expect(permission!).toBe('granted');
      expect(onPermissionChange).toHaveBeenCalledWith('granted');
    });

    it('requests permission and updates state on denied', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });

      (window.Notification.requestPermission as Mock).mockResolvedValue('denied');

      const onPermissionChange = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onPermissionChange })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let permission: string;
      await act(async () => {
        permission = await result.current.requestPermission();
      });

      expect(permission!).toBe('denied');
      expect(onPermissionChange).toHaveBeenCalledWith('denied');
    });

    it('returns unsupported when APIs are not available', async () => {
      setupBrowserMocks({ serviceWorkerSupported: false });

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let permission: string;
      await act(async () => {
        permission = await result.current.requestPermission();
      });

      expect(permission!).toBe('unsupported');
      expect(onError).toHaveBeenCalledWith(
        'Push notifications are not supported in this browser'
      );
    });

    it('handles permission request errors', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });

      (window.Notification.requestPermission as Mock).mockRejectedValue(
        new Error('Permission request failed')
      );

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let permission: string;
      await act(async () => {
        permission = await result.current.requestPermission();
      });

      expect(permission!).toBe('denied');
      expect(onError).toHaveBeenCalledWith('Failed to request notification permission');
      expect(result.current.error).toBe('Failed to request notification permission');
    });
  });

  describe('checkSubscription', () => {
    it('detects existing subscription', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isSubscribed).toBe(true);
      expect(result.current.subscription).toBeTruthy();
    });

    it('returns null when no subscription exists', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(null);

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isSubscribed).toBe(false);
      expect(result.current.subscription).toBeNull();
    });

    it('returns null when APIs not supported', async () => {
      setupBrowserMocks({ serviceWorkerSupported: false });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let subscription: PushSubscription | null;
      await act(async () => {
        subscription = await result.current.checkSubscription();
      });

      expect(subscription!).toBeNull();
    });
  });

  describe('subscribeToNotifications', () => {
    it('returns null when permission not granted', async () => {
      setupBrowserMocks({ notificationPermission: 'denied' });

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let subscription: PushSubscription | null;
      await act(async () => {
        subscription = await result.current.subscribeToNotifications();
      });

      expect(subscription!).toBeNull();
    });

    it('returns null when APIs not supported', async () => {
      setupBrowserMocks({ serviceWorkerSupported: false });

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let subscription: PushSubscription | null;
      await act(async () => {
        subscription = await result.current.subscribeToNotifications();
      });

      expect(subscription!).toBeNull();
      // onError may be called with different messages depending on the API check order
      expect(onError).toHaveBeenCalled();
    });

    it('handles missing VAPID key', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let subscription: PushSubscription | null;
      await act(async () => {
        subscription = await result.current.subscribeToNotifications();
      });

      // With empty VAPID key, should error
      expect(subscription!).toBeNull();
      expect(result.current.error).toContain('VAPID');
    });
  });

  describe('unsubscribe', () => {
    it('unsubscribes successfully when subscription exists', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);

      const onSubscriptionChange = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onSubscriptionChange })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSubscribed).toBe(true);
      });

      let success: boolean;
      await act(async () => {
        success = await result.current.unsubscribe();
      });

      expect(success!).toBe(true);
      expect(result.current.isSubscribed).toBe(false);
      expect(result.current.subscription).toBeNull();
      expect(mockSubscription.unsubscribe).toHaveBeenCalled();
      expect(onSubscriptionChange).toHaveBeenCalledWith(null);
    });

    it('notifies server when authenticated', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSubscribed).toBe(true);
      });

      await act(async () => {
        await result.current.unsubscribe();
      });

      expect(apiClient.delete).toHaveBeenCalledWith(
        '/devices/push-subscription',
        { data: { endpoint: mockSubscription.endpoint } }
      );
    });

    it('succeeds even when server notification fails', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);
      vi.mocked(apiClient.delete).mockRejectedValue(new Error('Server error'));

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let success: boolean;
      await act(async () => {
        success = await result.current.unsubscribe();
      });

      // Should still succeed locally even if server fails
      expect(success!).toBe(true);
      expect(result.current.isSubscribed).toBe(false);
    });

    it('returns false when APIs not supported', async () => {
      setupBrowserMocks({ serviceWorkerSupported: false });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let success: boolean;
      await act(async () => {
        success = await result.current.unsubscribe();
      });

      expect(success!).toBe(false);
    });

    it('handles unsubscribe errors gracefully', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);
      mockSubscription.unsubscribe.mockRejectedValue(
        new Error('Unsubscribe failed')
      );

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let success: boolean;
      await act(async () => {
        success = await result.current.unsubscribe();
      });

      expect(success!).toBe(false);
      expect(onError).toHaveBeenCalledWith(
        'Failed to unsubscribe from push notifications'
      );
      expect(result.current.error).toBe(
        'Failed to unsubscribe from push notifications'
      );
    });
  });

  describe('initial state', () => {
    it('initializes with correct default state', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });

      const { result } = renderHook(() => usePushNotifications());

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('default');
      expect(result.current.isSubscribed).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.subscription).toBeNull();
    });

    it('reflects granted permission on mount', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('granted');
    });

    it('reflects denied permission on mount', async () => {
      setupBrowserMocks({ notificationPermission: 'denied' });

      const { result } = renderHook(() => usePushNotifications());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.permission).toBe('denied');
    });
  });

  describe('callback options', () => {
    it('calls onPermissionChange callback', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });
      (window.Notification.requestPermission as Mock).mockResolvedValue('granted');

      const onPermissionChange = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onPermissionChange })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.requestPermission();
      });

      expect(onPermissionChange).toHaveBeenCalledWith('granted');
    });

    it('calls onError callback on errors', async () => {
      setupBrowserMocks({ notificationPermission: 'default' });
      (window.Notification.requestPermission as Mock).mockRejectedValue(
        new Error('Permission request failed')
      );

      const onError = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onError })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.requestPermission();
      });

      expect(onError).toHaveBeenCalled();
    });

    it('calls onSubscriptionChange on unsubscribe', async () => {
      setupBrowserMocks({ notificationPermission: 'granted' });
      mockPushManager.getSubscription.mockResolvedValue(mockSubscription);

      const onSubscriptionChange = vi.fn();
      const { result } = renderHook(() =>
        usePushNotifications({ onSubscriptionChange })
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.isSubscribed).toBe(true);
      });

      await act(async () => {
        await result.current.unsubscribe();
      });

      expect(onSubscriptionChange).toHaveBeenCalledWith(null);
    });
  });
});
