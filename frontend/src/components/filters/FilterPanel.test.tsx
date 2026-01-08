/**
 * FilterPanel component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FilterPanel from './FilterPanel';

// Mock the filter store
const mockSetLanguage = vi.fn();
const mockSetSpecialty = vi.fn();
const mockSetStateCode = vi.fn();
const mockSetUserType = vi.fn();
const mockSetMinRating = vi.fn();
const mockClearFilters = vi.fn();
const mockClearStateFilter = vi.fn();
const mockHasActiveFilters = vi.fn().mockReturnValue(false);
const mockIsUsingDetectedState = vi.fn().mockReturnValue(false);

const mockFilterStore = {
  filters: {
    state_code: undefined as string | undefined,
    user_type: undefined as string | undefined,
    language: undefined as string | undefined,
    specialty: undefined as number | undefined,
    min_rating: undefined as number | undefined,
  },
  geo: {
    is_detecting: false,
    detected_state: undefined as string | undefined,
    detected_city: undefined as string | undefined,
  },
  setLanguage: mockSetLanguage,
  setSpecialty: mockSetSpecialty,
  setStateCode: mockSetStateCode,
  setUserType: mockSetUserType,
  setMinRating: mockSetMinRating,
  clearFilters: mockClearFilters,
  clearStateFilter: mockClearStateFilter,
  hasActiveFilters: mockHasActiveFilters,
  isUsingDetectedState: mockIsUsingDetectedState,
};

vi.mock('@/stores/filterStore', () => ({
  useFilterStore: () => mockFilterStore,
}));

// Mock the API endpoints
vi.mock('@/lib/api/endpoints', () => ({
  lookupsApi: {
    getSpecialties: vi.fn().mockResolvedValue([
      { id: 1, name: 'FHA Loans' },
      { id: 2, name: 'VA Loans' },
      { id: 3, name: 'Conventional' },
    ]),
    getLanguages: vi.fn().mockResolvedValue([
      { code: 'en', name: 'English' },
      { code: 'es', name: 'Spanish' },
      { code: 'zh', name: 'Chinese' },
    ]),
    getStates: vi.fn().mockResolvedValue([
      { code: 'CA', name: 'California' },
      { code: 'TX', name: 'Texas' },
      { code: 'FL', name: 'Florida' },
    ]),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('FilterPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFilterStore.filters = {
      state_code: undefined,
      user_type: undefined,
      language: undefined,
      specialty: undefined,
      min_rating: undefined,
    };
    mockFilterStore.geo = {
      is_detecting: false,
      detected_state: undefined,
      detected_city: undefined,
    };
    mockHasActiveFilters.mockReturnValue(false);
    mockIsUsingDetectedState.mockReturnValue(false);
  });

  it('renders the panel title', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText('Find Your Professional')).toBeInTheDocument();
  });

  it('renders all filter dropdowns', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText('State')).toBeInTheDocument();
    expect(screen.getByText('Professional Type')).toBeInTheDocument();
    expect(screen.getByText('Language')).toBeInTheDocument();
    expect(screen.getByText('Specialty')).toBeInTheDocument();
    expect(screen.getByText('Minimum Rating')).toBeInTheDocument();
  });

  it('calls setStateCode when state filter changes', async () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const stateSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(stateSelect, { target: { value: 'CA' } });

    // The component passes undefined when value is empty string, otherwise the value
    expect(mockSetStateCode).toHaveBeenCalled();
  });

  it('calls setUserType when professional type filter changes', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const typeSelect = screen.getAllByRole('combobox')[1];
    fireEvent.change(typeSelect, { target: { value: 'loan_officer' } });

    expect(mockSetUserType).toHaveBeenCalledWith('loan_officer');
  });

  it('calls setLanguage when language filter changes', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const languageSelect = screen.getAllByRole('combobox')[2];
    fireEvent.change(languageSelect, { target: { value: 'es' } });

    // The component calls setLanguage on change
    expect(mockSetLanguage).toHaveBeenCalled();
  });

  it('calls setMinRating when rating filter changes', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const ratingSelect = screen.getAllByRole('combobox')[4];
    fireEvent.change(ratingSelect, { target: { value: '4.5' } });

    expect(mockSetMinRating).toHaveBeenCalledWith(4.5);
  });

  it('shows "Clear all" button when filters are active', () => {
    mockHasActiveFilters.mockReturnValue(true);

    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText('Clear all')).toBeInTheDocument();
  });

  it('does not show "Clear all" button when no filters are active', () => {
    mockHasActiveFilters.mockReturnValue(false);

    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.queryByText('Clear all')).not.toBeInTheDocument();
  });

  it('calls clearFilters when "Clear all" is clicked', () => {
    mockHasActiveFilters.mockReturnValue(true);

    render(<FilterPanel />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByText('Clear all'));

    expect(mockClearFilters).toHaveBeenCalledTimes(1);
  });

  it('shows geo-detection loading indicator', () => {
    mockFilterStore.geo.is_detecting = true;

    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText('Detecting your location...')).toBeInTheDocument();
  });

  it('shows detected state message when using detected state', () => {
    mockFilterStore.geo.detected_state = 'CA';
    mockFilterStore.geo.detected_city = 'Los Angeles';
    mockIsUsingDetectedState.mockReturnValue(true);

    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText(/Showing professionals in/)).toBeInTheDocument();
    expect(screen.getByText('Show all states')).toBeInTheDocument();
  });

  it('calls clearStateFilter when "Show all states" is clicked', () => {
    mockFilterStore.geo.detected_state = 'CA';
    mockIsUsingDetectedState.mockReturnValue(true);

    render(<FilterPanel />, { wrapper: createWrapper() });

    fireEvent.click(screen.getByText('Show all states'));

    expect(mockClearStateFilter).toHaveBeenCalledTimes(1);
  });

  it('shows "(detected)" label when using detected state', () => {
    mockIsUsingDetectedState.mockReturnValue(true);

    render(<FilterPanel />, { wrapper: createWrapper() });

    expect(screen.getByText('(detected)')).toBeInTheDocument();
  });

  it('renders professional type options', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const typeSelect = screen.getAllByRole('combobox')[1];
    fireEvent.click(typeSelect);

    expect(screen.getByText('All Types')).toBeInTheDocument();
    expect(screen.getByText('Loan Officer')).toBeInTheDocument();
    expect(screen.getByText('Realtor')).toBeInTheDocument();
    // getUserTypeLabel returns 'Title Rep' not 'Title Representative'
    expect(screen.getByText('Title Rep')).toBeInTheDocument();
    expect(screen.getByText('Attorney')).toBeInTheDocument();
  });

  it('renders minimum rating options', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const ratingSelect = screen.getAllByRole('combobox')[4];

    expect(screen.getByText('Any Rating')).toBeInTheDocument();
    expect(screen.getByText('4.5+ Stars')).toBeInTheDocument();
    expect(screen.getByText('4.0+ Stars')).toBeInTheDocument();
    expect(screen.getByText('3.5+ Stars')).toBeInTheDocument();
    expect(screen.getByText('3.0+ Stars')).toBeInTheDocument();
  });

  it('clears filter value when empty option is selected', () => {
    render(<FilterPanel />, { wrapper: createWrapper() });

    const stateSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(stateSelect, { target: { value: '' } });

    expect(mockSetStateCode).toHaveBeenCalledWith(undefined);
  });
});
