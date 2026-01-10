'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useGridStore } from '@/stores/gridStore';
import type { ProfessionalStatus } from '@/types';
import { WS_BASE_URL, config } from '@/lib/config';
import { logger } from '@/lib/utils';

interface GridUpdateEvent {
  event: string;
  professional_id: string;
  room_id?: string;
  camera_on?: boolean;
}

interface UseRealtimeGridOptions {
  enabled?: boolean;
  onProfessionalOnline?: (professionalId: string) => void;
  onProfessionalOffline?: (professionalId: string) => void;
  onProfessionalBusy?: (professionalId: string) => void;
  onProfessionalAvailable?: (professionalId: string) => void;
}

export function useRealtimeGrid(options: UseRealtimeGridOptions = {}) {
  const {
    enabled = true,
    onProfessionalOnline,
    onProfessionalOffline,
    onProfessionalBusy,
    onProfessionalAvailable,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const { updateProfessional, removeProfessional } = useGridStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: GridUpdateEvent = JSON.parse(event.data);

        switch (data.event) {
          case 'professional_online':
          case 'professional_available':
            updateProfessional(data.professional_id, {
              status: 'online_available' as ProfessionalStatus,
            });
            if (data.event === 'professional_online') {
              onProfessionalOnline?.(data.professional_id);
            } else {
              onProfessionalAvailable?.(data.professional_id);
            }
            break;

          case 'professional_offline':
            removeProfessional(data.professional_id);
            onProfessionalOffline?.(data.professional_id);
            break;

          case 'professional_busy':
          case 'professional_in_call':
            updateProfessional(data.professional_id, {
              status: 'online_busy' as ProfessionalStatus,
            });
            onProfessionalBusy?.(data.professional_id);
            break;

          case 'professional_away':
            updateProfessional(data.professional_id, {
              status: 'away' as ProfessionalStatus,
            });
            break;

          case 'camera_toggle':
            // Could update a cameraOn field if we add it to the store
            break;

          case 'connected':
            logger.log('Connected to grid updates WebSocket');
            reconnectAttempts.current = 0;
            break;

          case 'pong':
            // Heartbeat response
            break;

          default:
            logger.log('Unknown grid event:', data.event);
        }
      } catch (error) {
        logger.error('Error parsing WebSocket message:', error);
      }
    },
    [
      updateProfessional,
      removeProfessional,
      onProfessionalOnline,
      onProfessionalOffline,
      onProfessionalBusy,
      onProfessionalAvailable,
    ]
  );

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      // Grid WebSocket is public (no authentication required for browsing)
      wsRef.current = new WebSocket(`${WS_BASE_URL}/ws/grid`);

      wsRef.current.onopen = () => {
        logger.log('Grid WebSocket connected');
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = handleMessage;

      wsRef.current.onclose = (event) => {
        logger.log('Grid WebSocket closed:', event.code, event.reason);

        // Attempt reconnection with exponential backoff
        if (reconnectAttempts.current < config.ws.reconnectAttempts) {
          const delay = Math.min(config.ws.reconnectDelay * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current++;

          logger.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        } else {
          logger.error('Max reconnection attempts reached');
        }
      };

      wsRef.current.onerror = (error) => {
        logger.error('Grid WebSocket error:', error);
      };
    } catch (error) {
      logger.error('Failed to create WebSocket connection:', error);
    }
  }, [handleMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounted');
      wsRef.current = null;
    }
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  const getOnlineCount = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'get_online_count' }));
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();

      // Send periodic pings to keep connection alive
      const pingInterval = setInterval(sendPing, 30000);

      return () => {
        clearInterval(pingInterval);
        disconnect();
      };
    }
  }, [enabled, connect, disconnect, sendPing]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    sendPing,
    getOnlineCount,
    reconnect: connect,
    disconnect,
  };
}
