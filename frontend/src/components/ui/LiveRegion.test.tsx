/**
 * LiveRegion component tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, renderHook } from '@testing-library/react';
import { LiveRegion, useLiveRegion } from './LiveRegion';

describe('LiveRegion', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders with the provided message', () => {
      render(<LiveRegion message="Loading..." />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders empty when message is empty', () => {
      const { container } = render(<LiveRegion message="" />);

      const liveRegion = container.querySelector('[role="status"]');
      expect(liveRegion).toHaveTextContent('');
    });
  });

  describe('Accessibility Attributes', () => {
    it('has role="status" for screen reader announcements', () => {
      render(<LiveRegion message="Test message" />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live="polite" by default', () => {
      render(<LiveRegion message="Test message" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
    });

    it('has aria-live="assertive" when priority is assertive', () => {
      render(<LiveRegion message="Error!" priority="assertive" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'assertive');
    });

    it('has aria-atomic="true" for atomic announcements', () => {
      render(<LiveRegion message="Test message" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-atomic', 'true');
    });

    it('has sr-only class for visual hiding', () => {
      render(<LiveRegion message="Test message" />);

      expect(screen.getByRole('status')).toHaveClass('sr-only');
    });
  });

  describe('Message Updates', () => {
    it('updates message when prop changes', () => {
      const { rerender } = render(<LiveRegion message="Initial message" />);

      expect(screen.getByText('Initial message')).toBeInTheDocument();

      rerender(<LiveRegion message="Updated message" />);

      expect(screen.getByText('Updated message')).toBeInTheDocument();
    });
  });

  describe('Clear After', () => {
    it('clears message after specified time', async () => {
      render(<LiveRegion message="Temporary message" clearAfter={3000} />);

      expect(screen.getByText('Temporary message')).toBeInTheDocument();

      // Advance time by 3 seconds
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000);
      });

      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveTextContent('');
    });

    it('does not clear message when clearAfter is 0', async () => {
      render(<LiveRegion message="Persistent message" clearAfter={0} />);

      expect(screen.getByText('Persistent message')).toBeInTheDocument();

      // Advance time by 10 seconds
      await act(async () => {
        await vi.advanceTimersByTimeAsync(10000);
      });

      // Message should still be there
      expect(screen.getByText('Persistent message')).toBeInTheDocument();
    });

    it('does not clear when message is empty', async () => {
      const { container } = render(<LiveRegion message="" clearAfter={1000} />);

      const liveRegion = container.querySelector('[role="status"]');
      expect(liveRegion).toHaveTextContent('');

      // No error should occur
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(liveRegion).toHaveTextContent('');
    });

    it('clears previous timer when message changes', async () => {
      const { rerender } = render(
        <LiveRegion message="First message" clearAfter={5000} />
      );

      // Advance 2 seconds
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      // Message should still be there
      expect(screen.getByText('First message')).toBeInTheDocument();

      // Update message
      rerender(<LiveRegion message="Second message" clearAfter={5000} />);

      // New timer should start
      await act(async () => {
        await vi.advanceTimersByTimeAsync(4000);
      });

      // Still there after 4 seconds
      expect(screen.getByText('Second message')).toBeInTheDocument();

      // Should clear after full 5 seconds from new message
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000);
      });

      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveTextContent('');
    });
  });
});

describe('useLiveRegion', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // Test wrapper component to properly test the hook
  function TestComponent({
    onMount,
    defaultPriority,
  }: {
    onMount?: (api: ReturnType<typeof useLiveRegion>) => void;
    defaultPriority?: 'polite' | 'assertive';
  }) {
    const api = useLiveRegion(defaultPriority);

    // Expose the API to the test via onMount
    if (onMount) {
      onMount(api);
    }

    return <api.LiveRegionComponent />;
  }

  it('returns announce function, clear function, and LiveRegionComponent', () => {
    const { result } = renderHook(() => useLiveRegion());

    expect(result.current.announce).toBeDefined();
    expect(typeof result.current.announce).toBe('function');
    expect(result.current.clear).toBeDefined();
    expect(typeof result.current.clear).toBe('function');
    expect(result.current.LiveRegionComponent).toBeDefined();
  });

  it('uses default polite priority', () => {
    const { container } = render(<TestComponent />);

    const liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
  });

  it('can be initialized with assertive default priority', () => {
    const { container } = render(<TestComponent defaultPriority="assertive" />);

    const liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveAttribute('aria-live', 'assertive');
  });

  it('announces messages through LiveRegionComponent', async () => {
    let hookApi: ReturnType<typeof useLiveRegion>;

    const { container } = render(
      <TestComponent onMount={(api) => (hookApi = api)} />
    );

    await act(async () => {
      hookApi.announce('Hello world');
      await vi.advanceTimersByTimeAsync(100);
    });

    const liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('Hello world');
  });

  it('clears message with clear function', async () => {
    let hookApi: ReturnType<typeof useLiveRegion>;

    const { container } = render(
      <TestComponent onMount={(api) => (hookApi = api)} />
    );

    await act(async () => {
      hookApi.announce('Message to clear');
      await vi.advanceTimersByTimeAsync(100);
    });

    let liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('Message to clear');

    await act(async () => {
      hookApi.clear();
    });

    liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('');
  });

  it('clears message after specified time', async () => {
    let hookApi: ReturnType<typeof useLiveRegion>;

    const { container } = render(
      <TestComponent onMount={(api) => (hookApi = api)} />
    );

    await act(async () => {
      hookApi.announce('Temporary', { clearAfter: 2000 });
      await vi.advanceTimersByTimeAsync(100);
    });

    let liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('Temporary');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100);
    });

    liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('');
  });

  it('re-announces same message by clearing first', async () => {
    let hookApi: ReturnType<typeof useLiveRegion>;

    const { container } = render(
      <TestComponent onMount={(api) => (hookApi = api)} />
    );

    // First announcement
    await act(async () => {
      hookApi.announce('Same message');
      await vi.advanceTimersByTimeAsync(100);
    });

    let liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('Same message');

    // Same announcement again - should clear and re-announce
    await act(async () => {
      hookApi.announce('Same message');
      // Wait for clear and re-set
      await vi.advanceTimersByTimeAsync(100);
    });

    liveRegion = container.querySelector('[role="status"]');
    expect(liveRegion).toHaveTextContent('Same message');
  });
});
