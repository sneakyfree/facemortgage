/**
 * LeadCaptureModal component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LeadCaptureModal from './LeadCaptureModal';

// Mock the API
const mockCaptureLead = vi.fn();
vi.mock('@/lib/api/endpoints', () => ({
  callsApi: {
    captureLead: (...args: unknown[]) => mockCaptureLead(...args),
  },
}));

describe('LeadCaptureModal', () => {
  const defaultProps = {
    callId: 'call-123',
    professionalName: 'John Doe',
    onClose: vi.fn(),
    onSkip: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockCaptureLead.mockResolvedValue({});
  });

  it('renders the modal with title and description', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    expect(screen.getByText('Stay Connected')).toBeInTheDocument();
    expect(screen.getByText(/Share your info so John Doe can follow up/)).toBeInTheDocument();
  });

  it('renders all form fields', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    expect(screen.getByText(/Your Name/)).toBeInTheDocument();
    expect(screen.getByText(/Email Address/)).toBeInTheDocument();
    expect(screen.getByText(/Phone Number/)).toBeInTheDocument();
    expect(screen.getByText(/What are you looking for/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('John Smith')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('john@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('(555) 123-4567')).toBeInTheDocument();
  });

  it('renders Submit and Skip buttons', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    expect(screen.getByText('Submit')).toBeInTheDocument();
    expect(screen.getByText('Skip for Now')).toBeInTheDocument();
  });

  it('calls onSkip when Skip button is clicked', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.click(screen.getByText('Skip for Now'));

    expect(defaultProps.onSkip).toHaveBeenCalledTimes(1);
  });

  it('calls onSkip when X button is clicked', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    // Find the X button (close button) by its aria-label
    const closeButton = screen.getByRole('button', { name: /close modal/i });
    fireEvent.click(closeButton);

    expect(defaultProps.onSkip).toHaveBeenCalledTimes(1);
  });

  it('updates form fields on input', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    const nameInput = screen.getByPlaceholderText('John Smith');
    fireEvent.change(nameInput, { target: { value: 'Jane Smith' } });
    expect(nameInput).toHaveValue('Jane Smith');

    const emailInput = screen.getByPlaceholderText('john@example.com');
    fireEvent.change(emailInput, { target: { value: 'jane@example.com' } });
    expect(emailInput).toHaveValue('jane@example.com');

    const phoneInput = screen.getByPlaceholderText('(555) 123-4567');
    fireEvent.change(phoneInput, { target: { value: '(555) 999-8888' } });
    expect(phoneInput).toHaveValue('(555) 999-8888');
  });

  it('submits form with correct data', async () => {
    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('John Smith'), {
      target: { value: 'Jane Smith' },
    });
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'jane@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText('(555) 123-4567'), {
      target: { value: '(555) 999-8888' },
    });
    const selectElement = screen.getByRole('combobox');
    fireEvent.change(selectElement, {
      target: { value: 'purchase' },
    });

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(mockCaptureLead).toHaveBeenCalledWith('call-123', {
        name: 'Jane Smith',
        email: 'jane@example.com',
        phone: '(555) 999-8888',
        loan_purpose: 'purchase',
      });
    });
  });

  it('shows success message after successful submission', async () => {
    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('John Smith'), {
      target: { value: 'Jane Smith' },
    });
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'jane@example.com' },
    });

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Thank You!')).toBeInTheDocument();
      expect(screen.getByText(/John Doe will follow up with you shortly/)).toBeInTheDocument();
    });
  });

  it('shows error message on API failure', async () => {
    mockCaptureLead.mockRejectedValueOnce(new Error('API Error'));

    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('John Smith'), {
      target: { value: 'Jane Smith' },
    });
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'jane@example.com' },
    });

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Failed to save your information. Please try again.')).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    mockCaptureLead.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('John Smith'), {
      target: { value: 'Jane Smith' },
    });
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'jane@example.com' },
    });

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });
  });

  it('disables submit button during submission', async () => {
    mockCaptureLead.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<LeadCaptureModal {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('John Smith'), {
      target: { value: 'Jane Smith' },
    });
    fireEvent.change(screen.getByPlaceholderText('john@example.com'), {
      target: { value: 'jane@example.com' },
    });

    fireEvent.click(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Saving...').closest('button')).toBeDisabled();
    });
  });

  it('renders loan purpose options', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();

    // Check options
    expect(screen.getByText('Select...')).toBeInTheDocument();
    expect(screen.getByText('Buying a Home')).toBeInTheDocument();
    expect(screen.getByText('Refinancing')).toBeInTheDocument();
    expect(screen.getByText('Cash-Out Refinance')).toBeInTheDocument();
    expect(screen.getByText('Pre-Approval')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Other' })).toBeInTheDocument();
  });

  it('shows privacy note at bottom', () => {
    render(<LeadCaptureModal {...defaultProps} />);

    expect(
      screen.getByText(/Your information is secure and will only be shared with John Doe/)
    ).toBeInTheDocument();
  });
});
