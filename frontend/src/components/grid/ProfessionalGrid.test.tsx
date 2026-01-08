/**
 * ProfessionalGrid component tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProfessionalGrid from './ProfessionalGrid';
import type { ProfessionalGridItem } from '@/types';

// Mock stores
const mockSetProfessionals = vi.fn();
const mockSetLoading = vi.fn();
const mockSetError = vi.fn();
let mockProfessionals: ProfessionalGridItem[] = [];

vi.mock('@/stores/gridStore', () => ({
  useGridStore: () => ({
    professionals: mockProfessionals,
    setProfessionals: mockSetProfessionals,
    setLoading: mockSetLoading,
    setError: mockSetError,
  }),
}));

let mockFilters = {};
vi.mock('@/stores/filterStore', () => ({
  useFilterStore: () => ({
    filters: mockFilters,
  }),
}));

// Mock WebSocket hook
const mockOnProfessionalOnline = vi.fn();
const mockOnProfessionalOffline = vi.fn();
vi.mock('@/hooks/useRealtimeGrid', () => ({
  useRealtimeGrid: (options: {
    enabled: boolean;
    onProfessionalOnline?: () => void;
    onProfessionalOffline?: (id: string) => void;
  }) => {
    mockOnProfessionalOnline.mockImplementation(options.onProfessionalOnline);
    mockOnProfessionalOffline.mockImplementation(options.onProfessionalOffline);
    return {};
  },
}));

// Mock API
const mockGetGrid = vi.fn();
const mockTrackImpressions = vi.fn();
const mockTrackClick = vi.fn();

vi.mock('@/lib/api/endpoints', () => ({
  professionalsApi: {
    getGrid: (...args: unknown[]) => mockGetGrid(...args),
  },
  gridTrackingApi: {
    trackImpressions: (...args: unknown[]) => mockTrackImpressions(...args),
    trackClick: (...args: unknown[]) => mockTrackClick(...args),
  },
}));

// Mock VideoCallModal
vi.mock('@/components/call', () => ({
  VideoCallModal: ({
    professionalId,
    professionalName,
    onClose,
  }: {
    professionalId: string;
    professionalName: string;
    onClose: () => void;
  }) => (
    <div data-testid="video-call-modal">
      <span data-testid="modal-professional-id">{professionalId}</span>
      <span data-testid="modal-professional-name">{professionalName}</span>
      <button onClick={onClose}>Close Modal</button>
    </div>
  ),
}));

// Mock ProfessionalCard
vi.mock('./ProfessionalCard', () => ({
  default: ({
    professional,
    onCallClick,
  }: {
    professional: ProfessionalGridItem;
    onCallClick: (p: ProfessionalGridItem) => void;
  }) => (
    <div data-testid={`professional-card-${professional.id}`}>
      <span>{professional.first_name} {professional.last_name}</span>
      <button onClick={() => onCallClick(professional)}>
        Call {professional.first_name}
      </button>
    </div>
  ),
}));

// Mock sessionStorage
const mockSessionStorage: Record<string, string> = {};
Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: (key: string) => mockSessionStorage[key] || null,
    setItem: (key: string, value: string) => {
      mockSessionStorage[key] = value;
    },
    removeItem: (key: string) => {
      delete mockSessionStorage[key];
    },
    clear: () => {
      Object.keys(mockSessionStorage).forEach(key => delete mockSessionStorage[key]);
    },
  },
  writable: true,
});

const createTestProfessional = (id: string, firstName: string, lastName: string): ProfessionalGridItem => ({
  id,
  first_name: firstName,
  last_name: lastName,
  user_type: 'loan_officer',
  nmls_id: '123456',
  company_name: 'Test Company',
  city: 'Test City',
  state_code: 'CA',
  is_available: true,
  grid_position: 1,
  languages: ['en'],
});

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

describe('ProfessionalGrid', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockProfessionals = [];
    mockFilters = {};
    mockTrackImpressions.mockResolvedValue({});
    mockTrackClick.mockResolvedValue({});
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  describe('Loading State', () => {
    it('renders loading skeleton when loading', () => {
      mockGetGrid.mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<ProfessionalGrid />, { wrapper: createWrapper() });

      // Should show 10 skeleton items
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(10);
    });

    it('syncs loading state to store', async () => {
      mockGetGrid.mockImplementation(() => new Promise(() => {}));

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockSetLoading).toHaveBeenCalledWith(true);
      });
    });
  });

  describe('Error State', () => {
    it('displays error message on fetch failure', async () => {
      mockGetGrid.mockRejectedValueOnce(new Error('Network error'));

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load professionals')).toBeInTheDocument();
      });
    });

    it('syncs error to store', async () => {
      mockGetGrid.mockRejectedValueOnce(new Error('API Error'));

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockSetError).toHaveBeenCalledWith('API Error');
      });
    });

    it('renders try again button on error', async () => {
      mockGetGrid.mockRejectedValueOnce(new Error('Error'));

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Try again')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no professionals found', async () => {
      mockGetGrid.mockResolvedValueOnce({
        professionals: [],
        total: 0,
      });
      mockProfessionals = [];

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockSetProfessionals).toHaveBeenCalledWith([], 0);
      });
    });

    it('shows filter adjustment message in empty state', async () => {
      mockGetGrid.mockResolvedValueOnce({
        professionals: [],
        total: 0,
      });
      mockProfessionals = [];

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('No professionals found')).toBeInTheDocument();
        expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument();
      });
    });
  });

  describe('Success State', () => {
    const testProfessionals = [
      createTestProfessional('1', 'John', 'Smith'),
      createTestProfessional('2', 'Jane', 'Doe'),
    ];

    beforeEach(() => {
      mockGetGrid.mockResolvedValueOnce({
        professionals: testProfessionals,
        total: 2,
      });
      mockProfessionals = testProfessionals;
    });

    it('renders professional cards', async () => {
      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId('professional-card-1')).toBeInTheDocument();
        expect(screen.getByTestId('professional-card-2')).toBeInTheDocument();
      });
    });

    it('syncs professionals to store', async () => {
      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockSetProfessionals).toHaveBeenCalledWith(testProfessionals, 2);
      });
    });
  });

  describe('Impression Tracking', () => {
    it('tracks impressions for newly loaded professionals', async () => {
      const professionals = [createTestProfessional('1', 'John', 'Smith')];
      mockGetGrid.mockResolvedValueOnce({
        professionals,
        total: 1,
      });
      mockProfessionals = professionals;

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockTrackImpressions).toHaveBeenCalled();
      });
    });
  });

  describe('Video Call Modal', () => {
    const testProfessionals = [createTestProfessional('1', 'John', 'Smith')];

    beforeEach(() => {
      mockGetGrid.mockResolvedValueOnce({
        professionals: testProfessionals,
        total: 1,
      });
      mockProfessionals = testProfessionals;
    });

    it('opens video call modal when call button clicked', async () => {
      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Call John')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Call John'));

      await waitFor(() => {
        expect(screen.getByTestId('video-call-modal')).toBeInTheDocument();
        expect(screen.getByTestId('modal-professional-id')).toHaveTextContent('1');
        expect(screen.getByTestId('modal-professional-name')).toHaveTextContent('John Smith');
      });
    });

    it('tracks call click', async () => {
      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Call John')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Call John'));

      await waitFor(() => {
        expect(mockTrackClick).toHaveBeenCalledWith(
          expect.objectContaining({
            professional_id: '1',
            click_type: 'call_initiated',
          })
        );
      });
    });

    it('closes video call modal when close is clicked', async () => {
      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Call John')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Call John'));

      await waitFor(() => {
        expect(screen.getByTestId('video-call-modal')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Close Modal'));

      await waitFor(() => {
        expect(screen.queryByTestId('video-call-modal')).not.toBeInTheDocument();
      });
    });
  });

  describe('Grid Layout', () => {
    it('renders responsive grid container', async () => {
      const professionals = [createTestProfessional('1', 'John', 'Smith')];
      mockGetGrid.mockResolvedValueOnce({
        professionals,
        total: 1,
      });
      mockProfessionals = professionals;

      const { container } = render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        const grid = container.querySelector('.grid');
        expect(grid).toBeInTheDocument();
        expect(grid).toHaveClass('grid-cols-1');
        expect(grid).toHaveClass('sm:grid-cols-2');
        expect(grid).toHaveClass('lg:grid-cols-3');
        expect(grid).toHaveClass('xl:grid-cols-4');
        expect(grid).toHaveClass('2xl:grid-cols-5');
      });
    });
  });

  describe('API Calls', () => {
    it('calls API with filters', async () => {
      mockFilters = { state_code: 'CA', user_type: 'loan_officer' };
      mockGetGrid.mockResolvedValueOnce({
        professionals: [],
        total: 0,
      });

      render(<ProfessionalGrid />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockGetGrid).toHaveBeenCalledWith(
          { state_code: 'CA', user_type: 'loan_officer' },
          50,
          0
        );
      });
    });
  });
});
