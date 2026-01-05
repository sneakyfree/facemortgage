'use client';

import { ReactNode } from 'react';

interface ResponsiveContainerProps {
  children: ReactNode;
  className?: string;
  /** Add padding for mobile navigation */
  withMobileNav?: boolean;
}

/**
 * Responsive container with consistent max-width and padding.
 */
export function ResponsiveContainer({
  children,
  className = '',
  withMobileNav = false,
}: ResponsiveContainerProps) {
  return (
    <div
      className={`
        w-full max-w-7xl mx-auto
        px-4 sm:px-6 lg:px-8
        ${withMobileNav ? 'pt-20 pb-20 lg:pt-6 lg:pb-6' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

interface ResponsiveGridProps {
  children: ReactNode;
  className?: string;
  /** Minimum column width in pixels */
  minColWidth?: number;
  /** Gap between items */
  gap?: 'sm' | 'md' | 'lg';
}

/**
 * Responsive grid that automatically adjusts columns based on screen size.
 */
export function ResponsiveGrid({
  children,
  className = '',
  minColWidth = 280,
  gap = 'md',
}: ResponsiveGridProps) {
  const gapClasses = {
    sm: 'gap-3',
    md: 'gap-4 sm:gap-6',
    lg: 'gap-6 sm:gap-8',
  };

  return (
    <div
      className={`grid ${gapClasses[gap]} ${className}`}
      style={{
        gridTemplateColumns: `repeat(auto-fill, minmax(min(${minColWidth}px, 100%), 1fr))`,
      }}
    >
      {children}
    </div>
  );
}

interface StackProps {
  children: ReactNode;
  className?: string;
  gap?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Stack direction on different breakpoints */
  direction?: 'vertical' | 'horizontal' | 'responsive';
}

/**
 * Stack component for consistent vertical/horizontal spacing.
 */
export function Stack({
  children,
  className = '',
  gap = 'md',
  direction = 'vertical',
}: StackProps) {
  const gapClasses = {
    xs: 'gap-1',
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
    xl: 'gap-8',
  };

  const directionClasses = {
    vertical: 'flex flex-col',
    horizontal: 'flex flex-row',
    responsive: 'flex flex-col sm:flex-row',
  };

  return (
    <div className={`${directionClasses[direction]} ${gapClasses[gap]} ${className}`}>
      {children}
    </div>
  );
}

interface HideOnMobileProps {
  children: ReactNode;
  /** Breakpoint to show content */
  showAt?: 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * Hide content on mobile devices.
 */
export function HideOnMobile({ children, showAt = 'md' }: HideOnMobileProps) {
  const classes = {
    sm: 'hidden sm:block',
    md: 'hidden md:block',
    lg: 'hidden lg:block',
    xl: 'hidden xl:block',
  };

  return <div className={classes[showAt]}>{children}</div>;
}

interface ShowOnMobileProps {
  children: ReactNode;
  /** Breakpoint to hide content */
  hideAt?: 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * Show content only on mobile devices.
 */
export function ShowOnMobile({ children, hideAt = 'md' }: ShowOnMobileProps) {
  const classes = {
    sm: 'sm:hidden',
    md: 'md:hidden',
    lg: 'lg:hidden',
    xl: 'xl:hidden',
  };

  return <div className={classes[hideAt]}>{children}</div>;
}
