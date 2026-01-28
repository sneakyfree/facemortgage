'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket Hook (Row #48 Gap Fix)
 * 
 * Connects to backend WebSocket for real-time updates:
 * - Presence changes
 * - Grid refresh signals
 * - Call notifications
 * - Lead alerts
 */

type MessageHandler = (data: any) => void;

interface UseWebSocketOptions {
    autoConnect?: boolean;
    reconnectDelay?: number;
    maxReconnectAttempts?: number;
}

interface WebSocketState {
    connected: boolean;
    connecting: boolean;
    error: string | null;
}

export function useWebSocket(
    userId: string | null,
    options: UseWebSocketOptions = {}
) {
    const {
        autoConnect = true,
        reconnectDelay = 3000,
        maxReconnectAttempts = 5,
    } = options;

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());

    const [state, setState] = useState<WebSocketState>({
        connected: false,
        connecting: false,
        error: null,
    });

    const connect = useCallback(() => {
        if (!userId || wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        setState(s => ({ ...s, connecting: true, error: null }));

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${userId}`;

        try {
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setState({ connected: true, connecting: false, error: null });
                reconnectAttemptsRef.current = 0;
                console.log('[WS] Connected');
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    const { type, data } = message;

                    // Dispatch to handlers
                    const handlers = handlersRef.current.get(type);
                    if (handlers) {
                        handlers.forEach(handler => handler(data));
                    }

                    // Also dispatch to wildcard handlers
                    const wildcardHandlers = handlersRef.current.get('*');
                    if (wildcardHandlers) {
                        wildcardHandlers.forEach(handler => handler(message));
                    }
                } catch (e) {
                    console.error('[WS] Parse error:', e);
                }
            };

            ws.onclose = () => {
                setState(s => ({ ...s, connected: false, connecting: false }));
                wsRef.current = null;

                // Attempt reconnect
                if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                    reconnectAttemptsRef.current++;
                    console.log(`[WS] Reconnecting (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
                    setTimeout(connect, reconnectDelay);
                }
            };

            ws.onerror = (error) => {
                console.error('[WS] Error:', error);
                setState(s => ({ ...s, error: 'Connection error' }));
            };
        } catch (e) {
            setState({ connected: false, connecting: false, error: 'Failed to connect' });
        }
    }, [userId, reconnectDelay, maxReconnectAttempts]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const subscribe = useCallback((type: string, handler: MessageHandler) => {
        if (!handlersRef.current.has(type)) {
            handlersRef.current.set(type, new Set());
        }
        handlersRef.current.get(type)!.add(handler);

        return () => {
            handlersRef.current.get(type)?.delete(handler);
        };
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        if (autoConnect && userId) {
            connect();
        }
        return () => disconnect();
    }, [autoConnect, userId, connect, disconnect]);

    return {
        ...state,
        connect,
        disconnect,
        subscribe,
    };
}

/**
 * Hook for presence updates
 */
export function usePresenceUpdates(userId: string | null) {
    const { connected, subscribe } = useWebSocket(userId);
    const [presenceMap, setPresenceMap] = useState<Map<string, string>>(new Map());

    useEffect(() => {
        const unsubscribe = subscribe('presence_update', (data) => {
            const { professional_id, status } = data;
            setPresenceMap(prev => {
                const next = new Map(prev);
                next.set(professional_id, status);
                return next;
            });
        });
        return unsubscribe;
    }, [subscribe]);

    return { connected, presenceMap };
}

/**
 * Hook for grid refresh signals
 */
export function useGridRefresh(userId: string | null, onRefresh: () => void) {
    const { subscribe } = useWebSocket(userId);

    useEffect(() => {
        const unsubscribe = subscribe('grid_refresh', () => {
            onRefresh();
        });
        return unsubscribe;
    }, [subscribe, onRefresh]);
}

/**
 * Hook for incoming call notifications
 */
export function useCallNotifications(userId: string | null, onCall: (callInfo: any) => void) {
    const { subscribe } = useWebSocket(userId);

    useEffect(() => {
        const unsubscribe = subscribe('incoming_call', (data) => {
            onCall(data);
        });
        return unsubscribe;
    }, [subscribe, onCall]);
}

/**
 * Hook for new lead notifications
 */
export function useLeadNotifications(userId: string | null, onLead: (leadInfo: any) => void) {
    const { subscribe } = useWebSocket(userId);

    useEffect(() => {
        const unsubscribe = subscribe('new_lead', (data) => {
            onLead(data);
        });
        return unsubscribe;
    }, [subscribe, onLead]);
}
