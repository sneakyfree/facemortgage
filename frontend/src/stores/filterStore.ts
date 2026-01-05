import { create } from 'zustand';
import type { GridFilters, UserType } from '@/types';

interface GeoDetectionState {
  detected_state: string | null;
  detected_city: string | null;
  detection_source: 'browser' | 'ip' | 'cached' | null;
  is_detecting: boolean;
  detection_error: string | null;
}

interface FilterState {
  filters: GridFilters;
  geo: GeoDetectionState;
  setLanguage: (language: string | undefined) => void;
  setSpecialty: (specialty: number | undefined) => void;
  setCounty: (county: number | undefined) => void;
  setStateCode: (state_code: string | undefined) => void;
  setUserType: (userType: UserType | undefined) => void;
  setMinRating: (rating: number | undefined) => void;
  clearFilters: () => void;
  clearStateFilter: () => void;
  hasActiveFilters: () => boolean;
  // Geo-detection methods
  setDetectedLocation: (state_code: string | null, city: string | null, source: 'browser' | 'ip' | 'cached' | null) => void;
  setGeoDetecting: (is_detecting: boolean) => void;
  setGeoError: (error: string | null) => void;
  applyDetectedState: () => void;
  isUsingDetectedState: () => boolean;
}

const initialGeoState: GeoDetectionState = {
  detected_state: null,
  detected_city: null,
  detection_source: null,
  is_detecting: false,
  detection_error: null,
};

export const useFilterStore = create<FilterState>((set, get) => ({
  filters: {},
  geo: initialGeoState,

  setLanguage: (language) =>
    set((state) => ({
      filters: { ...state.filters, language },
    })),

  setSpecialty: (specialty) =>
    set((state) => ({
      filters: { ...state.filters, specialty },
    })),

  setCounty: (county) =>
    set((state) => ({
      filters: { ...state.filters, county },
    })),

  setStateCode: (state_code) =>
    set((state) => ({
      filters: { ...state.filters, state_code },
    })),

  setUserType: (user_type) =>
    set((state) => ({
      filters: { ...state.filters, user_type },
    })),

  setMinRating: (min_rating) =>
    set((state) => ({
      filters: { ...state.filters, min_rating },
    })),

  clearFilters: () => set({ filters: {} }),

  clearStateFilter: () =>
    set((state) => ({
      filters: { ...state.filters, state_code: undefined },
    })),

  hasActiveFilters: () => {
    const { filters } = get();
    return Object.values(filters).some((v) => v !== undefined);
  },

  // Geo-detection methods
  setDetectedLocation: (detected_state, detected_city, detection_source) =>
    set((state) => ({
      geo: {
        ...state.geo,
        detected_state,
        detected_city,
        detection_source,
        is_detecting: false,
        detection_error: null,
      },
    })),

  setGeoDetecting: (is_detecting) =>
    set((state) => ({
      geo: { ...state.geo, is_detecting },
    })),

  setGeoError: (detection_error) =>
    set((state) => ({
      geo: {
        ...state.geo,
        detection_error,
        is_detecting: false,
      },
    })),

  applyDetectedState: () => {
    const { geo, filters } = get();
    if (geo.detected_state && !filters.state_code) {
      set({
        filters: { ...filters, state_code: geo.detected_state },
      });
    }
  },

  isUsingDetectedState: () => {
    const { geo, filters } = get();
    return filters.state_code === geo.detected_state && geo.detected_state !== null;
  },
}));
