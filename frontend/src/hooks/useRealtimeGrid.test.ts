/**
 * useRealtimeGrid hook tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useRealtimeGrid } from './useRealtimeGrid';

// Mock localStorage
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage.store[key];
  }),
  clear: vi.fn(() => {
    mockLocalStorage.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Track WebSocket instances for testing
let wsInstances: MockWebSocket[] = [];

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    wsInstances.push(this);
    // Simulate connection opening
    setTimeout(() => {
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close', { code: code || 1000, reason }));
  }

  // Helper to simulate receiving a message
  receiveMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// Mock config
vi.mock('@/lib/config', () => ({
  WS_BASE_URL: 'ws://localhost:8000',
  config: {
    ws: {
      reconnectAttempts: 3,
      reconnectDelay: 100,
    },
  },
}));

// Mock grid store
const mockUpdateProfessional = vi.fn();
const mockRemoveProfessional = vi.fn();

vi.mock('@/stores/gridStore', () => ({
  useGridStore: vi.fn(() => ({
    updateProfessional: mockUpdateProfessional,
    removeProfessional: mockRemoveProfessional,
  })),
}));

describe('useRealtimeGrid', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    wsInstances = [];
    mockLocalStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: false }));

    expect(result.current.isConnected).toBe(false);
    expect(typeof result.current.sendPing).toBe('function');
    expect(typeof result.current.getOnlineCount).toBe('function');
    expect(typeof result.current.reconnect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
  });

  it('connects when enabled', async () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: true }));

    // Fast-forward to allow WebSocket connection
    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(1);
    expect(wsInstances[0].url).toBe('ws://localhost:8000/ws/grid');
  });

  it('uses the same URL regardless of auth (auth via httpOnly cookies)', async () => {
    // Token in localStorage doesn't affect the WebSocket URL anymore
    // Authentication is now handled via httpOnly cookies automatically sent by browser
    mockLocalStorage.store['access_token'] = 'my-auth-token';

    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // URL should not contain token - auth is via cookies, not URL params
    expect(wsInstances[0].url).toBe('ws://localhost:8000/ws/grid');
  });

  it('does not connect when disabled', () => {
    renderHook(() => useRealtimeGrid({ enabled: false }));

    expect(wsInstances.length).toBe(0);
  });

  it('handles professional_online event', async () => {
    const onProfessionalOnline = vi.fn();

    renderHook(() =>
      useRealtimeGrid({
        enabled: true,
        onProfessionalOnline,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_online',
        professional_id: 'pro-123',
      });
    });

    expect(mockUpdateProfessional).toHaveBeenCalledWith('pro-123', {
      status: 'online_available',
    });
    expect(onProfessionalOnline).toHaveBeenCalledWith('pro-123');
  });

  it('handles professional_offline event', async () => {
    const onProfessionalOffline = vi.fn();

    renderHook(() =>
      useRealtimeGrid({
        enabled: true,
        onProfessionalOffline,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_offline',
        professional_id: 'pro-456',
      });
    });

    expect(mockRemoveProfessional).toHaveBeenCalledWith('pro-456');
    expect(onProfessionalOffline).toHaveBeenCalledWith('pro-456');
  });

  it('handles professional_busy event', async () => {
    const onProfessionalBusy = vi.fn();

    renderHook(() =>
      useRealtimeGrid({
        enabled: true,
        onProfessionalBusy,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_busy',
        professional_id: 'pro-789',
      });
    });

    expect(mockUpdateProfessional).toHaveBeenCalledWith('pro-789', {
      status: 'online_busy',
    });
    expect(onProfessionalBusy).toHaveBeenCalledWith('pro-789');
  });

  it('handles professional_available event', async () => {
    const onProfessionalAvailable = vi.fn();

    renderHook(() =>
      useRealtimeGrid({
        enabled: true,
        onProfessionalAvailable,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_available',
        professional_id: 'pro-999',
      });
    });

    expect(mockUpdateProfessional).toHaveBeenCalledWith('pro-999', {
      status: 'online_available',
    });
    expect(onProfessionalAvailable).toHaveBeenCalledWith('pro-999');
  });

  it('handles professional_in_call event', async () => {
    const onProfessionalBusy = vi.fn();

    renderHook(() =>
      useRealtimeGrid({
        enabled: true,
        onProfessionalBusy,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_in_call',
        professional_id: 'pro-incall',
      });
    });

    expect(mockUpdateProfessional).toHaveBeenCalledWith('pro-incall', {
      status: 'online_busy',
    });
    expect(onProfessionalBusy).toHaveBeenCalledWith('pro-incall');
  });

  it('handles professional_away event', async () => {
    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({
        event: 'professional_away',
        professional_id: 'pro-away',
      });
    });

    expect(mockUpdateProfessional).toHaveBeenCalledWith('pro-away', {
      status: 'away',
    });
  });

  it('handles connected event and resets reconnect attempts', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({ event: 'connected' });
    });

    expect(consoleSpy).toHaveBeenCalledWith('Connected to grid updates WebSocket');

    consoleSpy.mockRestore();
  });

  it('handles pong event silently', async () => {
    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Should not throw
    act(() => {
      ws.receiveMessage({ event: 'pong' });
    });

    // No assertions needed - just ensuring it doesn't crash
  });

  it('handles unknown events gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({ event: 'some_unknown_event', data: 'test' });
    });

    expect(consoleSpy).toHaveBeenCalledWith('Unknown grid event:', 'some_unknown_event');

    consoleSpy.mockRestore();
  });

  it('handles malformed messages', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Send malformed JSON
    act(() => {
      ws.onmessage?.(new MessageEvent('message', { data: 'not json' }));
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Error parsing WebSocket message:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('sendPing sends a ping message', async () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      result.current.sendPing();
    });

    expect(ws.sentMessages).toContainEqual(JSON.stringify({ type: 'ping' }));
  });

  it('getOnlineCount sends get_online_count message', async () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      result.current.getOnlineCount();
    });

    expect(ws.sentMessages).toContainEqual(JSON.stringify({ type: 'get_online_count' }));
  });

  it('disconnect closes the WebSocket', async () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      result.current.disconnect();
    });

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });

  it('reconnect creates a new WebSocket connection', async () => {
    const { result } = renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(1);

    // Disconnect first
    act(() => {
      result.current.disconnect();
    });

    // Then reconnect
    act(() => {
      result.current.reconnect();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Should have created a new connection
    expect(wsInstances.length).toBe(2);
  });

  it('sends periodic pings when connected', async () => {
    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Fast forward 30 seconds for first ping
    await act(async () => {
      vi.advanceTimersByTime(30000);
    });

    expect(ws.sentMessages).toContainEqual(JSON.stringify({ type: 'ping' }));
  });

  it('cleans up on unmount', async () => {
    const { unmount } = renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    unmount();

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });

  it('logs reconnection attempt on close', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    renderHook(() => useRealtimeGrid({ enabled: true }));

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(1);
    const ws = wsInstances[0];

    // Simulate connection close (not by user)
    act(() => {
      ws.onclose?.(new CloseEvent('close', { code: 1006, reason: 'Connection lost' }));
    });

    // Should log reconnection attempt - the format is a single string
    const reconnectLogs = consoleSpy.mock.calls.filter(
      (call) => typeof call[0] === 'string' && call[0].includes('Reconnecting in')
    );
    expect(reconnectLogs.length).toBeGreaterThan(0);

    consoleSpy.mockRestore();
  });
});
