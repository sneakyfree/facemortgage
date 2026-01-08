import { useEffect, useRef, useCallback, RefObject } from 'react';

/**
 * Custom hook to trap focus within a container element.
 * Essential for modal accessibility - prevents focus from escaping the modal
 * and returns focus to the trigger element when closed.
 *
 * @param isActive - Whether the focus trap is currently active
 * @returns ref to attach to the container element
 *
 * @example
 * ```tsx
 * function Modal({ isOpen, onClose }) {
 *   const containerRef = useFocusTrap(isOpen);
 *   return (
 *     <div ref={containerRef} role="dialog" aria-modal="true">
 *       ...
 *     </div>
 *   );
 * }
 * ```
 */
export function useFocusTrap<T extends HTMLElement = HTMLDivElement>(
  isActive: boolean
): RefObject<T> {
  const containerRef = useRef<T>(null);
  const previousActiveElement = useRef<Element | null>(null);

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return [];

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(focusableSelectors)
    ).filter((el) => {
      // Filter out hidden elements
      return el.offsetParent !== null;
    });
  }, []);

  // Handle tab key navigation
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isActive || event.key !== 'Tab') return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Shift + Tab: Move focus to last element if at first
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      }
      // Tab: Move focus to first element if at last
      else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [isActive, getFocusableElements]
  );

  // Set up and tear down the focus trap
  useEffect(() => {
    if (!isActive) return;

    // Store the previously focused element to restore later
    previousActiveElement.current = document.activeElement;

    // Focus the first focusable element in the container
    const focusableElements = getFocusableElements();
    if (focusableElements.length > 0) {
      // Small delay to ensure the modal is rendered
      setTimeout(() => {
        focusableElements[0].focus();
      }, 10);
    } else if (containerRef.current) {
      // If no focusable elements, focus the container itself
      containerRef.current.setAttribute('tabindex', '-1');
      containerRef.current.focus();
    }

    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // Restore focus to the previously focused element
      if (
        previousActiveElement.current &&
        previousActiveElement.current instanceof HTMLElement
      ) {
        previousActiveElement.current.focus();
      }
    };
  }, [isActive, getFocusableElements, handleKeyDown]);

  return containerRef;
}

/**
 * Hook to handle Escape key press for closing modals.
 *
 * @param isActive - Whether to listen for Escape key
 * @param onEscape - Callback when Escape is pressed
 *
 * @example
 * ```tsx
 * function Modal({ isOpen, onClose }) {
 *   useEscapeKey(isOpen, onClose);
 *   return <div>...</div>;
 * }
 * ```
 */
export function useEscapeKey(isActive: boolean, onEscape: () => void): void {
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onEscape();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isActive, onEscape]);
}

export default useFocusTrap;
