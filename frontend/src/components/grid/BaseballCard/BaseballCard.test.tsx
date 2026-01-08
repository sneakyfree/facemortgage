/**
 * BaseballCard component tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BaseballCard } from './BaseballCard';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockBaseballCardData = {
  nmls_id: '123456',
  name: 'John Smith',
  company: 'ABC Mortgage',
  license_status: 'Active',
  license_status_color: 'green',
  years_experience_display: '10+ years',
  total_loans_display: '500',
  total_volume_display: '$125M',
  loans_12m_display: '45',
  volume_12m_display: '$12.5M',
  avg_loan_display: '$278K',
  loan_mix: [
    { type: 'Conventional', pct: 45.5 },
    { type: 'FHA', pct: 30.0 },
    { type: 'VA', pct: 15.5 },
    { type: 'Other', pct: 9.0 },
  ],
  purpose_mix: [
    { type: 'Purchase', pct: 60.0 },
    { type: 'Refinance', pct: 40.0 },
  ],
  rankings: [
    { label: 'State Rank', value: '#15' },
    { label: 'Market Rank', value: '#5' },
  ],
  states_licensed: ['CA', 'TX', 'FL', 'NY'],
  top_markets: ['Los Angeles, CA', 'San Francisco, CA'],
};

describe('BaseballCard', () => {
  const defaultProps = {
    nmlsId: '123456',
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Loading State', () => {
    it('renders loading skeleton while fetching data', async () => {
      // Never resolve to stay in loading state
      mockFetch.mockImplementation(() => new Promise(() => {}));

      const { container } = render(<BaseballCard {...defaultProps} />);

      // Should show loading skeleton with animate-pulse
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    });

    it('fetches data from correct endpoint', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });

      render(<BaseballCard {...defaultProps} />);

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/stats/123456/baseball-card');
    });
  });

  describe('Error State', () => {
    it('displays error message when fetch fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to fetch stats')).toBeInTheDocument();
      });
    });

    it('displays generic error when non-Error thrown', async () => {
      mockFetch.mockRejectedValueOnce('Network error');

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('An error occurred')).toBeInTheDocument();
      });
    });

    it('renders close button in error state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
      });
    });

    it('calls onClose when close button is clicked in error state', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i });
        fireEvent.click(closeButton);
      });

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Success State', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });
    });

    it('renders professional name', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument();
      });
    });

    it('renders custom professional name when provided', async () => {
      render(<BaseballCard {...defaultProps} professionalName="Jane Doe" />);

      await waitFor(() => {
        expect(screen.getByText('Jane Doe')).toBeInTheDocument();
      });
    });

    it('renders company name', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('ABC Mortgage')).toBeInTheDocument();
      });
    });

    it('renders NMLS ID', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('NMLS# 123456')).toBeInTheDocument();
      });
    });

    it('renders license status', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
      });
    });

    it('renders key metrics (experience, career loans, volume)', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('10+ years')).toBeInTheDocument();
        expect(screen.getByText('500')).toBeInTheDocument();
        expect(screen.getByText('$125M')).toBeInTheDocument();
      });
    });

    it('renders last 12 months performance stats', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument();
        expect(screen.getByText('$12.5M')).toBeInTheDocument();
        expect(screen.getByText('$278K')).toBeInTheDocument();
      });
    });

    it('renders loan type mix', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Conventional')).toBeInTheDocument();
        expect(screen.getByText('45.5%')).toBeInTheDocument();
        expect(screen.getByText('FHA')).toBeInTheDocument();
        expect(screen.getByText('30.0%')).toBeInTheDocument();
        expect(screen.getByText('VA')).toBeInTheDocument();
        expect(screen.getByText('15.5%')).toBeInTheDocument();
      });
    });

    it('renders purpose mix', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Purchase')).toBeInTheDocument();
        expect(screen.getByText('60.0%')).toBeInTheDocument();
        expect(screen.getByText('Refinance')).toBeInTheDocument();
        expect(screen.getByText('40.0%')).toBeInTheDocument();
      });
    });

    it('renders rankings when available', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('State Rank')).toBeInTheDocument();
        expect(screen.getByText('#15')).toBeInTheDocument();
        expect(screen.getByText('Market Rank')).toBeInTheDocument();
        expect(screen.getByText('#5')).toBeInTheDocument();
      });
    });

    it('renders licensed states', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('CA')).toBeInTheDocument();
        expect(screen.getByText('TX')).toBeInTheDocument();
        expect(screen.getByText('FL')).toBeInTheDocument();
        expect(screen.getByText('NY')).toBeInTheDocument();
      });
    });

    it('renders top markets', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Los Angeles, CA')).toBeInTheDocument();
        expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
      });
    });

    it('renders footer disclaimer', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText('Data provided by industry sources. Updated periodically.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Close Functionality', () => {
    it('has close button in header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });

      const { container } = render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        // Find the X button in the header (not the error state close button)
        const closeButtons = container.querySelectorAll('button');
        expect(closeButtons.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('calls onClose when close button is clicked', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });

      const { container } = render(<BaseballCard {...defaultProps} />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('John Smith')).toBeInTheDocument();
      });

      // Find and click the close button
      const closeButton = container.querySelector('button');
      expect(closeButton).toBeInTheDocument();
      fireEvent.click(closeButton!);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Professional Image', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });
    });

    it('renders professional image when provided', async () => {
      render(
        <BaseballCard
          {...defaultProps}
          professionalImage="https://example.com/photo.jpg"
        />
      );

      await waitFor(() => {
        const img = screen.getByRole('img');
        expect(img).toHaveAttribute('src', 'https://example.com/photo.jpg');
        expect(img).toHaveAttribute('alt', 'John Smith');
      });
    });

    it('renders initials when no image provided', async () => {
      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('J')).toBeInTheDocument();
      });
    });
  });

  describe('Empty Data Handling', () => {
    it('does not render rankings section when empty', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockBaseballCardData,
            rankings: [],
          }),
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('State Rank')).not.toBeInTheDocument();
      });
    });

    it('does not render top markets section when empty', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockBaseballCardData,
            top_markets: [],
          }),
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('Top Markets')).not.toBeInTheDocument();
      });
    });

    it('does not render company when null', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            ...mockBaseballCardData,
            company: null,
          }),
      });

      render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.queryByText('ABC Mortgage')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockBaseballCardData),
      });
    });

    it('has modal overlay with proper z-index', async () => {
      const { container } = render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        const overlay = container.firstChild as HTMLElement;
        expect(overlay).toHaveClass('z-50');
      });
    });

    it('is centered in viewport', async () => {
      const { container } = render(<BaseballCard {...defaultProps} />);

      await waitFor(() => {
        const overlay = container.firstChild as HTMLElement;
        expect(overlay).toHaveClass('flex');
        expect(overlay).toHaveClass('items-center');
        expect(overlay).toHaveClass('justify-center');
      });
    });
  });
});
