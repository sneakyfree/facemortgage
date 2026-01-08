'use client';

import type { CallState } from '@/hooks/useVideoCall';

interface CallControlsProps {
  isMuted: boolean;
  isCameraOff: boolean;
  onToggleMute: () => void;
  onToggleCamera: () => void;
  onEndCall: () => void;
  callState: CallState;
}

export default function CallControls({
  isMuted,
  isCameraOff,
  onToggleMute,
  onToggleCamera,
  onEndCall,
  callState,
}: CallControlsProps) {
  const isCallActive = callState === 'active' || callState === 'connecting';
  const canEndCall = ['initiating', 'ringing', 'connecting', 'active'].includes(callState);

  return (
    <div
      className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/70 to-transparent"
      role="toolbar"
      aria-label="Call controls"
    >
      <div className="flex items-center justify-center space-x-6">
        {/* Mute Button */}
        <button
          onClick={onToggleMute}
          disabled={!isCallActive}
          aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          aria-pressed={isMuted}
          className={`
            w-14 h-14 rounded-full flex items-center justify-center transition-all
            focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black
            ${isMuted
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-gray-700 hover:bg-gray-600'
            }
            ${!isCallActive ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isMuted ? (
            <MicOffIcon className="w-6 h-6 text-white" aria-hidden="true" />
          ) : (
            <MicIcon className="w-6 h-6 text-white" aria-hidden="true" />
          )}
        </button>

        {/* End Call Button */}
        <button
          onClick={onEndCall}
          disabled={!canEndCall}
          aria-label="End call"
          className={`
            w-16 h-16 rounded-full flex items-center justify-center transition-all
            focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black
            bg-red-600 hover:bg-red-700
            ${!canEndCall ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <PhoneIcon className="w-8 h-8 text-white rotate-[135deg]" aria-hidden="true" />
        </button>

        {/* Camera Button */}
        <button
          onClick={onToggleCamera}
          disabled={!isCallActive}
          aria-label={isCameraOff ? 'Turn on camera' : 'Turn off camera'}
          aria-pressed={isCameraOff}
          className={`
            w-14 h-14 rounded-full flex items-center justify-center transition-all
            focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black
            ${isCameraOff
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-gray-700 hover:bg-gray-600'
            }
            ${!isCallActive ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isCameraOff ? (
            <CameraOffIcon className="w-6 h-6 text-white" aria-hidden="true" />
          ) : (
            <CameraIcon className="w-6 h-6 text-white" aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}

// Icon props type
interface IconProps {
  className?: string;
  'aria-hidden'?: boolean | 'true' | 'false';
}

// Icons
function MicIcon({ className, 'aria-hidden': ariaHidden }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden={ariaHidden}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
      />
    </svg>
  );
}

function MicOffIcon({ className, 'aria-hidden': ariaHidden }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden={ariaHidden}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
      />
    </svg>
  );
}

function CameraIcon({ className, 'aria-hidden': ariaHidden }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden={ariaHidden}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
      />
    </svg>
  );
}

function CameraOffIcon({ className, 'aria-hidden': ariaHidden }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden={ariaHidden}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
      />
    </svg>
  );
}

function PhoneIcon({ className, 'aria-hidden': ariaHidden }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden={ariaHidden}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
      />
    </svg>
  );
}
