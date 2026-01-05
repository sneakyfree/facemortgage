'use client';

import { useEffect, useRef } from 'react';
import { useGeoLocation } from '@/hooks/useGeoLocation';
import { useFilterStore } from '@/stores/filterStore';

interface GeoDetectionProviderProps {
  children: React.ReactNode;
  autoApplyState?: boolean;
}

/**
 * Provider component that handles geo-detection and syncs with the filter store.
 * Wrap your grid/page with this component to enable automatic geo-detection.
 */
export default function GeoDetectionProvider({
  children,
  autoApplyState = true,
}: GeoDetectionProviderProps) {
  const { location, isLoading, error, isPermissionDenied } = useGeoLocation({
    autoDetect: true,
    useBrowserLocation: true,
    useIPFallback: true,
  });

  const {
    setDetectedLocation,
    setGeoDetecting,
    setGeoError,
    applyDetectedState,
    filters,
  } = useFilterStore();

  const hasAppliedRef = useRef(false);

  // Sync loading state
  useEffect(() => {
    setGeoDetecting(isLoading);
  }, [isLoading, setGeoDetecting]);

  // Sync location data when detected
  useEffect(() => {
    if (location) {
      setDetectedLocation(
        location.state_code,
        location.city,
        location.source as 'browser' | 'ip' | 'cached' | null
      );

      // Auto-apply state filter on first detection if no state filter is already set
      if (autoApplyState && !hasAppliedRef.current && !filters.state_code) {
        hasAppliedRef.current = true;
        applyDetectedState();
      }
    }
  }, [location, setDetectedLocation, applyDetectedState, autoApplyState, filters.state_code]);

  // Sync error state
  useEffect(() => {
    if (error) {
      setGeoError(error);
    }
  }, [error, setGeoError]);

  // Log permission denial for analytics (optional)
  useEffect(() => {
    if (isPermissionDenied) {
      console.debug('Geo permission denied, using IP-based fallback');
    }
  }, [isPermissionDenied]);

  return <>{children}</>;
}
