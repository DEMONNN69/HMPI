import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { useAuth } from '@/lib/auth-context';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Essential data structure - only what we need
interface MapDataPoint {
  id: number;
  latitude: number;
  longitude: number;
  hmpi_value: number;
  location_name?: string;
  quality_category?: string;
}

interface MapStats {
  total_samples: number;
  average_hmpi: number;
  quality_distribution: {
    excellent: number;
    good: number;
    poor: number;
    very_poor: number;
    unsuitable: number;
  };
}

interface MapApiResponse {
  data: MapDataPoint[];
  stats: MapStats;
  pagination: {
    current_page: number;
    total_pages: number;
    total_records: number;
    has_next: boolean;
    has_previous: boolean;
    page_size: number;
  };
}

// Single unified color function based on HMPI value
const getColorByHMPI = (hmpiValue: number): string => {
  if (hmpiValue < 25) return '#2E7D32';      // Excellent - Green
  if (hmpiValue < 50) return '#66BB6A';      // Good - Light Green
  if (hmpiValue < 75) return '#FFA726';      // Poor - Orange
  if (hmpiValue < 100) return '#FF5722';     // Very Poor - Red
  return '#D32F2F';                          // Unsuitable - Dark Red
};

// Get quality category from HMPI value
const getQualityCategory = (hmpiValue: number): string => {
  if (hmpiValue < 25) return 'Excellent';
  if (hmpiValue < 50) return 'Good';
  if (hmpiValue < 75) return 'Poor';
  if (hmpiValue < 100) return 'Very Poor';
  return 'Unsuitable';
};

// Optimized popup component
const PopupContent = React.memo(({ point }: { point: MapDataPoint }) => (
  <div className="p-3 min-w-[200px]">
    <h3 className="font-bold text-sm mb-2">
      📍 {point.location_name || `Site ${point.id}`}
    </h3>
    <div className="space-y-1 text-xs">
      <div className="flex justify-between">
        <span>HMPI Value:</span>
        <span className="font-semibold">{point.hmpi_value.toFixed(2)}</span>
      </div>
      <div className="flex justify-between">
        <span>Quality:</span>
        <span 
          className="px-2 py-1 rounded text-white text-xs font-medium"
          style={{ backgroundColor: getColorByHMPI(point.hmpi_value) }}
        >
          {point.quality_category || getQualityCategory(point.hmpi_value)}
        </span>
      </div>
      <div className="text-gray-500 text-xs mt-2">
        {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}
      </div>
    </div>
  </div>
));

const InteractiveMap: React.FC = () => {
  const [mapData, setMapData] = useState<MapDataPoint[]>([]);
  const [stats, setStats] = useState<MapStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const { tokens, isAuthenticated } = useAuth();

  //  Optimized data fetching
  const fetchMapData = useCallback(async (page = 1, fields = 'basic') => {
    console.log('Auth state:', { isAuthenticated, hasTokens: !!tokens, hasAccess: !!tokens?.access });
    
    if (!tokens?.access) {
      console.log('No access token available');
      setError('Authentication required - please log in');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('Making request with token:', tokens.access.substring(0, 20) + '...');
      
      const response = await fetch(
        `http://localhost:8000/api/v1/map-data/?page=${page}&limit=500&fields=${fields}`, 
        {
          headers: {
            'Authorization': `Bearer ${tokens.access}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        console.log('Response not ok:', response.status, response.statusText);
        if (response.status === 401) {
          setError('Authentication expired - please log in again');
          // You might want to trigger a logout here
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return;
      }

      const result: MapApiResponse = await response.json();
      
      // Filter out invalid coordinates
      const validData = result.data.filter(
        point => point.latitude && point.longitude && 
                !isNaN(point.latitude) && !isNaN(point.longitude)
      );
      
      setMapData(validData);
      setStats(result.stats);
      setTotalPages(result.pagination.total_pages);
      setCurrentPage(result.pagination.current_page);
      
    } catch (err) {
      console.error('Error fetching map data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch map data');
    } finally {
      setLoading(false);
    }
  }, [tokens?.access]);

  useEffect(() => {
    if (isAuthenticated && tokens?.access) {
      fetchMapData(1, 'basic');
    }
  }, [isAuthenticated, tokens?.access, fetchMapData]);

  // Memoized markers for performance
  const markers = useMemo(() => {
    return mapData.map((point) => (
      <CircleMarker
        key={point.id}
        center={[point.latitude, point.longitude]}
        pathOptions={{
          radius: 6,
          fillColor: getColorByHMPI(point.hmpi_value),
          color: "white",
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }}
      >
        <Popup>
          <PopupContent point={point} />
        </Popup>
      </CircleMarker>
    ));
  }, [mapData]);

  // Load more data function
  const loadMoreData = useCallback(() => {
    if (currentPage < totalPages && !loading) {
      fetchMapData(currentPage + 1, 'basic');
    }
  }, [currentPage, totalPages, loading, fetchMapData]);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-gray-500 mb-2 text-2xl">🔐</div>
          <p className="text-gray-600">Please log in to view the map</p>
        </div>
      </div>
    );
  }

  if (loading && mapData.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading map data...</p>
          <p className="text-sm text-gray-500 mt-1">Fetching water quality data</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg">
        <div className="text-center">
          <div className="text-red-500 mb-2 text-2xl">⚠️</div>
          <p className="text-red-600 mb-2">{error}</p>
          <button 
            onClick={() => fetchMapData(1, 'basic')}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-[600px] rounded-lg overflow-hidden border">
      {/* Stats Card */}
      {stats && (
        <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3 min-w-[200px]">
          <h3 className="font-bold text-sm mb-2">📊 Water Quality Stats</h3>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span>Total Samples:</span>
              <span className="font-semibold">{stats.total_samples}</span>
            </div>
            <div className="flex justify-between">
              <span>Avg HMPI:</span>
              <span className="font-semibold">{stats.average_hmpi.toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Load More Button */}
      {currentPage < totalPages && (
        <div className="absolute top-4 right-4 z-[1000]">
          <button
            onClick={loadMoreData}
            disabled={loading}
            className="bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Loading...' : `Load Page ${currentPage + 1}/${totalPages}`}
          </button>
        </div>
      )}

        {/* Map Container */}
        <MapContainer
          center={[20.5937, 78.9629]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {markers}
        </MapContainer>      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
        <h4 className="font-bold text-xs mb-2">🌊 HMPI Quality Scale</h4>
        <div className="space-y-1 text-xs">
          {[
            { label: 'Excellent (< 25)', color: '#2E7D32' },
            { label: 'Good (25-50)', color: '#66BB6A' },
            { label: 'Poor (50-75)', color: '#FFA726' },
            { label: 'Very Poor (75-100)', color: '#FF5722' },
            { label: 'Unsuitable (> 100)', color: '#D32F2F' }
          ].map(item => (
            <div key={item.label} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full border border-white" 
                style={{ backgroundColor: item.color }}
              />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Loading overlay for additional pages */}
      {loading && mapData.length > 0 && (
        <div className="absolute top-16 right-4 z-[1000] bg-white rounded-lg shadow-lg p-2">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            <span className="text-xs">Loading more data...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveMap;