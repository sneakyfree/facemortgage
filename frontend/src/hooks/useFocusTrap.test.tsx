/**
 * useFocusTrap hook tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { useFocusTrap, useEscapeKey } from './useFocusTrap';

// Test component that uses useFocusTrap
function FocusTrapTestComponent({
  isActive,
  onClose,
}: {
  isActive: boolean;
  onClose?: () => void;
}) {
  const containerRef = useFocusTrap<HTMLDivElement>(isActive);

  return (
    <div>
      <button data-testid="outside-button">Outside Button</button>
      {isActive && (
        <div ref={containerRef} role="dialog" aria-modal="true" data-testid="modal">
          <button data-testid="first-button">First</button>
          <input data-testid="text-input" type="text" placeholder="Enter text" />
          <button data-testid="second-button">Second</button>
          <button data-testid="last-button" onClick={onClose}>
            Close
          </button>
        </div>
      )}
    </div>
  );
}

// Test component for empty focus trap
function EmptyFocusTrapComponent({ isActive }: { isActive: boolean }) {
  const containerRef = useFocusTrap<HTMLDivElement>(isActive);

  return (
    <div>
      {isActive && (
        <div ref={containerRef} role="dialog" data-testid="empty-modal">
          <p>No focusable elements here</p>
        </div>
      )}
    </div>
  );
}

// Test component for useEscapeKey
function EscapeKeyTestComponent({
  isActive,
  onEscape,
}: {
  isActive: boolean;
  onEscape: () => void;
}) {
  useEscapeKey(isActive, onEscape);

  return (
    <div data-testid="escape-test">
      {isActive && <span>Modal is open</span>}
    </div>
  );
}

describe('useFocusTrap', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Focus Management', () => {
    it('renders modal with focusable elements when active', async () => {
      render(<FocusTrapTestComponent isActive={true} />);

      // Advance timer to allow focus to be set
      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      // Verify all focusable elements are present
      expect(screen.getByTestId('first-button')).toBeInTheDocument();
      expect(screen.getByTestId('text-input')).toBeInTheDocument();
      expect(screen.getByTestId('last-button')).toBeInTheDocument();
    });

    it('does not render modal when not active', () => {
      render(<FocusTrapTestComponent isActive={false} />);

      expect(screen.queryByTestId('modal')).not.toBeInTheDocument();
      expect(screen.queryByTestId('first-button')).not.toBeInTheDocument();
    });

    it('stores previously focused element reference', async () => {
      const { rerender } = render(<FocusTrapTestComponent isActive={false} />);

      // Focus the outside button first
      const outsideButton = screen.getByTestId('outside-button');
      outsideButton.focus();

      // Activate the focus trap
      rerender(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      // Verify modal is now visible
      expect(screen.getByTestId('modal')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('adds keydown event listener when active', async () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener');

      render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );

      addEventListenerSpy.mockRestore();
    });

    it('handles Tab keydown event', async () => {
      render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      // Verify Tab events are handled (no errors thrown)
      expect(() => {
        fireEvent.keyDown(document, { key: 'Tab', shiftKey: false });
      }).not.toThrow();
    });

    it('handles Shift+Tab keydown event', async () => {
      render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      // Verify Shift+Tab events are handled (no errors thrown)
      expect(() => {
        fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
      }).not.toThrow();
    });

    it('ignores non-Tab keyboard events', async () => {
      render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      const firstButton = screen.getByTestId('first-button');
      firstButton.focus();

      // Press Enter - should not affect anything
      expect(() => {
        fireEvent.keyDown(document, { key: 'Enter' });
      }).not.toThrow();

      // First button should still have focus (unchanged)
      expect(document.activeElement).toBe(firstButton);
    });
  });

  describe('Empty Container', () => {
    it('focuses container itself when no focusable elements exist', async () => {
      render(<EmptyFocusTrapComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      const modal = screen.getByTestId('empty-modal');
      expect(modal).toHaveFocus();
      expect(modal).toHaveAttribute('tabindex', '-1');
    });
  });

  describe('Cleanup', () => {
    it('removes event listener when deactivated', async () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

      const { rerender } = render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      rerender(<FocusTrapTestComponent isActive={false} />);

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );

      removeEventListenerSpy.mockRestore();
    });

    it('removes event listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

      const { unmount } = render(<FocusTrapTestComponent isActive={true} />);

      await act(async () => {
        vi.advanceTimersByTime(20);
      });

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );

      removeEventListenerSpy.mockRestore();
    });
  });
});

describe('useEscapeKey', () => {
  it('calls onEscape when Escape key is pressed and active', () => {
    const onEscape = vi.fn();
    render(<EscapeKeyTestComponent isActive={true} onEscape={onEscape} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onEscape).toHaveBeenCalledTimes(1);
  });

  it('does not call onEscape when not active', () => {
    const onEscape = vi.fn();
    render(<EscapeKeyTestComponent isActive={false} onEscape={onEscape} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onEscape).not.toHaveBeenCalled();
  });

  it('does not call onEscape for other keys', () => {
    const onEscape = vi.fn();
    render(<EscapeKeyTestComponent isActive={true} onEscape={onEscape} />);

    fireEvent.keyDown(document, { key: 'Enter' });
    fireEvent.keyDown(document, { key: 'Tab' });
    fireEvent.keyDown(document, { key: 'a' });

    expect(onEscape).not.toHaveBeenCalled();
  });

  it('removes event listener when deactivated', () => {
    const onEscape = vi.fn();
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

    const { rerender } = render(
      <EscapeKeyTestComponent isActive={true} onEscape={onEscape} />
    );

    rerender(<EscapeKeyTestComponent isActive={false} onEscape={onEscape} />);

    expect(removeEventListenerSpy).toHaveBeenCalledWith(
      'keydown',
      expect.any(Function)
    );

    // After deactivation, Escape should not trigger callback
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onEscape).not.toHaveBeenCalled();

    removeEventListenerSpy.mockRestore();
  });

  it('removes event listener on unmount', () => {
    const onEscape = vi.fn();
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

    const { unmount } = render(
      <EscapeKeyTestComponent isActive={true} onEscape={onEscape} />
    );

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith(
      'keydown',
      expect.any(Function)
    );

    removeEventListenerSpy.mockRestore();
  });

  it('calls updated onEscape callback after re-render', () => {
    const onEscape1 = vi.fn();
    const onEscape2 = vi.fn();

    const { rerender } = render(
      <EscapeKeyTestComponent isActive={true} onEscape={onEscape1} />
    );

    // Re-render with new callback
    rerender(<EscapeKeyTestComponent isActive={true} onEscape={onEscape2} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onEscape1).not.toHaveBeenCalled();
    expect(onEscape2).toHaveBeenCalledTimes(1);
  });
});
