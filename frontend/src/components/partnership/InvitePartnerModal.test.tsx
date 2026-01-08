/**
 * InvitePartnerModal component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InvitePartnerModal from './InvitePartnerModal';

// Mock the API
const mockInvitePartner = vi.fn();
vi.mock('@/lib/api/endpoints', () => ({
  partnershipsApi: {
    invitePartner: (...args: unknown[]) => mockInvitePartner(...args),
  },
}));

// Mock useFocusTrap and useEscapeKey hooks
vi.mock('@/hooks/useFocusTrap', () => ({
  useFocusTrap: () => ({ current: null }),
  useEscapeKey: vi.fn(),
}));

describe('InvitePartnerModal', () => {
  const defaultProps = {
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockInvitePartner.mockResolvedValue({});
  });

  describe('Rendering', () => {
    it('renders the modal with title and description', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByText('Invite Partner')).toBeInTheDocument();
      expect(screen.getByText('Add a realtor to your network')).toBeInTheDocument();
    });

    it('renders all form fields', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByText('Realtor Name *')).toBeInTheDocument();
      expect(screen.getByText('Email Address *')).toBeInTheDocument();
      expect(screen.getByText('Phone Number')).toBeInTheDocument();
      expect(screen.getByText('Company/Brokerage')).toBeInTheDocument();
    });

    it('renders Cancel and Send Invitation buttons', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Send Invitation')).toBeInTheDocument();
    });

    it('renders footer instruction text', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(
        screen.getByText("They'll receive an email with a link to accept the partnership.")
      ).toBeInTheDocument();
    });

    it('renders input placeholders', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('jane@realty.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('(555) 123-4567')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('ABC Realty')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has accessible dialog role', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has aria-modal attribute', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute(
        'aria-labelledby',
        'invite-modal-title'
      );
    });

    it('has close button with aria-label', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByRole('button', { name: /close modal/i })).toBeInTheDocument();
    });

    it('icons have aria-hidden attribute', () => {
      const { container } = render(<InvitePartnerModal {...defaultProps} />);

      const svgs = container.querySelectorAll('svg');
      svgs.forEach((svg) => {
        expect(svg).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('success modal has proper accessibility attributes', async () => {
      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        const successDialog = screen.getByRole('dialog');
        expect(successDialog).toHaveAttribute('aria-modal', 'true');
        expect(successDialog).toHaveAttribute('aria-labelledby', 'invite-success-title');
      });
    });

    it('error message has role="alert" for accessibility', async () => {
      mockInvitePartner.mockRejectedValueOnce(new Error('API Error'));

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });
  });

  describe('Form interactions', () => {
    it('calls onClose when Cancel button is clicked', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when X button is clicked', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      fireEvent.click(closeButton);
      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('updates form fields on input', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText('Jane Smith');
      fireEvent.change(nameInput, { target: { value: 'John Realtor' } });
      expect(nameInput).toHaveValue('John Realtor');

      const emailInput = screen.getByPlaceholderText('jane@realty.com');
      fireEvent.change(emailInput, { target: { value: 'john@realty.com' } });
      expect(emailInput).toHaveValue('john@realty.com');

      const phoneInput = screen.getByPlaceholderText('(555) 123-4567');
      fireEvent.change(phoneInput, { target: { value: '(555) 999-8888' } });
      expect(phoneInput).toHaveValue('(555) 999-8888');

      const companyInput = screen.getByPlaceholderText('ABC Realty');
      fireEvent.change(companyInput, { target: { value: 'XYZ Brokerage' } });
      expect(companyInput).toHaveValue('XYZ Brokerage');
    });
  });

  describe('Form submission', () => {
    it('submits form with correct data', async () => {
      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('(555) 123-4567'), {
        target: { value: '(555) 999-8888' },
      });
      fireEvent.change(screen.getByPlaceholderText('ABC Realty'), {
        target: { value: 'XYZ Brokerage' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(mockInvitePartner).toHaveBeenCalledWith({
          realtor_name: 'John Realtor',
          realtor_email: 'john@realty.com',
          realtor_phone: '(555) 999-8888',
          realtor_company: 'XYZ Brokerage',
        });
      });
    });

    it('submits form with only required fields', async () => {
      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(mockInvitePartner).toHaveBeenCalledWith({
          realtor_name: 'John Realtor',
          realtor_email: 'john@realty.com',
          realtor_phone: '',
          realtor_company: '',
        });
      });
    });

    it('shows loading state during submission', async () => {
      mockInvitePartner.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument();
      });
    });

    it('disables submit button during submission', async () => {
      mockInvitePartner.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByText('Sending...').closest('button')).toBeDisabled();
      });
    });

    it('shows success message after successful submission', async () => {
      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByText('Invitation Sent!')).toBeInTheDocument();
      });

      // Check success message content
      expect(
        screen.getByText(
          /John Realtor will receive an email with instructions to join your partnership/
        )
      ).toBeInTheDocument();
    });

    it('calls onSuccess after timeout following successful submission', async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      // Wait for success state
      await vi.waitFor(() => {
        expect(screen.getByText('Invitation Sent!')).toBeInTheDocument();
      });

      // Advance timers by 2 seconds
      await vi.advanceTimersByTimeAsync(2000);

      expect(defaultProps.onSuccess).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });

    it('shows error message on API failure', async () => {
      mockInvitePartner.mockRejectedValueOnce(new Error('API Error'));

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('shows generic error message when error is not an Error instance', async () => {
      mockInvitePartner.mockRejectedValueOnce('Some string error');

      render(<InvitePartnerModal {...defaultProps} />);

      fireEvent.change(screen.getByPlaceholderText('Jane Smith'), {
        target: { value: 'John Realtor' },
      });
      fireEvent.change(screen.getByPlaceholderText('jane@realty.com'), {
        target: { value: 'john@realty.com' },
      });

      fireEvent.click(screen.getByText('Send Invitation'));

      await waitFor(() => {
        expect(screen.getByText('Failed to send invitation')).toBeInTheDocument();
      });
    });
  });

  describe('Required fields', () => {
    it('realtor name input has required attribute', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('Jane Smith')).toBeRequired();
    });

    it('email input has required attribute', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('jane@realty.com')).toBeRequired();
    });

    it('optional fields do not have required attribute', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('(555) 123-4567')).not.toBeRequired();
      expect(screen.getByPlaceholderText('ABC Realty')).not.toBeRequired();
    });
  });

  describe('Input types', () => {
    it('email input has type="email"', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('jane@realty.com')).toHaveAttribute('type', 'email');
    });

    it('phone input has type="tel"', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('(555) 123-4567')).toHaveAttribute('type', 'tel');
    });

    it('name and company inputs have type="text"', () => {
      render(<InvitePartnerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText('Jane Smith')).toHaveAttribute('type', 'text');
      expect(screen.getByPlaceholderText('ABC Realty')).toHaveAttribute('type', 'text');
    });
  });
});
