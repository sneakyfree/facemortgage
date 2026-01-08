/**
 * PostCallRating component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PostCallRating from './PostCallRating';

// Mock the focus trap hook
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
  useEscapeKey: (active: boolean, callback: () => void) => {
    // Mocked
  },
}));

describe('PostCallRating', () => {
  const defaultProps = {
    professionalName: 'John Smith',
    callDuration: 125, // 2 minutes 5 seconds
    onSubmit: vi.fn(),
    onSkip: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    defaultProps.onSubmit.mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('renders the modal with proper accessibility attributes', () => {
      render(<PostCallRating {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'rating-title');
    });

    it('displays professional name and call duration', () => {
      render(<PostCallRating {...defaultProps} />);

      expect(screen.getByText(/You spoke with John Smith/)).toBeInTheDocument();
      expect(screen.getByText(/2 minutes 5 seconds/)).toBeInTheDocument();
    });

    it('displays "Call Ended" title', () => {
      render(<PostCallRating {...defaultProps} />);

      expect(screen.getByRole('heading', { name: 'Call Ended' })).toBeInTheDocument();
    });

    it('renders 5 star rating buttons', () => {
      render(<PostCallRating {...defaultProps} />);

      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toBeInTheDocument();

      const stars = screen.getAllByRole('radio');
      expect(stars).toHaveLength(5);
    });

    it('renders Skip and Submit buttons', () => {
      render(<PostCallRating {...defaultProps} />);

      expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit rating/i })).toBeInTheDocument();
    });
  });

  describe('Duration formatting', () => {
    it('formats duration with minutes and seconds', () => {
      render(<PostCallRating {...defaultProps} callDuration={125} />);

      expect(screen.getByText(/2 minutes 5 seconds/)).toBeInTheDocument();
    });

    it('formats singular minute correctly', () => {
      render(<PostCallRating {...defaultProps} callDuration={65} />);

      expect(screen.getByText(/1 minute 5 seconds/)).toBeInTheDocument();
    });

    it('formats seconds-only duration', () => {
      render(<PostCallRating {...defaultProps} callDuration={30} />);

      expect(screen.getByText(/30 seconds/)).toBeInTheDocument();
    });

    it('formats singular second correctly', () => {
      render(<PostCallRating {...defaultProps} callDuration={61} />);

      expect(screen.getByText(/1 minute 1 second/)).toBeInTheDocument();
    });
  });

  describe('Star rating interactions', () => {
    it('selects rating when star is clicked', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[2]); // Click 3rd star (3-star rating)

      expect(stars[2]).toHaveAttribute('aria-checked', 'true');
    });

    it('displays rating label when star is selected', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[4]); // Click 5th star

      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });

    it('shows correct labels for each rating', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');

      // Test rating labels
      await userEvent.click(stars[0]);
      expect(screen.getByText('Poor')).toBeInTheDocument();

      await userEvent.click(stars[1]);
      expect(screen.getByText('Fair')).toBeInTheDocument();

      await userEvent.click(stars[2]);
      expect(screen.getByText('Good')).toBeInTheDocument();

      await userEvent.click(stars[3]);
      expect(screen.getByText('Very Good')).toBeInTheDocument();

      await userEvent.click(stars[4]);
      expect(screen.getByText('Excellent')).toBeInTheDocument();
    });

    it('star buttons have proper aria-label', () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');

      expect(stars[0]).toHaveAttribute('aria-label', '1 star - Poor');
      expect(stars[1]).toHaveAttribute('aria-label', '2 stars - Fair');
      expect(stars[2]).toHaveAttribute('aria-label', '3 stars - Good');
      expect(stars[3]).toHaveAttribute('aria-label', '4 stars - Very Good');
      expect(stars[4]).toHaveAttribute('aria-label', '5 stars - Excellent');
    });
  });

  describe('Comment field', () => {
    it('does not show comment field initially', () => {
      render(<PostCallRating {...defaultProps} />);

      expect(screen.queryByPlaceholderText(/share your experience/i)).not.toBeInTheDocument();
    });

    it('shows comment field after selecting a rating', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[3]);

      expect(screen.getByPlaceholderText(/share your experience/i)).toBeInTheDocument();
    });

    it('allows entering a comment', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[3]);

      const textarea = screen.getByPlaceholderText(/share your experience/i);
      await userEvent.type(textarea, 'Great conversation!');

      expect(textarea).toHaveValue('Great conversation!');
    });
  });

  describe('Submit functionality', () => {
    it('submit button is disabled when no rating selected', () => {
      render(<PostCallRating {...defaultProps} />);

      expect(screen.getByRole('button', { name: /submit rating/i })).toBeDisabled();
    });

    it('submit button is enabled when rating is selected', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[3]);

      expect(screen.getByRole('button', { name: /submit rating/i })).not.toBeDisabled();
    });

    it('calls onSubmit with rating and comment when submitted', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[3]); // 4-star rating

      const textarea = screen.getByPlaceholderText(/share your experience/i);
      await userEvent.type(textarea, 'Great call!');

      await userEvent.click(screen.getByRole('button', { name: /submit rating/i }));

      await waitFor(() => {
        expect(defaultProps.onSubmit).toHaveBeenCalledWith(4, 'Great call!');
      });
    });

    it('calls onSubmit with rating only when no comment provided', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[4]); // 5-star rating

      await userEvent.click(screen.getByRole('button', { name: /submit rating/i }));

      await waitFor(() => {
        expect(defaultProps.onSubmit).toHaveBeenCalledWith(5, undefined);
      });
    });

    it('shows "Submitting..." text while submitting', async () => {
      defaultProps.onSubmit.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      await userEvent.click(stars[3]);

      await userEvent.click(screen.getByRole('button', { name: /submit rating/i }));

      expect(screen.getByText('Submitting...')).toBeInTheDocument();
    });
  });

  describe('Skip functionality', () => {
    it('calls onSkip when Skip button is clicked', async () => {
      render(<PostCallRating {...defaultProps} />);

      await userEvent.click(screen.getByRole('button', { name: /skip/i }));

      expect(defaultProps.onSkip).toHaveBeenCalledTimes(1);
    });
  });

  describe('Keyboard navigation', () => {
    it('navigates stars with arrow keys', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');

      // Click first star to select it
      await userEvent.click(stars[0]);
      expect(stars[0]).toHaveAttribute('aria-checked', 'true');

      // Navigate right
      fireEvent.keyDown(stars[0], { key: 'ArrowRight' });
      expect(stars[1]).toHaveAttribute('aria-checked', 'true');
    });

    it('selects star with Enter key', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');

      // Focus and press Enter on 3rd star
      stars[2].focus();
      fireEvent.keyDown(stars[2], { key: 'Enter' });

      expect(stars[2]).toHaveAttribute('aria-checked', 'true');
    });

    it('selects star with Space key', async () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');

      // Focus and press Space on 4th star
      stars[3].focus();
      fireEvent.keyDown(stars[3], { key: ' ' });

      expect(stars[3]).toHaveAttribute('aria-checked', 'true');
    });
  });

  describe('Accessibility', () => {
    it('rating question has proper id for aria-labelledby', () => {
      render(<PostCallRating {...defaultProps} />);

      const question = screen.getByText('How was your experience?');
      expect(question).toHaveAttribute('id', 'rating-question');
    });

    it('radiogroup has aria-labelledby pointing to question', () => {
      render(<PostCallRating {...defaultProps} />);

      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toHaveAttribute('aria-labelledby', 'rating-question');
    });

    it('star buttons have focus styles', () => {
      render(<PostCallRating {...defaultProps} />);

      const stars = screen.getAllByRole('radio');
      stars.forEach((star) => {
        expect(star).toHaveClass('focus:ring-2');
      });
    });

    it('icons have aria-hidden attribute', () => {
      const { container } = render(<PostCallRating {...defaultProps} />);

      const svgs = container.querySelectorAll('svg');
      svgs.forEach((svg) => {
        expect(svg).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });
});
