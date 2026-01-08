/**
 * VideoCallModal component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import VideoCallModal from './VideoCallModal';

// Mock the useVideoCall hook
const mockInitiateCall = vi.fn();
const mockEndCall = vi.fn();
const mockToggleMute = vi.fn();
const mockToggleCamera = vi.fn();

const defaultHookReturn = {
  callState: 'idle' as const,
  callInfo: null as { roomId: string; isCaller: boolean } | null,
  localStream: null as MediaStream | null,
  remoteStream: null as MediaStream | null,
  isMuted: false,
  isCameraOff: false,
  pickupTimeSeconds: null as number | null,
  isAnonymous: false,
  callId: null as string | null,
  initiateCall: mockInitiateCall,
  endCall: mockEndCall,
  toggleMute: mockToggleMute,
  toggleCamera: mockToggleCamera,
  answerCall: vi.fn(),
  declineCall: vi.fn(),
  incomingCall: null,
};

let mockHookReturn = { ...defaultHookReturn };

vi.mock('@/hooks/useVideoCall', () => ({
  useVideoCall: () => mockHookReturn,
}));

// Mock the API
vi.mock('@/lib/api/endpoints', () => ({
  callsApi: {
    rate: vi.fn().mockResolvedValue({}),
    captureLead: vi.fn().mockResolvedValue({}),
  },
}));

// Mock child components
vi.mock('./CallControls', () => ({
  default: ({ onEndCall, onToggleMute, onToggleCamera, isMuted, isCameraOff }: {
    onEndCall: () => void;
    onToggleMute: () => void;
    onToggleCamera: () => void;
    isMuted: boolean;
    isCameraOff: boolean;
  }) => (
    <div data-testid="call-controls">
      <button onClick={onEndCall} data-testid="end-call-btn">End Call</button>
      <button onClick={onToggleMute} data-testid="toggle-mute-btn">
        {isMuted ? 'Unmute' : 'Mute'}
      </button>
      <button onClick={onToggleCamera} data-testid="toggle-camera-btn">
        {isCameraOff ? 'Turn On Camera' : 'Turn Off Camera'}
      </button>
    </div>
  ),
}));

vi.mock('./PostCallRating', () => ({
  default: ({ professionalName, onSubmit, onSkip }: {
    professionalName: string;
    onSubmit: (rating: number, comment?: string) => void;
    onSkip: () => void;
  }) => (
    <div data-testid="post-call-rating">
      <p>Rate your call with {professionalName}</p>
      <button onClick={() => onSubmit(5, 'Great call!')}>Submit Rating</button>
      <button onClick={onSkip}>Skip Rating</button>
    </div>
  ),
}));

vi.mock('./LeadCaptureModal', () => ({
  default: ({ professionalName, onClose }: {
    professionalName: string;
    onClose: () => void;
  }) => (
    <div data-testid="lead-capture-modal">
      <p>Share your info with {professionalName}</p>
      <button onClick={onClose}>Close Lead Capture</button>
    </div>
  ),
}));

describe('VideoCallModal', () => {
  const defaultProps = {
    professionalId: 'pro-123',
    professionalName: 'Jane Smith',
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockHookReturn = { ...defaultHookReturn };
  });

  it('initiates call on mount', () => {
    render(<VideoCallModal {...defaultProps} />);

    expect(mockInitiateCall).toHaveBeenCalledWith('pro-123');
  });

  it('displays professional name in header', () => {
    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  it('shows "Connecting..." status when initiating', () => {
    mockHookReturn.callState = 'initiating';

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('shows "Calling..." status when ringing', () => {
    mockHookReturn.callState = 'ringing';

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Calling Jane Smith...')).toBeInTheDocument();
  });

  it('shows "Setting up connection..." status when connecting', () => {
    mockHookReturn.callState = 'connecting';

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Setting up connection...')).toBeInTheDocument();
  });

  it('renders call controls', () => {
    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByTestId('call-controls')).toBeInTheDocument();
  });

  it('calls endCall when end call button is clicked', () => {
    render(<VideoCallModal {...defaultProps} />);

    fireEvent.click(screen.getByTestId('end-call-btn'));

    expect(mockEndCall).toHaveBeenCalledTimes(1);
  });

  it('calls toggleMute when mute button is clicked', () => {
    render(<VideoCallModal {...defaultProps} />);

    fireEvent.click(screen.getByTestId('toggle-mute-btn'));

    expect(mockToggleMute).toHaveBeenCalledTimes(1);
  });

  it('calls toggleCamera when camera button is clicked', () => {
    render(<VideoCallModal {...defaultProps} />);

    fireEvent.click(screen.getByTestId('toggle-camera-btn'));

    expect(mockToggleCamera).toHaveBeenCalledTimes(1);
  });

  it('shows placeholder with initial when no remote stream', () => {
    mockHookReturn.remoteStream = null;

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('J')).toBeInTheDocument();
  });

  it('shows "Camera Off" text when camera is off', () => {
    mockHookReturn.isCameraOff = true;

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Camera Off')).toBeInTheDocument();
  });

  it('shows ringing animation when call is ringing', () => {
    mockHookReturn.callState = 'ringing';

    const { container } = render(<VideoCallModal {...defaultProps} />);

    // Check for bouncing dots animation
    const bouncingDots = container.querySelectorAll('.animate-bounce');
    expect(bouncingDots.length).toBe(3);
  });

  it('shows PostCallRating for authenticated users after call ends', () => {
    mockHookReturn.callState = 'ended';
    mockHookReturn.callInfo = { roomId: 'room-123', isCaller: true };
    mockHookReturn.isAnonymous = false;

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByTestId('post-call-rating')).toBeInTheDocument();
    expect(screen.getByText('Rate your call with Jane Smith')).toBeInTheDocument();
  });

  it('shows LeadCaptureModal for anonymous users after call ends', () => {
    mockHookReturn.callState = 'ended';
    mockHookReturn.callInfo = { roomId: 'room-123', isCaller: true };
    mockHookReturn.isAnonymous = true;
    mockHookReturn.callId = 'call-456';

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByTestId('lead-capture-modal')).toBeInTheDocument();
    expect(screen.getByText('Share your info with Jane Smith')).toBeInTheDocument();
  });

  it('calls onClose when skipping rating', () => {
    mockHookReturn.callState = 'ended';
    mockHookReturn.callInfo = { roomId: 'room-123', isCaller: true };

    render(<VideoCallModal {...defaultProps} />);

    fireEvent.click(screen.getByText('Skip Rating'));

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('shows error overlay for failed calls', () => {
    mockHookReturn.callState = 'failed';

    render(<VideoCallModal {...defaultProps} />);

    // Text appears in both header and overlay, so use getAllByText
    const failedTexts = screen.getAllByText('Connection failed');
    expect(failedTexts.length).toBeGreaterThan(0);
    expect(screen.getByText('Close')).toBeInTheDocument();
  });

  it('shows error overlay for declined calls', () => {
    mockHookReturn.callState = 'declined';

    render(<VideoCallModal {...defaultProps} />);

    // Text appears in both header and overlay
    const declinedTexts = screen.getAllByText('Call declined');
    expect(declinedTexts.length).toBeGreaterThan(0);
  });

  it('shows error overlay for missed calls', () => {
    mockHookReturn.callState = 'missed';

    render(<VideoCallModal {...defaultProps} />);

    // Text appears in both header and overlay
    const missedTexts = screen.getAllByText('Call missed');
    expect(missedTexts.length).toBeGreaterThan(0);
  });

  it('calls onClose when clicking Close on error overlay', () => {
    mockHookReturn.callState = 'failed';

    render(<VideoCallModal {...defaultProps} />);

    fireEvent.click(screen.getByText('Close'));

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('renders local video element', () => {
    const { container } = render(<VideoCallModal {...defaultProps} />);

    const videos = container.querySelectorAll('video');
    expect(videos.length).toBe(2); // Local and remote video elements
  });

  it('shows mute state from hook', () => {
    mockHookReturn.isMuted = true;

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Unmute')).toBeInTheDocument();
  });

  it('shows camera state from hook', () => {
    mockHookReturn.isCameraOff = true;

    render(<VideoCallModal {...defaultProps} />);

    expect(screen.getByText('Turn On Camera')).toBeInTheDocument();
  });
});
