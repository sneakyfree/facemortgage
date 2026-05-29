/**
 * GeoDetectionProvider component tests.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import GeoDetectionProvider from './GeoDetectionProvider';

// Mock the hooks and stores
const mockSetDetectedLocation = vi.fn();
const mockSetGeoDetecting = vi.fn();
const mockSetGeoError = vi.fn();
const mockApplyDetectedState = vi.fn();

let mockLocation: {
  state_code: string;
  city: string;
  source: string;
} | null = null;
let mockIsLoading = false;
let mockError: string | null = null;
let mockIsPermissionDenied = false;
let mockFiltersState: { state_code: string | null } = { state_code: null };

vi.mock('@/hooks/useGeoLocation', () => ({
  useGeoLocation: () => ({
    location: mockLocation,
    isLoading: mockIsLoading,
    error: mockError,
    isPermissionDenied: mockIsPermissionDenied,
  }),
}));

vi.mock('@/stores/filterStore', () => ({
  useFilterStore: () => ({
    setDetectedLocation: mockSetDetectedLocation,
    setGeoDetecting: mockSetGeoDetecting,
    setGeoError: mockSetGeoError,
    applyDetectedState: mockApplyDetectedState,
    filters: mockFiltersState,
  }),
}));

describe('GeoDetectionProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocation = null;
    mockIsLoading = false;
    mockError = null;
    mockIsPermissionDenied = false;
    mockFiltersState = { state_code: null };
  });

  describe('Rendering', () => {
    it('renders children', () => {
      render(
        <GeoDetectionProvider>
          <div>Child content</div>
        </GeoDetectionProvider>
      );

      expect(screen.getByText('Child content')).toBeInTheDocument();
    });

    it('renders without children', () => {
      const { container } = render(<GeoDetectionProvider>{null}</GeoDetectionProvider>);

      expect(container).toBeInTheDocument();
    });
  });

  describe('Loading State Sync', () => {
    it('syncs loading state to store when loading', () => {
      mockIsLoading = true;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetGeoDetecting).toHaveBeenCalledWith(true);
    });

    it('syncs loading state to store when not loading', () => {
      mockIsLoading = false;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetGeoDetecting).toHaveBeenCalledWith(false);
    });
  });

  describe('Location Detection', () => {
    it('sets detected location when location is available', () => {
      mockLocation = {
        state_code: 'CA',
        city: 'Los Angeles',
        source: 'browser',
      };

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetDetectedLocation).toHaveBeenCalledWith('CA', 'Los Angeles', 'browser');
    });

    it('auto-applies state filter when autoApplyState is true', () => {
      mockLocation = {
        state_code: 'TX',
        city: 'Austin',
        source: 'ip',
      };

      render(
        <GeoDetectionProvider autoApplyState={true}>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockApplyDetectedState).toHaveBeenCalledTimes(1);
    });

    it('does not auto-apply state when autoApplyState is false', () => {
      mockLocation = {
        state_code: 'TX',
        city: 'Austin',
        source: 'ip',
      };

      render(
        <GeoDetectionProvider autoApplyState={false}>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockApplyDetectedState).not.toHaveBeenCalled();
    });

    it('does not auto-apply state when filter is already set', () => {
      mockLocation = {
        state_code: 'TX',
        city: 'Austin',
        source: 'ip',
      };
      mockFiltersState = { state_code: 'NY' };

      render(
        <GeoDetectionProvider autoApplyState={true}>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockApplyDetectedState).not.toHaveBeenCalled();
    });

    it('does not set location when location is null', () => {
      mockLocation = null;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetDetectedLocation).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('syncs error to store when error occurs', () => {
      mockError = 'Geolocation failed';

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetGeoError).toHaveBeenCalledWith('Geolocation failed');
    });

    it('does not call setGeoError when there is no error', () => {
      mockError = null;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetGeoError).not.toHaveBeenCalled();
    });
  });

  describe('Permission Denied', () => {
    it('logs debug message when permission is denied', () => {
      const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
      mockIsPermissionDenied = true;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        'Geo permission denied, using IP-based fallback'
      );

      consoleSpy.mockRestore();
    });

    it('does not log when permission is not denied', () => {
      const consoleSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
      mockIsPermissionDenied = false;

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(consoleSpy).not.toHaveBeenCalledWith(
        'Geo permission denied, using IP-based fallback'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Default Props', () => {
    it('autoApplyState defaults to true', () => {
      mockLocation = {
        state_code: 'FL',
        city: 'Miami',
        source: 'cached',
      };

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      // With default autoApplyState=true, applyDetectedState should be called
      expect(mockApplyDetectedState).toHaveBeenCalledTimes(1);
    });
  });

  describe('Source Type Handling', () => {
    it('handles browser source', () => {
      mockLocation = {
        state_code: 'WA',
        city: 'Seattle',
        source: 'browser',
      };

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetDetectedLocation).toHaveBeenCalledWith('WA', 'Seattle', 'browser');
    });

    it('handles ip source', () => {
      mockLocation = {
        state_code: 'OR',
        city: 'Portland',
        source: 'ip',
      };

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetDetectedLocation).toHaveBeenCalledWith('OR', 'Portland', 'ip');
    });

    it('handles cached source', () => {
      mockLocation = {
        state_code: 'NV',
        city: 'Las Vegas',
        source: 'cached',
      };

      render(
        <GeoDetectionProvider>
          <div>Content</div>
        </GeoDetectionProvider>
      );

      expect(mockSetDetectedLocation).toHaveBeenCalledWith('NV', 'Las Vegas', 'cached');
    });
  });
});
