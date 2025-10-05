import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { useAuth } from '@/lib/auth-context';
import 'leaflet/dist/leaflet.css';

interface MapDataPoint {
  id: number;
  latitude: number;
  longitude: number;
  hmpi_value: number;
  location_name?: string;
}

const getColorByHMPI = (hmpiValue: number): string => {
  if (hmpiValue < 25) return '#2E7D32';      // Excellent - Green
  if (hmpiValue < 50) return '#66BB6A';      // Good - Light Green
  if (hmpiValue < 75) return '#FFA726';      // Poor - Orange
  if (hmpiValue < 100) return '#FF5722';     // Very Poor - Red
  return '#D32F2F';                          // Unsuitable - Dark Red
};

const SimpleMap: React.FC = () => {
  const [mapData, setMapData] = useState<MapDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { tokens, isAuthenticated } = useAuth();

  const fetchMapData = async () => {
    if (!tokens?.access) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        'http://localhost:8000/api/v1/map-data/?page=1&limit=100&fields=basic', 
        {
          headers: {
            'Authorization': `Bearer ${tokens.access}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      const validData = result.data.filter(
        (point: MapDataPoint) => point.latitude && point.longitude && 
                !isNaN(point.latitude) && !isNaN(point.longitude)
      );
      
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
  }, [isAuthenticated, tokens?.access]);

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
        <p className="text-gray-600">Loading map data...</p>
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
          📍 {mapData.length} water quality samples
        </p>
      </div>
    </div>
  );
};

export default SimpleMap;