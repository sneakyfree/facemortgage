/**
 * Accessibility Utilities for FaceMortgage
 * 
 * Provides WCAG AA compliance helpers:
 * - Skip links
 * - Focus management
 * - ARIA live regions
 * - Keyboard navigation
 * - Screen reader announcements
 */

'use client';

import { useEffect, useRef, useCallback } from 'react';

// ==================== Skip Link Component ====================

export function SkipLink({ targetId = 'main-content' }: { targetId?: string }) {
    return (
        <a
            href={`#${targetId}`}
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            onClick={(e) => {
                e.preventDefault();
                const target = document.getElementById(targetId);
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }}
        >
            Skip to main content
        </a>
    );
}

// ==================== Focus Management Hook ====================

export function useFocusTrap(isActive: boolean) {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isActive || !containerRef.current) return;

        const container = containerRef.current;
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement?.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement?.focus();
                }
            }
        };

        // Focus first element when trap activates
        firstElement?.focus();

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [isActive]);

    return containerRef;
}

// ==================== Restore Focus Hook ====================

export function useRestoreFocus() {
    const previousActiveElement = useRef<HTMLElement | null>(null);

    const saveFocus = useCallback(() => {
        previousActiveElement.current = document.activeElement as HTMLElement;
    }, []);

    const restoreFocus = useCallback(() => {
        previousActiveElement.current?.focus();
    }, []);

    return { saveFocus, restoreFocus };
}

// ==================== Live Region Component ====================

interface LiveRegionProps {
    message: string;
    politeness?: 'polite' | 'assertive';
    clearAfter?: number;
}

export function LiveRegion({
    message,
    politeness = 'polite',
    clearAfter = 5000
}: LiveRegionProps) {
    const regionRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!message) return;

        const timer = setTimeout(() => {
            if (regionRef.current) {
                regionRef.current.textContent = '';
            }
        }, clearAfter);

        return () => clearTimeout(timer);
    }, [message, clearAfter]);

    return (
        <div
            ref={regionRef}
            role="status"
            aria-live={politeness}
            aria-atomic="true"
            className="sr-only"
        >
            {message}
        </div>
    );
}

// ==================== Screen Reader Announcer ====================

let announcer: HTMLDivElement | null = null;

function getAnnouncer(): HTMLDivElement {
    if (!announcer) {
        announcer = document.createElement('div');
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);
    }
    return announcer;
}

export function announce(message: string, politeness: 'polite' | 'assertive' = 'polite') {
    const el = getAnnouncer();
    el.setAttribute('aria-live', politeness);

    // Clear and set to trigger announcement
    el.textContent = '';
    setTimeout(() => {
        el.textContent = message;
    }, 100);
}

// ==================== Keyboard Navigation Hook ====================

interface KeyboardNavOptions {
    orientation?: 'horizontal' | 'vertical' | 'both';
    wrap?: boolean;
    onSelect?: (index: number) => void;
}

export function useKeyboardNavigation(
    itemCount: number,
    options: KeyboardNavOptions = {}
) {
    const { orientation = 'vertical', wrap = true, onSelect } = options;
    const currentIndex = useRef(0);

    const handleKeyDown = useCallback((e: React.KeyboardEvent, initialIndex: number) => {
        currentIndex.current = initialIndex;

        let newIndex = currentIndex.current;
        let handled = false;

        switch (e.key) {
            case 'ArrowDown':
                if (orientation !== 'horizontal') {
                    newIndex = currentIndex.current + 1;
                    handled = true;
                }
                break;
            case 'ArrowUp':
                if (orientation !== 'horizontal') {
                    newIndex = currentIndex.current - 1;
                    handled = true;
                }
                break;
            case 'ArrowRight':
                if (orientation !== 'vertical') {
                    newIndex = currentIndex.current + 1;
                    handled = true;
                }
                break;
            case 'ArrowLeft':
                if (orientation !== 'vertical') {
                    newIndex = currentIndex.current - 1;
                    handled = true;
                }
                break;
            case 'Home':
                newIndex = 0;
                handled = true;
                break;
            case 'End':
                newIndex = itemCount - 1;
                handled = true;
                break;
            case 'Enter':
            case ' ':
                onSelect?.(currentIndex.current);
                handled = true;
                break;
        }

        if (handled) {
            e.preventDefault();

            // Handle wrapping
            if (wrap) {
                if (newIndex < 0) newIndex = itemCount - 1;
                if (newIndex >= itemCount) newIndex = 0;
            } else {
                newIndex = Math.max(0, Math.min(itemCount - 1, newIndex));
            }

            currentIndex.current = newIndex;
        }

        return newIndex;
    }, [itemCount, orientation, wrap, onSelect]);

    return { handleKeyDown, currentIndex: currentIndex.current };
}

// ==================== Visible Focus Indicator ====================

export function FocusIndicator({
    children,
    className = ''
}: {
    children: React.ReactNode;
    className?: string;
}) {
    return (
        <div className={`focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 rounded-lg ${className}`}>
            {children}
        </div>
    );
}

// ==================== Accessible Button ====================

interface AccessibleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    loading?: boolean;
    loadingText?: string;
}

export function AccessibleButton({
    children,
    loading,
    loadingText = 'Loading...',
    disabled,
    ...props
}: AccessibleButtonProps) {
    return (
        <button
            disabled={disabled || loading}
            aria-busy={loading}
            aria-disabled={disabled || loading}
            {...props}
        >
            {loading ? (
                <>
                    <span className="sr-only">{loadingText}</span>
                    <span aria-hidden="true">{loadingText}</span>
                </>
            ) : (
                children
            )}
        </button>
    );
}

// ==================== Visually Hidden ====================

export function VisuallyHidden({ children }: { children: React.ReactNode }) {
    return (
        <span className="sr-only">
            {children}
        </span>
    );
}

export default {
    SkipLink,
    useFocusTrap,
    useRestoreFocus,
    LiveRegion,
    announce,
    useKeyboardNavigation,
    FocusIndicator,
    AccessibleButton,
    VisuallyHidden,
};
