/**
 * ProfessionalCard component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ProfessionalCard from './ProfessionalCard';
import type { ProfessionalGridItem } from '@/types';

// Mock the API
vi.mock('@/lib/api/endpoints', () => ({
  gridTrackingApi: {
    trackClick: vi.fn().mockResolvedValue({}),
  },
}));

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn().mockReturnValue('test-session-id'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(),
  length: 0,
};
Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

const mockProfessional: ProfessionalGridItem = {
  id: '123',
  user_id: 'user-123',
  first_name: 'John',
  last_name: 'Doe',
  user_type: 'loan_officer',
  company_name: 'ABC Mortgage',
  avatar_url: undefined,
  status: 'online_available',
  subscription_tier: 'professional',
  video_type: 'live',
  avg_rating: 4.5,
  total_reviews: 25,
  avg_pickup_time_seconds: 8,
  years_experience: 10,
  specialty_names: ['Purchase', 'Refinance', 'FHA'],
  language_codes: ['en', 'es'],
  nmls_id: '123456',
  grid_position: 1,
  score: 100,
};

describe('ProfessionalCard', () => {
  const mockOnCallClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders professional name correctly', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('displays company name when provided', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText(/ABC Mortgage/)).toBeInTheDocument();
  });

  it('shows Available status for online professional', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('Available')).toBeInTheDocument();
  });

  it('shows Busy status for offline professional', () => {
    const offlinePro = { ...mockProfessional, status: 'offline' as const };
    render(
      <ProfessionalCard
        professional={offlinePro}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('Busy')).toBeInTheDocument();
  });

  it('displays LIVE badge for live video type', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('LIVE')).toBeInTheDocument();
  });

  it('displays Video badge for recorded video type', () => {
    const recordedPro = { ...mockProfessional, video_type: 'recorded' as const };
    render(
      <ProfessionalCard
        professional={recordedPro}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('Video')).toBeInTheDocument();
  });

  it('displays rating correctly', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('4.5')).toBeInTheDocument();
    expect(screen.getByText('(25)')).toBeInTheDocument();
  });

  it('displays specialties', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('Purchase')).toBeInTheDocument();
    expect(screen.getByText('Refinance')).toBeInTheDocument();
    expect(screen.getByText('FHA')).toBeInTheDocument();
  });

  it('shows +X more when more than 3 specialties', () => {
    const manySpecialties = {
      ...mockProfessional,
      specialty_names: ['Purchase', 'Refinance', 'FHA', 'VA', 'USDA'],
    };
    render(
      <ProfessionalCard
        professional={manySpecialties}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('+2 more')).toBeInTheDocument();
  });

  it('displays language codes', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('EN')).toBeInTheDocument();
    expect(screen.getByText('ES')).toBeInTheDocument();
  });

  it('shows View Stats button when nmls_id is present', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('View Stats')).toBeInTheDocument();
  });

  it('hides View Stats button when nmls_id is absent', () => {
    const noNmls = { ...mockProfessional, nmls_id: undefined };
    render(
      <ProfessionalCard
        professional={noNmls}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.queryByText('View Stats')).not.toBeInTheDocument();
  });

  it('displays initials when no avatar', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('displays years of experience', () => {
    render(
      <ProfessionalCard
        professional={mockProfessional}
        onCallClick={mockOnCallClick}
      />
    );

    expect(screen.getByText('10yr')).toBeInTheDocument();
  });

  it('has reduced opacity when not available', () => {
    const offlinePro = { ...mockProfessional, status: 'offline' as const };
    const { container } = render(
      <ProfessionalCard
        professional={offlinePro}
        onCallClick={mockOnCallClick}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('opacity-75');
  });
});
