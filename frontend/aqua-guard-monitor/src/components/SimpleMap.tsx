import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { useAuth } from '@/lib/auth-context';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { groundWaterSampleApi } from '@/lib/api';
import 'leaflet/dist/leaflet.css';

interface MapDataPoint {
  id: number;
  latitude: number;
  longitude: number;
  hmpi_value: number;
  location_name?: string;
  year?: number;
}

interface SimpleMapProps {
  selectedYear?: number | null;
  onYearChange?: (year: number | null) => void;
}

const getColorByHMPI = (hmpiValue: number): string => {
  if (hmpiValue < 25) return '#2E7D32';      // Excellent - Green
  if (hmpiValue < 50) return '#66BB6A';      // Good - Light Green
  if (hmpiValue < 75) return '#FFA726';      // Poor - Orange
  if (hmpiValue < 100) return '#FF5722';     // Very Poor - Red
  return '#D32F2F';                          // Unsuitable - Dark Red
};

const SimpleMap: React.FC<SimpleMapProps> = ({ selectedYear, onYearChange }) => {
  const [mapData, setMapData] = useState<MapDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const { tokens, isAuthenticated } = useAuth();

  // Fetch available years
  const fetchAvailableYears = async () => {
    try {
      const data = await groundWaterSampleApi.getGroundWaterSamples();
      const samples = Array.isArray(data) ? data : data.results;
      const years = new Set<number>();
      
      samples.forEach((sample: any) => {
        if (sample.year && typeof sample.year === 'number') {
          years.add(sample.year);
        } else {
          const dateFields = ['collection_date', 'date_collected', 'created_at', 'date'];
          for (const field of dateFields) {
            if (sample[field]) {
              const year = new Date(sample[field]).getFullYear();
              if (!isNaN(year)) {
                years.add(year);
                break;
              }
            }
          }
        }
      });
      
      const sortedYears = Array.from(years).sort((a, b) => b - a);
      setAvailableYears(sortedYears);
      
      // Set default year if none selected
      if (!selectedYear && sortedYears.length > 0) {
        onYearChange?.(sortedYears[0]);
      }
    } catch (err) {
      console.error('Error fetching available years:', err);
    }
  };

  const fetchMapData = async () => {
    if (!tokens?.access) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching ALL map data for year:', selectedYear);
      
      let url = 'http://localhost:8000/api/v1/map-data/?limit=all&fields=basic';
      if (selectedYear) {
        url += `&year=${selectedYear}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${tokens.access}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log(`Loaded ${result.data.length} total samples from backend`);
      
      const validData = result.data.filter(
        (point: MapDataPoint) => point.latitude && point.longitude && 
                !isNaN(point.latitude) && !isNaN(point.longitude)
      );
      
      console.log(`${validData.length} samples have valid coordinates`);
      setMapData(validData);
    } catch (err) {
      console.error('Error fetching map data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch map data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && tokens?.access) {
      fetchMapData();
    }
  }, [isAuthenticated, tokens?.access, selectedYear]); // Re-fetch when year changes

  useEffect(() => {
    fetchAvailableYears();
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <p className="text-gray-600">Please log in to view the map</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading all water quality data...</p>
          <p className="text-sm text-gray-500 mt-1">This may take a moment to load 15k+ samples</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg">
        <div className="text-center">
          <p className="text-red-600 mb-2">{error}</p>
          <button 
            onClick={fetchMapData}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Year Selector */}
      <div className="flex items-center space-x-4 p-4 bg-white rounded-lg shadow-sm border">
        <label className="font-medium text-gray-700">Select Year:</label>
        <select
          value={selectedYear || ''}
          onChange={(e) => onYearChange?.(e.target.value ? Number(e.target.value) : null)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Years</option>
          {availableYears.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
        {selectedYear && (
          <span className="text-sm text-gray-600">
            Showing data for {selectedYear}
          </span>
        )}
      </div>

      {/* Map Container */}
      <div className="relative h-[600px] rounded-lg overflow-hidden border">
      {/* @ts-ignore */}
      <MapContainer
        center={[20.5937, 78.9629] as LatLngExpression}
        zoom={5}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {mapData.map((point) => (
          <CircleMarker
            key={point.id}
            center={[point.latitude, point.longitude] as LatLngExpression}
            radius={6}
            pathOptions={{
              fillColor: getColorByHMPI(point.hmpi_value),
              color: "white",
              weight: 2,
              opacity: 1,
              fillOpacity: 0.8
            }}
          >
            <Popup>
              <div className="p-2">
                <h3 className="font-bold">{point.location_name || `Site ${point.id}`}</h3>
                <p>HMPI: {point.hmpi_value.toFixed(2)}</p>
                <p>Location: {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Legend */}
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

      {/* Data count indicator */}
      <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-2">
        <p className="text-xs text-gray-600">
          📍 All {mapData.length.toLocaleString()} water quality samples
        </p>
        <p className="text-xs text-green-600 font-medium">
          ✓ Complete dataset loaded
        </p>
      </div>
      </div>
    </div>
  );
};

export default SimpleMap;