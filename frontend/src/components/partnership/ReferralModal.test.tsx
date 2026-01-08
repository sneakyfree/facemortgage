/**
 * ReferralModal component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReferralModal from './ReferralModal';
import type { PartnershipDetail } from '@/lib/api/endpoints';

// Mock the API
const mockSubmitReferral = vi.fn();
vi.mock('@/lib/api/endpoints', () => ({
  partnershipsApi: {
    submitReferral: (...args: unknown[]) => mockSubmitReferral(...args),
  },
}));

// Mock useFocusTrap and useEscapeKey hooks
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
  useEscapeKey: vi.fn(),
}));

describe('ReferralModal', () => {
  const mockPartnership: PartnershipDetail = {
    id: 'partnership-123',
    loan_officer_id: 'lo-456',
    loan_officer_name: 'John Smith',
    loan_officer_email: 'john@example.com',
    realtor_id: 'realtor-789',
    realtor_name: 'Jane Doe',
    realtor_email: 'jane@example.com',
    status: 'active',
    referral_count: 5,
    created_at: '2024-01-01T00:00:00Z',
  };

  const defaultProps = {
    partnership: mockPartnership,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSubmitReferral.mockResolvedValue({});
  });

  describe('Rendering', () => {
    it('renders the modal with title and loan officer name', () => {
      render(<ReferralModal {...defaultProps} />);

      // Check the title heading
      expect(screen.getByRole('heading', { name: 'Send Referral' })).toBeInTheDocument();
      expect(screen.getByText('to John Smith')).toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByText('Client Name *')).toBeInTheDocument();
      expect(screen.getByText('Email *')).toBeInTheDocument();
      expect(screen.getByText('Phone')).toBeInTheDocument();
      expect(screen.getByText('Property Address')).toBeInTheDocument();
      expect(screen.getByText('Loan Purpose')).toBeInTheDocument();
      expect(screen.getByText('Est. Loan Amount')).toBeInTheDocument();
      expect(screen.getByText(/Notes for John/)).toBeInTheDocument();
    });

    it('renders Cancel and Send Referral buttons', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Send Referral' })).toBeInTheDocument();
    });

    it('renders loan purpose options', () => {
      render(<ReferralModal {...defaultProps} />);

      const selects = screen.getAllByRole('combobox');
      expect(selects).toHaveLength(2);

      const loanPurposeSelect = selects[0];
      expect(loanPurposeSelect).toBeInTheDocument();

      // Check loan purpose options exist
      expect(screen.getByRole('option', { name: 'Purchase' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Refinance' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Cash-Out' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Pre-Approval' })).toBeInTheDocument();
    });

    it('renders estimated loan amount options', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('option', { name: 'Under $200K' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '$200K - $400K' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '$400K - $600K' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: '$600K - $1M' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Over $1M' })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible dialog role', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has aria-modal attribute', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute(
        'aria-labelledby',
        'referral-modal-title'
      );
    });

    it('has close button with aria-label', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByRole('button', { name: /close modal/i })).toBeInTheDocument();
    });

    it('icons have aria-hidden attribute', () => {
      const { container } = render(<ReferralModal {...defaultProps} />);

      const svgs = container.querySelectorAll('svg');
      svgs.forEach((svg) => {
        expect(svg).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });

  describe('Form interactions', () => {
    it('calls onClose when Cancel button is clicked', () => {
      render(<ReferralModal {...defaultProps} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when X button is clicked', () => {
      render(<ReferralModal {...defaultProps} />);

      fireEvent.click(screen.getByRole('button', { name: /close modal/i }));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('updates form fields on input', () => {
      render(<ReferralModal {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText('John Smith');
      fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });
      expect(nameInput).toHaveValue('Jane Smith');

      const emailInput = screen.getByPlaceholderText('john@email.com');
      fireEvent.change(emailInput, { target: { value: 'jane@email.com' } });
      expect(emailInput).toHaveValue('jane@email.com');

      const phoneInput = screen.getByPlaceholderText('(555) 123-4567');
      fireEvent.change(phoneInput, { target: { value: '(555) 999-8888' } });
      expect(phoneInput).toHaveValue('(555) 999-8888');

      const addressInput = screen.getByPlaceholderText('123 Main St, City, State 12345');
      fireEvent.change(addressInput, { target: { value: '456 Oak Ave' } });
      expect(addressInput).toHaveValue('456 Oak Ave');
    });

    it('updates select fields on change', () => {
      render(<ReferralModal {...defaultProps} />);

      const selects = screen.getAllByRole('combobox');
      const loanPurposeSelect = selects[0];
      const amountSelect = selects[1];

      fireEvent.change(loanPurposeSelect, { target: { value: 'purchase' } });
      expect(loanPurposeSelect).toHaveValue('purchase');

      fireEvent.change(amountSelect, { target: { value: '350000' } });
      expect(amountSelect).toHaveValue('350000');
    });

    it('updates notes textarea on input', () => {
      render(<ReferralModal {...defaultProps} />);

      const textarea = screen.getByPlaceholderText('Any additional info that would help...');
      fireEvent.change(textarea, { target: { value: 'Some notes' } });
      expect(textarea).toHaveValue('Some notes');
    });
  });

  describe('Form submission', () => {
    it('submits form with correct data', async () => {
      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('(555) 123-4567'), {
        target: { value: '(555) 111-2222' },
      });
      fireEvent.change(screen.getByPlaceholderText('123 Main St, City, State 12345'), {
        target: { value: '789 Pine St' },
      });

      const selects = screen.getAllByRole('combobox');
      fireEvent.change(selects[0], { target: { value: 'purchase' } });
      fireEvent.change(selects[1], { target: { value: '550000' } });

      fireEvent.change(screen.getByPlaceholderText('Any additional info that would help...'), {
        target: { value: 'Test notes' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(mockSubmitReferral).toHaveBeenCalledWith('partnership-123', {
          borrower_name: 'Client Name',
          borrower_email: 'client@example.com',
          borrower_phone: '(555) 111-2222',
          property_address: '789 Pine St',
          loan_purpose: 'purchase',
          estimated_amount: 550000,
          notes: 'Test notes',
        });
      });
    });

    it('shows loading state during submission', async () => {
      mockSubmitReferral.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument();
      });
    });

    it('disables submit button during submission', async () => {
      mockSubmitReferral.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByText('Sending...').closest('button')).toBeDisabled();
      });
    });

    it('shows success message after successful submission', async () => {
      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByText('Referral Sent!')).toBeInTheDocument();
      });

      // Check success message content
      expect(
        screen.getByText(/John Smith has been notified and will reach out to Client Name shortly/)
      ).toBeInTheDocument();
    });

    it('success modal has proper accessibility attributes', async () => {
      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        const successDialog = screen.getByRole('dialog');
        expect(successDialog).toHaveAttribute('aria-modal', 'true');
        expect(successDialog).toHaveAttribute('aria-labelledby', 'referral-success-title');
      });
    });

    it('calls onSuccess after timeout following successful submission', async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      // Wait for success state
      await vi.waitFor(() => {
        expect(screen.getByText('Referral Sent!')).toBeInTheDocument();
      });

      // Advance timers by 2 seconds
      await vi.advanceTimersByTimeAsync(2000);

      expect(defaultProps.onSuccess).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });

    it('shows error message on API failure', async () => {
      mockSubmitReferral.mockRejectedValueOnce(new Error('API Error'));

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('error message has role="alert" for accessibility', async () => {
      mockSubmitReferral.mockRejectedValueOnce(new Error('API Error'));

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('shows generic error message when error is not an Error instance', async () => {
      mockSubmitReferral.mockRejectedValueOnce('Some string error');

      render(<ReferralModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('John Smith'), {
        target: { value: 'Client Name' },
      });
      fireEvent.change(screen.getByPlaceholderText('john@email.com'), {
        target: { value: 'client@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Send Referral' }));

      await waitFor(() => {
        expect(screen.getByText('Failed to submit referral')).toBeInTheDocument();
      });
    });
  });

  describe('Required fields', () => {
    it('client name input has required attribute', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('John Smith')).toBeRequired();
    });

    it('email input has required attribute', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('john@email.com')).toBeRequired();
    });

    it('optional fields do not have required attribute', () => {
      render(<ReferralModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('(555) 123-4567')).not.toBeRequired();
      expect(
        screen.getByPlaceholderText('123 Main St, City, State 12345')
      ).not.toBeRequired();
      expect(
        screen.getByPlaceholderText('Any additional info that would help...')
      ).not.toBeRequired();
    });
  });
});
