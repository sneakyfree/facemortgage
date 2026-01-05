'use client';

import { useState, useEffect, useCallback } from 'react';

// US State codes for validation
const US_STATE_CODES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
  'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
];

export interface GeoLocationData {
  state_code: string | null;
  state_name: string | null;
  city: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  source: 'browser' | 'ip' | 'cached' | null;
  timestamp: number;
}

export interface GeoLocationResult {
  location: GeoLocationData | null;
  isLoading: boolean;
  error: string | null;
  isPermissionDenied: boolean;
  refresh: () => Promise<void>;
}

const CACHE_KEY = 'fm_geo_location';
const CACHE_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours

// State name to code mapping
const STATE_NAME_TO_CODE: Record<string, string> = {
  'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
  'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
  'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
  'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
  'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
  'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
  'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
  'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
  'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
  'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
  'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
  'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
  'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC',
  'puerto rico': 'PR', 'virgin islands': 'VI', 'guam': 'GU',
  'american samoa': 'AS', 'northern mariana islands': 'MP'
};

// Code to name mapping
const STATE_CODE_TO_NAME: Record<string, string> = Object.fromEntries(
  Object.entries(STATE_NAME_TO_CODE).map(([name, code]) => [code, name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')])
);

function normalizeStateCode(stateInput: string | null | undefined): string | null {
  if (!stateInput) return null;

  const upper = stateInput.toUpperCase().trim();

  // Check if it's already a valid code
  if (US_STATE_CODES.includes(upper)) {
    return upper;
  }

  // Try to convert from state name
  const lower = stateInput.toLowerCase().trim();
  const code = STATE_NAME_TO_CODE[lower];
  if (code) {
    return code;
  }

  return null;
}

function getStateName(code: string | null): string | null {
  if (!code) return null;
  return STATE_CODE_TO_NAME[code.toUpperCase()] || null;
}

function getCachedLocation(): GeoLocationData | null {
  if (typeof window === 'undefined') return null;

  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;

    const data: GeoLocationData = JSON.parse(cached);

    // Check if cache is still valid
    if (Date.now() - data.timestamp < CACHE_DURATION_MS) {
      return { ...data, source: 'cached' };
    }

    // Cache expired, remove it
    localStorage.removeItem(CACHE_KEY);
    return null;
  } catch {
    return null;
  }
}

function cacheLocation(data: GeoLocationData): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // localStorage might be full or disabled
    console.debug('Failed to cache geo location');
  }
}

async function reverseGeocode(lat: number, lon: number): Promise<Partial<GeoLocationData>> {
  // Use our backend API for reverse geocoding
  try {
    const { API_URL } = await import('@/lib/config');
    const response = await fetch(`${API_URL}/lookups/geo?lat=${lat}&lon=${lon}`);

    if (response.ok) {
      const data = await response.json();
      return {
        state_code: normalizeStateCode(data.state_code || data.region),
        state_name: data.state_name || getStateName(data.state_code || data.region),
        city: data.city || null,
        country: data.country || 'US',
      };
    }
  } catch {
    console.debug('Backend reverse geocode failed, trying fallback');
  }

  // Fallback to BigDataCloud free API (no key required)
  try {
    const response = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`
    );

    if (response.ok) {
      const data = await response.json();
      const stateCode = normalizeStateCode(data.principalSubdivisionCode?.replace('US-', '') || data.principalSubdivision);
      return {
        state_code: stateCode,
        state_name: data.principalSubdivision || getStateName(stateCode),
        city: data.city || data.locality || null,
        country: data.countryCode || 'US',
      };
    }
  } catch {
    console.debug('BigDataCloud reverse geocode failed');
  }

  return {};
}

async function getLocationFromIP(): Promise<GeoLocationData> {
  // Try multiple IP geolocation services for redundancy
  const services = [
    // ip-api.com (free, no key required)
    async () => {
      const response = await fetch('http://ip-api.com/json/?fields=status,country,regionName,region,city,lat,lon');
      if (!response.ok) throw new Error('IP API failed');
      const data = await response.json();
      if (data.status !== 'success') throw new Error('IP API returned error');

      return {
        state_code: normalizeStateCode(data.region),
        state_name: data.regionName || getStateName(data.region),
        city: data.city || null,
        country: data.country || null,
        latitude: data.lat || null,
        longitude: data.lon || null,
        source: 'ip' as const,
        timestamp: Date.now(),
      };
    },
    // ipapi.co (free tier, no key required for limited requests)
    async () => {
      const response = await fetch('https://ipapi.co/json/');
      if (!response.ok) throw new Error('ipapi.co failed');
      const data = await response.json();

      return {
        state_code: normalizeStateCode(data.region_code),
        state_name: data.region || getStateName(data.region_code),
        city: data.city || null,
        country: data.country_name || null,
        latitude: data.latitude || null,
        longitude: data.longitude || null,
        source: 'ip' as const,
        timestamp: Date.now(),
      };
    },
    // Our backend as fallback (will use server's IP detection)
    async () => {
      const { API_URL } = await import('@/lib/config');
      const response = await fetch(`${API_URL}/lookups/geo`);
      if (!response.ok) throw new Error('Backend geo API failed');
      const data = await response.json();

      return {
        state_code: normalizeStateCode(data.state_code || data.region),
        state_name: data.state_name || getStateName(data.state_code),
        city: data.city || null,
        country: data.country || 'US',
        latitude: data.latitude || null,
        longitude: data.longitude || null,
        source: 'ip' as const,
        timestamp: Date.now(),
      };
    },
  ];

  for (const service of services) {
    try {
      const result = await service();
      if (result.state_code) {
        return result;
      }
    } catch {
      continue;
    }
  }

  // All services failed
  throw new Error('All IP geolocation services failed');
}

async function getBrowserLocation(): Promise<GeoLocationData> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        // Reverse geocode to get state/city
        const geoData = await reverseGeocode(latitude, longitude);

        resolve({
          state_code: geoData.state_code || null,
          state_name: geoData.state_name || null,
          city: geoData.city || null,
          country: geoData.country || 'US',
          latitude,
          longitude,
          source: 'browser',
          timestamp: Date.now(),
        });
      },
      (error) => {
        reject(error);
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    );
  });
}

export function useGeoLocation(options: {
  autoDetect?: boolean;
  useBrowserLocation?: boolean;
  useIPFallback?: boolean;
} = {}): GeoLocationResult {
  const {
    autoDetect = true,
    useBrowserLocation = true,
    useIPFallback = true,
  } = options;

  const [location, setLocation] = useState<GeoLocationData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  const detectLocation = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // First, check cache
      const cached = getCachedLocation();
      if (cached) {
        setLocation(cached);
        setIsLoading(false);
        return;
      }

      let result: GeoLocationData | null = null;

      // Try browser geolocation first
      if (useBrowserLocation && typeof navigator !== 'undefined' && navigator.geolocation) {
        try {
          result = await getBrowserLocation();
        } catch (geoError) {
          const error = geoError as GeolocationPositionError;
          if (error.code === 1) {
            // PERMISSION_DENIED
            setIsPermissionDenied(true);
          }
          console.debug('Browser geolocation failed:', error.message || error);
        }
      }

      // Fall back to IP geolocation if browser failed
      if (!result && useIPFallback) {
        try {
          result = await getLocationFromIP();
        } catch (ipError) {
          console.debug('IP geolocation failed:', ipError);
        }
      }

      if (result && result.state_code) {
        cacheLocation(result);
        setLocation(result);
      } else {
        setError('Could not determine location');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Location detection failed');
    } finally {
      setIsLoading(false);
    }
  }, [useBrowserLocation, useIPFallback]);

  const refresh = useCallback(async () => {
    // Clear cache before refreshing
    if (typeof window !== 'undefined') {
      localStorage.removeItem(CACHE_KEY);
    }
    await detectLocation();
  }, [detectLocation]);

  useEffect(() => {
    if (autoDetect) {
      detectLocation();
    }
  }, [autoDetect, detectLocation]);

  return {
    location,
    isLoading,
    error,
    isPermissionDenied,
    refresh,
  };
}

// Export utilities for use elsewhere
export { normalizeStateCode, getStateName, US_STATE_CODES };
