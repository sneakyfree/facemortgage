'use client';

import { useEffect, useState } from 'react';

interface LiveRegionProps {
  /** Message to announce to screen readers */
  message: string;
  /** Priority level - 'polite' waits for user to finish, 'assertive' interrupts */
  priority?: 'polite' | 'assertive';
  /** Clear message after this many milliseconds (0 = never clear) */
  clearAfter?: number;
}

/**
 * LiveRegion component for announcing dynamic content changes to screen readers.
 *
 * This component is visually hidden but accessible to screen readers.
 * Use it to announce important status changes, form errors, loading states, etc.
 *
 * @example
 * ```tsx
 * // Announce a loading state
 * <LiveRegion message={isLoading ? "Loading results..." : ""} />
 *
 * // Announce form errors (assertive for immediate attention)
 * <LiveRegion message={error} priority="assertive" />
 *
 * // Announce success and clear after 3 seconds
 * <LiveRegion message="Saved successfully" clearAfter={3000} />
 * ```
 */
export function LiveRegion({
  message,
  priority = 'polite',
  clearAfter = 0,
}: LiveRegionProps) {
  const [announcement, setAnnouncement] = useState(message);

  useEffect(() => {
    setAnnouncement(message);

    if (clearAfter > 0 && message) {
      const timer = setTimeout(() => {
        setAnnouncement('');
      }, clearAfter);
      return () => clearTimeout(timer);
    }
  }, [message, clearAfter]);

  return (
    <div
      role="status"
      aria-live={priority}
      aria-atomic="true"
      className="sr-only"
    >
      {announcement}
    </div>
  );
}

/**
 * Hook to manage live region announcements programmatically.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { announce, LiveRegionComponent } = useLiveRegion();
 *
 *   const handleSave = async () => {
 *     await save();
 *     announce("Changes saved successfully");
 *   };
 *
 *   return (
 *     <>
 *       <LiveRegionComponent />
 *       <button onClick={handleSave}>Save</button>
 *     </>
 *   );
 * }
 * ```
 */
export function useLiveRegion(defaultPriority: 'polite' | 'assertive' = 'polite') {
  const [message, setMessage] = useState('');
  const [priority, setPriority] = useState(defaultPriority);

  const announce = (
    text: string,
    options?: { priority?: 'polite' | 'assertive'; clearAfter?: number }
  ) => {
    // Clear first to ensure re-announcement of same message
    setMessage('');
    setTimeout(() => {
      setMessage(text);
      if (options?.priority) {
        setPriority(options.priority);
      }
    }, 50);

    if (options?.clearAfter) {
      setTimeout(() => {
        setMessage('');
      }, options.clearAfter);
    }
  };

  const clear = () => setMessage('');

  const LiveRegionComponent = () => (
    <LiveRegion message={message} priority={priority} />
  );

  return { announce, clear, LiveRegionComponent };
}

export default LiveRegion;
