/**
 * useProfessionalPresence hook tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useProfessionalPresence } from './useProfessionalPresence';

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
      heartbeatInterval: 1000,
    },
  },
}));

// Mock auth store
let mockUser: { professional_profile?: { id: string } } | null = null;
const mockGetAccessToken = vi.fn(() => 'test-token');

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: mockUser,
    getAccessToken: mockGetAccessToken,
  })),
}));

describe('useProfessionalPresence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    wsInstances = [];
    mockUser = null;
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => useProfessionalPresence());

    expect(result.current.isConnected).toBe(false);
    expect(result.current.currentStatus).toBe('offline');
    expect(result.current.error).toBe(null);
  });

  it('provides all required functions', () => {
    const { result } = renderHook(() => useProfessionalPresence());

    expect(typeof result.current.goOnline).toBe('function');
    expect(typeof result.current.goOffline).toBe('function');
    expect(typeof result.current.setAvailable).toBe('function');
    expect(typeof result.current.setBusy).toBe('function');
    expect(typeof result.current.setInCall).toBe('function');
    expect(typeof result.current.setAway).toBe('function');
    expect(typeof result.current.toggleCamera).toBe('function');
    expect(typeof result.current.reconnect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
  });

  it('does not connect without professional profile', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    mockUser = { professional_profile: undefined };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    expect(consoleSpy).toHaveBeenCalledWith('Cannot connect: No professional profile');
    expect(wsInstances.length).toBe(0);

    consoleSpy.mockRestore();
  });

  it('connects with professional profile', async () => {
    mockUser = { professional_profile: { id: 'pro-123' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(1);
    expect(wsInstances[0].url).toBe('ws://localhost:8000/ws/presence/pro-123?token=test-token');
  });

  it('updates state on connection open', async () => {
    mockUser = { professional_profile: { id: 'pro-456' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.currentStatus).toBe('online_available');
    expect(result.current.error).toBe(null);
  });

  it('handles status_updated message', async () => {
    const onStatusChange = vi.fn();
    mockUser = { professional_profile: { id: 'pro-789' } };

    const { result } = renderHook(() =>
      useProfessionalPresence({ onStatusChange })
    );

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({ type: 'status_updated', status: 'busy' });
    });

    expect(result.current.currentStatus).toBe('online_busy');
    expect(onStatusChange).toHaveBeenCalledWith('online_busy');
  });

  it('maps status strings correctly', async () => {
    mockUser = { professional_profile: { id: 'pro-map' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Test various status mappings
    const statusTests = [
      { input: 'available', expected: 'online_available' },
      { input: 'online_available', expected: 'online_available' },
      { input: 'busy', expected: 'online_busy' },
      { input: 'online_busy', expected: 'online_busy' },
      { input: 'in_call', expected: 'in_call' },
      { input: 'away', expected: 'away' },
      { input: 'offline', expected: 'offline' },
      { input: 'unknown_status', expected: 'offline' }, // Default fallback
    ];

    for (const test of statusTests) {
      act(() => {
        ws.receiveMessage({ type: 'status_updated', status: test.input });
      });
      expect(result.current.currentStatus).toBe(test.expected);
    }
  });

  it('handles error message', async () => {
    const onError = vi.fn();
    mockUser = { professional_profile: { id: 'pro-err' } };

    const { result } = renderHook(() =>
      useProfessionalPresence({ onError })
    );

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({ type: 'error', message: 'Test error message' });
    });

    expect(result.current.error).toBe('Test error message');
    expect(onError).toHaveBeenCalledWith('Test error message');
  });

  it('handles heartbeat_ack silently', async () => {
    mockUser = { professional_profile: { id: 'pro-hb' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Should not throw
    act(() => {
      ws.receiveMessage({ type: 'heartbeat_ack' });
    });
  });

  it('handles unknown message types gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    mockUser = { professional_profile: { id: 'pro-unk' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.receiveMessage({ type: 'some_unknown_type' });
    });

    expect(consoleSpy).toHaveBeenCalledWith('Unknown presence message:', 'some_unknown_type');

    consoleSpy.mockRestore();
  });

  it('starts heartbeat on connection', async () => {
    mockUser = { professional_profile: { id: 'pro-hb2' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Advance time for heartbeat
    await act(async () => {
      vi.advanceTimersByTime(1000);
    });

    expect(ws.sentMessages).toContainEqual(JSON.stringify({ type: 'heartbeat' }));
  });

  it('setAvailable sends status_update message', async () => {
    mockUser = { professional_profile: { id: 'pro-avail' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];
    ws.sentMessages = []; // Clear previous messages

    act(() => {
      result.current.setAvailable();
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'status_update',
        data: { status: 'online_available', room_id: undefined },
      })
    );
  });

  it('setBusy sends status_update with optional roomId', async () => {
    mockUser = { professional_profile: { id: 'pro-busy' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];
    ws.sentMessages = [];

    act(() => {
      result.current.setBusy('room-123');
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'status_update',
        data: { status: 'online_busy', room_id: 'room-123' },
      })
    );
  });

  it('setInCall sends status_update with roomId', async () => {
    mockUser = { professional_profile: { id: 'pro-incall' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];
    ws.sentMessages = [];

    act(() => {
      result.current.setInCall('call-room-456');
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'status_update',
        data: { status: 'in_call', room_id: 'call-room-456' },
      })
    );
  });

  it('setAway sends status_update', async () => {
    mockUser = { professional_profile: { id: 'pro-away' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];
    ws.sentMessages = [];

    act(() => {
      result.current.setAway();
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'status_update',
        data: { status: 'away', room_id: undefined },
      })
    );
  });

  it('toggleCamera sends camera_toggle message', async () => {
    mockUser = { professional_profile: { id: 'pro-cam' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];
    ws.sentMessages = [];

    act(() => {
      result.current.toggleCamera(true);
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'camera_toggle',
        data: { camera_on: true },
      })
    );

    act(() => {
      result.current.toggleCamera(false);
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'camera_toggle',
        data: { camera_on: false },
      })
    );
  });

  it('goOffline sends offline status and disconnects', async () => {
    mockUser = { professional_profile: { id: 'pro-off' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      result.current.goOffline();
    });

    expect(ws.sentMessages).toContainEqual(
      JSON.stringify({
        type: 'status_update',
        data: { status: 'offline', room_id: undefined },
      })
    );
    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
    expect(result.current.currentStatus).toBe('offline');
    expect(result.current.isConnected).toBe(false);
  });

  it('disconnect closes WebSocket and clears state', async () => {
    mockUser = { professional_profile: { id: 'pro-disc' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      result.current.disconnect();
    });

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
    expect(result.current.isConnected).toBe(false);
    expect(result.current.currentStatus).toBe('offline');
    expect(result.current.error).toBe(null);
  });

  it('handles WebSocket close and attempts reconnection', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    mockUser = { professional_profile: { id: 'pro-reconn' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Simulate unexpected close
    act(() => {
      ws.onclose?.(new CloseEvent('close', { code: 1006, reason: 'Lost connection' }));
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.currentStatus).toBe('offline');

    // Should log reconnection attempt - the format is a single string
    const reconnectLogs = consoleSpy.mock.calls.filter(
      (call) => typeof call[0] === 'string' && call[0].includes('Reconnecting in')
    );
    expect(reconnectLogs.length).toBeGreaterThan(0);

    consoleSpy.mockRestore();
  });

  it('sets error after max reconnection attempts', async () => {
    const onError = vi.fn();
    mockUser = { professional_profile: { id: 'pro-maxreconn' } };

    const { result } = renderHook(() =>
      useProfessionalPresence({ onError })
    );

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    // Simulate multiple disconnections
    for (let i = 0; i < 6; i++) {
      const ws = wsInstances[wsInstances.length - 1];
      act(() => {
        ws.onclose?.(new CloseEvent('close', { code: 1006 }));
      });

      await act(async () => {
        vi.advanceTimersByTime(35000); // Allow for exponential backoff
      });
    }

    expect(result.current.error).toBe('Connection lost. Please refresh the page.');
    expect(onError).toHaveBeenCalledWith('Connection lost. Please refresh the page.');
  });

  it('handles WebSocket error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockUser = { professional_profile: { id: 'pro-wserr' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    act(() => {
      ws.onerror?.(new Event('error'));
    });

    expect(result.current.error).toBe('WebSocket connection error');
    expect(consoleSpy).toHaveBeenCalledWith('Presence WebSocket error:', expect.any(Event));

    consoleSpy.mockRestore();
  });

  it('cleans up on unmount', async () => {
    mockUser = { professional_profile: { id: 'pro-cleanup' } };

    const { result, unmount } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    unmount();

    expect(ws.readyState).toBe(MockWebSocket.CLOSED);
  });

  it('handles malformed messages', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockUser = { professional_profile: { id: 'pro-malformed' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    const ws = wsInstances[0];

    // Send malformed JSON
    act(() => {
      ws.onmessage?.(new MessageEvent('message', { data: 'invalid json' }));
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Error parsing presence message:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });

  it('reconnect function reconnects after disconnect', async () => {
    mockUser = { professional_profile: { id: 'pro-reconnfn' } };

    const { result } = renderHook(() => useProfessionalPresence());

    act(() => {
      result.current.goOnline();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(1);

    act(() => {
      result.current.disconnect();
    });

    act(() => {
      result.current.reconnect();
    });

    await act(async () => {
      vi.advanceTimersByTime(20);
    });

    expect(wsInstances.length).toBe(2);
    expect(result.current.isConnected).toBe(true);
  });
});
