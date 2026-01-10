'use client';

import { useQuery } from '@tanstack/react-query';
import { X, MapPin, Loader2 } from 'lucide-react';
import { useFilterStore } from '@/stores/filterStore';
import { lookupsApi } from '@/lib/api/endpoints';
import { cn, getUserTypeLabel } from '@/lib/utils';
import type { UserType } from '@/types';

const USER_TYPES: UserType[] = ['loan_officer', 'realtor', 'title_rep', 'attorney'];

export default function FilterPanel() {
  const {
    filters,
    geo,
    setLanguage,
    setSpecialty,
    setStateCode,
    setUserType,
    setMinRating,
    clearFilters,
    clearStateFilter,
    hasActiveFilters,
    isUsingDetectedState,
  } = useFilterStore();

  const { data: specialties } = useQuery({
    queryKey: ['specialties'],
    queryFn: () => lookupsApi.getSpecialties(),
  });

  const { data: languages } = useQuery({
    queryKey: ['languages'],
    queryFn: () => lookupsApi.getLanguages(),
  });

  const { data: states } = useQuery({
    queryKey: ['states'],
    queryFn: () => lookupsApi.getStates(),
  });

  const isDetectedState = isUsingDetectedState();

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Find Your Professional</h2>
        {hasActiveFilters() && (
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Clear all
          </button>
        )}
      </div>

      {/* Geo-detection indicator */}
      {geo.is_detecting && (
        <div className="mb-4 flex items-center gap-2 text-sm text-blue-600 bg-blue-50 px-3 py-2 rounded-lg">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Detecting your location...</span>
        </div>
      )}

      {geo.detected_state && !geo.is_detecting && isDetectedState && (
        <div className="mb-4 flex items-center justify-between bg-green-50 px-3 py-2 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-green-700">
            <MapPin className="w-4 h-4" />
            <span>
              Showing professionals in{' '}
              <strong>
                {states?.find((s) => s.code === geo.detected_state)?.name || geo.detected_state}
              </strong>
              {geo.detected_city && <span className="text-green-600"> ({geo.detected_city})</span>}
            </span>
          </div>
          <button
            onClick={clearStateFilter}
            className="text-sm text-green-600 hover:text-green-800 underline"
          >
            Show all states
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* State Filter */}
        <div>
          <label htmlFor="filter-state" className="block text-sm font-medium text-gray-700 mb-2">
            State
            {isDetectedState && (
              <span className="ml-1 text-xs text-green-600">(detected)</span>
            )}
          </label>
          <select
            id="filter-state"
            value={filters.state_code || ''}
            onChange={(e) => setStateCode(e.target.value || undefined)}
            className={cn(
              "w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
              isDetectedState ? "border-green-300 bg-green-50" : "border-gray-300"
            )}
          >
            <option value="">All States</option>
            {states?.map((state) => (
              <option key={state.code} value={state.code}>
                {state.name}
              </option>
            ))}
          </select>
        </div>

        {/* Professional Type */}
        <div>
          <label htmlFor="filter-type" className="block text-sm font-medium text-gray-700 mb-2">Professional Type</label>
          <select
            id="filter-type"
            value={filters.user_type || ''}
            onChange={(e) => setUserType(e.target.value as UserType || undefined)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Types</option>
            {USER_TYPES.map((type) => (
              <option key={type} value={type}>
                {getUserTypeLabel(type)}
              </option>
            ))}
          </select>
        </div>

        {/* Language */}
        <div>
          <label htmlFor="filter-language" className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <select
            id="filter-language"
            value={filters.language || ''}
            onChange={(e) => setLanguage(e.target.value || undefined)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Any Language</option>
            {languages?.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Specialty */}
        <div>
          <label htmlFor="filter-specialty" className="block text-sm font-medium text-gray-700 mb-2">Specialty</label>
          <select
            id="filter-specialty"
            value={filters.specialty || ''}
            onChange={(e) => setSpecialty(e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Any Specialty</option>
            {specialties?.map((spec) => (
              <option key={spec.id} value={spec.id}>
                {spec.name}
              </option>
            ))}
          </select>
        </div>

        {/* Minimum Rating */}
        <div>
          <label htmlFor="filter-rating" className="block text-sm font-medium text-gray-700 mb-2">Minimum Rating</label>
          <select
            id="filter-rating"
            value={filters.min_rating || ''}
            onChange={(e) => setMinRating(e.target.value ? parseFloat(e.target.value) : undefined)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Any Rating</option>
            <option value="4.5">4.5+ Stars</option>
            <option value="4.0">4.0+ Stars</option>
            <option value="3.5">3.5+ Stars</option>
            <option value="3.0">3.0+ Stars</option>
          </select>
        </div>
      </div>

      {/* Active Filters Tags */}
      {hasActiveFilters() && (
        <div className="mt-4 flex flex-wrap gap-2">
          {filters.state_code && states && (
            <FilterTag
              label={`State: ${states.find((s) => s.code === filters.state_code)?.name || filters.state_code}`}
              onRemove={() => setStateCode(undefined)}
              variant={isDetectedState ? 'detected' : 'default'}
            />
          )}
          {filters.user_type && (
            <FilterTag
              label={getUserTypeLabel(filters.user_type)}
              onRemove={() => setUserType(undefined)}
            />
          )}
          {filters.language && (
            <FilterTag
              label={`Language: ${filters.language.toUpperCase()}`}
              onRemove={() => setLanguage(undefined)}
            />
          )}
          {filters.specialty && specialties && (
            <FilterTag
              label={specialties.find((s) => s.id === filters.specialty)?.name || 'Specialty'}
              onRemove={() => setSpecialty(undefined)}
            />
          )}
          {filters.min_rating && (
            <FilterTag
              label={`${filters.min_rating}+ Stars`}
              onRemove={() => setMinRating(undefined)}
            />
          )}
        </div>
      )}
    </div>
  );
}

function FilterTag({
  label,
  onRemove,
  variant = 'default',
}: {
  label: string;
  onRemove: () => void;
  variant?: 'default' | 'detected';
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm",
        variant === 'detected'
          ? "bg-green-100 text-green-700"
          : "bg-blue-100 text-blue-700"
      )}
    >
      {variant === 'detected' && <MapPin className="w-3 h-3" />}
      {label}
      <button
        onClick={onRemove}
        className={cn(
          "rounded-full p-0.5",
          variant === 'detected' ? "hover:bg-green-200" : "hover:bg-blue-200"
        )}
      >
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}
