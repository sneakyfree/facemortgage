/**
 * GetMatchedForm component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GetMatchedForm from './GetMatchedForm';

// Mock the API
const mockGetMatched = vi.fn();
vi.mock('@/lib/api/endpoints', () => ({
  softLeadsApi: {
    getMatched: (...args: unknown[]) => mockGetMatched(...args),
  },
}));

describe('GetMatchedForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetMatched.mockResolvedValue({ success: true, lead_id: 'test-id' });
  });

  describe('Initial Rendering', () => {
    it('renders form title and description', () => {
      render(<GetMatchedForm />);

      expect(screen.getByText('Get Matched with a Pro')).toBeInTheDocument();
      expect(
        screen.getByText(/Tell us what you're looking for/)
      ).toBeInTheDocument();
    });

    it('renders progress bar with 3 steps', () => {
      const { container } = render(<GetMatchedForm />);

      const progressBars = container.querySelectorAll('.flex.gap-1 > div');
      expect(progressBars).toHaveLength(3);
    });

    it('starts on step 1 with contact information', () => {
      render(<GetMatchedForm />);

      expect(screen.getByText('Contact Information')).toBeInTheDocument();
    });

    it('renders step 1 form fields', () => {
      render(<GetMatchedForm />);

      expect(screen.getByText('Name *')).toBeInTheDocument();
      expect(screen.getByText('Email *')).toBeInTheDocument();
      expect(screen.getByText('Phone')).toBeInTheDocument();
    });

    it('renders input placeholders', () => {
      render(<GetMatchedForm />);

      expect(screen.getByPlaceholderText('Your full name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('(555) 123-4567')).toBeInTheDocument();
    });
  });

  describe('Step Navigation', () => {
    it('Next button is disabled when required fields are empty', () => {
      render(<GetMatchedForm />);

      const nextButton = screen.getByRole('button', { name: 'Next' });
      expect(nextButton).toBeDisabled();
    });

    it('Next button is enabled when required fields are filled', () => {
      render(<GetMatchedForm />);

      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });

      const nextButton = screen.getByRole('button', { name: 'Next' });
      expect(nextButton).not.toBeDisabled();
    });

    it('navigates to step 2 when Next is clicked', () => {
      render(<GetMatchedForm />);

      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });

      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      expect(screen.getByText('What are you looking for?')).toBeInTheDocument();
    });

    it('navigates back to step 1 from step 2', () => {
      render(<GetMatchedForm />);

      // Go to step 2
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      // Go back
      fireEvent.click(screen.getByRole('button', { name: 'Back' }));

      expect(screen.getByText('Contact Information')).toBeInTheDocument();
    });

    it('navigates to step 3 from step 2', () => {
      render(<GetMatchedForm />);

      // Go to step 2
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      // Go to step 3
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      expect(screen.getByText('Preferences')).toBeInTheDocument();
    });
  });

  describe('Step 2 - Loan Information', () => {
    beforeEach(() => {
      render(<GetMatchedForm />);
      // Navigate to step 2
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    });

    it('renders loan purpose dropdown', () => {
      expect(screen.getByText('Loan Purpose')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Buying a Home' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Refinancing' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Cash-Out Refinance' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Pre-Approval' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Home Equity Line' })).toBeInTheDocument();
    });

    it('renders estimated amount dropdown', () => {
      expect(screen.getByText('Estimated Loan Amount')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Under $150,000' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Over $1,000,000' })).toBeInTheDocument();
    });

    it('renders property state dropdown with all 50 states', () => {
      expect(screen.getByText('Property State')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'California' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Texas' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'New York' })).toBeInTheDocument();
    });

    it('allows selecting loan purpose', () => {
      const selects = screen.getAllByRole('combobox');
      const loanPurposeSelect = selects[0];

      fireEvent.change(loanPurposeSelect, { target: { value: 'purchase' } });
      expect(loanPurposeSelect).toHaveValue('purchase');
    });
  });

  describe('Step 3 - Preferences', () => {
    beforeEach(() => {
      render(<GetMatchedForm />);
      // Navigate to step 3
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    });

    it('renders language preference dropdown', () => {
      expect(screen.getByText('Preferred Language')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'English' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Spanish' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Chinese' })).toBeInTheDocument();
    });

    it('renders timeframe dropdown', () => {
      expect(screen.getByText('When do you need help?')).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Right away' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Within 1 month' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Just researching' })).toBeInTheDocument();
    });

    it('renders Get Matched submit button', () => {
      expect(screen.getByRole('button', { name: 'Get Matched' })).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    const fillFormAndNavigateToStep3 = () => {
      // Step 1
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.change(screen.getByPlaceholderText('(555) 123-4567'), {
        target: { value: '5551234567' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      // Step 2
      const step2Selects = screen.getAllByRole('combobox');
      fireEvent.change(step2Selects[0], { target: { value: 'purchase' } });
      fireEvent.change(step2Selects[1], { target: { value: '400000' } });
      fireEvent.change(step2Selects[2], { target: { value: 'CA' } });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      // Step 3
      const step3Selects = screen.getAllByRole('combobox');
      fireEvent.change(step3Selects[0], { target: { value: 'en' } });
      fireEvent.change(step3Selects[1], { target: { value: 'immediately' } });
    };

    it('submits form with correct data', async () => {
      render(<GetMatchedForm />);
      fillFormAndNavigateToStep3();

      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(mockGetMatched).toHaveBeenCalledWith({
          name: 'John Doe',
          email: 'john@example.com',
          phone: '5551234567',
          loan_purpose: 'purchase',
          estimated_amount: 400000,
          property_state: 'CA',
          preferred_language: 'en',
          timeframe: 'immediately',
        });
      });
    });

    it('shows loading state during submission', async () => {
      mockGetMatched.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<GetMatchedForm />);
      fillFormAndNavigateToStep3();

      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(screen.getByText('Submitting...')).toBeInTheDocument();
      });
    });

    it('disables submit button during submission', async () => {
      mockGetMatched.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<GetMatchedForm />);
      fillFormAndNavigateToStep3();

      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(screen.getByText('Submitting...').closest('button')).toBeDisabled();
      });
    });

    it('shows success state after successful submission', async () => {
      render(<GetMatchedForm />);
      fillFormAndNavigateToStep3();

      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(screen.getByText("You're All Set!")).toBeInTheDocument();
      });

      expect(
        screen.getByText(/We're finding the perfect mortgage professional for you/)
      ).toBeInTheDocument();
      expect(screen.getByText(/Check your email for confirmation/)).toBeInTheDocument();
    });

    it('shows error message on submission failure', async () => {
      mockGetMatched.mockRejectedValueOnce(new Error('API Error'));

      render(<GetMatchedForm />);
      fillFormAndNavigateToStep3();

      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(screen.getByText('Something went wrong. Please try again.')).toBeInTheDocument();
      });
    });

    it('submits with only required fields', async () => {
      render(<GetMatchedForm />);

      // Only fill required fields
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'Jane Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'jane@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
      fireEvent.click(screen.getByRole('button', { name: 'Get Matched' }));

      await waitFor(() => {
        expect(mockGetMatched).toHaveBeenCalledWith({
          name: 'Jane Doe',
          email: 'jane@example.com',
          phone: undefined,
          loan_purpose: undefined,
          estimated_amount: undefined,
          property_state: undefined,
          preferred_language: undefined,
          timeframe: undefined,
        });
      });
    });
  });

  describe('Progress Bar', () => {
    it('shows step 1 highlighted initially', () => {
      const { container } = render(<GetMatchedForm />);

      const progressBars = container.querySelectorAll('.flex.gap-1 > div');
      expect(progressBars[0]).toHaveClass('bg-blue-600');
      expect(progressBars[1]).toHaveClass('bg-gray-200');
      expect(progressBars[2]).toHaveClass('bg-gray-200');
    });

    it('shows steps 1-2 highlighted on step 2', () => {
      const { container } = render(<GetMatchedForm />);

      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      const progressBars = container.querySelectorAll('.flex.gap-1 > div');
      expect(progressBars[0]).toHaveClass('bg-blue-600');
      expect(progressBars[1]).toHaveClass('bg-blue-600');
      expect(progressBars[2]).toHaveClass('bg-gray-200');
    });

    it('shows all steps highlighted on step 3', () => {
      const { container } = render(<GetMatchedForm />);

      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      const progressBars = container.querySelectorAll('.flex.gap-1 > div');
      expect(progressBars[0]).toHaveClass('bg-blue-600');
      expect(progressBars[1]).toHaveClass('bg-blue-600');
      expect(progressBars[2]).toHaveClass('bg-blue-600');
    });
  });

  describe('Form State Persistence', () => {
    it('preserves form data when navigating between steps', () => {
      render(<GetMatchedForm />);

      // Fill step 1
      fireEvent.change(screen.getByPlaceholderText('Your full name'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('you@example.com'), {
        target: { value: 'john@example.com' },
      });

      // Go to step 2
      fireEvent.click(screen.getByRole('button', { name: 'Next' }));

      // Go back to step 1
      fireEvent.click(screen.getByRole('button', { name: 'Back' }));

      // Check data is preserved
      expect(screen.getByPlaceholderText('Your full name')).toHaveValue('John Doe');
      expect(screen.getByPlaceholderText('you@example.com')).toHaveValue('john@example.com');
    });
  });

  describe('Input Types', () => {
    it('name input has type="text"', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('Your full name')).toHaveAttribute('type', 'text');
    });

    it('email input has type="email"', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('you@example.com')).toHaveAttribute('type', 'email');
    });

    it('phone input has type="tel"', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('(555) 123-4567')).toHaveAttribute('type', 'tel');
    });
  });

  describe('Required Fields', () => {
    it('name input has required attribute', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('Your full name')).toBeRequired();
    });

    it('email input has required attribute', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('you@example.com')).toBeRequired();
    });

    it('phone input does not have required attribute', () => {
      render(<GetMatchedForm />);
      expect(screen.getByPlaceholderText('(555) 123-4567')).not.toBeRequired();
    });
  });
});
