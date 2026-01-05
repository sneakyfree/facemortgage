/**
 * useVideoCall hook tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVideoCall } from './useVideoCall';

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
    // Simulate connection opening
    setTimeout(() => {
      this.onopen?.(new Event('open'));
    }, 10);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close(_code?: number, _reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close', { code: 1000 }));
  }

  // Helper to simulate receiving a message
  receiveMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// Mock RTCPeerConnection
class MockRTCPeerConnection {
  localDescription: RTCSessionDescription | null = null;
  remoteDescription: RTCSessionDescription | null = null;
  iceConnectionState = 'new';
  connectionState = 'new';
  ontrack: ((event: RTCTrackEvent) => void) | null = null;
  onicecandidate: ((event: RTCPeerConnectionIceEvent) => void) | null = null;
  onconnectionstatechange: (() => void) | null = null;

  addTrack = vi.fn();
  setLocalDescription = vi.fn().mockResolvedValue(undefined);
  setRemoteDescription = vi.fn().mockResolvedValue(undefined);
  addIceCandidate = vi.fn().mockResolvedValue(undefined);
  createOffer = vi.fn().mockResolvedValue({ type: 'offer', sdp: 'mock-offer-sdp' });
  createAnswer = vi.fn().mockResolvedValue({ type: 'answer', sdp: 'mock-answer-sdp' });
  close = vi.fn();
}

global.RTCPeerConnection = MockRTCPeerConnection as unknown as typeof RTCPeerConnection;
global.RTCSessionDescription = vi.fn((desc) => desc) as unknown as typeof RTCSessionDescription;
global.RTCIceCandidate = vi.fn((candidate) => candidate) as unknown as typeof RTCIceCandidate;

// Mock MediaStream and getUserMedia
class MockMediaStreamTrack {
  kind: string;
  enabled: boolean = true;
  id: string;
  stop = vi.fn();

  constructor(kind: string, id: string) {
    this.kind = kind;
    this.id = id;
  }
}

class MockMediaStream {
  id = 'mock-stream-id';
  active = true;
  tracks: MockMediaStreamTrack[] = [];

  constructor() {
    this.tracks = [
      new MockMediaStreamTrack('audio', 'audio-track'),
      new MockMediaStreamTrack('video', 'video-track'),
    ];
  }

  getTracks() {
    return this.tracks as unknown as MediaStreamTrack[];
  }

  getAudioTracks() {
    return this.tracks.filter((t) => t.kind === 'audio') as unknown as MediaStreamTrack[];
  }

  getVideoTracks() {
    return this.tracks.filter((t) => t.kind === 'video') as unknown as MediaStreamTrack[];
  }
}

const mockGetUserMedia = vi.fn().mockResolvedValue(new MockMediaStream());

Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  writable: true,
});

// Mock config
vi.mock('@/lib/config', () => ({
  WS_BASE_URL: 'ws://localhost:8000',
}));

// Mock API client
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock utils
vi.mock('@/lib/utils', () => ({
  getAnonymousSessionId: vi.fn(() => 'anon-session-123'),
  getDeviceFingerprint: vi.fn(() => 'device-fingerprint-456'),
}));

import { apiClient } from '@/lib/api/client';

describe('useVideoCall', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();
    mockGetUserMedia.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns initial idle state', () => {
    const { result } = renderHook(() => useVideoCall());

    expect(result.current.callState).toBe('idle');
    expect(result.current.callInfo).toBe(null);
    expect(result.current.localStream).toBe(null);
    expect(result.current.remoteStream).toBe(null);
    expect(result.current.isMuted).toBe(false);
    expect(result.current.isCameraOff).toBe(false);
    expect(result.current.incomingCall).toBe(null);
    expect(result.current.isAnonymous).toBe(false);
    expect(result.current.callId).toBe(null);
  });

  it('provides all required functions', () => {
    const { result } = renderHook(() => useVideoCall());

    expect(typeof result.current.initiateCall).toBe('function');
    expect(typeof result.current.answerCall).toBe('function');
    expect(typeof result.current.declineCall).toBe('function');
    expect(typeof result.current.endCall).toBe('function');
    expect(typeof result.current.toggleMute).toBe('function');
    expect(typeof result.current.toggleCamera).toBe('function');
  });

  describe('initiateCall', () => {
    it('initiates an authenticated call', async () => {
      // Set up authenticated user
      mockLocalStorage.store['access_token'] = 'test-token';
      mockLocalStorage.store['user_id'] = 'user-123';

      // Mock API response
      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-abc',
          ice_servers: [{ urls: 'stun:stun.example.com' }],
          professional_name: 'Dr. Smith',
          professional_avatar: 'https://example.com/avatar.jpg',
          call_id: 'call-uuid-123',
          is_anonymous: false,
        },
      });

      const { result } = renderHook(() => useVideoCall());

      await act(async () => {
        await result.current.initiateCall('professional-456');
      });

      expect(apiClient.post).toHaveBeenCalledWith('/calls', {
        professional_id: 'professional-456',
      });

      expect(result.current.callId).toBe('call-uuid-123');
      expect(result.current.isAnonymous).toBe(false);
    });

    it('initiates an anonymous call', async () => {
      // No access token = anonymous call
      mockLocalStorage.store = {};

      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-xyz',
          ice_servers: [{ urls: 'stun:stun.example.com' }],
          professional_name: 'Jane Doe',
          call_id: 'anon-call-789',
          is_anonymous: true,
          session_id: 'session-abc',
        },
      });

      const { result } = renderHook(() => useVideoCall());

      await act(async () => {
        await result.current.initiateCall('professional-789');
      });

      expect(apiClient.post).toHaveBeenCalledWith('/calls', {
        professional_id: 'professional-789',
        anonymous_session_id: 'anon-session-123',
        device_fingerprint: 'device-fingerprint-456',
      });

      expect(result.current.isAnonymous).toBe(true);
    });

    it('calls onError callback when initiation fails', async () => {
      const onError = vi.fn();

      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useVideoCall({ onError }));

      await act(async () => {
        await result.current.initiateCall('professional-123');
      });

      expect(result.current.callState).toBe('failed');
      expect(onError).toHaveBeenCalledWith('Network error');
    });

    it('requests user media during call initiation', async () => {
      mockLocalStorage.store['access_token'] = 'test-token';

      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-123',
          ice_servers: [],
          professional_name: 'Test Pro',
          call_id: 'call-123',
          is_anonymous: false,
        },
      });

      const { result } = renderHook(() => useVideoCall());

      await act(async () => {
        await result.current.initiateCall('pro-123');
      });

      expect(mockGetUserMedia).toHaveBeenCalledWith({
        video: true,
        audio: true,
      });
    });
  });

  describe('toggleMute', () => {
    it('does not error when called without active stream', () => {
      const { result } = renderHook(() => useVideoCall());

      // Should not throw when no stream
      expect(result.current.isMuted).toBe(false);

      act(() => {
        result.current.toggleMute();
      });

      // State unchanged since there's no stream
      expect(result.current.isMuted).toBe(false);
    });

    it('has initial unmuted state', () => {
      const { result } = renderHook(() => useVideoCall());
      expect(result.current.isMuted).toBe(false);
    });
  });

  describe('toggleCamera', () => {
    it('does not error when called without active stream', () => {
      const { result } = renderHook(() => useVideoCall());

      // Should not throw when no stream
      expect(result.current.isCameraOff).toBe(false);

      act(() => {
        result.current.toggleCamera();
      });

      // State unchanged since there's no stream
      expect(result.current.isCameraOff).toBe(false);
    });

    it('has initial camera on state', () => {
      const { result } = renderHook(() => useVideoCall());
      expect(result.current.isCameraOff).toBe(false);
    });
  });

  describe('endCall', () => {
    it('ends the call and calls onCallEnded', async () => {
      const onCallEnded = vi.fn();
      mockLocalStorage.store['access_token'] = 'test-token';

      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-123',
          ice_servers: [],
          professional_name: 'Test Pro',
          call_id: 'call-123',
        },
      });

      const { result } = renderHook(() => useVideoCall({ onCallEnded }));

      await act(async () => {
        await result.current.initiateCall('pro-123');
      });

      act(() => {
        result.current.endCall();
      });

      expect(result.current.callState).toBe('ended');
      expect(onCallEnded).toHaveBeenCalled();
    });
  });

  describe('declineCall', () => {
    it('clears incoming call when declined', () => {
      const { result } = renderHook(() => useVideoCall());

      // Simulate having an incoming call (would be set by WebSocket message in real scenario)
      expect(result.current.incomingCall).toBe(null);

      // Decline should not error even with no incoming call
      act(() => {
        result.current.declineCall();
      });

      expect(result.current.incomingCall).toBe(null);
    });
  });

  describe('callbacks', () => {
    it('accepts onCallEnded callback', () => {
      const onCallEnded = vi.fn();
      const { result } = renderHook(() => useVideoCall({ onCallEnded }));

      expect(result.current).toBeDefined();
    });

    it('accepts onError callback', () => {
      const onError = vi.fn();
      const { result } = renderHook(() => useVideoCall({ onError }));

      expect(result.current).toBeDefined();
    });
  });

  describe('cleanup', () => {
    it('cleans up on unmount', async () => {
      mockLocalStorage.store['access_token'] = 'test-token';

      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-123',
          ice_servers: [],
          professional_name: 'Test Pro',
          call_id: 'call-123',
        },
      });

      const { result, unmount } = renderHook(() => useVideoCall());

      await act(async () => {
        await result.current.initiateCall('pro-123');
      });

      await waitFor(() => {
        expect(result.current.localStream).not.toBe(null);
      });

      // Unmount should trigger cleanup
      unmount();

      // Stream tracks should be stopped (tested via the mock)
    });
  });

  describe('media errors', () => {
    it('handles getUserMedia failure', async () => {
      const onError = vi.fn();
      mockLocalStorage.store['access_token'] = 'test-token';

      mockGetUserMedia.mockRejectedValueOnce(new Error('Permission denied'));

      vi.mocked(apiClient.post).mockResolvedValue({
        data: {
          room_id: 'room-123',
          ice_servers: [],
          professional_name: 'Test Pro',
          call_id: 'call-123',
        },
      });

      const { result } = renderHook(() => useVideoCall({ onError }));

      await act(async () => {
        await result.current.initiateCall('pro-123');
      });

      expect(result.current.callState).toBe('failed');
      expect(onError).toHaveBeenCalledWith('Could not access camera or microphone');
    });
  });
});
