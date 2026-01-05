'use client';

import { useQuery } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { useFilterStore } from '@/stores/filterStore';
import { lookupsApi } from '@/lib/api/endpoints';
import { cn, getUserTypeLabel } from '@/lib/utils';
import type { UserType } from '@/types';

const USER_TYPES: UserType[] = ['loan_officer', 'realtor', 'title_rep', 'attorney'];

export default function FilterPanel() {
  const { filters, setLanguage, setSpecialty, setUserType, setMinRating, clearFilters, hasActiveFilters } =
    useFilterStore();

  const { data: specialties } = useQuery({
    queryKey: ['specialties'],
    queryFn: () => lookupsApi.getSpecialties(),
  });

  const { data: languages } = useQuery({
    queryKey: ['languages'],
    queryFn: () => lookupsApi.getLanguages(),
  });

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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Professional Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Professional Type</label>
          <select
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
          <select
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Specialty</label>
          <select
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
          <label className="block text-sm font-medium text-gray-700 mb-2">Minimum Rating</label>
          <select
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

function FilterTag({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
      {label}
      <button onClick={onRemove} className="hover:bg-blue-200 rounded-full p-0.5">
        <X className="w-3 h-3" />
      </button>
    </span>
  );
}
