'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import { getAnonymousSessionId, getDeviceFingerprint } from '@/lib/utils';
import { WS_BASE_URL } from '@/lib/config';

export type CallState =
  | 'idle'
  | 'initiating'
  | 'ringing'
  | 'connecting'
  | 'active'
  | 'ended'
  | 'missed'
  | 'declined'
  | 'failed';

interface CallInfo {
  roomId: string;
  peerId: string;
  peerName: string;
  peerAvatar?: string;
  isCaller: boolean;
  callId?: string;  // UUID of the call record in database
}

interface UseVideoCallOptions {
  onCallEnded?: (pickupTimeSeconds?: number) => void;
  onError?: (error: string) => void;
}

interface UseVideoCallReturn {
  // State
  callState: CallState;
  callInfo: CallInfo | null;
  localStream: MediaStream | null;
  remoteStream: MediaStream | null;
  isMuted: boolean;
  isCameraOff: boolean;
  pickupTimeSeconds: number | null;
  isAnonymous: boolean;  // True if caller is not authenticated
  callId: string | null; // UUID of the call record for post-call actions

  // Actions
  initiateCall: (professionalId: string) => Promise<void>;
  answerCall: () => void;
  declineCall: () => void;
  endCall: () => void;
  toggleMute: () => void;
  toggleCamera: () => void;

  // For incoming calls (professional side)
  incomingCall: CallInfo | null;
}

export function useVideoCall(options: UseVideoCallOptions = {}): UseVideoCallReturn {
  const { onCallEnded, onError } = options;

  // State
  const [callState, setCallState] = useState<CallState>('idle');
  const [callInfo, setCallInfo] = useState<CallInfo | null>(null);
  const [incomingCall, setIncomingCall] = useState<CallInfo | null>(null);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOff, setIsCameraOff] = useState(false);
  const [pickupTimeSeconds, setPickupTimeSeconds] = useState<number | null>(null);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [callId, setCallId] = useState<string | null>(null);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const iceServersRef = useRef<RTCIceServer[]>([]);

  // Cleanup function
  const cleanup = useCallback(() => {
    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    // Stop local stream
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
      setLocalStream(null);
    }

    setRemoteStream(null);
    setCallInfo(null);
    setIncomingCall(null);
  }, [localStream]);

  // Get user media
  const getUserMedia = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setLocalStream(stream);
      return stream;
    } catch (error) {
      console.error('Failed to get user media:', error);
      onError?.('Could not access camera or microphone');
      throw error;
    }
  }, [onError]);

  // Create peer connection
  const createPeerConnection = useCallback(
    (stream: MediaStream) => {
      const pc = new RTCPeerConnection({
        iceServers: iceServersRef.current,
      });

      // Add local tracks
      stream.getTracks().forEach((track) => {
        pc.addTrack(track, stream);
      });

      // Handle remote tracks
      pc.ontrack = (event) => {
        setRemoteStream(event.streams[0]);
      };

      // Handle ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: 'ice_candidate',
              payload: { candidate: event.candidate },
            })
          );
        }
      };

      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        console.log('Connection state:', pc.connectionState);
        if (pc.connectionState === 'connected') {
          setCallState('active');
        } else if (pc.connectionState === 'failed') {
          setCallState('failed');
          onError?.('Connection failed');
        }
      };

      peerConnectionRef.current = pc;
      return pc;
    },
    [onError]
  );

  // Connect to signaling server
  const connectSignaling = useCallback(
    (roomId: string, userId: string) => {
      return new Promise<void>((resolve, reject) => {
        // Get auth token from localStorage
        const token = localStorage.getItem('access_token');
        const tokenParam = token ? `?token=${token}` : '';
        const ws = new WebSocket(`${WS_BASE_URL}/ws/signaling/${roomId}/${userId}${tokenParam}`);

        ws.onopen = () => {
          console.log('Signaling connected');
          resolve();
        };

        ws.onerror = (error) => {
          console.error('Signaling error:', error);
          reject(error);
        };

        ws.onmessage = async (event) => {
          const data = JSON.parse(event.data);
          console.log('Signaling message:', data.type);

          switch (data.type) {
            case 'room_joined':
              iceServersRef.current = data.payload.ice_servers;
              break;

            case 'peer_joined':
              // Start the call if we're the caller
              if (callInfo?.isCaller && peerConnectionRef.current) {
                const offer = await peerConnectionRef.current.createOffer();
                await peerConnectionRef.current.setLocalDescription(offer);
                ws.send(
                  JSON.stringify({
                    type: 'offer',
                    payload: { sdp: offer },
                  })
                );
              }
              break;

            case 'offer':
              if (peerConnectionRef.current) {
                await peerConnectionRef.current.setRemoteDescription(
                  new RTCSessionDescription(data.payload.sdp)
                );
                const answer = await peerConnectionRef.current.createAnswer();
                await peerConnectionRef.current.setLocalDescription(answer);
                ws.send(
                  JSON.stringify({
                    type: 'answer',
                    payload: { sdp: answer },
                  })
                );
              }
              break;

            case 'answer':
              if (peerConnectionRef.current) {
                await peerConnectionRef.current.setRemoteDescription(
                  new RTCSessionDescription(data.payload.sdp)
                );
              }
              break;

            case 'ice_candidate':
              if (peerConnectionRef.current && data.payload.candidate) {
                await peerConnectionRef.current.addIceCandidate(
                  new RTCIceCandidate(data.payload.candidate)
                );
              }
              break;

            case 'call_state':
              const newState = data.payload.state as CallState;
              setCallState(newState);
              if (data.payload.pickup_time_seconds) {
                setPickupTimeSeconds(data.payload.pickup_time_seconds);
              }
              if (['ended', 'missed', 'declined', 'failed'].includes(newState)) {
                onCallEnded?.(data.payload.pickup_time_seconds);
                cleanup();
              }
              break;

            case 'peer_muted':
              // Handle peer mute state if needed
              break;

            case 'peer_camera':
              // Handle peer camera state if needed
              break;

            case 'peer_left':
              setCallState('ended');
              onCallEnded?.(pickupTimeSeconds || undefined);
              cleanup();
              break;

            case 'error':
              onError?.(data.payload.message);
              break;
          }
        };

        ws.onclose = () => {
          console.log('Signaling disconnected');
        };

        wsRef.current = ws;
      });
    },
    [callInfo, cleanup, onCallEnded, onError, pickupTimeSeconds]
  );

  // Initiate a call (borrower side)
  const initiateCall = useCallback(
    async (professionalId: string) => {
      try {
        setCallState('initiating');

        // Check if user is authenticated
        const accessToken = localStorage.getItem('access_token');
        const isAnonymousCall = !accessToken;
        setIsAnonymous(isAnonymousCall);

        // Build the request payload
        const payload: Record<string, unknown> = {
          professional_id: professionalId,
        };

        // For anonymous calls, include session ID and device fingerprint
        if (isAnonymousCall) {
          payload.anonymous_session_id = getAnonymousSessionId();
          payload.device_fingerprint = getDeviceFingerprint();
        }

        // Call the API to initiate
        const response = await apiClient.post('/calls', payload);

        const {
          room_id,
          ice_servers,
          professional_name,
          professional_avatar,
          call_id,
          is_anonymous,
          session_id,
        } = response.data;

        iceServersRef.current = ice_servers;

        // Store call ID for post-call actions (like lead capture)
        setCallId(call_id);

        // Determine user ID for signaling connection
        let userId: string;
        if (is_anonymous && session_id) {
          // Anonymous caller - use session-based ID
          userId = `anon:${session_id}`;
        } else {
          // Authenticated user
          userId = localStorage.getItem('user_id') || 'borrower';
        }

        setCallInfo({
          roomId: room_id,
          peerId: professionalId,
          peerName: professional_name,
          peerAvatar: professional_avatar,
          isCaller: true,
          callId: call_id,
        });

        setCallState('ringing');

        // Get media and create connection
        const stream = await getUserMedia();
        createPeerConnection(stream);

        // Connect to signaling
        await connectSignaling(room_id, userId);
      } catch (error: unknown) {
        console.error('Failed to initiate call:', error);
        setCallState('failed');
        const errorMessage = error instanceof Error ? error.message : 'Failed to initiate call';
        onError?.(errorMessage);
        cleanup();
      }
    },
    [getUserMedia, createPeerConnection, connectSignaling, cleanup, onError]
  );

  // Answer an incoming call (professional side)
  const answerCall = useCallback(async () => {
    if (!incomingCall) return;

    try {
      setCallState('connecting');
      setCallInfo(incomingCall);

      // Get media and create connection
      const stream = await getUserMedia();
      createPeerConnection(stream);

      // Connect to signaling
      await connectSignaling(incomingCall.roomId, incomingCall.peerId);

      // Send answer action
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: 'call_action',
            payload: { action: 'answer' },
          })
        );
      }

      setIncomingCall(null);
    } catch (error) {
      console.error('Failed to answer call:', error);
      setCallState('failed');
      onError?.('Failed to answer call');
      cleanup();
    }
  }, [incomingCall, getUserMedia, createPeerConnection, connectSignaling, cleanup, onError]);

  // Decline an incoming call
  const declineCall = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'call_action',
          payload: { action: 'decline' },
        })
      );
    }
    setIncomingCall(null);
    cleanup();
  }, [cleanup]);

  // End the current call
  const endCall = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'call_action',
          payload: { action: 'end' },
        })
      );
    }
    setCallState('ended');
    onCallEnded?.(pickupTimeSeconds || undefined);
    cleanup();
  }, [cleanup, onCallEnded, pickupTimeSeconds]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);

        // Notify peer
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: 'call_action',
              payload: { action: 'mute', muted: !audioTrack.enabled },
            })
          );
        }
      }
    }
  }, [localStream]);

  // Toggle camera
  const toggleCamera = useCallback(() => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsCameraOff(!videoTrack.enabled);

        // Notify peer
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: 'call_action',
              payload: { action: 'camera_off', camera_off: !videoTrack.enabled },
            })
          );
        }
      }
    }
  }, [localStream]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    callState,
    callInfo,
    localStream,
    remoteStream,
    isMuted,
    isCameraOff,
    pickupTimeSeconds,
    isAnonymous,
    callId,
    initiateCall,
    answerCall,
    declineCall,
    endCall,
    toggleMute,
    toggleCamera,
    incomingCall,
  };
}
