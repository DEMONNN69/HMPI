import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatsCard } from "@/components/StatsCard";
import { QualityDistributionChart, HPIBarChart, HPITrendChart } from "@/components/charts/PollutionCharts";
import { PollutionMap } from "@/components/PollutionMap";
import { FileUpload } from "@/components/FileUpload";
import { Link } from "react-router-dom";
import { 
  Droplets, 
  TrendingUp, 
  AlertTriangle, 
  ShieldCheck,
  Upload,
  RefreshCw,
  Download,
  Settings,
  Bell,
  Activity,
  Database
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// Professional mock data with realistic values
const mockStats = {
  totalSamples: 3842,
  averageHPI: 34.7,
  contaminatedSites: 89,
  safeSites: 3198,
  lastUpdate: "2024-01-15 09:42"
};

const qualityData = [
  { name: "Excellent", value: 2156, color: "hsl(var(--excellent))" },
  { name: "Good", value: 1042, color: "hsl(var(--good))" },
  { name: "Fair", value: 455, color: "hsl(var(--poor))" },
  { name: "Poor", value: 189, color: "hsl(var(--very-poor))" }
];

const trendData = [
  { date: "Jan 8", average_hpi: 32.1, sample_count: 67 },
  { date: "Jan 9", average_hpi: 35.8, sample_count: 74 },
  { date: "Jan 10", average_hpi: 31.4, sample_count: 69 },
  { date: "Jan 11", average_hpi: 38.2, sample_count: 82 },
  { date: "Jan 12", average_hpi: 34.9, sample_count: 76 },
  { date: "Jan 13", average_hpi: 33.1, sample_count: 71 },
  { date: "Jan 14", average_hpi: 36.7, sample_count: 79 },
  { date: "Jan 15", average_hpi: 34.7, sample_count: 84 }
];

export function Dashboard() {
  const [showUpload, setShowUpload] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  const handleRefresh = async () => {
    setRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 1200));
    setRefreshing(false);
    
    toast({
      title: "System Updated",
      description: "Latest monitoring data synchronized from field stations.",
    });
  };

  const handleUploadComplete = (result: any) => {
    if (result.success) {
      toast({
        title: "Data Processing Complete",
        description: `Successfully integrated ${result.data.recordsProcessed} samples from ${result.data.filename}`,
      });
      setShowUpload(false);
    }
  };

  const getHPIStatus = (hpi: number) => {
    if (hpi < 25) return { status: "Excellent", variant: "excellent" as const };
    if (hpi < 50) return { status: "Good", variant: "good" as const };
    if (hpi < 75) return { status: "Fair", variant: "poor" as const };
    return { status: "Poor", variant: "very-poor" as const };
  };

  const hpiStatus = getHPIStatus(mockStats.averageHPI);

  return (
    <div className="min-h-screen bg-background">
      {/* Professional Header */}
      <header className="bg-card border-b border-border/50 shadow-professional">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-9 h-9 bg-primary rounded-lg">
                <Droplets className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-heading text-foreground">AQUA-GUARD</h1>
                <p className="text-caption">Environmental Monitoring Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-caption">
                <Activity className="h-3 w-3 text-excellent" />
                <span>Live Monitoring</span>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowUpload(!showUpload)}
                className="text-sm"
              >
                <Upload className="h-4 w-4 mr-2" />
                Import Data
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="text-sm"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                Sync
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                className="text-sm"
                asChild
              >
                <Link to="/ground-water-samples">
                  <Database className="h-4 w-4 mr-2" />
                  Water Samples
                </Link>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                className="text-sm"
              >
                <Bell className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        {/* Data Import Section */}
        {showUpload && (
          <div className="mb-8">
            <FileUpload onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Monitoring Points"
            value={mockStats.totalSamples.toLocaleString()}
            icon={Droplets}
            description="Active sample locations across network"
            change={{ value: "12.3%", positive: true }}
          />
          <StatsCard
            title="Heavy Metal Pollution Index"
            value={mockStats.averageHPI}
            icon={TrendingUp}
            variant={hpiStatus.variant}
            description={`Network average - ${hpiStatus.status} condition`}
            change={{ value: "2.1", positive: false }}
          />
          <StatsCard
            title="Attention Required"
            value={mockStats.contaminatedSites}
            icon={AlertTriangle}
            variant="poor"
            description="Sites exceeding threshold limits"
            change={{ value: "8", positive: false }}
          />
          <StatsCard
            title="Compliant Sites"
            value={mockStats.safeSites}
            icon={ShieldCheck}
            variant="excellent"
            description="Within regulatory parameters"
            change={{ value: "127", positive: true }}
          />
        </div>

        {/* Analytics Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <QualityDistributionChart data={qualityData} />
          <HPIBarChart data={qualityData} />
        </div>

        {/* Temporal Analysis */}
        <div className="mb-8">
          <HPITrendChart data={trendData} />
        </div>

        {/* Geographic Overview */}
        <PollutionMap />

        {/* System Information */}
        <div className="mt-8 pt-6 border-t border-border/50">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="space-y-1">
              <div className="text-body text-foreground">
                Last synchronized: {mockStats.lastUpdate} UTC
              </div>
              <div className="text-caption">
                Data source: National Environmental Monitoring Network • Quality assured dataset
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" className="text-sm">
                <Download className="h-4 w-4 mr-2" />
                Export Analysis
              </Button>
              <Button variant="outline" size="sm" className="text-sm">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}