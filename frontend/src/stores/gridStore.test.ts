/**
 * gridStore tests.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useGridStore } from './gridStore';
import type { ProfessionalGridItem } from '@/types';

// Helper to create mock professionals
function createMockProfessional(
  id: string,
  overrides: Partial<ProfessionalGridItem> = {}
): ProfessionalGridItem {
  return {
    id,
    user_id: `user-${id}`,
    first_name: 'Test',
    last_name: 'Professional',
    user_type: 'loan_officer',
    company_name: 'Test Company',
    avatar_url: undefined,
    status: 'online_available',
    subscription_tier: 'professional',
    video_type: 'live',
    avg_rating: 4.5,
    total_reviews: 10,
    avg_pickup_time_seconds: 5,
    years_experience: 5,
    specialty_names: ['Purchase'],
    language_codes: ['en'],
    nmls_id: '123456',
    grid_position: 1,
    score: 100,
    ...overrides,
  };
}

describe('gridStore', () => {
  // Reset store before each test
  beforeEach(() => {
    const { result } = renderHook(() => useGridStore());
    act(() => {
      result.current.setProfessionals([], 0);
      result.current.setError(null);
    });
  });

  describe('initial state', () => {
    it('has empty professionals array', () => {
      const { result } = renderHook(() => useGridStore());

      expect(result.current.professionals).toEqual([]);
    });

    it('has zero total', () => {
      const { result } = renderHook(() => useGridStore());

      expect(result.current.total).toBe(0);
    });

    it('is not loading initially', () => {
      const { result } = renderHook(() => useGridStore());

      expect(result.current.isLoading).toBe(false);
    });

    it('has no error initially', () => {
      const { result } = renderHook(() => useGridStore());

      expect(result.current.error).toBe(null);
    });
  });

  describe('setProfessionals', () => {
    it('sets professionals array', () => {
      const { result } = renderHook(() => useGridStore());

      const professionals = [
        createMockProfessional('pro-1'),
        createMockProfessional('pro-2'),
      ];

      act(() => {
        result.current.setProfessionals(professionals, 2);
      });

      expect(result.current.professionals).toHaveLength(2);
      expect(result.current.professionals[0].id).toBe('pro-1');
      expect(result.current.professionals[1].id).toBe('pro-2');
    });

    it('sets total count', () => {
      const { result } = renderHook(() => useGridStore());

      const professionals = [createMockProfessional('pro-1')];

      act(() => {
        result.current.setProfessionals(professionals, 100);
      });

      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.total).toBe(100);
    });

    it('clears loading state', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setProfessionals([], 0);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('clears error state', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setError('Previous error');
      });

      expect(result.current.error).toBe('Previous error');

      act(() => {
        result.current.setProfessionals([], 0);
      });

      expect(result.current.error).toBe(null);
    });

    it('replaces existing professionals', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      expect(result.current.professionals[0].id).toBe('pro-1');

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-2')],
          1
        );
      });

      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.professionals[0].id).toBe('pro-2');
    });
  });

  describe('updateProfessional', () => {
    it('updates professional by id', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [
            createMockProfessional('pro-1', { status: 'online_available' }),
            createMockProfessional('pro-2', { status: 'online_available' }),
          ],
          2
        );
      });

      act(() => {
        result.current.updateProfessional('pro-1', { status: 'online_busy' });
      });

      expect(result.current.professionals[0].status).toBe('online_busy');
      expect(result.current.professionals[1].status).toBe('online_available');
    });

    it('can update multiple fields', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      act(() => {
        result.current.updateProfessional('pro-1', {
          status: 'in_call',
          avg_rating: 4.8,
          total_reviews: 15,
        });
      });

      const updated = result.current.professionals[0];
      expect(updated.status).toBe('in_call');
      expect(updated.avg_rating).toBe(4.8);
      expect(updated.total_reviews).toBe(15);
    });

    it('does nothing for non-existent id', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      act(() => {
        result.current.updateProfessional('non-existent', { status: 'offline' });
      });

      // Should not crash and professionals should remain unchanged
      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.professionals[0].status).toBe('online_available');
    });

    it('preserves other fields', () => {
      const { result } = renderHook(() => useGridStore());

      const original = createMockProfessional('pro-1', {
        first_name: 'John',
        last_name: 'Doe',
        company_name: 'Acme Inc',
      });

      act(() => {
        result.current.setProfessionals([original], 1);
      });

      act(() => {
        result.current.updateProfessional('pro-1', { status: 'offline' });
      });

      const updated = result.current.professionals[0];
      expect(updated.first_name).toBe('John');
      expect(updated.last_name).toBe('Doe');
      expect(updated.company_name).toBe('Acme Inc');
      expect(updated.status).toBe('offline');
    });
  });

  describe('removeProfessional', () => {
    it('removes professional by id', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [
            createMockProfessional('pro-1'),
            createMockProfessional('pro-2'),
            createMockProfessional('pro-3'),
          ],
          3
        );
      });

      act(() => {
        result.current.removeProfessional('pro-2');
      });

      expect(result.current.professionals).toHaveLength(2);
      expect(result.current.professionals.map((p) => p.id)).toEqual(['pro-1', 'pro-3']);
    });

    it('decrements total count', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          5
        );
      });

      expect(result.current.total).toBe(5);

      act(() => {
        result.current.removeProfessional('pro-1');
      });

      expect(result.current.total).toBe(4);
    });

    it('handles removing non-existent id', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      act(() => {
        result.current.removeProfessional('non-existent');
      });

      // Should still decrement total (current behavior)
      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.total).toBe(0);
    });

    it('removes from empty array without error', () => {
      const { result } = renderHook(() => useGridStore());

      // Should not throw
      act(() => {
        result.current.removeProfessional('some-id');
      });

      expect(result.current.professionals).toEqual([]);
      expect(result.current.total).toBe(-1);
    });
  });

  describe('addProfessional', () => {
    it('adds professional to array', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      act(() => {
        result.current.addProfessional(createMockProfessional('pro-2'));
      });

      expect(result.current.professionals).toHaveLength(2);
      expect(result.current.professionals[1].id).toBe('pro-2');
    });

    it('increments total count', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals([], 0);
      });

      expect(result.current.total).toBe(0);

      act(() => {
        result.current.addProfessional(createMockProfessional('pro-1'));
      });

      expect(result.current.total).toBe(1);
    });

    it('adds to empty array', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.addProfessional(createMockProfessional('pro-1'));
      });

      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.professionals[0].id).toBe('pro-1');
    });

    it('appends to end of array', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [
            createMockProfessional('pro-1'),
            createMockProfessional('pro-2'),
          ],
          2
        );
      });

      act(() => {
        result.current.addProfessional(createMockProfessional('pro-3'));
      });

      expect(result.current.professionals[2].id).toBe('pro-3');
    });
  });

  describe('setLoading', () => {
    it('sets loading to true', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);
    });

    it('sets loading to false', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setLoading(true);
      });

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('setError', () => {
    it('sets error message', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setError('Network error');
      });

      expect(result.current.error).toBe('Network error');
    });

    it('clears loading when error is set', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setError('Some error');
      });

      expect(result.current.isLoading).toBe(false);
    });

    it('clears error with null', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setError('Error message');
      });

      act(() => {
        result.current.setError(null);
      });

      expect(result.current.error).toBe(null);
    });
  });

  describe('combined operations', () => {
    it('handles add then remove', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.addProfessional(createMockProfessional('pro-1'));
        result.current.addProfessional(createMockProfessional('pro-2'));
      });

      expect(result.current.professionals).toHaveLength(2);

      act(() => {
        result.current.removeProfessional('pro-1');
      });

      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.professionals[0].id).toBe('pro-2');
    });

    it('handles update during loading', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
        result.current.setLoading(true);
      });

      act(() => {
        result.current.updateProfessional('pro-1', { status: 'offline' });
      });

      // Update should work even during loading
      expect(result.current.professionals[0].status).toBe('offline');
      expect(result.current.isLoading).toBe(true);
    });

    it('maintains professionals when setting error', () => {
      const { result } = renderHook(() => useGridStore());

      act(() => {
        result.current.setProfessionals(
          [createMockProfessional('pro-1')],
          1
        );
      });

      act(() => {
        result.current.setError('Some error occurred');
      });

      // Professionals should remain
      expect(result.current.professionals).toHaveLength(1);
      expect(result.current.error).toBe('Some error occurred');
    });
  });
});
