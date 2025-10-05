import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { StatsCard } from '@/components/StatsCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { 
  Droplets, 
  TrendingUp, 
  MapPin, 
  BarChart3,
  Loader2,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';

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

interface MapDataPoint {
  id: number;
  latitude: number;
  longitude: number;
  hmpi_value: number;
  quality_category: string;
  location_name: string;
  sample_date: string;
}

interface DashboardData {
  data: MapDataPoint[];
  stats: MapStats;
}

// Color schemes matching existing theme
const QUALITY_COLORS = {
  'Excellent': 'hsl(var(--excellent))',
  'Good': 'hsl(var(--good))', 
  'Poor': 'hsl(var(--poor))',
  'Very Poor': 'hsl(var(--very-poor))',
  'Unsuitable': 'hsl(var(--destructive))'
};

const Dashboard: React.FC = () => {
  const { tokens, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tokens?.access) {
      fetchDashboardData();
    }
  }, [tokens]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!tokens?.access) {
        throw new Error('No access token available');
      }
      
      const response = await fetch('http://localhost:8000/api/v1/map-data/', {
        headers: {
          'Authorization': `Bearer ${tokens.access}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setDashboardData(result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Prepare data for charts using existing structure
  const prepareQualityDistributionData = () => {
    if (!dashboardData?.stats.quality_distribution) return [];
    
    return Object.entries(dashboardData.stats.quality_distribution).map(([key, value]) => ({
      name: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
      value: value,
      color: QUALITY_COLORS[key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ') as keyof typeof QUALITY_COLORS]
    }));
  };

  const prepareHMPIRangeData = () => {
    if (!dashboardData?.data) return [];
    
    const ranges = [
      { name: '0-25\n(Excellent)', min: 0, max: 25, count: 0, color: QUALITY_COLORS.Excellent },
      { name: '25-50\n(Good)', min: 25, max: 50, count: 0, color: QUALITY_COLORS.Good },
      { name: '50-75\n(Poor)', min: 50, max: 75, count: 0, color: QUALITY_COLORS.Poor },
      { name: '75-100\n(Very Poor)', min: 75, max: 100, count: 0, color: QUALITY_COLORS['Very Poor'] },
      { name: '100+\n(Unsuitable)', min: 100, max: Infinity, count: 0, color: QUALITY_COLORS.Unsuitable },
    ];

    dashboardData.data.forEach((point: MapDataPoint) => {
      const range = ranges.find(r => point.hmpi_value >= r.min && point.hmpi_value < r.max);
      if (range) range.count++;
    });

    return ranges;
  };

  const getQualityCompliance = () => {
    if (!dashboardData?.stats.quality_distribution) return 0;
    const { excellent, good, poor, very_poor, unsuitable } = dashboardData.stats.quality_distribution;
    const total = excellent + good + poor + very_poor + (unsuitable || 0);
    return total > 0 ? Math.round(((excellent + good) / total) * 100) : 0;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Button variant="outline" onClick={() => logout()}>Logout</Button>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="pb-3">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-4 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Water Quality Dashboard</h1>
          <Button variant="outline" onClick={() => logout()}>Logout</Button>
        </div>
        
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>Error Loading Dashboard: {error}</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchDashboardData}
              className="ml-4"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Water Quality Dashboard</h1>
        </div>
        
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>No data available for dashboard</AlertDescription>
        </Alert>
      </div>
    );
  }

  const qualityData = prepareQualityDistributionData();
  const hmpiRangeData = prepareHMPIRangeData();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Water Quality Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and analyze water quality indices across monitoring locations
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchDashboardData}
            disabled={loading}
          >
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Performance Indicators using existing StatsCard */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Water Samples"
          value={dashboardData.stats.total_samples}
          icon={Droplets}
          variant="default"
          description="Active monitoring locations"
        />
        
        <StatsCard
          title="Average HMPI Score"
          value={dashboardData.stats.average_hmpi.toFixed(1)}
          icon={BarChart3}
          variant={dashboardData.stats.average_hmpi < 25 ? "excellent" : 
                   dashboardData.stats.average_hmpi < 50 ? "good" :
                   dashboardData.stats.average_hmpi < 75 ? "poor" : "very-poor"}
          description="Heavy Metal Pollution Index"
        />
        
        <StatsCard
          title="Monitoring Locations"
          value={new Set(dashboardData.data.map((d: MapDataPoint) => d.location_name)).size}
          icon={MapPin}
          variant="default"
          description="Unique sampling sites"
        />
        
        <StatsCard
          title="Quality Compliance"
          value={`${getQualityCompliance()}%`}
          icon={TrendingUp}
          variant={getQualityCompliance() >= 75 ? "excellent" : 
                   getQualityCompliance() >= 50 ? "good" :
                   getQualityCompliance() >= 25 ? "poor" : "very-poor"}
          description="Excellent + Good quality samples"
        />
      </div>

      {/* Charts and Analysis using Tabs */}
      <Tabs defaultValue="distribution" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="distribution">Quality Distribution</TabsTrigger>
          <TabsTrigger value="ranges">HMPI Ranges</TabsTrigger>
          <TabsTrigger value="breakdown">Detailed Breakdown</TabsTrigger>
        </TabsList>

        <TabsContent value="distribution" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Water Quality Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ChartContainer config={{}} className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={qualityData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }: { name: string; percent: number }) => 
                          `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {qualityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quality Categories</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(dashboardData.stats.quality_distribution).map(([key, value]) => {
                  const categoryName = key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ');
                  const numericValue = typeof value === 'number' ? value : 0;
                  const percentage = (numericValue / dashboardData.stats.total_samples) * 100;
                  
                  return (
                    <div key={key} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: QUALITY_COLORS[categoryName as keyof typeof QUALITY_COLORS] }}
                        />
                        <span className="font-medium">{categoryName}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">
                          {numericValue} samples
                        </span>
                        <Badge variant="outline">
                          {percentage.toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ranges" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HMPI Score Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={{}} className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hmpiRangeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="count" fill="hsl(var(--primary))" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="breakdown" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Quality Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {Object.entries(dashboardData.stats.quality_distribution).map(([key, value]) => {
                  const categoryName = key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ');
                  const numericValue = typeof value === 'number' ? value : 0;
                  const percentage = (numericValue / dashboardData.stats.total_samples) * 100;
                  
                  return (
                    <StatsCard
                      key={key}
                      title={categoryName}
                      value={numericValue}
                      variant={key as any}
                      description={`${percentage.toFixed(1)}% of total samples`}
                    />
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;