'use client';

import { useEffect, useCallback, useState, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useGridStore } from '@/stores/gridStore';
import { useFilterStore } from '@/stores/filterStore';
import { useRealtimeGrid } from '@/hooks/useRealtimeGrid';
import { professionalsApi, gridTrackingApi } from '@/lib/api/endpoints';
import ProfessionalCard from './ProfessionalCard';
import { VideoCallModal } from '@/components/call';
import type { ProfessionalGridItem } from '@/types';

// Generate a session ID for tracking
const getSessionId = (): string => {
  if (typeof window === 'undefined') return '';
  let sessionId = sessionStorage.getItem('grid_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('grid_session_id', sessionId);
  }
  return sessionId;
};

export default function ProfessionalGrid() {
  const queryClient = useQueryClient();
  const { professionals, setProfessionals, setLoading, setError } = useGridStore();
  const { filters } = useFilterStore();
  const trackedImpressionsRef = useRef<Set<string>>(new Set());

  // Video call state
  const [activeCall, setActiveCall] = useState<{
    professionalId: string;
    professionalName: string;
  } | null>(null);

  // Real-time grid updates via WebSocket
  useRealtimeGrid({
    enabled: true,
    onProfessionalOnline: () => {
      // Refetch to get the new professional's data
      queryClient.invalidateQueries({ queryKey: ['professionals'] });
    },
    onProfessionalOffline: (professionalId) => {
      // Already handled by the hook updating the store
      console.log('Professional went offline:', professionalId);
    },
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['professionals', filters],
    queryFn: () => professionalsApi.getGrid(filters, 50, 0),
    refetchInterval: 30000, // Refresh every 30 seconds as fallback
  });

  useEffect(() => {
    setLoading(isLoading);
    if (data) {
      setProfessionals(data.professionals, data.total);

      // Track impressions for newly loaded professionals
      const newImpressions = data.professionals.filter(
        (p) => !trackedImpressionsRef.current.has(p.id)
      );

      if (newImpressions.length > 0) {
        const impressions = newImpressions.map((p, index) => ({
          professional_id: p.id,
          position: p.grid_position || index + 1,
        }));

        // Track impressions (fire and forget)
        gridTrackingApi.trackImpressions(impressions, getSessionId()).catch((err) => {
          console.debug('Failed to track impressions:', err);
        });

        // Mark as tracked
        newImpressions.forEach((p) => trackedImpressionsRef.current.add(p.id));
      }
    }
    if (error) {
      setError(error instanceof Error ? error.message : 'Failed to load professionals');
    }
  }, [data, isLoading, error, setProfessionals, setLoading, setError]);

  const handleCallClick = useCallback((professional: ProfessionalGridItem) => {
    // Track call click
    gridTrackingApi.trackClick({
      professional_id: professional.id,
      click_type: 'call_initiated',
      grid_position: professional.grid_position,
      session_id: getSessionId(),
      filter_context: filters as Record<string, unknown>,
    }).catch((err) => {
      console.debug('Failed to track call click:', err);
    });

    setActiveCall({
      professionalId: professional.id,
      professionalName: `${professional.first_name} ${professional.last_name}`,
    });
  }, [filters]);

  const handleCallClose = useCallback(() => {
    setActiveCall(null);
    // Refresh the grid in case availability changed
    queryClient.invalidateQueries({ queryKey: ['professionals'] });
  }, [queryClient]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        {[...Array(10)].map((_, i) => (
          <div key={i} className="bg-gray-200 rounded-xl animate-pulse aspect-[4/5]" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Failed to load professionals</p>
        <button
          onClick={() => window.location.reload()}
          className="text-blue-600 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  if (professionals.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg mb-2">No professionals found</p>
        <p className="text-gray-400">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        {professionals.map((professional) => (
          <ProfessionalCard
            key={professional.id}
            professional={professional}
            onCallClick={handleCallClick}
          />
        ))}
      </div>

      {/* Video Call Modal */}
      {activeCall && (
        <VideoCallModal
          professionalId={activeCall.professionalId}
          professionalName={activeCall.professionalName}
          onClose={handleCallClose}
        />
      )}
    </>
  );
}
