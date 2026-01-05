/**
 * useGeoLocation hook tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import {
  useGeoLocation,
  normalizeStateCode,
  getStateName,
  US_STATE_CODES,
} from './useGeoLocation';

// Mock localStorage
const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem: vi.fn((key: string) => mockLocalStorage.store[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    mockLocalStorage.store[key] = value;
  }),
  removeItem: vi.fn((key: string) => {
    delete mockLocalStorage.store[key];
  }),
  clear: vi.fn(() => {
    mockLocalStorage.store = {};
  }),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock config module
vi.mock('@/lib/config', () => ({
  API_URL: 'http://localhost:8000/api/v1',
}));

describe('normalizeStateCode', () => {
  it('returns valid state code as-is', () => {
    expect(normalizeStateCode('CA')).toBe('CA');
    expect(normalizeStateCode('ny')).toBe('NY');
    expect(normalizeStateCode('TX')).toBe('TX');
  });

  it('converts state name to code', () => {
    expect(normalizeStateCode('California')).toBe('CA');
    expect(normalizeStateCode('new york')).toBe('NY');
    expect(normalizeStateCode('TEXAS')).toBe('TX'); // Case-insensitive match
    expect(normalizeStateCode('TexAs')).toBe('TX'); // Mixed case also works
  });

  it('returns null for invalid input', () => {
    expect(normalizeStateCode(null)).toBe(null);
    expect(normalizeStateCode(undefined)).toBe(null);
    expect(normalizeStateCode('')).toBe(null);
    expect(normalizeStateCode('XX')).toBe(null);
    expect(normalizeStateCode('InvalidState')).toBe(null);
  });

  it('handles whitespace', () => {
    expect(normalizeStateCode('  CA  ')).toBe('CA');
    expect(normalizeStateCode(' california ')).toBe('CA');
  });
});

describe('getStateName', () => {
  it('returns state name for valid code', () => {
    expect(getStateName('CA')).toBe('California');
    expect(getStateName('NY')).toBe('New York');
    expect(getStateName('TX')).toBe('Texas');
  });

  it('handles lowercase codes', () => {
    expect(getStateName('ca')).toBe('California');
  });

  it('returns null for invalid code', () => {
    expect(getStateName(null)).toBe(null);
    expect(getStateName('XX')).toBe(null);
  });
});

describe('US_STATE_CODES', () => {
  it('contains all 50 states plus territories', () => {
    expect(US_STATE_CODES).toContain('CA');
    expect(US_STATE_CODES).toContain('NY');
    expect(US_STATE_CODES).toContain('TX');
    expect(US_STATE_CODES).toContain('DC');
    expect(US_STATE_CODES).toContain('PR');
    expect(US_STATE_CODES.length).toBeGreaterThanOrEqual(50);
  });
});

describe('useGeoLocation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.clear();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns initial loading state', () => {
    // Mock fetch to never resolve
    mockFetch.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useGeoLocation());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.location).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('returns cached location when available', async () => {
    const cachedData = {
      state_code: 'CA',
      state_name: 'California',
      city: 'Los Angeles',
      country: 'US',
      latitude: 34.0522,
      longitude: -118.2437,
      source: 'browser',
      timestamp: Date.now(),
    };

    mockLocalStorage.store['fm_geo_location'] = JSON.stringify(cachedData);

    const { result } = renderHook(() => useGeoLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.location).toBeDefined();
    expect(result.current.location?.state_code).toBe('CA');
    expect(result.current.location?.source).toBe('cached');
  });

  it('ignores expired cache', async () => {
    const expiredCache = {
      state_code: 'CA',
      state_name: 'California',
      city: 'Los Angeles',
      country: 'US',
      latitude: 34.0522,
      longitude: -118.2437,
      source: 'browser',
      timestamp: Date.now() - 25 * 60 * 60 * 1000, // 25 hours ago
    };

    mockLocalStorage.store['fm_geo_location'] = JSON.stringify(expiredCache);

    // Mock IP geolocation to return a result
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'success',
          country: 'United States',
          regionName: 'New York',
          region: 'NY',
          city: 'New York City',
          lat: 40.7128,
          lon: -74.006,
        }),
    });

    const { result } = renderHook(() =>
      useGeoLocation({ useBrowserLocation: false, useIPFallback: true })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have fetched new location
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('fm_geo_location');
  });

  it('handles IP geolocation fallback', async () => {
    // Mock navigator.geolocation to not exist
    const originalGeolocation = navigator.geolocation;
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      configurable: true,
    });

    // Mock IP API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'success',
          country: 'United States',
          regionName: 'Texas',
          region: 'TX',
          city: 'Austin',
          lat: 30.2672,
          lon: -97.7431,
        }),
    });

    const { result } = renderHook(() => useGeoLocation({ useBrowserLocation: true }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.location?.state_code).toBe('TX');
    expect(result.current.location?.city).toBe('Austin');
    expect(result.current.location?.source).toBe('ip');

    // Restore
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      configurable: true,
    });
  });

  it('handles all IP services failing', async () => {
    // Mock navigator.geolocation to not exist
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      configurable: true,
    });

    // All IP services fail
    mockFetch.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useGeoLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Could not determine location');
    expect(result.current.location).toBe(null);
  });

  it('respects autoDetect: false option', () => {
    const { result } = renderHook(() => useGeoLocation({ autoDetect: false }));

    expect(result.current.isLoading).toBe(false);
    expect(result.current.location).toBe(null);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('refresh clears cache and re-detects', async () => {
    const cachedData = {
      state_code: 'CA',
      state_name: 'California',
      city: 'Los Angeles',
      country: 'US',
      latitude: 34.0522,
      longitude: -118.2437,
      source: 'cached',
      timestamp: Date.now(),
    };

    mockLocalStorage.store['fm_geo_location'] = JSON.stringify(cachedData);

    // Mock IP API for refresh
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'success',
          country: 'United States',
          regionName: 'Florida',
          region: 'FL',
          city: 'Miami',
          lat: 25.7617,
          lon: -80.1918,
        }),
    });

    const { result } = renderHook(() => useGeoLocation({ useBrowserLocation: false }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Initially gets cached
    expect(result.current.location?.state_code).toBe('CA');

    // Call refresh
    await act(async () => {
      await result.current.refresh();
    });

    await waitFor(() => {
      expect(result.current.location?.state_code).toBe('FL');
    });

    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('fm_geo_location');
  });

  it('handles browser geolocation permission denied', async () => {
    // Mock geolocation with permission denied
    const mockGetCurrentPosition = vi.fn(
      (
        _success: PositionCallback,
        error: PositionErrorCallback
      ) => {
        error({
          code: 1, // PERMISSION_DENIED
          message: 'User denied geolocation',
          PERMISSION_DENIED: 1,
          POSITION_UNAVAILABLE: 2,
          TIMEOUT: 3,
        });
      }
    );

    Object.defineProperty(navigator, 'geolocation', {
      value: {
        getCurrentPosition: mockGetCurrentPosition,
      },
      configurable: true,
    });

    // IP fallback succeeds
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'success',
          country: 'United States',
          regionName: 'Oregon',
          region: 'OR',
          city: 'Portland',
          lat: 45.5152,
          lon: -122.6784,
        }),
    });

    const { result } = renderHook(() => useGeoLocation());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isPermissionDenied).toBe(true);
    // Should fall back to IP
    expect(result.current.location?.state_code).toBe('OR');
    expect(result.current.location?.source).toBe('ip');
  });

  it('caches successful location detection', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          status: 'success',
          country: 'United States',
          regionName: 'Nevada',
          region: 'NV',
          city: 'Las Vegas',
          lat: 36.1699,
          lon: -115.1398,
        }),
    });

    const { result } = renderHook(() =>
      useGeoLocation({ useBrowserLocation: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockLocalStorage.setItem).toHaveBeenCalled();
    const cachedCall = mockLocalStorage.setItem.mock.calls.find(
      (call: string[]) => call[0] === 'fm_geo_location'
    );
    expect(cachedCall).toBeDefined();
    if (!cachedCall) throw new Error('cachedCall should be defined');

    const cachedData = JSON.parse(cachedCall[1]);
    expect(cachedData.state_code).toBe('NV');
    expect(cachedData.source).toBe('ip');
  });
});
