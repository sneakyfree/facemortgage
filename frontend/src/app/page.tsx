import FilterPanel from "@/components/filters/FilterPanel";
import ProfessionalGrid from "@/components/grid/ProfessionalGrid";
import { GeoDetectionProvider } from "@/components/geo";

export default function Home() {
  return (
    <GeoDetectionProvider autoApplyState={true}>
      <div className="min-h-screen">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-600 to-blue-800 text-white py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Find Your Mortgage Professional
            </h1>
            <p className="text-xl text-blue-100 max-w-2xl mx-auto">
              Connect instantly with loan officers, realtors, and mortgage professionals
              via live video. Browse, filter, and call professionals ready to help you right now.
            </p>
          </div>
        </section>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Filters */}
          <FilterPanel />

          {/* Grid Header */}
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-gray-900">
              Available Professionals
            </h2>
            <div className="text-sm text-gray-500">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-1" />
              Green dot = Available now
            </div>
          </div>

          {/* Professional Grid */}
          <ProfessionalGrid />
        </div>
      </div>
    </GeoDetectionProvider>
  );
}
