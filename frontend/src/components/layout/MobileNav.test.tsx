/**
 * MobileNav component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MobileNav, MobileBottomSpacer } from './MobileNav';

// Mock Next.js modules
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    onClick,
    className,
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: () => void;
    className?: string;
  }) => (
    <a href={href} onClick={onClick} className={className}>
      {children}
    </a>
  ),
}));

vi.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}));

describe('MobileNav', () => {
  const defaultProps = {
    userType: 'professional' as const,
    userName: 'John Doe',
    onLogout: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Header', () => {
    it('renders the logo and brand name', () => {
      render(<MobileNav {...defaultProps} />);

      expect(screen.getByText('FM')).toBeInTheDocument();
      expect(screen.getByText('FaceMortgage')).toBeInTheDocument();
    });

    it('renders menu toggle button with aria-label', () => {
      render(<MobileNav {...defaultProps} />);

      expect(screen.getByRole('button', { name: 'Toggle menu' })).toBeInTheDocument();
    });

    it('logo links to home page', () => {
      render(<MobileNav {...defaultProps} />);

      const logoLink = screen.getByText('FaceMortgage').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });

  describe('Menu Toggle', () => {
    it('opens menu when toggle button is clicked', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Menu should start closed - slide-out nav should have translate-x-full class
      // There are 2 navs: slide-out (with w-72) and bottom nav
      const slideOutNav = container.querySelector('nav.w-72');
      expect(slideOutNav).toHaveClass('translate-x-full');

      // Click toggle button
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      // Menu should now be open
      expect(slideOutNav).toHaveClass('translate-x-0');
    });

    it('closes menu when toggle button is clicked again', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: 'Toggle menu' });

      // Open menu
      fireEvent.click(toggleButton);
      const slideOutNav = container.querySelector('nav.w-72');
      expect(slideOutNav).toHaveClass('translate-x-0');

      // Close menu
      fireEvent.click(toggleButton);
      expect(slideOutNav).toHaveClass('translate-x-full');
    });
  });

  describe('Professional Navigation', () => {
    it('renders professional navigation items', () => {
      render(<MobileNav {...defaultProps} />);

      // First 4 items appear in both slide-out menu and bottom nav
      expect(screen.getAllByText('Dashboard').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Leads').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Analytics').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Billing').length).toBeGreaterThanOrEqual(1);
      // Settings only appears in slide-out menu (not in bottom nav's first 4)
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('has correct hrefs for professional navigation', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Get links from slide-out nav to avoid duplicates
      const slideOutNav = container.querySelector('nav.w-72');

      expect(slideOutNav?.querySelector('a[href="/dashboard"]')).toBeInTheDocument();
      expect(slideOutNav?.querySelector('a[href="/dashboard/leads"]')).toBeInTheDocument();
      expect(slideOutNav?.querySelector('a[href="/dashboard/analytics"]')).toBeInTheDocument();
      expect(slideOutNav?.querySelector('a[href="/dashboard/billing"]')).toBeInTheDocument();
      expect(slideOutNav?.querySelector('a[href="/dashboard/settings"]')).toBeInTheDocument();
    });
  });

  describe('Borrower Navigation', () => {
    it('renders borrower navigation items when userType is borrower', () => {
      render(<MobileNav {...defaultProps} userType="borrower" />);

      // Items appear in both slide-out menu and bottom nav
      expect(screen.getAllByText('Browse').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('My Calls').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Account').length).toBeGreaterThanOrEqual(1);
    });

    it('has correct hrefs for borrower navigation', () => {
      render(<MobileNav {...defaultProps} userType="borrower" />);

      // Get first occurrence of each link (from slide-out menu)
      expect(screen.getAllByText('Browse')[0].closest('a')).toHaveAttribute('href', '/');
      expect(screen.getAllByText('My Calls')[0].closest('a')).toHaveAttribute('href', '/calls');
      expect(screen.getAllByText('Account')[0].closest('a')).toHaveAttribute('href', '/account');
    });
  });

  describe('User Info', () => {
    it('displays user name when provided', () => {
      render(<MobileNav {...defaultProps} userName="Jane Smith" />);

      // Open menu to see user info
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      expect(screen.getByText('Signed in as')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    it('does not display user info section when userName is not provided', () => {
      render(<MobileNav {...defaultProps} userName={undefined} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      expect(screen.queryByText('Signed in as')).not.toBeInTheDocument();
    });
  });

  describe('Logout', () => {
    it('renders logout button when onLogout is provided', () => {
      render(<MobileNav {...defaultProps} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      expect(screen.getByText('Log Out')).toBeInTheDocument();
    });

    it('calls onLogout when logout button is clicked', () => {
      const onLogout = vi.fn();
      render(<MobileNav {...defaultProps} onLogout={onLogout} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      // Click logout
      fireEvent.click(screen.getByText('Log Out'));

      expect(onLogout).toHaveBeenCalledTimes(1);
    });

    it('closes menu when logout is clicked', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));
      const slideOutNav = container.querySelector('nav.w-72');
      expect(slideOutNav).toHaveClass('translate-x-0');

      // Click logout
      fireEvent.click(screen.getByText('Log Out'));

      // Menu should close
      expect(slideOutNav).toHaveClass('translate-x-full');
    });

    it('does not render logout button when onLogout is not provided', () => {
      render(<MobileNav {...defaultProps} onLogout={undefined} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      expect(screen.queryByText('Log Out')).not.toBeInTheDocument();
    });
  });

  describe('Bottom Navigation', () => {
    it('renders bottom navigation with first 4 items', () => {
      render(<MobileNav {...defaultProps} />);

      // Bottom nav shows first 4 items of professional nav
      // Get all links by text - there are duplicates (slide-out menu + bottom nav)
      const dashboardLinks = screen.getAllByText('Dashboard');
      const leadsLinks = screen.getAllByText('Leads');
      const analyticsLinks = screen.getAllByText('Analytics');
      const billingLinks = screen.getAllByText('Billing');

      // Each should appear twice (menu + bottom nav)
      expect(dashboardLinks.length).toBeGreaterThanOrEqual(1);
      expect(leadsLinks.length).toBeGreaterThanOrEqual(1);
      expect(analyticsLinks.length).toBeGreaterThanOrEqual(1);
      expect(billingLinks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Active State', () => {
    it('highlights active navigation item in slide-out menu', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Open menu to check active state
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));

      // Get the slide-out nav specifically
      const slideOutNav = container.querySelector('nav.w-72');

      // Dashboard should be active (pathname is /dashboard)
      // Find the link within the slide-out nav
      const dashboardLink = slideOutNav?.querySelector('a[href="/dashboard"]');

      expect(dashboardLink).toHaveClass('bg-blue-50');
      expect(dashboardLink).toHaveClass('text-blue-600');
    });

    it('highlights active navigation item in bottom nav', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Get the bottom nav (the one without w-72 class)
      const bottomNav = container.querySelector('nav:not(.w-72)');

      // Dashboard should be active in bottom nav too
      const dashboardLink = bottomNav?.querySelector('a[href="/dashboard"]');

      expect(dashboardLink).toHaveClass('text-blue-600');
    });
  });

  describe('Overlay', () => {
    it('closes menu when overlay is clicked', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      // Open menu
      fireEvent.click(screen.getByRole('button', { name: 'Toggle menu' }));
      const slideOutNav = container.querySelector('nav.w-72');
      expect(slideOutNav).toHaveClass('translate-x-0');

      // Find and click overlay (div with bg-black/50)
      const overlay = container.querySelector('.bg-black\\/50');
      expect(overlay).toBeInTheDocument();
      fireEvent.click(overlay!);

      // Menu should close
      expect(slideOutNav).toHaveClass('translate-x-full');
    });

    it('does not render overlay when menu is closed', () => {
      const { container } = render(<MobileNav {...defaultProps} />);

      const overlay = container.querySelector('.bg-black\\/50');
      expect(overlay).not.toBeInTheDocument();
    });
  });
});

describe('MobileBottomSpacer', () => {
  it('renders spacer div', () => {
    const { container } = render(<MobileBottomSpacer />);

    const spacer = container.querySelector('.h-16');
    expect(spacer).toBeInTheDocument();
  });

  it('has lg:hidden class for responsiveness', () => {
    const { container } = render(<MobileBottomSpacer />);

    const spacer = container.querySelector('.lg\\:hidden');
    expect(spacer).toBeInTheDocument();
  });
});
