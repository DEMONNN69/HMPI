import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import Navigation from '../components/Navigation';
import { Loader2, Calculator, CheckCircle, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { 
  groundWaterSampleApi, 
  hmpiCalculationApi,
  type YearCalculationRequest,
  type YearCalculationResult 
} from '../lib/api';

export default function HMPICalculations() {
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [calculationResult, setCalculationResult] = useState<YearCalculationResult | null>(null);
  const { toast } = useToast();

  // Fetch available years from ground water samples
  const fetchAvailableYears = async () => {
    try {
      const data = await groundWaterSampleApi.getGroundWaterSamples();
      
      const samples = Array.isArray(data) ? data : data.results;
      const years = new Set<number>();
      
      samples.forEach((sample: any) => {
        // Use the year field directly if it exists
        if (sample.year && typeof sample.year === 'number') {
          years.add(sample.year);
        } else {
          // Fallback to date fields if year field doesn't exist
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
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch available years.",
        variant: "destructive",
      });
      console.error('Error fetching available years:', error);
    }
  };



  // Calculate HMPI for all samples from selected year
  const calculateByYear = async (forceRecalculate: boolean = false) => {
    setIsLoading(true);
    setCalculationResult(null);
    
    try {
      if (!selectedYear) {
        toast({
          title: "No Year Selected",
          description: "Please select a year before calculating HMPI.",
          variant: "destructive",
        });
        return;
      }

      const request: YearCalculationRequest = {
        year: selectedYear,
        sample_type: 'ground_water',
        force_recalculate: forceRecalculate
      };

      const result = await hmpiCalculationApi.calculateByYear(request);
      setCalculationResult(result);
      
      toast({
        title: "Year Calculation Complete",
        description: `Processed ${result.total_calculated} samples for year ${selectedYear}. Success rate: ${result.success_rate.toFixed(1)}%`,
      });
      

      
    } catch (error) {
      toast({
        title: "Calculation Error",
        description: error instanceof Error ? error.message : "Failed to calculate HMPI for year",
        variant: "destructive",
      });
      console.error('Error calculating HMPI by year:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchAvailableYears();
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Navigation />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">HMPI Calculations</h1>
          <p className="text-muted-foreground">
            Calculate Heavy Metal Pollution Index for ground water samples by year
          </p>
        </div>
        <Calculator className="h-8 w-8 text-blue-600" />
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Calculation Configuration</CardTitle>
          <CardDescription>
            Select the year for ground water HMPI calculations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Year Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Year for Ground Water HMPI Calculation</label>
            <Select 
              value={selectedYear?.toString() || ""} 
              onValueChange={(value) => setSelectedYear(parseInt(value))}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select year" />
              </SelectTrigger>
              <SelectContent>
                {availableYears.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button 
              onClick={() => calculateByYear(false)}
              disabled={isLoading || availableYears.length === 0 || !selectedYear}
              className="flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
              {selectedYear ? `Calculate HMPI for ${selectedYear}` : "Calculate HMPI"}
            </Button>
            
            <Button 
              variant="outline"
              onClick={() => calculateByYear(true)}
              disabled={isLoading || availableYears.length === 0 || !selectedYear}
              className="flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
              Force Recalculate
            </Button>
          </div>

          {availableYears.length === 0 && (
            <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
              <AlertCircle className="h-4 w-4 inline mr-2" />
              No ground water sample data available. Please check your database.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Calculation Status */}
      {calculationResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Calculation Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-4">
              <div className="text-lg font-medium text-green-600 mb-2">
                ✓ HMPI calculations completed for {calculationResult.year}
              </div>
              <div className="text-sm text-muted-foreground">
                {calculationResult.total_calculated} samples processed successfully
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}