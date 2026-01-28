/**
 * Accessibility Utilities for FaceMortgage
 * 
 * WCAG 2.1 AA compliance helpers including:
 * - Screen reader announcements
 * - Focus management
 * - Keyboard navigation
 * - Color contrast helpers
 * - ARIA attribute helpers
 */

// ==================== Live Region Announcements ====================

/**
 * Announce message to screen readers using ARIA live region.
 * Creates a temporary element that's read aloud.
 */
export function announce(
    message: string,
    priority: 'polite' | 'assertive' = 'polite'
): void {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.setAttribute('class', 'sr-only');
    announcer.style.cssText = `
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    `;

    document.body.appendChild(announcer);

    // Delay to ensure the live region is registered
    setTimeout(() => {
        announcer.textContent = message;
    }, 100);

    // Clean up after announcement
    setTimeout(() => {
        document.body.removeChild(announcer);
    }, 1000);
}

/**
 * Announce loading state changes.
 */
export function announceLoading(isLoading: boolean, context?: string): void {
    if (isLoading) {
        announce(`Loading ${context || 'content'}...`);
    } else {
        announce(`${context || 'Content'} loaded`);
    }
}

/**
 * Announce form validation errors.
 */
export function announceError(error: string): void {
    announce(error, 'assertive');
}

/**
 * Announce successful actions.
 */
export function announceSuccess(message: string): void {
    announce(message, 'polite');
}

// ==================== Focus Management ====================

/**
 * Focus an element by ID, with fallback handling.
 */
export function focusElement(elementId: string): boolean {
    const element = document.getElementById(elementId);
    if (element) {
        element.focus();
        return true;
    }
    return false;
}

/**
 * Focus the first focusable element within a container.
 */
export function focusFirstFocusable(container: HTMLElement): boolean {
    const focusable = container.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusable.length > 0) {
        focusable[0].focus();
        return true;
    }
    return false;
}

/**
 * Trap focus within a container (for modals, dialogs).
 */
export function createFocusTrap(container: HTMLElement): () => void {
    const focusableElements = container.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            if (document.activeElement === firstFocusable) {
                lastFocusable?.focus();
                e.preventDefault();
            }
        } else {
            if (document.activeElement === lastFocusable) {
                firstFocusable?.focus();
                e.preventDefault();
            }
        }
    };

    container.addEventListener('keydown', handleKeyDown);

    // Return cleanup function
    return () => {
        container.removeEventListener('keydown', handleKeyDown);
    };
}

// ==================== Keyboard Navigation ====================

/**
 * Handle arrow key navigation in a list.
 */
export function handleArrowNavigation(
    e: React.KeyboardEvent,
    items: HTMLElement[],
    currentIndex: number,
    onIndexChange: (newIndex: number) => void
): void {
    let newIndex = currentIndex;

    switch (e.key) {
        case 'ArrowDown':
        case 'ArrowRight':
            newIndex = Math.min(currentIndex + 1, items.length - 1);
            break;
        case 'ArrowUp':
        case 'ArrowLeft':
            newIndex = Math.max(currentIndex - 1, 0);
            break;
        case 'Home':
            newIndex = 0;
            break;
        case 'End':
            newIndex = items.length - 1;
            break;
        default:
            return;
    }

    if (newIndex !== currentIndex) {
        e.preventDefault();
        onIndexChange(newIndex);
        items[newIndex]?.focus();
    }
}

// ==================== Color Contrast ====================

/**
 * Calculate relative luminance of a hex color.
 */
function getLuminance(hexColor: string): number {
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;

    const toLinear = (c: number) =>
        c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);

    return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

/**
 * Calculate contrast ratio between two colors.
 * WCAG AA requires 4.5:1 for normal text, 3:1 for large text.
 */
export function getContrastRatio(color1: string, color2: string): number {
    const l1 = getLuminance(color1);
    const l2 = getLuminance(color2);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Check if color combination meets WCAG AA standards.
 */
export function meetsContrastRequirement(
    foreground: string,
    background: string,
    isLargeText: boolean = false
): boolean {
    const ratio = getContrastRatio(foreground, background);
    return isLargeText ? ratio >= 3 : ratio >= 4.5;
}

// ==================== ARIA Helpers ====================

/**
 * Generate unique ID for ARIA relationships.
 */
export function generateAriaId(prefix: string): string {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * ARIA attributes for loading states.
 */
export function getLoadingAriaProps(isLoading: boolean) {
    return {
        'aria-busy': isLoading,
        'aria-live': 'polite' as const,
    };
}

/**
 * ARIA attributes for expandable sections.
 */
export function getExpandableAriaProps(isExpanded: boolean, controlsId: string) {
    return {
        'aria-expanded': isExpanded,
        'aria-controls': controlsId,
    };
}

/**
 * ARIA attributes for tabs.
 */
export function getTabAriaProps(
    isSelected: boolean,
    tabId: string,
    panelId: string
) {
    return {
        id: tabId,
        role: 'tab' as const,
        'aria-selected': isSelected,
        'aria-controls': panelId,
        tabIndex: isSelected ? 0 : -1,
    };
}

/**
 * ARIA attributes for tab panels.
 */
export function getTabPanelAriaProps(tabId: string, panelId: string) {
    return {
        id: panelId,
        role: 'tabpanel' as const,
        'aria-labelledby': tabId,
        tabIndex: 0,
    };
}

// ==================== Skip Link ====================

/**
 * Component-ready skip link attributes.
 * Place at the start of the page for keyboard users.
 */
export const SKIP_LINK_STYLES = `
    position: absolute;
    left: -10000px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
    
    &:focus {
        position: fixed;
        top: 0;
        left: 0;
        width: auto;
        height: auto;
        padding: 1rem;
        background: white;
        color: black;
        z-index: 10000;
        font-weight: bold;
    }
`;

// ==================== Reduced Motion ====================

/**
 * Check if user prefers reduced motion.
 */
export function prefersReducedMotion(): boolean {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Get animation duration based on user preference.
 */
export function getAnimationDuration(normalDurationMs: number): number {
    return prefersReducedMotion() ? 0 : normalDurationMs;
}
