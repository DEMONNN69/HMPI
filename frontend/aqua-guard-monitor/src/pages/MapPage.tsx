import { useState } from 'react';
import SimpleMap from '../components/SimpleMap';
import HeatMap from '../components/HeatMap';
import Navigation from '../components/Navigation';
import { useAuth } from '../lib/auth-context';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { 
  Map, 
  Globe, 
  Layers, 
  Flame,
  MapPin,
  Activity,
  Shield,
  AlertTriangle
} from 'lucide-react';

type MapType = 'interactive' | 'heatmap';

const MapPage = () => {
  const { isAuthenticated, tokens } = useAuth();
  const [selectedMapType, setSelectedMapType] = useState<MapType>('interactive');
  const [selectedYear, setSelectedYear] = useState<number | null>(null);

  const mapTypes = [
    {
      id: 'interactive' as MapType,
      name: 'Interactive Map',
      description: 'Real-time data with clustering and popups',
      icon: Map,
      component: <SimpleMap selectedYear={selectedYear} onYearChange={setSelectedYear} />
    },
    {
      id: 'heatmap' as MapType,
      name: 'Heat Map',
      description: 'Density visualization of water quality data',
      icon: Flame,
      component: <HeatMap selectedYear={selectedYear} onYearChange={setSelectedYear} />
    }
  ];

  const currentMap = mapTypes.find(map => map.id === selectedMapType);

  return (
    <div className="p-4 space-y-4">
      <Navigation />
      
      {/* Authentication Status */}
      {isAuthenticated ? (
        <Alert className="border-green-200 bg-green-50">
          <Shield className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>Authenticated</strong> - You can access all map features and real-time water quality data.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            <strong>Authentication Required</strong> - Please log in to access interactive map features with real-time data.
          </AlertDescription>
        </Alert>
      )}
      
      {/* Map Type Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Map Visualization Types
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mapTypes.map((mapType) => {
              const Icon = mapType.icon;
              const isActive = selectedMapType === mapType.id;
              
              return (
                <Button
                  key={mapType.id}
                  variant={isActive ? "default" : "outline"}
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => setSelectedMapType(mapType.id)}
                >
                  <Icon className="h-6 w-6" />
                  <div className="text-center">
                    <div className="font-semibold">{mapType.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {mapType.description}
                    </div>
                  </div>
                  {isActive && (
                    <Badge variant="secondary" className="mt-1">
                      Active
                    </Badge>
                  )}
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Current Map Display */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {currentMap && <currentMap.icon className="h-5 w-5" />}
            {currentMap?.name} - Water Quality Monitoring
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="min-h-[600px]">
            {currentMap?.component}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MapPage;