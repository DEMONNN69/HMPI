import React, { useState, useEffect } from 'react';
// FIX: Using relative imports for robustness
import { GroundWaterSample, GroundWaterSampleFilters, groundWaterSampleApi } from '../lib/api'; 
import { GroundWaterSamplesTable } from '../components/GroundWaterSamplesTable';
import Navigation from '../components/Navigation';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'; 
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '../components/ui/pagination';

export default function GroundWaterSamples() {
  const [samples, setSamples] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  
  // FIX: Filters now include only 'search' (for state/district/location) and 'year'
  const [filters, setFilters] = useState({
    search: '', // Matches Django SearchFilter
    year: undefined,
    page: 1,
    page_size: 10
  });
  
  // State to hold the temporary search input value
  const [searchTerm, setSearchTerm] = useState('');


  // Fetch ground water samples with current filters
  const fetchSamples = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await groundWaterSampleApi.getGroundWaterSamples({
        ...filters,
        page: currentPage
      });
      setSamples(response.results);
      setTotalCount(response.count);
    } catch (err) {
      setError('Failed to fetch ground water samples. Please try again later.');
      console.error('Error fetching samples:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial fetch on component mount and whenever page or committed search filter changes
  useEffect(() => {
    fetchSamples();
  }, [currentPage, filters.search, filters.year]); // Depend on committed filters

  // Handle filter changes (only for non-search fields like year)
  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle the single search input change
  const handleSearchChange = (value) => {
    setSearchTerm(value);
  };
  
  // Apply filters (Commit search term to filter state and reset page)
  const applyFilters = () => {
    setFilters(prev => ({
        ...prev,
        search: searchTerm, // Commit the input value to the filter state
    }));
    setCurrentPage(1); // Reset to first page when applying new filters
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      search: '',
      year: undefined,
      page: 1,
      page_size: pageSize
    });
    setSearchTerm('');
    setCurrentPage(1);
  };

  // Calculate total pages
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <Navigation />
      <Card className="rounded-xl shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-gray-800">Ground Water Samples Database</CardTitle>
          <CardDescription>
            View and filter ground water samples collected across different locations ({totalCount} total records)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 rounded-lg bg-gray-50 border">
            
            {/* Combined Search Box */}
            <div className="col-span-2 md:col-span-2">
              <label className="text-sm font-medium text-gray-600">State / District / Location Search</label>
              <Input
                placeholder="Search across State, District, or Location"
                value={searchTerm || ''}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="mt-1"
              />
            </div>
            
            {/* Year Filter */}
            <div>
              <label className="text-sm font-medium text-gray-600">Year (Filter)</label>
              <Input
                type="number"
                placeholder="Filter by year (e.g., 2023)"
                value={filters.year || ''}
                onChange={(e) => handleFilterChange('year', e.target.value ? parseInt(e.target.value) : undefined)}
                className="mt-1"
              />
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-end space-x-2">
              <Button onClick={applyFilters} className="shadow-md rounded-md">
                Apply Filters
              </Button>
              <Button variant="outline" onClick={resetFilters} className="rounded-md">
                Reset
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" role="alert">
              {error}
            </div>
          )}

          <GroundWaterSamplesTable samples={samples} isLoading={isLoading} />

          {!isLoading && totalPages > 1 && (
            <div className="mt-6 flex justify-center">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious 
                      onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                      aria-disabled={currentPage === 1}
                      className={currentPage === 1 ? "pointer-events-none opacity-50" : "hover:bg-gray-100"}
                    />
                  </PaginationItem>
                  
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5 || currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <PaginationItem key={pageNum}>
                        <PaginationLink
                          isActive={currentPage === pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                        >
                          {pageNum}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  })}
                  
                  <PaginationItem>
                    <PaginationNext 
                      onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                      aria-disabled={currentPage === totalPages}
                      className={currentPage === totalPages ? "pointer-events-none opacity-50" : "hover:bg-gray-100"}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
