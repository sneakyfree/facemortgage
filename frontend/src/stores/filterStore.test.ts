/**
 * filterStore tests.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useFilterStore } from './filterStore';

describe('filterStore', () => {
  // Reset store before each test
  beforeEach(() => {
    const { result } = renderHook(() => useFilterStore());
    act(() => {
      result.current.clearFilters();
      result.current.setDetectedLocation(null, null, null);
      result.current.setGeoError(null);
    });
  });

  describe('initial state', () => {
    it('has empty filters initially', () => {
      const { result } = renderHook(() => useFilterStore());

      expect(result.current.filters).toEqual({});
    });

    it('has initial geo state', () => {
      const { result } = renderHook(() => useFilterStore());

      expect(result.current.geo).toEqual({
        detected_state: null,
        detected_city: null,
        detection_source: null,
        is_detecting: false,
        detection_error: null,
      });
    });

    it('hasActiveFilters returns false initially', () => {
      const { result } = renderHook(() => useFilterStore());

      expect(result.current.hasActiveFilters()).toBe(false);
    });
  });

  describe('setLanguage', () => {
    it('sets language filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
      });

      expect(result.current.filters.language).toBe('en');
    });

    it('clears language filter with undefined', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('es');
      });

      expect(result.current.filters.language).toBe('es');

      act(() => {
        result.current.setLanguage(undefined);
      });

      expect(result.current.filters.language).toBeUndefined();
    });
  });

  describe('setSpecialty', () => {
    it('sets specialty filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setSpecialty(5);
      });

      expect(result.current.filters.specialty).toBe(5);
    });

    it('clears specialty filter with undefined', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setSpecialty(3);
      });

      act(() => {
        result.current.setSpecialty(undefined);
      });

      expect(result.current.filters.specialty).toBeUndefined();
    });
  });

  describe('setCounty', () => {
    it('sets county filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setCounty(42);
      });

      expect(result.current.filters.county).toBe(42);
    });
  });

  describe('setStateCode', () => {
    it('sets state_code filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setStateCode('CA');
      });

      expect(result.current.filters.state_code).toBe('CA');
    });

    it('handles multiple state changes', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setStateCode('CA');
      });

      expect(result.current.filters.state_code).toBe('CA');

      act(() => {
        result.current.setStateCode('NY');
      });

      expect(result.current.filters.state_code).toBe('NY');
    });
  });

  describe('setUserType', () => {
    it('sets user_type filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setUserType('loan_officer');
      });

      expect(result.current.filters.user_type).toBe('loan_officer');
    });

    it('handles different user types', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setUserType('realtor');
      });

      expect(result.current.filters.user_type).toBe('realtor');

      act(() => {
        result.current.setUserType('title_rep');
      });

      expect(result.current.filters.user_type).toBe('title_rep');
    });
  });

  describe('setMinRating', () => {
    it('sets min_rating filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setMinRating(4.5);
      });

      expect(result.current.filters.min_rating).toBe(4.5);
    });

    it('handles zero rating', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setMinRating(0);
      });

      expect(result.current.filters.min_rating).toBe(0);
    });
  });

  describe('clearFilters', () => {
    it('clears all filters', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
        result.current.setSpecialty(5);
        result.current.setStateCode('CA');
        result.current.setMinRating(4.0);
      });

      expect(result.current.hasActiveFilters()).toBe(true);

      act(() => {
        result.current.clearFilters();
      });

      expect(result.current.filters).toEqual({});
      expect(result.current.hasActiveFilters()).toBe(false);
    });
  });

  describe('clearStateFilter', () => {
    it('clears only state_code filter', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
        result.current.setStateCode('CA');
      });

      act(() => {
        result.current.clearStateFilter();
      });

      expect(result.current.filters.state_code).toBeUndefined();
      expect(result.current.filters.language).toBe('en');
    });
  });

  describe('hasActiveFilters', () => {
    it('returns true when filters are set', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
      });

      expect(result.current.hasActiveFilters()).toBe(true);
    });

    it('returns false when filters are cleared', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
        result.current.clearFilters();
      });

      expect(result.current.hasActiveFilters()).toBe(false);
    });

    it('returns true with multiple filters', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
        result.current.setStateCode('CA');
        result.current.setMinRating(4.0);
      });

      expect(result.current.hasActiveFilters()).toBe(true);
    });
  });

  describe('geo-detection methods', () => {
    describe('setDetectedLocation', () => {
      it('sets detected location', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'Los Angeles', 'browser');
        });

        expect(result.current.geo.detected_state).toBe('CA');
        expect(result.current.geo.detected_city).toBe('Los Angeles');
        expect(result.current.geo.detection_source).toBe('browser');
        expect(result.current.geo.is_detecting).toBe(false);
        expect(result.current.geo.detection_error).toBe(null);
      });

      it('clears any existing error', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoError('Previous error');
        });

        expect(result.current.geo.detection_error).toBe('Previous error');

        act(() => {
          result.current.setDetectedLocation('NY', 'New York', 'ip');
        });

        expect(result.current.geo.detection_error).toBe(null);
      });

      it('handles cached source', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('TX', 'Austin', 'cached');
        });

        expect(result.current.geo.detection_source).toBe('cached');
      });

      it('handles null values', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'LA', 'browser');
        });

        act(() => {
          result.current.setDetectedLocation(null, null, null);
        });

        expect(result.current.geo.detected_state).toBe(null);
        expect(result.current.geo.detected_city).toBe(null);
        expect(result.current.geo.detection_source).toBe(null);
      });
    });

    describe('setGeoDetecting', () => {
      it('sets detecting state to true', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoDetecting(true);
        });

        expect(result.current.geo.is_detecting).toBe(true);
      });

      it('sets detecting state to false', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoDetecting(true);
        });

        act(() => {
          result.current.setGeoDetecting(false);
        });

        expect(result.current.geo.is_detecting).toBe(false);
      });
    });

    describe('setGeoError', () => {
      it('sets geo error', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoError('Geolocation failed');
        });

        expect(result.current.geo.detection_error).toBe('Geolocation failed');
        expect(result.current.geo.is_detecting).toBe(false);
      });

      it('clears detecting state when error is set', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoDetecting(true);
        });

        expect(result.current.geo.is_detecting).toBe(true);

        act(() => {
          result.current.setGeoError('Some error');
        });

        expect(result.current.geo.is_detecting).toBe(false);
      });

      it('clears error with null', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setGeoError('Some error');
        });

        act(() => {
          result.current.setGeoError(null);
        });

        expect(result.current.geo.detection_error).toBe(null);
      });
    });

    describe('applyDetectedState', () => {
      it('applies detected state when no state_code filter is set', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'LA', 'browser');
        });

        expect(result.current.filters.state_code).toBeUndefined();

        act(() => {
          result.current.applyDetectedState();
        });

        expect(result.current.filters.state_code).toBe('CA');
      });

      it('does not apply detected state when state_code filter exists', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setStateCode('NY');
          result.current.setDetectedLocation('CA', 'LA', 'browser');
        });

        act(() => {
          result.current.applyDetectedState();
        });

        // Should keep the manually set state
        expect(result.current.filters.state_code).toBe('NY');
      });

      it('does not apply when no detected state', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.applyDetectedState();
        });

        expect(result.current.filters.state_code).toBeUndefined();
      });
    });

    describe('isUsingDetectedState', () => {
      it('returns true when using detected state', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'LA', 'browser');
          result.current.applyDetectedState();
        });

        expect(result.current.isUsingDetectedState()).toBe(true);
      });

      it('returns false when using different state', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'LA', 'browser');
          result.current.setStateCode('NY');
        });

        expect(result.current.isUsingDetectedState()).toBe(false);
      });

      it('returns false when no detected state', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setStateCode('CA');
        });

        expect(result.current.isUsingDetectedState()).toBe(false);
      });

      it('returns false when no state filter set', () => {
        const { result } = renderHook(() => useFilterStore());

        act(() => {
          result.current.setDetectedLocation('CA', 'LA', 'browser');
        });

        // state_code is undefined, detected_state is 'CA'
        expect(result.current.isUsingDetectedState()).toBe(false);
      });
    });
  });

  describe('combined operations', () => {
    it('maintains filters when setting geo location', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setLanguage('en');
        result.current.setSpecialty(5);
        result.current.setDetectedLocation('CA', 'LA', 'browser');
      });

      expect(result.current.filters.language).toBe('en');
      expect(result.current.filters.specialty).toBe(5);
      expect(result.current.geo.detected_state).toBe('CA');
    });

    it('maintains geo when clearing filters', () => {
      const { result } = renderHook(() => useFilterStore());

      act(() => {
        result.current.setDetectedLocation('CA', 'LA', 'browser');
        result.current.setLanguage('en');
        result.current.clearFilters();
      });

      expect(result.current.filters).toEqual({});
      expect(result.current.geo.detected_state).toBe('CA');
    });
  });
});
