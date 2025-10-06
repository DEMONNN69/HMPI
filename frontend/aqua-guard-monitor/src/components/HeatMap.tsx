import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { useAuth } from '@/lib/auth-context';
import 'leaflet/dist/leaflet.css';

// Import leaflet heatmap plugin
import 'leaflet.heat';

// Declare global type for leaflet heat layer
declare global {
  interface Window {
    L: any;
  }
}

interface MapDataPoint {
  id: number;
  latitude: number;
  longitude: number;
  hmpi_value: number;
  location_name?: string;
  year?: number;
}

interface HeatMapProps {
  selectedYear?: number | null;
  onYearChange?: (year: number | null) => void;
}

// Custom component to handle heatmap layer
const HeatmapLayer: React.FC<{ data: MapDataPoint[] }> = ({ data }) => {
  const map = useMap();

  useEffect(() => {
    console.log('HeatmapLayer useEffect triggered:', {
      dataLength: data.length,
      hasLeaflet: !!window.L,
      hasHeatLayer: !!(window.L && (window.L as any).heatLayer)
    });

    if (data.length > 0 && window.L && (window.L as any).heatLayer) {
      // Remove existing heatmap layers
      map.eachLayer((layer: any) => {
        if (layer.options && layer.options.isHeatmapLayer) {
          console.log('Removing existing heatmap layer');
          map.removeLayer(layer);
        }
      });

      // Prepare heatmap data points with threshold-based coloring
      // ACTUAL data shows: Avg HMPI = 1.17, Max = 180.57, Min = 0.00
      // Use extremely small values to prevent any orange/red when zoomed in
      const heatPoints = data.map(point => {
        let intensity;
        
        if (point.hmpi_value < 2) {
          // Excellent (most of 15,479 samples) - HMPI < 2
          intensity = 0.0005; // Extremely tiny
        } else if (point.hmpi_value < 10) {
          // Good - HMPI 2-10
          intensity = 0.005;
        } else if (point.hmpi_value < 50) {
          // Poor - HMPI 10-50
          intensity = 0.05;
        } else if (point.hmpi_value < 100) {
          // Very Poor - HMPI 50-100
          intensity = 0.3;
        } else {
          // Unsuitable - HMPI > 100 (only a few samples)
          intensity = 0.7;
        }
        
        return [
          point.latitude,
          point.longitude,
          intensity
        ];
      });

      console.log(`Creating heatmap with ${heatPoints.length} points`);
      console.log('Sample heat points:', heatPoints.slice(0, 3));
      console.log('Sample HMPI values:', data.slice(0, 5).map(p => `HMPI: ${p.hmpi_value}`));
      
      // Debug: Show HMPI value distribution
      const hmpiValues = data.map(p => p.hmpi_value);
      const minHMPI = Math.min(...hmpiValues);
      const maxHMPI = Math.max(...hmpiValues);
      const avgHMPI = hmpiValues.reduce((a, b) => a + b, 0) / hmpiValues.length;
      console.log(`HMPI Distribution - Min: ${minHMPI.toFixed(2)}, Max: ${maxHMPI.toFixed(2)}, Avg: ${avgHMPI.toFixed(2)}`);
      
      // Count values in each range
      const excellent = hmpiValues.filter(v => v < 25).length;
      const good = hmpiValues.filter(v => v >= 25 && v < 50).length;
      const poor = hmpiValues.filter(v => v >= 50 && v < 75).length;
      const veryPoor = hmpiValues.filter(v => v >= 75 && v < 100).length;
      const unsuitable = hmpiValues.filter(v => v >= 100).length;
      console.log(`HMPI Categories - Excellent: ${excellent}, Good: ${good}, Poor: ${poor}, Very Poor: ${veryPoor}, Unsuitable: ${unsuitable}`);

      // Create and add heatmap layer optimized for actual data (avg HMPI = 1.17)
      const heatLayer = (window.L as any).heatLayer(heatPoints, {
        radius: 15,
        blur: 10,
        maxZoom: 18,
        max: 50.0,      // Much higher to handle extreme overlap without turning red
        minOpacity: 0.3,
        gradient: {
          0.0: '#1B5E20',   // Dark Green - HMPI < 2
          0.05: '#2E7D32',  // Green
          0.15: '#66BB6A',  // Light Green - HMPI 2-10
          0.4: '#FFA726',   // Orange - HMPI 10-50
          0.7: '#FF5722',   // Red - HMPI 50-100
          1.0: '#B71C1C'    // Dark Red - HMPI > 100
        },
        isHeatmapLayer: true
      });

      heatLayer.addTo(map);
      console.log('Heatmap layer added successfully');
    } else if (data.length === 0) {
      console.log('No data available for heatmap');
    } else if (!window.L) {
      console.error('Leaflet not loaded');
    } else if (!(window.L as any).heatLayer) {
      console.error('Leaflet.heat plugin not loaded');
    }
  }, [data, map]);

  return null;
};

interface HeatMapProps {
  selectedYear?: number | null;
  onYearChange?: (year: number | null) => void;
}

const HeatMap: React.FC<HeatMapProps> = ({ selectedYear, onYearChange }) => {
  const [mapData, setMapData] = useState<MapDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const { tokens, isAuthenticated } = useAuth();

  // Check if heatmap plugin is loaded
  useEffect(() => {
    const checkHeatmapPlugin = () => {
      console.log('Checking heatmap plugin availability:', {
        hasLeaflet: !!window.L,
        hasHeatLayer: !!(window.L && (window.L as any).heatLayer),
        leafletVersion: window.L?.version
      });
    };
    
    // Check immediately and after a short delay
    checkHeatmapPlugin();
    setTimeout(checkHeatmapPlugin, 1000);
  }, []);

  // Fetch available years
  const fetchAvailableYears = async () => {
    if (!tokens?.access) {
      console.log('No access token available for fetching years');
      return;
    }

    try {
      console.log('Fetching available years from map-data endpoint...');
      
      const response = await fetch('http://localhost:8000/api/v1/map-data/?limit=all&fields=basic', {
        headers: {
          'Authorization': `Bearer ${tokens.access}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      const samples = result.data || [];
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
      console.log('Available years for heatmap:', sortedYears);
      
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
      
      console.log('Fetching heatmap data for year:', selectedYear);
      
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
      console.log(`Loaded ${result.data.length} samples for heatmap`);
      
      const validData = result.data.filter(
        (point: MapDataPoint) => point.latitude && point.longitude && 
                !isNaN(point.latitude) && !isNaN(point.longitude)
      );
      
      setMapData(validData);
    } catch (err) {
      console.error('Error fetching heatmap data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch heatmap data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && tokens?.access) {
      fetchAvailableYears();
      fetchMapData(); // Also fetch initial data
    }
  }, [isAuthenticated, tokens?.access]);

  useEffect(() => {
    if (isAuthenticated && tokens?.access) {
      fetchMapData(); // Re-fetch when year changes
    }
  }, [selectedYear]);

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <p className="text-gray-600">Please log in to view the heatmap</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading heatmap data...</p>
          <p className="text-sm text-gray-500 mt-1">Generating density visualization</p>
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
      {/* Year Selector - Match SimpleMap style */}
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
            Showing heatmap for {selectedYear}
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
        <HeatmapLayer data={mapData} />
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3">
        <h4 className="font-bold text-xs mb-2">🔥 HMPI Heatmap Legend</h4>
        <div className="space-y-1 text-xs">
          {[
            { label: 'Excellent (< 2)', color: '#66BB6A' },
            { label: 'Good (2-10)', color: '#FFA726' },
            { label: 'Poor (10-50)', color: '#FF5722' },
            { label: 'Very Poor (50-100)', color: '#B71C1C' },
            { label: 'Unsuitable (> 100)', color: '#8B0000' }
          ].map(item => (
            <div key={item.label} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full border border-white" 
                style={{ backgroundColor: item.color }}
              />
              <span>{item.label}</span>
            </div>
          ))}
          <p className="text-gray-500 text-xs mt-2 pt-1 border-t">
            ✅ Green = Safe | 🔴 Red = High Pollution
          </p>
        </div>
      </div>

      {/* Data count indicator */}
      <div className="absolute top-4 right-4 z-[1000] bg-white rounded-lg shadow-lg p-2">
        <p className="text-xs text-gray-600">
          🔥 {mapData.length.toLocaleString()} samples
        </p>
        <p className="text-xs text-blue-600 font-medium">
          {selectedYear ? `Year ${selectedYear}` : 'All Years'}
        </p>
      </div>
      </div>
    </div>
  );
};

export default HeatMap;