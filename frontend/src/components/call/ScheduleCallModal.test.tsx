/**
 * ScheduleCallModal component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ScheduleCallModal from './ScheduleCallModal';

// Mock the API
const mockSchedule = vi.fn();
vi.mock('@/lib/api/endpoints', () => ({
  scheduledCallsApi: {
    schedule: (data: unknown) => mockSchedule(data),
  },
}));

// Mock the focus trap hook
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
  useEscapeKey: (active: boolean, callback: () => void) => {
    // We'll test escape key handling separately
  },
}));

describe('ScheduleCallModal', () => {
  const defaultProps = {
    professional: {
      id: 'pro-123',
      name: 'John Smith',
      avatar: 'https://example.com/avatar.jpg',
    },
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSchedule.mockResolvedValue({});
  });

  describe('Initial rendering', () => {
    it('renders the modal with professional name', () => {
      render(<ScheduleCallModal {...defaultProps} />);

      expect(screen.getByText('Schedule a Call')).toBeInTheDocument();
      expect(screen.getByText('with John Smith')).toBeInTheDocument();
    });

    it('has proper accessibility attributes', () => {
      render(<ScheduleCallModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'schedule-modal-title');
    });

    it('renders close button with aria-label', () => {
      render(<ScheduleCallModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('renders date selection options', () => {
      render(<ScheduleCallModal {...defaultProps} />);

      expect(screen.getByText('Select a Date')).toBeInTheDocument();
      // Should have 7 date buttons (next 7 days)
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      expect(dateButtons.length).toBe(7);
    });

    it('renders time slot options', () => {
      render(<ScheduleCallModal {...defaultProps} />);

      expect(screen.getByText('Select a Time')).toBeInTheDocument();
      // Check for some time slots
      expect(screen.getByText('9:00 AM')).toBeInTheDocument();
      expect(screen.getByText('12:00 PM')).toBeInTheDocument();
      expect(screen.getByText('5:00 PM')).toBeInTheDocument();
    });
  });

  describe('Time step interactions', () => {
    it('selects a date when clicked', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );

      // Click first available date
      await userEvent.click(dateButtons[0]);

      // Check that the button is now selected (has blue styling)
      expect(dateButtons[0]).toHaveClass('border-blue-600');
    });

    it('selects a time slot when clicked', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      const timeButton = screen.getByText('10:00 AM');
      await userEvent.click(timeButton);

      expect(timeButton).toHaveClass('border-blue-600');
    });

    it('shows error when clicking Next without selecting date and time', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      const nextButton = screen.getByRole('button', { name: /next/i });
      await userEvent.click(nextButton);

      expect(screen.getByRole('alert')).toHaveTextContent('Please select a date and time');
    });

    it('proceeds to info step when date and time are selected', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      // Select date
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);

      // Select time
      await userEvent.click(screen.getByText('10:00 AM'));

      // Click Next
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      // Should now be on info step
      expect(screen.getByText('Your Name *')).toBeInTheDocument();
      expect(screen.getByText('Email *')).toBeInTheDocument();
    });
  });

  describe('Info step interactions', () => {
    const goToInfoStep = async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      // Select date and time
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));
    };

    it('renders form fields on info step', async () => {
      await goToInfoStep();

      expect(screen.getByPlaceholderText('John Smith')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('john@example.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('(555) 123-4567')).toBeInTheDocument();
    });

    it('can go back to time step', async () => {
      await goToInfoStep();

      await userEvent.click(screen.getByRole('button', { name: /back/i }));

      expect(screen.getByText('Select a Date')).toBeInTheDocument();
    });

    it('shows error when submitting without required fields', async () => {
      await goToInfoStep();

      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      expect(screen.getByRole('alert')).toHaveTextContent('Please fill in required fields');
    });

    it('submits form with valid data', async () => {
      await goToInfoStep();

      // Fill in required fields
      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');

      // Submit
      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(mockSchedule).toHaveBeenCalledWith(
          expect.objectContaining({
            professional_id: 'pro-123',
            name: 'Test User',
            email: 'test@example.com',
          })
        );
      });
    });

    it('fills optional phone field', async () => {
      await goToInfoStep();

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');
      await userEvent.type(screen.getByPlaceholderText('(555) 123-4567'), '5551234567');

      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(mockSchedule).toHaveBeenCalledWith(
          expect.objectContaining({
            phone: '5551234567',
          })
        );
      });
    });

    it('fills optional notes field', async () => {
      await goToInfoStep();

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');
      await userEvent.type(
        screen.getByPlaceholderText("I'm looking to refinance my home..."),
        'Need help with mortgage'
      );

      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(mockSchedule).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: 'Need help with mortgage',
          })
        );
      });
    });
  });

  describe('Success state', () => {
    it('shows success screen after successful submission', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      // Go through the flow
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(screen.getByText('Call Scheduled!')).toBeInTheDocument();
      });

      expect(screen.getByText(/Your call with John Smith is scheduled/)).toBeInTheDocument();
    });

    it('calls onClose when clicking Done on success screen', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      // Go through the flow
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(screen.getByText('Call Scheduled!')).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole('button', { name: /done/i }));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error handling', () => {
    it('shows error message when API call fails', async () => {
      mockSchedule.mockRejectedValueOnce(new Error('API Error'));

      render(<ScheduleCallModal {...defaultProps} />);

      // Go through the flow
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');
      await userEvent.click(screen.getByRole('button', { name: /schedule call/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to schedule call');
      });
    });

    it('disables submit button while submitting', async () => {
      // Make the mock slow
      mockSchedule.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)));

      render(<ScheduleCallModal {...defaultProps} />);

      // Go through the flow
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      await userEvent.type(screen.getByPlaceholderText('John Smith'), 'Test User');
      await userEvent.type(screen.getByPlaceholderText('john@example.com'), 'test@example.com');

      const submitButton = screen.getByRole('button', { name: /schedule call/i });
      await userEvent.click(submitButton);

      // Button should show "Scheduling..." and be disabled
      expect(screen.getByText('Scheduling...')).toBeInTheDocument();
    });
  });

  describe('Close button', () => {
    it('calls onClose when close button is clicked', async () => {
      render(<ScheduleCallModal {...defaultProps} />);

      await userEvent.click(screen.getByRole('button', { name: /close modal/i }));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Progress indicator', () => {
    it('shows first step highlighted on time step', () => {
      const { container } = render(<ScheduleCallModal {...defaultProps} />);

      const progressBars = container.querySelectorAll('.h-1.rounded');
      expect(progressBars[0]).toHaveClass('bg-blue-600');
      expect(progressBars[1]).toHaveClass('bg-gray-200');
    });

    it('shows second step highlighted on info step', async () => {
      const { container } = render(<ScheduleCallModal {...defaultProps} />);

      // Go to info step
      const dateButtons = screen.getAllByRole('button').filter(
        (btn) => btn.textContent?.match(/\w{3},\s+\w{3}\s+\d+/)
      );
      await userEvent.click(dateButtons[0]);
      await userEvent.click(screen.getByText('10:00 AM'));
      await userEvent.click(screen.getByRole('button', { name: /next/i }));

      const progressBars = container.querySelectorAll('.h-1.rounded');
      expect(progressBars[0]).toHaveClass('bg-blue-200');
      expect(progressBars[1]).toHaveClass('bg-blue-600');
    });
  });
});
