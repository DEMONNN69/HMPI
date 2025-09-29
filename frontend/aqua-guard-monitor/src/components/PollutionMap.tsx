import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Layers, Satellite, Navigation, Filter } from "lucide-react";

interface SampleData {
  sample_id: string;
  site_name: string;
  latitude: number;
  longitude: number;
  hpi: number;
  sample_date: string;
  dominant_metal: string;
  status: "excellent" | "good" | "poor" | "very-poor";
}

interface PollutionMapProps {
  samples?: SampleData[];
  center?: [number, number];
  zoom?: number;
  showHeatmap?: boolean;
}

const getStatusColor = (hpi: number) => {
  if (hpi < 25) return "excellent";
  if (hpi < 50) return "good";
  if (hpi < 75) return "poor";
  return "very-poor";
};

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "excellent": return "default";
    case "good": return "secondary";
    case "poor": return "destructive";
    case "very-poor": return "destructive";
    default: return "outline";
  }
};

// Professional mock data with realistic locations
const mockSamples: SampleData[] = [
  {
    sample_id: "ENV-2401-087",
    site_name: "Yamuna River Sampling Point A-12",
    latitude: 28.6519,
    longitude: 77.2315,
    hpi: 67.2,
    sample_date: "2024-01-14",
    dominant_metal: "Lead (Pb)",
    status: "poor"
  },
  {
    sample_id: "ENV-2401-092", 
    site_name: "Mumbai Coastal Monitoring Station B-7",
    latitude: 19.0825,
    longitude: 72.8231,
    hpi: 28.4,
    sample_date: "2024-01-14",
    dominant_metal: "Copper (Cu)",
    status: "good"
  },
  {
    sample_id: "ENV-2401-104",
    site_name: "Bengaluru Urban Lake Network C-3",
    latitude: 12.9352,
    longitude: 77.6245,
    hpi: 15.8,
    sample_date: "2024-01-13",
    dominant_metal: "Zinc (Zn)",
    status: "excellent"
  },
  {
    sample_id: "ENV-2401-118",
    site_name: "Kolkata Wetland Reserve D-15",
    latitude: 22.5354,
    longitude: 88.3644,
    hpi: 52.1,
    sample_date: "2024-01-13",
    dominant_metal: "Cadmium (Cd)",
    status: "poor"
  },
  {
    sample_id: "ENV-2401-125",
    site_name: "Chennai Metropolitan Water E-9",
    latitude: 13.0843,
    longitude: 80.2705,
    hpi: 31.7,
    sample_date: "2024-01-12",
    dominant_metal: "Mercury (Hg)",
    status: "good"
  }
];

export function PollutionMap({ 
  samples = mockSamples, 
  center = [20.5937, 78.9629], 
  zoom = 5,
  showHeatmap = true 
}: PollutionMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [selectedSample, setSelectedSample] = useState<SampleData | null>(samples[0]);
  const [mapType, setMapType] = useState<"terrain" | "satellite">("terrain");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    console.log("Professional map interface initialized with", samples.length, "monitoring points");
  }, [samples]);

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "excellent": return "Excellent";
      case "good": return "Good";
      case "poor": return "Fair";
      case "very-poor": return "Poor";
      default: return "Unknown";
    }
  };

  return (
    <Card className="col-span-full shadow-professional">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-heading flex items-center gap-3">
              <MapPin className="h-5 w-5 text-primary" />
              Geographic Distribution
            </CardTitle>
            <p className="text-caption mt-1">Real-time monitoring network overview</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters ? "default" : "outline"}
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="text-sm"
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
            <Button
              variant={mapType === "terrain" ? "default" : "outline"}
              size="sm"
              onClick={() => setMapType("terrain")}
              className="text-sm"
            >
              <Layers className="h-4 w-4 mr-2" />
              Terrain
            </Button>
            <Button
              variant={mapType === "satellite" ? "default" : "outline"}
              size="sm"
              onClick={() => setMapType("satellite")}
              className="text-sm"
            >
              <Satellite className="h-4 w-4 mr-2" />
              Satellite
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          {/* Professional Map Interface */}
          <div className="xl:col-span-3">
            <div 
              ref={mapRef}
              className="w-full h-[520px] bg-card border border-border/50 rounded-lg relative overflow-hidden shadow-sm"
              style={{
                backgroundImage: `
                  linear-gradient(45deg, hsl(var(--muted)) 25%, transparent 25%),
                  linear-gradient(-45deg, hsl(var(--muted)) 25%, transparent 25%),
                  linear-gradient(45deg, transparent 75%, hsl(var(--muted)) 75%),
                  linear-gradient(-45deg, transparent 75%, hsl(var(--muted)) 75%)
                `,
                backgroundSize: '20px 20px',
                backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px'
              }}
            >
              {/* Professional Map Placeholder */}
              <div className="absolute inset-0 bg-gradient-to-br from-muted/30 to-background/80">
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center max-w-md">
                    <Navigation className="h-12 w-12 text-primary mx-auto mb-4" />
                    <h3 className="text-heading text-foreground mb-2">
                      Interactive Monitoring Network
                    </h3>
                    <p className="text-body text-muted-foreground leading-relaxed">
                      Production deployment features real-time geographic visualization with Leaflet integration, 
                      heatmap overlays, and detailed site analysis capabilities.
                    </p>
                  </div>
                </div>
                
                {/* Sample Point Indicators */}
                <div className="absolute inset-8">
                  {samples.slice(0, 5).map((sample, index) => (
                    <button
                      key={sample.sample_id}
                      className={`absolute w-6 h-6 rounded-full border-2 border-background shadow-md cursor-pointer transition-all hover:scale-110 ${
                        selectedSample?.sample_id === sample.sample_id 
                          ? 'ring-2 ring-primary ring-offset-2 ring-offset-background scale-110' 
                          : ''
                      }`}
                      style={{
                        backgroundColor: `hsl(var(--${sample.status}))`,
                        left: `${15 + index * 18}%`,
                        top: `${25 + (index % 2) * 30}%`,
                      }}
                      onClick={() => setSelectedSample(sample)}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Site Details Panel */}
          <div className="space-y-4">
            <div>
              <h3 className="text-subheading mb-3">Monitoring Sites</h3>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {samples.map((sample) => (
                  <button
                    key={sample.sample_id}
                    className={`w-full p-4 rounded-lg border text-left transition-all hover:shadow-sm ${
                      selectedSample?.sample_id === sample.sample_id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border/50 hover:border-border'
                    }`}
                    onClick={() => setSelectedSample(sample)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-body font-medium truncate">
                          {sample.site_name}
                        </p>
                        <p className="text-caption text-muted-foreground">
                          ID: {sample.sample_id}
                        </p>
                      </div>
                      <Badge 
                        variant={getStatusBadgeVariant(sample.status)} 
                        className="ml-2 text-xs font-mono"
                      >
                        {sample.hpi}
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Status:</span>
                        <Badge variant="outline" className="text-xs">
                          {getStatusLabel(sample.status)}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Primary contaminant:</span>
                        <span className="font-mono">{sample.dominant_metal}</span>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Last sampled:</span>
                        <span className="font-mono">{sample.sample_date}</span>
                      </div>
                      
                      <div className="pt-2 border-t border-border/30">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Coordinates:</span>
                          <span className="font-mono">
                            {sample.latitude.toFixed(4)}, {sample.longitude.toFixed(4)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Statistics */}
            <div className="pt-4 border-t border-border/50">
              <h4 className="text-subheading mb-3">Network Summary</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="text-center p-3 bg-muted/30 rounded-lg">
                  <div className="stat-value text-lg">{samples.length}</div>
                  <div className="text-caption">Active Sites</div>
                </div>
                <div className="text-center p-3 bg-muted/30 rounded-lg">
                  <div className="stat-value text-lg">
                    {(samples.reduce((sum, s) => sum + s.hpi, 0) / samples.length).toFixed(1)}
                  </div>
                  <div className="text-caption">Avg. HPI</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}