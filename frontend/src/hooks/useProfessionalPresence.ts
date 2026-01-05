'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import type { ProfessionalStatus } from '@/types';
import { WS_BASE_URL, config } from '@/lib/config';

// Map WebSocket status strings to frontend status types
const STATUS_MAP: Record<string, ProfessionalStatus> = {
  'available': 'online_available',
  'online_available': 'online_available',
  'busy': 'online_busy',
  'online_busy': 'online_busy',
  'in_call': 'in_call',
  'away': 'away',
  'offline': 'offline',
};

interface UseProfessionalPresenceOptions {
  onStatusChange?: (status: ProfessionalStatus) => void;
  onError?: (error: string) => void;
}

interface PresenceState {
  isConnected: boolean;
  currentStatus: ProfessionalStatus;
  error: string | null;
}

export function useProfessionalPresence(options: UseProfessionalPresenceOptions = {}) {
  const { onStatusChange, onError } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const { user, getAccessToken } = useAuthStore();

  const [state, setState] = useState<PresenceState>({
    isConnected: false,
    currentStatus: 'offline',
    error: null,
  });

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'heartbeat_ack':
            // Heartbeat acknowledged
            break;

          case 'status_updated':
            const mappedStatus = STATUS_MAP[data.status] || 'offline';
            setState((prev) => ({
              ...prev,
              currentStatus: mappedStatus,
            }));
            onStatusChange?.(mappedStatus);
            break;

          case 'error':
            setState((prev) => ({
              ...prev,
              error: data.message,
            }));
            onError?.(data.message);
            break;

          default:
            console.log('Unknown presence message:', data.type);
        }
      } catch (error) {
        console.error('Error parsing presence message:', error);
      }
    },
    [onStatusChange, onError]
  );

  const startHeartbeat = useCallback(() => {
    // Clear existing heartbeat
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    // Send heartbeat at configured interval
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'heartbeat' }));
      }
    }, config.ws.heartbeatInterval);
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!user?.professional_profile?.id) {
      console.warn('Cannot connect: No professional profile');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const professionalId = user.professional_profile.id;
      const token = getAccessToken();
      const url = `${WS_BASE_URL}/ws/presence/${professionalId}${token ? `?token=${token}` : ''}`;

      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log('Professional presence WebSocket connected');
        setState((prev) => ({
          ...prev,
          isConnected: true,
          currentStatus: 'online_available',
          error: null,
        }));
        reconnectAttempts.current = 0;
        startHeartbeat();
      };

      wsRef.current.onmessage = handleMessage;

      wsRef.current.onclose = (event) => {
        console.log('Presence WebSocket closed:', event.code, event.reason);
        stopHeartbeat();
        setState((prev) => ({
          ...prev,
          isConnected: false,
          currentStatus: 'offline',
        }));

        // Attempt reconnection
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current++;

          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        } else {
          setState((prev) => ({
            ...prev,
            error: 'Connection lost. Please refresh the page.',
          }));
          onError?.('Connection lost. Please refresh the page.');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Presence WebSocket error:', error);
        setState((prev) => ({
          ...prev,
          error: 'WebSocket connection error',
        }));
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setState((prev) => ({
        ...prev,
        error: 'Failed to connect',
      }));
    }
  }, [user, getAccessToken, handleMessage, startHeartbeat, stopHeartbeat, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopHeartbeat();

    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setState({
      isConnected: false,
      currentStatus: 'offline',
      error: null,
    });
  }, [stopHeartbeat]);

  const setStatus = useCallback((status: ProfessionalStatus, roomId?: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'status_update',
          data: { status, room_id: roomId },
        })
      );
    }
  }, []);

  const toggleCamera = useCallback((cameraOn: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'camera_toggle',
          data: { camera_on: cameraOn },
        })
      );
    }
  }, []);

  const goOnline = useCallback(() => {
    connect();
  }, [connect]);

  const goOffline = useCallback(() => {
    setStatus('offline');
    disconnect();
  }, [setStatus, disconnect]);

  const setBusy = useCallback(
    (roomId?: string) => {
      setStatus('online_busy', roomId);
    },
    [setStatus]
  );

  const setInCall = useCallback(
    (roomId: string) => {
      setStatus('in_call', roomId);
    },
    [setStatus]
  );

  const setAvailable = useCallback(() => {
    setStatus('online_available');
  }, [setStatus]);

  const setAway = useCallback(() => {
    setStatus('away');
  }, [setStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    goOnline,
    goOffline,
    setAvailable,
    setBusy,
    setInCall,
    setAway,
    toggleCamera,
    reconnect: connect,
    disconnect,
  };
}
