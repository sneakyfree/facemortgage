import { create } from 'zustand';
import type { GridFilters, UserType } from '@/types';

interface FilterState {
  filters: GridFilters;
  setLanguage: (language: string | undefined) => void;
  setSpecialty: (specialty: number | undefined) => void;
  setCounty: (county: number | undefined) => void;
  setUserType: (userType: UserType | undefined) => void;
  setMinRating: (rating: number | undefined) => void;
  clearFilters: () => void;
  hasActiveFilters: () => boolean;
}

export const useFilterStore = create<FilterState>((set, get) => ({
  filters: {},

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

  setUserType: (user_type) =>
    set((state) => ({
      filters: { ...state.filters, user_type },
    })),

  setMinRating: (min_rating) =>
    set((state) => ({
      filters: { ...state.filters, min_rating },
    })),

  clearFilters: () => set({ filters: {} }),

  hasActiveFilters: () => {
    const { filters } = get();
    return Object.values(filters).some((v) => v !== undefined);
  },
}));
