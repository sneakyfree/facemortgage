'use client';

import { useState } from 'react';
import { Star, Phone, Clock, Award, BarChart2 } from 'lucide-react';
import { cn, formatRating, formatPickupTime, getStatusColor, getInitials, getUserTypeLabel } from '@/lib/utils';
import { gridTrackingApi } from '@/lib/api/endpoints';
import { BaseballCard } from './BaseballCard';
import type { ProfessionalGridItem } from '@/types';

// Get session ID from session storage
const getSessionId = (): string => {
  if (typeof window === 'undefined') return '';
  return sessionStorage.getItem('grid_session_id') || '';
};

interface ProfessionalCardProps {
  professional: ProfessionalGridItem;
  onCallClick: (professional: ProfessionalGridItem) => void;
}

export default function ProfessionalCard({ professional, onCallClick }: ProfessionalCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [showBaseballCard, setShowBaseballCard] = useState(false);

  const isAvailable = professional.status === 'online_available';
  const fullName = `${professional.first_name} ${professional.last_name}`;

  // Handle keyboard interaction for calling
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.key === 'Enter' || e.key === ' ') && isAvailable) {
      e.preventDefault();
      onCallClick(professional);
    }
  };

  return (
    <article
      role="article"
      aria-label={`${fullName}, ${getUserTypeLabel(professional.user_type)}${isAvailable ? ', available for calls' : ', currently busy'}`}
      tabIndex={isAvailable ? 0 : -1}
      onKeyDown={handleKeyDown}
      className={cn(
        'relative bg-white rounded-xl shadow-md overflow-hidden transition-all duration-300',
        'hover:shadow-xl hover:scale-[1.02]',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        !isAvailable && 'opacity-75'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Video/Avatar Area */}
      <div className="relative aspect-video bg-gray-900">
        {professional.avatar_url ? (
          <img
            src={professional.avatar_url}
            alt={`${professional.first_name} ${professional.last_name}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700">
            <span className="text-4xl font-bold text-white">
              {getInitials(professional.first_name, professional.last_name)}
            </span>
          </div>
        )}

        {/* Status Indicator */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <span
            className={cn(
              'w-3 h-3 rounded-full ring-2 ring-white',
              getStatusColor(professional.status)
            )}
            aria-hidden="true"
          />
          <span className="text-xs font-medium text-white bg-black/50 px-2 py-0.5 rounded">
            {isAvailable ? 'Available' : 'Busy'}
          </span>
        </div>

        {/* Video Type Badge */}
        <div className="absolute top-3 right-3">
          <span
            className={cn(
              'text-xs font-medium px-2 py-0.5 rounded',
              professional.video_type === 'live'
                ? 'bg-red-500 text-white'
                : 'bg-gray-500 text-white'
            )}
          >
            {professional.video_type === 'live' ? 'LIVE' : 'Video'}
          </span>
        </div>

        {/* Hover Overlay with Call Button */}
        {isHovered && isAvailable && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center transition-opacity">
            <button
              onClick={() => onCallClick(professional)}
              aria-label={`Call ${fullName} now`}
              className="bg-green-500 hover:bg-green-600 text-white font-semibold px-6 py-3 rounded-full flex items-center gap-2 transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-black"
            >
              <Phone className="w-5 h-5" aria-hidden="true" />
              Call Now
            </button>
          </div>
        )}
      </div>

      {/* Info Section */}
      <div className="p-4">
        {/* Name and Type */}
        <div className="mb-2">
          <h3 className="font-semibold text-gray-900 text-lg">
            {professional.first_name} {professional.last_name}
          </h3>
          <p className="text-sm text-gray-500">
            {getUserTypeLabel(professional.user_type)}
            {professional.company_name && ` at ${professional.company_name}`}
          </p>
        </div>

        {/* Stats Row */}
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
          {/* Rating */}
          <div className="flex items-center gap-1" aria-label={`Rating: ${formatRating(professional.avg_rating)} stars from ${professional.total_reviews} reviews`}>
            <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" aria-hidden="true" />
            <span className="font-medium">{formatRating(professional.avg_rating)}</span>
            <span className="text-gray-400">({professional.total_reviews})</span>
          </div>

          {/* Pickup Time */}
          {professional.avg_pickup_time_seconds && (
            <div className="flex items-center gap-1" aria-label={`Average response time: ${formatPickupTime(professional.avg_pickup_time_seconds)}`}>
              <Clock className="w-4 h-4 text-gray-400" aria-hidden="true" />
              <span>{formatPickupTime(professional.avg_pickup_time_seconds)}</span>
            </div>
          )}

          {/* Experience */}
          {professional.years_experience && (
            <div className="flex items-center gap-1" aria-label={`${professional.years_experience} years of experience`}>
              <Award className="w-4 h-4 text-gray-400" aria-hidden="true" />
              <span>{professional.years_experience}yr</span>
            </div>
          )}
        </div>

        {/* Specialties */}
        {professional.specialty_names.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {professional.specialty_names.slice(0, 3).map((specialty) => (
              <span
                key={specialty}
                className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full"
              >
                {specialty}
              </span>
            ))}
            {professional.specialty_names.length > 3 && (
              <span className="text-xs text-gray-400">
                +{professional.specialty_names.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Languages */}
        {professional.language_codes.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {professional.language_codes.map((code) => (
              <span
                key={code}
                className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
              >
                {code.toUpperCase()}
              </span>
            ))}
          </div>
        )}

        {/* View Stats Button */}
        {professional.nmls_id && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Track profile view click
              gridTrackingApi.trackClick({
                professional_id: professional.id,
                click_type: 'profile_view',
                grid_position: professional.grid_position,
                session_id: getSessionId(),
              }).catch((err) => {
                console.debug('Failed to track profile view:', err);
              });
              setShowBaseballCard(true);
            }}
            aria-label={`View detailed stats for ${fullName}`}
            className="mt-3 w-full flex items-center justify-center gap-2 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <BarChart2 className="w-4 h-4" aria-hidden="true" />
            View Stats
          </button>
        )}
      </div>

      {/* Baseball Card Modal */}
      {showBaseballCard && professional.nmls_id && (
        <BaseballCard
          nmlsId={professional.nmls_id}
          professionalName={`${professional.first_name} ${professional.last_name}`}
          professionalImage={professional.avatar_url}
          onClose={() => setShowBaseballCard(false)}
        />
      )}
    </article>
  );
}
