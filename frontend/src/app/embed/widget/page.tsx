'use client';

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Video,
  Phone,
  Star,
  Clock,
  Shield,
  X,
  Mic,
  MicOff,
  VideoOff,
  PhoneOff,
  CheckCircle,
  AlertCircle,
  Calendar,
  User,
  Mail,
  MessageSquare,
} from 'lucide-react';

// Types
interface Professional {
  id: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
  user_type: string;
  company_name?: string;
  job_title?: string;
  bio?: string;
  status: string;
  subscription_tier: string;
  prerecorded_video_url?: string;
  avg_rating: number;
  total_reviews: number;
  avg_pickup_time_seconds?: number;
  years_experience?: number;
  specialty_names: string[];
  language_codes: string[];
}

interface CallInfo {
  room_id: string;
  signaling_url: string;
  ice_servers: RTCIceServer[];
  professional_name: string;
  professional_avatar?: string;
}

type ViewState = 'loading' | 'profile' | 'calling' | 'connected' | 'ended' | 'schedule' | 'error';

// API Configuration - use centralized config
import { API_URL } from '@/lib/config';

function WidgetPageContent() {
  const searchParams = useSearchParams();
  const professionalId = searchParams.get('professional_id');
  const partnerId = searchParams.get('partner_id');
  const theme = searchParams.get('theme') || 'light';

  const [viewState, setViewState] = useState<ViewState>('loading');
  const [professional, setProfessional] = useState<Professional | null>(null);
  const [callInfo, setCallInfo] = useState<CallInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOff, setIsCameraOff] = useState(false);
  const [rating, setRating] = useState(0);
  const [ratingComment, setRatingComment] = useState('');
  const [ratingSubmitted, setRatingSubmitted] = useState(false);

  // Schedule form state
  const [scheduleForm, setScheduleForm] = useState({
    name: '',
    email: '',
    phone: '',
    date: '',
    time: '',
    notes: '',
  });
  const [scheduleSubmitted, setScheduleSubmitted] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  // Video refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const callTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Session ID for anonymous tracking
  const [sessionId] = useState(() => 'widget-' + Math.random().toString(36).substr(2, 9));

  // Theme colors
  const isDark = theme === 'dark';
  const colors = {
    bg: isDark ? '#1f2937' : '#ffffff',
    cardBg: isDark ? '#374151' : '#ffffff',
    text: isDark ? '#f9fafb' : '#111827',
    textSecondary: isDark ? '#9ca3af' : '#6b7280',
    primary: '#2563eb',
    primaryHover: '#1d4ed8',
    available: '#16a34a',
    border: isDark ? '#4b5563' : '#e5e7eb',
  };

  // Fetch professional data
  useEffect(() => {
    if (!professionalId) {
      setError('No professional specified');
      setViewState('error');
      return;
    }

    const fetchProfessional = async () => {
      try {
        const response = await fetch(`${API_URL}/professionals/${professionalId}`, {
          headers: {
            'Content-Type': 'application/json',
            'X-Partner-ID': partnerId || '',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to load professional');
        }

        const data = await response.json();
        setProfessional(data);
        setViewState('profile');
      } catch (err) {
        console.error('Error fetching professional:', err);
        setError('Unable to load professional');
        setViewState('error');
      }
    };

    fetchProfessional();
  }, [professionalId, partnerId]);

  // Initialize video call
  const initiateCall = async () => {
    if (!professional) return;

    try {
      setViewState('calling');

      // Request media permissions
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      localStreamRef.current = stream;

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Create call via API
      const response = await fetch(`${API_URL}/calls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Partner-ID': partnerId || '',
        },
        body: JSON.stringify({
          professional_id: professional.id,
          anonymous_session_id: sessionId,
          source: 'widget',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to initiate call');
      }

      const callData = await response.json();
      setCallInfo(callData);

      // Set up WebRTC connection
      await setupWebRTC(callData);
    } catch (err) {
      console.error('Error initiating call:', err);
      setError('Failed to start call. Please check your camera and microphone permissions.');
      setViewState('error');
      cleanupCall();
    }
  };

  // Set up WebRTC peer connection
  const setupWebRTC = async (info: CallInfo) => {
    try {
      const pc = new RTCPeerConnection({
        iceServers: info.ice_servers,
      });
      peerConnectionRef.current = pc;

      // Add local tracks
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach((track) => {
          pc.addTrack(track, localStreamRef.current!);
        });
      }

      // Handle remote stream
      pc.ontrack = (event) => {
        if (remoteVideoRef.current && event.streams[0]) {
          remoteVideoRef.current.srcObject = event.streams[0];
          setViewState('connected');
          startCallTimer();
        }
      };

      // Handle ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          // Send candidate to signaling server
          sendSignal(info.signaling_url, {
            type: 'ice-candidate',
            candidate: event.candidate,
            room_id: info.room_id,
          });
        }
      };

      // Connection state changes
      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
          endCall();
        }
      };

      // Create and send offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      sendSignal(info.signaling_url, {
        type: 'offer',
        sdp: offer.sdp,
        room_id: info.room_id,
      });

      // Listen for answer
      const ws = new WebSocket(info.signaling_url);
      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'answer') {
          await pc.setRemoteDescription(new RTCSessionDescription({
            type: 'answer',
            sdp: message.sdp,
          }));
        } else if (message.type === 'ice-candidate') {
          await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
        } else if (message.type === 'call-ended') {
          endCall();
        }
      };
    } catch (err) {
      console.error('WebRTC setup error:', err);
      throw err;
    }
  };

  // Send signaling message
  const sendSignal = async (url: string, message: object) => {
    try {
      const ws = new WebSocket(url);
      ws.onopen = () => {
        ws.send(JSON.stringify(message));
        ws.close();
      };
    } catch (err) {
      console.error('Signaling error:', err);
    }
  };

  // Start call timer
  const startCallTimer = () => {
    callTimerRef.current = setInterval(() => {
      setCallDuration((d) => d + 1);
    }, 1000);
  };

  // End call
  const endCall = useCallback(() => {
    if (callTimerRef.current) {
      clearInterval(callTimerRef.current);
    }

    cleanupCall();
    setViewState('ended');

    // Notify parent window
    if (window.parent !== window) {
      window.parent.postMessage({ type: 'fm-call-ended' }, '*');
    }
  }, []);

  // Cleanup call resources
  const cleanupCall = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop());
      localStreamRef.current = null;
    }

    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
  };

  // Toggle mute
  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };

  // Toggle camera
  const toggleCamera = () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsCameraOff(!videoTrack.enabled);
      }
    }
  };

  // Submit rating
  const submitRating = async () => {
    if (!callInfo || rating === 0) return;

    try {
      await fetch(`${API_URL}/calls/${callInfo.room_id}/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Partner-ID': partnerId || '',
          'X-Session-ID': sessionId,
        },
        body: JSON.stringify({
          overall_rating: rating,
          content: ratingComment,
        }),
      });

      setRatingSubmitted(true);

      // Notify parent and close
      setTimeout(() => {
        if (window.parent !== window) {
          window.parent.postMessage({ type: 'fm-call-success' }, '*');
        }
      }, 2000);
    } catch (err) {
      console.error('Error submitting rating:', err);
    }
  };

  // Submit schedule request
  const submitSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setScheduleError(null);

    if (!professional) return;

    try {
      const scheduledFor = new Date(`${scheduleForm.date}T${scheduleForm.time}`);

      await fetch(`${API_URL}/scheduled-calls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Partner-ID': partnerId || '',
        },
        body: JSON.stringify({
          professional_id: professional.id,
          scheduled_for: scheduledFor.toISOString(),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          name: scheduleForm.name,
          email: scheduleForm.email,
          phone: scheduleForm.phone,
          notes: scheduleForm.notes,
        }),
      });

      setScheduleSubmitted(true);
    } catch (err) {
      console.error('Error scheduling call:', err);
      setScheduleError('Failed to schedule call. Please try again.');
    }
  };

  // Format call duration
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Format user type
  const formatUserType = (type: string) => {
    const types: Record<string, string> = {
      loan_officer: 'Loan Officer',
      realtor: 'Realtor',
      title_rep: 'Title Representative',
      attorney: 'Attorney',
    };
    return types[type] || type;
  };

  // Render loading state
  if (viewState === 'loading') {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: colors.bg }}
      >
        <div className="text-center">
          <div
            className="w-10 h-10 border-3 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: colors.border, borderTopColor: colors.primary }}
          />
          <p style={{ color: colors.textSecondary }}>Loading...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (viewState === 'error') {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-6"
        style={{ backgroundColor: colors.bg }}
      >
        <div className="text-center max-w-sm">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
            Something went wrong
          </h2>
          <p className="mb-4" style={{ color: colors.textSecondary }}>
            {error || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 rounded-lg text-white"
            style={{ backgroundColor: colors.primary }}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Render profile view
  if (viewState === 'profile' && professional) {
    const isAvailable = professional.status === 'online_available';

    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: colors.bg }}>
        <div className="max-w-md mx-auto">
          {/* Professional Card */}
          <div
            className="rounded-xl p-6 mb-6"
            style={{ backgroundColor: colors.cardBg, border: `1px solid ${colors.border}` }}
          >
            {/* Avatar and Status */}
            <div className="flex items-start gap-4 mb-4">
              <div className="relative">
                {professional.avatar_url ? (
                  <img
                    src={professional.avatar_url}
                    alt={`${professional.first_name} ${professional.last_name}`}
                    className="w-20 h-20 rounded-full object-cover"
                  />
                ) : (
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-semibold"
                    style={{ background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryHover})` }}
                  >
                    {professional.first_name.charAt(0)}{professional.last_name.charAt(0)}
                  </div>
                )}
                <div
                  className="absolute bottom-0 right-0 w-5 h-5 rounded-full border-2"
                  style={{
                    backgroundColor: isAvailable ? colors.available : colors.textSecondary,
                    borderColor: colors.cardBg,
                  }}
                />
              </div>

              <div className="flex-1">
                <h1 className="text-xl font-semibold" style={{ color: colors.text }}>
                  {professional.first_name} {professional.last_name}
                </h1>
                <p style={{ color: colors.textSecondary }}>
                  {professional.job_title || formatUserType(professional.user_type)}
                </p>
                {professional.company_name && (
                  <p className="text-sm" style={{ color: colors.textSecondary }}>
                    {professional.company_name}
                  </p>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-4 mb-4">
              {professional.avg_rating > 0 && (
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                  <span style={{ color: colors.text }}>{professional.avg_rating.toFixed(1)}</span>
                  <span style={{ color: colors.textSecondary }}>({professional.total_reviews})</span>
                </div>
              )}
              {professional.years_experience && (
                <div className="flex items-center gap-1" style={{ color: colors.textSecondary }}>
                  <Shield className="w-4 h-4" />
                  <span>{professional.years_experience} years</span>
                </div>
              )}
              {professional.avg_pickup_time_seconds && (
                <div className="flex items-center gap-1" style={{ color: colors.textSecondary }}>
                  <Clock className="w-4 h-4" />
                  <span>{Math.round(professional.avg_pickup_time_seconds)}s avg</span>
                </div>
              )}
            </div>

            {/* Bio */}
            {professional.bio && (
              <p className="text-sm mb-4" style={{ color: colors.textSecondary }}>
                {professional.bio}
              </p>
            )}

            {/* Specialties */}
            {professional.specialty_names && professional.specialty_names.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {professional.specialty_names.slice(0, 4).map((specialty, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 rounded-full text-xs"
                    style={{
                      backgroundColor: isDark ? '#4b5563' : '#f3f4f6',
                      color: colors.textSecondary,
                    }}
                  >
                    {specialty}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={initiateCall}
              disabled={!isAvailable}
              className="w-full py-3 px-4 rounded-lg text-white font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                backgroundColor: isAvailable ? colors.primary : colors.textSecondary,
              }}
            >
              <Video className="w-5 h-5" />
              {isAvailable ? 'Start Video Call' : 'Currently Unavailable'}
            </button>

            <button
              onClick={() => setViewState('schedule')}
              className="w-full py-3 px-4 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
              style={{
                backgroundColor: 'transparent',
                color: colors.primary,
                border: `1px solid ${colors.primary}`,
              }}
            >
              <Calendar className="w-5 h-5" />
              Schedule a Call
            </button>
          </div>

          {/* Footer */}
          <p className="text-center text-xs mt-6" style={{ color: colors.textSecondary }}>
            Powered by{' '}
            <a
              href="https://facemortgage.com"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: colors.primary }}
            >
              FaceMortgage
            </a>
          </p>
        </div>
      </div>
    );
  }

  // Render calling/connected state
  if ((viewState === 'calling' || viewState === 'connected') && professional) {
    return (
      <div className="min-h-screen bg-black flex flex-col">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 z-10 p-4 bg-gradient-to-b from-black/70 to-transparent">
          <div className="flex items-center justify-between text-white">
            <div>
              <h2 className="text-lg font-semibold">
                {professional.first_name} {professional.last_name}
              </h2>
              <p className="text-sm text-gray-300">
                {viewState === 'calling' ? 'Connecting...' : formatDuration(callDuration)}
              </p>
            </div>
          </div>
        </div>

        {/* Video Container */}
        <div className="flex-1 relative">
          {/* Remote Video */}
          <video
            ref={remoteVideoRef}
            autoPlay
            playsInline
            className="w-full h-full object-cover"
          />

          {/* Placeholder when connecting */}
          {viewState === 'calling' && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
              <div className="text-center">
                <div className="w-24 h-24 bg-gray-700 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-4xl text-white">
                    {professional.first_name.charAt(0)}
                  </span>
                </div>
                <div className="flex items-center justify-center space-x-1">
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <span className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            </div>
          )}

          {/* Local Video (PiP) */}
          <div className="absolute bottom-24 right-4 w-28 h-36 rounded-lg overflow-hidden shadow-lg border-2 border-white/20">
            <video
              ref={localVideoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover ${isCameraOff ? 'hidden' : ''}`}
            />
            {isCameraOff && (
              <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                <VideoOff className="w-6 h-6 text-white" />
              </div>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/70 to-transparent">
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={toggleMute}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
                isMuted ? 'bg-red-500' : 'bg-gray-700'
              }`}
            >
              {isMuted ? (
                <MicOff className="w-6 h-6 text-white" />
              ) : (
                <Mic className="w-6 h-6 text-white" />
              )}
            </button>

            <button
              onClick={endCall}
              className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center"
            >
              <PhoneOff className="w-7 h-7 text-white" />
            </button>

            <button
              onClick={toggleCamera}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
                isCameraOff ? 'bg-red-500' : 'bg-gray-700'
              }`}
            >
              {isCameraOff ? (
                <VideoOff className="w-6 h-6 text-white" />
              ) : (
                <Video className="w-6 h-6 text-white" />
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render call ended/rating state
  if (viewState === 'ended' && professional) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center" style={{ backgroundColor: colors.bg }}>
        <div className="max-w-md w-full text-center">
          {ratingSubmitted ? (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
                Thank You!
              </h2>
              <p style={{ color: colors.textSecondary }}>
                Your feedback helps improve our service.
              </p>
            </>
          ) : (
            <>
              <h2 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
                Call Ended
              </h2>
              <p className="mb-4" style={{ color: colors.textSecondary }}>
                Duration: {formatDuration(callDuration)}
              </p>

              <div className="mb-6">
                <p className="mb-3" style={{ color: colors.text }}>
                  How was your call with {professional.first_name}?
                </p>
                <div className="flex justify-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className="p-1"
                    >
                      <Star
                        className={`w-8 h-8 transition-colors ${
                          star <= rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              {rating > 0 && (
                <div className="mb-4">
                  <textarea
                    value={ratingComment}
                    onChange={(e) => setRatingComment(e.target.value)}
                    placeholder="Add a comment (optional)"
                    className="w-full p-3 rounded-lg text-sm resize-none"
                    style={{
                      backgroundColor: isDark ? '#4b5563' : '#f9fafb',
                      color: colors.text,
                      border: `1px solid ${colors.border}`,
                    }}
                    rows={3}
                  />
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    if (window.parent !== window) {
                      window.parent.postMessage({ type: 'fm-call-ended' }, '*');
                    }
                  }}
                  className="flex-1 py-2 px-4 rounded-lg"
                  style={{
                    backgroundColor: 'transparent',
                    color: colors.textSecondary,
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  Skip
                </button>
                <button
                  onClick={submitRating}
                  disabled={rating === 0}
                  className="flex-1 py-2 px-4 rounded-lg text-white disabled:opacity-50"
                  style={{ backgroundColor: colors.primary }}
                >
                  Submit
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // Render schedule form
  if (viewState === 'schedule' && professional) {
    if (scheduleSubmitted) {
      return (
        <div className="min-h-screen p-6 flex items-center justify-center" style={{ backgroundColor: colors.bg }}>
          <div className="max-w-md w-full text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: colors.text }}>
              Call Scheduled!
            </h2>
            <p style={{ color: colors.textSecondary }}>
              {professional.first_name} will contact you at the scheduled time.
              Check your email for confirmation.
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen p-6" style={{ backgroundColor: colors.bg }}>
        <div className="max-w-md mx-auto">
          <button
            onClick={() => setViewState('profile')}
            className="flex items-center gap-2 mb-4"
            style={{ color: colors.textSecondary }}
          >
            <X className="w-5 h-5" />
            Back
          </button>

          <h2 className="text-xl font-semibold mb-4" style={{ color: colors.text }}>
            Schedule a Call with {professional.first_name}
          </h2>

          {scheduleError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {scheduleError}
            </div>
          )}

          <form onSubmit={submitSchedule} className="space-y-4">
            <div>
              <label className="block text-sm mb-1" style={{ color: colors.text }}>
                <User className="inline w-4 h-4 mr-1" />
                Your Name *
              </label>
              <input
                type="text"
                required
                value={scheduleForm.name}
                onChange={(e) => setScheduleForm({ ...scheduleForm, name: e.target.value })}
                className="w-full px-4 py-2 rounded-lg"
                style={{
                  backgroundColor: isDark ? '#4b5563' : '#ffffff',
                  color: colors.text,
                  border: `1px solid ${colors.border}`,
                }}
                placeholder="John Smith"
              />
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: colors.text }}>
                <Mail className="inline w-4 h-4 mr-1" />
                Email *
              </label>
              <input
                type="email"
                required
                value={scheduleForm.email}
                onChange={(e) => setScheduleForm({ ...scheduleForm, email: e.target.value })}
                className="w-full px-4 py-2 rounded-lg"
                style={{
                  backgroundColor: isDark ? '#4b5563' : '#ffffff',
                  color: colors.text,
                  border: `1px solid ${colors.border}`,
                }}
                placeholder="john@example.com"
              />
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: colors.text }}>
                <Phone className="inline w-4 h-4 mr-1" />
                Phone
              </label>
              <input
                type="tel"
                value={scheduleForm.phone}
                onChange={(e) => setScheduleForm({ ...scheduleForm, phone: e.target.value })}
                className="w-full px-4 py-2 rounded-lg"
                style={{
                  backgroundColor: isDark ? '#4b5563' : '#ffffff',
                  color: colors.text,
                  border: `1px solid ${colors.border}`,
                }}
                placeholder="(555) 123-4567"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-1" style={{ color: colors.text }}>
                  <Calendar className="inline w-4 h-4 mr-1" />
                  Date *
                </label>
                <input
                  type="date"
                  required
                  value={scheduleForm.date}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: isDark ? '#4b5563' : '#ffffff',
                    color: colors.text,
                    border: `1px solid ${colors.border}`,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm mb-1" style={{ color: colors.text }}>
                  <Clock className="inline w-4 h-4 mr-1" />
                  Time *
                </label>
                <input
                  type="time"
                  required
                  value={scheduleForm.time}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, time: e.target.value })}
                  className="w-full px-4 py-2 rounded-lg"
                  style={{
                    backgroundColor: isDark ? '#4b5563' : '#ffffff',
                    color: colors.text,
                    border: `1px solid ${colors.border}`,
                  }}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-1" style={{ color: colors.text }}>
                <MessageSquare className="inline w-4 h-4 mr-1" />
                Notes
              </label>
              <textarea
                value={scheduleForm.notes}
                onChange={(e) => setScheduleForm({ ...scheduleForm, notes: e.target.value })}
                className="w-full px-4 py-2 rounded-lg resize-none"
                style={{
                  backgroundColor: isDark ? '#4b5563' : '#ffffff',
                  color: colors.text,
                  border: `1px solid ${colors.border}`,
                }}
                rows={3}
                placeholder="What would you like to discuss?"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 px-4 rounded-lg text-white font-medium"
              style={{ backgroundColor: colors.primary }}
            >
              Schedule Call
            </button>
          </form>
        </div>
      </div>
    );
  }

  return null;
}

// Loading fallback
function WidgetLoadingFallback() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="w-10 h-10 border-3 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
    </div>
  );
}

export default function EmbedWidgetPage() {
  return (
    <Suspense fallback={<WidgetLoadingFallback />}>
      <WidgetPageContent />
    </Suspense>
  );
}
