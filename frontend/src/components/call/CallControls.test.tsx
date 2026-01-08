/**
 * CallControls component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CallControls from './CallControls';
import type { CallState } from '@/hooks/useVideoCall';

describe('CallControls', () => {
  const defaultProps = {
    isMuted: false,
    isCameraOff: false,
    onToggleMute: vi.fn(),
    onToggleCamera: vi.fn(),
    onEndCall: vi.fn(),
    callState: 'active' as CallState,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders toolbar with accessible label', () => {
      render(<CallControls {...defaultProps} />);

      expect(screen.getByRole('toolbar')).toHaveAttribute('aria-label', 'Call controls');
    });

    it('renders mute button', () => {
      render(<CallControls {...defaultProps} />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeInTheDocument();
    });

    it('renders camera button', () => {
      render(<CallControls {...defaultProps} />);

      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeInTheDocument();
    });

    it('renders end call button', () => {
      render(<CallControls {...defaultProps} />);

      expect(screen.getByRole('button', { name: /end call/i })).toBeInTheDocument();
    });
  });

  describe('Mute button', () => {
    it('shows "Mute microphone" label when not muted', () => {
      render(<CallControls {...defaultProps} isMuted={false} />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeInTheDocument();
    });

    it('shows "Unmute microphone" label when muted', () => {
      render(<CallControls {...defaultProps} isMuted={true} />);

      expect(screen.getByRole('button', { name: /unmute microphone/i })).toBeInTheDocument();
    });

    it('has aria-pressed=false when not muted', () => {
      render(<CallControls {...defaultProps} isMuted={false} />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toHaveAttribute(
        'aria-pressed',
        'false'
      );
    });

    it('has aria-pressed=true when muted', () => {
      render(<CallControls {...defaultProps} isMuted={true} />);

      expect(screen.getByRole('button', { name: /unmute microphone/i })).toHaveAttribute(
        'aria-pressed',
        'true'
      );
    });

    it('calls onToggleMute when clicked', () => {
      render(<CallControls {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /mute microphone/i }));

      expect(defaultProps.onToggleMute).toHaveBeenCalledTimes(1);
    });

    it('has red background when muted', () => {
      render(<CallControls {...defaultProps} isMuted={true} />);

      expect(screen.getByRole('button', { name: /unmute microphone/i })).toHaveClass('bg-red-500');
    });

    it('has gray background when not muted', () => {
      render(<CallControls {...defaultProps} isMuted={false} />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toHaveClass('bg-gray-700');
    });
  });

  describe('Camera button', () => {
    it('shows "Turn off camera" label when camera is on', () => {
      render(<CallControls {...defaultProps} isCameraOff={false} />);

      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeInTheDocument();
    });

    it('shows "Turn on camera" label when camera is off', () => {
      render(<CallControls {...defaultProps} isCameraOff={true} />);

      expect(screen.getByRole('button', { name: /turn on camera/i })).toBeInTheDocument();
    });

    it('has aria-pressed=false when camera is on', () => {
      render(<CallControls {...defaultProps} isCameraOff={false} />);

      expect(screen.getByRole('button', { name: /turn off camera/i })).toHaveAttribute(
        'aria-pressed',
        'false'
      );
    });

    it('has aria-pressed=true when camera is off', () => {
      render(<CallControls {...defaultProps} isCameraOff={true} />);

      expect(screen.getByRole('button', { name: /turn on camera/i })).toHaveAttribute(
        'aria-pressed',
        'true'
      );
    });

    it('calls onToggleCamera when clicked', () => {
      render(<CallControls {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /turn off camera/i }));

      expect(defaultProps.onToggleCamera).toHaveBeenCalledTimes(1);
    });

    it('has red background when camera is off', () => {
      render(<CallControls {...defaultProps} isCameraOff={true} />);

      expect(screen.getByRole('button', { name: /turn on camera/i })).toHaveClass('bg-red-500');
    });

    it('has gray background when camera is on', () => {
      render(<CallControls {...defaultProps} isCameraOff={false} />);

      expect(screen.getByRole('button', { name: /turn off camera/i })).toHaveClass('bg-gray-700');
    });
  });

  describe('End call button', () => {
    it('calls onEndCall when clicked', () => {
      render(<CallControls {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /end call/i }));

      expect(defaultProps.onEndCall).toHaveBeenCalledTimes(1);
    });

    it('is enabled during active call', () => {
      render(<CallControls {...defaultProps} callState="active" />);

      expect(screen.getByRole('button', { name: /end call/i })).not.toBeDisabled();
    });

    it('is enabled during connecting state', () => {
      render(<CallControls {...defaultProps} callState="connecting" />);

      expect(screen.getByRole('button', { name: /end call/i })).not.toBeDisabled();
    });

    it('is enabled during ringing state', () => {
      render(<CallControls {...defaultProps} callState="ringing" />);

      expect(screen.getByRole('button', { name: /end call/i })).not.toBeDisabled();
    });

    it('is enabled during initiating state', () => {
      render(<CallControls {...defaultProps} callState="initiating" />);

      expect(screen.getByRole('button', { name: /end call/i })).not.toBeDisabled();
    });

    it('is disabled during ended state', () => {
      render(<CallControls {...defaultProps} callState="ended" />);

      expect(screen.getByRole('button', { name: /end call/i })).toBeDisabled();
    });

    it('is disabled during idle state', () => {
      render(<CallControls {...defaultProps} callState="idle" />);

      expect(screen.getByRole('button', { name: /end call/i })).toBeDisabled();
    });
  });

  describe('Control button states based on call state', () => {
    it('disables mute and camera buttons when call is idle', () => {
      render(<CallControls {...defaultProps} callState="idle" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeDisabled();
    });

    it('disables mute and camera buttons when call is initiating', () => {
      render(<CallControls {...defaultProps} callState="initiating" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeDisabled();
    });

    it('disables mute and camera buttons when call is ringing', () => {
      render(<CallControls {...defaultProps} callState="ringing" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeDisabled();
    });

    it('enables mute and camera buttons when call is connecting', () => {
      render(<CallControls {...defaultProps} callState="connecting" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).not.toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).not.toBeDisabled();
    });

    it('enables mute and camera buttons when call is active', () => {
      render(<CallControls {...defaultProps} callState="active" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).not.toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).not.toBeDisabled();
    });

    it('disables mute and camera buttons when call has ended', () => {
      render(<CallControls {...defaultProps} callState="ended" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /turn off camera/i })).toBeDisabled();
    });

    it('shows opacity class when buttons are disabled', () => {
      render(<CallControls {...defaultProps} callState="idle" />);

      expect(screen.getByRole('button', { name: /mute microphone/i })).toHaveClass('opacity-50');
      expect(screen.getByRole('button', { name: /turn off camera/i })).toHaveClass('opacity-50');
    });
  });

  describe('Accessibility', () => {
    it('all buttons have focus styles', () => {
      render(<CallControls {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toHaveClass('focus:ring-2');
      });
    });

    it('icons have aria-hidden attribute', () => {
      const { container } = render(<CallControls {...defaultProps} />);

      const svgs = container.querySelectorAll('svg');
      svgs.forEach((svg) => {
        expect(svg).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });
});
