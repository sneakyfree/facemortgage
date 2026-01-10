'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { useVideoCall, CallState } from '@/hooks/useVideoCall';
import { callsApi } from '@/lib/api/endpoints';
import { useFocusTrap, useEscapeKey } from '@/hooks/useFocusTrap';
import CallControls from './CallControls';
import PostCallRating from './PostCallRating';
import LeadCaptureModal from './LeadCaptureModal';
import { logger } from '@/lib/utils';

interface VideoCallModalProps {
  professionalId: string;
  professionalName: string;
  onClose: () => void;
}

export default function VideoCallModal({
  professionalId,
  professionalName,
  onClose,
}: VideoCallModalProps) {
  const {
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
    endCall,
    toggleMute,
    toggleCamera,
  } = useVideoCall({
    onCallEnded: (pickupTime) => {
      logger.log('Call ended, pickup time:', pickupTime);
    },
    onError: (error) => {
      logger.error('Call error:', error);
    },
  });

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const modalRef = useFocusTrap<HTMLDivElement>(true);

  // Only allow Escape to close during error states, not during active call
  const canCloseWithEscape = ['failed', 'declined', 'missed'].includes(callState);
  const handleEscape = useCallback(() => {
    if (canCloseWithEscape) {
      onClose();
    }
  }, [canCloseWithEscape, onClose]);
  useEscapeKey(canCloseWithEscape, handleEscape);

  // Start call on mount
  useEffect(() => {
    initiateCall(professionalId);
  }, [professionalId, initiateCall]);

  // Attach local stream to video element
  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);

  // Attach remote stream to video element
  useEffect(() => {
    if (remoteVideoRef.current && remoteStream) {
      remoteVideoRef.current.srcObject = remoteStream;
    }
  }, [remoteStream]);

  const handleEndCall = () => {
    endCall();
  };

  const handleRatingSubmit = async (rating: number, comment?: string) => {
    // Submit rating via API
    if (callInfo?.roomId) {
      try {
        await callsApi.rate(callInfo.roomId, {
          overall_rating: rating,
          content: comment,
        });
      } catch (error) {
        logger.error('Failed to submit rating:', error);
      }
    }
    onClose();
  };

  const getStatusMessage = (state: CallState): string => {
    switch (state) {
      case 'initiating':
        return 'Connecting...';
      case 'ringing':
        return `Calling ${professionalName}...`;
      case 'connecting':
        return 'Setting up connection...';
      case 'active':
        return '';
      case 'ended':
        return 'Call ended';
      case 'missed':
        return 'Call missed';
      case 'declined':
        return 'Call declined';
      case 'failed':
        return 'Connection failed';
      default:
        return '';
    }
  };

  // Show appropriate modal after call ends
  if (callState === 'ended' && callInfo) {
    // For anonymous callers, show lead capture instead of rating
    if (isAnonymous && callId) {
      return (
        <LeadCaptureModal
          callId={callId}
          professionalName={professionalName}
          onClose={onClose}
          onSkip={onClose}
        />
      );
    }

    // For authenticated users, show rating modal
    return (
      <PostCallRating
        professionalName={professionalName}
        callDuration={pickupTimeSeconds || 0}
        onSubmit={handleRatingSubmit}
        onSkip={onClose}
      />
    );
  }

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="video-call-title"
      aria-describedby="video-call-status"
      className="fixed inset-0 z-50 bg-black flex flex-col"
    >
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 p-4 bg-gradient-to-b from-black/70 to-transparent">
        <div className="flex items-center justify-between text-white">
          <div>
            <h2 id="video-call-title" className="text-xl font-semibold">{professionalName}</h2>
            {getStatusMessage(callState) && (
              <p id="video-call-status" className="text-sm text-gray-300" aria-live="polite">
                {getStatusMessage(callState)}
              </p>
            )}
          </div>
          {callState === 'active' && (
            <div className="text-sm">
              <CallTimer />
            </div>
          )}
        </div>
      </div>

      {/* Video Container */}
      <div className="flex-1 relative">
        {/* Remote Video (Full Screen) */}
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          aria-label={`Video from ${professionalName}`}
          className="w-full h-full object-cover"
        />

        {/* Placeholder when no remote video */}
        {!remoteStream && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="text-center">
              <div className="w-24 h-24 bg-gray-700 rounded-full mx-auto mb-4 flex items-center justify-center">
                <span className="text-4xl text-white">
                  {professionalName.charAt(0).toUpperCase()}
                </span>
              </div>
              {callState === 'ringing' && (
                <div className="flex items-center justify-center space-x-1">
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-100" />
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce delay-200" />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Local Video (Picture-in-Picture) */}
        <div className="absolute bottom-24 right-4 w-32 h-44 rounded-lg overflow-hidden shadow-lg border-2 border-white/20">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            aria-label="Your video preview"
            className={`w-full h-full object-cover ${isCameraOff ? 'hidden' : ''}`}
          />
          {isCameraOff && (
            <div className="w-full h-full bg-gray-800 flex items-center justify-center">
              <span className="text-white text-xs">Camera Off</span>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <CallControls
        isMuted={isMuted}
        isCameraOff={isCameraOff}
        onToggleMute={toggleMute}
        onToggleCamera={toggleCamera}
        onEndCall={handleEndCall}
        callState={callState}
      />

      {/* Error/Status Overlay */}
      {['failed', 'declined', 'missed'].includes(callState) && (
        <div
          role="alert"
          className="absolute inset-0 flex items-center justify-center bg-black/80"
        >
          <div className="text-center text-white">
            <p className="text-xl mb-4">{getStatusMessage(callState)}</p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-white text-black rounded-full font-medium hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Call Timer Component
function CallTimer() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return <span className="font-mono">{formatTime(seconds)}</span>;
}
