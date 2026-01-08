/**
 * Header component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Header from './Header';

// Mock Next.js Link component
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock the auth store
const mockLogout = vi.fn();
const mockAuthStore = {
  user: null as { first_name: string; user_type: string } | null,
  isAuthenticated: false,
  logout: mockLogout,
};

vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => mockAuthStore,
}));

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthStore.user = null;
    mockAuthStore.isAuthenticated = false;
  });

  it('renders logo and brand name', () => {
    render(<Header />);

    expect(screen.getByText('FM')).toBeInTheDocument();
    expect(screen.getByText('FaceMortgage')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(<Header />);

    expect(screen.getByText('Find Professionals')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
    expect(screen.getByText('For Professionals')).toBeInTheDocument();
  });

  it('shows login and signup buttons when not authenticated', () => {
    render(<Header />);

    expect(screen.getByText('Log In')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();
  });

  it('does not show dashboard or logout when not authenticated', () => {
    render(<Header />);

    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Logout')).not.toBeInTheDocument();
  });

  it('shows user greeting when authenticated', () => {
    mockAuthStore.user = { first_name: 'John', user_type: 'loan_officer' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    expect(screen.getByText('Hello,')).toBeInTheDocument();
    expect(screen.getByText('John')).toBeInTheDocument();
  });

  it('shows logout button when authenticated', () => {
    mockAuthStore.user = { first_name: 'John', user_type: 'loan_officer' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  it('shows dashboard button for non-borrower users', () => {
    mockAuthStore.user = { first_name: 'John', user_type: 'loan_officer' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('hides dashboard button for borrower users', () => {
    mockAuthStore.user = { first_name: 'Jane', user_type: 'borrower' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });

  it('calls logout when logout button is clicked', () => {
    mockAuthStore.user = { first_name: 'John', user_type: 'loan_officer' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    fireEvent.click(screen.getByText('Logout'));

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it('has correct href for logo link', () => {
    render(<Header />);

    const logoLink = screen.getByText('FaceMortgage').closest('a');
    expect(logoLink).toHaveAttribute('href', '/');
  });

  it('has correct href for login link', () => {
    render(<Header />);

    const loginLink = screen.getByText('Log In').closest('a');
    expect(loginLink).toHaveAttribute('href', '/auth/login');
  });

  it('has correct href for signup link', () => {
    render(<Header />);

    const signupLink = screen.getByText('Sign Up').closest('a');
    expect(signupLink).toHaveAttribute('href', '/auth/register');
  });

  it('has correct href for dashboard link when authenticated', () => {
    mockAuthStore.user = { first_name: 'John', user_type: 'loan_officer' };
    mockAuthStore.isAuthenticated = true;

    render(<Header />);

    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
  });
});
