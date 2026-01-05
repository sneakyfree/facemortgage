import { create } from 'zustand';
import type { ProfessionalGridItem } from '@/types';

interface GridState {
  professionals: ProfessionalGridItem[];
  total: number;
  isLoading: boolean;
  error: string | null;

  setProfessionals: (professionals: ProfessionalGridItem[], total: number) => void;
  updateProfessional: (id: string, updates: Partial<ProfessionalGridItem>) => void;
  removeProfessional: (id: string) => void;
  addProfessional: (professional: ProfessionalGridItem) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useGridStore = create<GridState>((set) => ({
  professionals: [],
  total: 0,
  isLoading: false,
  error: null,

  setProfessionals: (professionals, total) =>
    set({
      professionals,
      total,
      isLoading: false,
      error: null,
    }),

  updateProfessional: (id, updates) =>
    set((state) => ({
      professionals: state.professionals.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),

  removeProfessional: (id) =>
    set((state) => ({
      professionals: state.professionals.filter((p) => p.id !== id),
      total: state.total - 1,
    })),

  addProfessional: (professional) =>
    set((state) => ({
      professionals: [...state.professionals, professional],
      total: state.total + 1,
    })),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error, isLoading: false }),
}));
