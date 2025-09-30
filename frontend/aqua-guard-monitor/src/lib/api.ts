import axios from 'axios';

// Use environment variable for API base path, defaulting to localhost
// This matches the Django API prefix: /api/v1
const API_BASE_URL = import.meta.env.VITE_DJANGO_API_BASE ?? 'http://localhost:8000/api/v1';

// --- Authenticated Axios Instance ---
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

// Request Interceptor: Attach the JWT token to every outgoing request
axiosInstance.interceptors.request.use(
  (config) => {
    // Retrieve tokens from localStorage using the same key as AuthProvider
    const tokensRaw = localStorage.getItem('auth_tokens');
    if (tokensRaw) {
      try {
        const tokens = JSON.parse(tokensRaw);
        if (tokens.access) {
          // Standard JWT format: "Bearer <token>"
          config.headers.Authorization = `Bearer ${tokens.access}`;
        }
      } catch (e) {
        console.error("Failed to parse auth tokens from localStorage:", e);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);
// --- End Authenticated Axios Instance ---


// Ground Water Sample interface (Updated to match full Django model)
export interface GroundWaterSample {
  id: number;
  s_no: number;
  state: string;
  district: string;
  location: string;
  longitude: number; // DecimalField serialized as number/string
  latitude: number;
  year: number;
  ph: number | null;
  ec_us_cm: number | null;
  co3_mg_l: number | null;
  hco3_mg_l: number | null;
  cl_mg_l: number | null;
  f_mg_l: number | null;
  so4_mg_l: number | null; // Added
  no3_mg_l: number | null; // Added
  po4_mg_l: number | null; // Added
  total_hardness_mg_l: number | null;
  ca_mg_l: number | null; // Added
  mg_mg_l: number | null; // Added
  na_mg_l: number | null; // Added
  k_mg_l: number | null; // Added
  fe_ppm: number | null;
  as_ppb: number | null;
  u_ppb: number | null;
  created_at: string;
  updated_at: string;
}

// Pagination interface (Structure remains the same)
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// FIX: Updated Filter parameters interface to use 'search' for text fields
export interface GroundWaterSampleFilters {
  search?: string; // Used by DRF SearchFilter (replaces state/district/location)
  year?: number; // Used by DRF DjangoFilterBackend (exact match)
  page?: number;
  page_size?: number;
}

// API service for ground water samples
export const groundWaterSampleApi = {
  // Get all ground water samples with optional filtering and pagination
  getGroundWaterSamples: async (filters: GroundWaterSampleFilters = {}): Promise<PaginatedResponse<GroundWaterSample>> => {
    try {
      // Use the authenticated axiosInstance and the correct DRF slug
      const response = await axiosInstance.get(`/ground-water-samples/`, { 
        params: filters
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching ground water samples:', error);
      throw error;
    }
  },

  // Get a single ground water sample by ID
  getGroundWaterSample: async (id: number): Promise<GroundWaterSample> => {
    try {
      const response = await axiosInstance.get(`/ground-water-samples/${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching ground water sample with ID ${id}:`, error);
      throw error;
    }
  },
};

// HMPI Calculation interfaces
export interface ComputedIndex {
  id: number;
  hpi_value: number;
  hei_value?: number;
  cd_value?: number;
  mi_value?: number;
  quality_category: string;
  computed_at: string;
  sample_display: string;
  computation_method?: string;
  computed_by?: string;
}

export interface CalculationRequest {
  sample_type: 'water_sample' | 'ground_water';
  sample_id: number;
  force_recalculate?: boolean;
}

export interface BatchCalculationRequest {
  sample_type: 'water_sample' | 'ground_water';
  sample_ids: number[];
  force_recalculate?: boolean;
}

export interface YearCalculationRequest {
  year: number;
  sample_type: 'water_sample' | 'ground_water';
  force_recalculate?: boolean;
}

export interface YearCalculationResult {
  message: string;
  year: number;
  sample_type: string;
  total_calculated: number;
  total_stored: number;
  total_failed_calculation: number;
  total_failed_storage: number;
  stored_indices: number[];
  failed_calculations: Array<{
    sample_id: string;
    error: string;
  }>;
  failed_storage: Array<{
    sample_id: string;
    error: string;
  }>;
  success_rate: number;
}

export interface CalculationResult {
  message: string;
  computed_index: ComputedIndex;
}

export interface BatchCalculationResult {
  batch_id: string;
  status: string;
  total_samples: number;
  processed_samples: number;
  failed_samples: number;
  results: Array<{
    sample_id: number;
    status: string;
    computed_index_id?: number;
    error?: string;
  }>;
}

export interface YearCalculationResult {
  message: string;
  year: number;
  sample_type: string;
  total_calculated: number;
  total_stored: number;
  total_failed_calculation: number;
  total_failed_storage: number;
  stored_indices: number[];
  failed_calculations: Array<{
    sample_id: string;
    error: string;
  }>;
  failed_storage: Array<{
    sample_id: string;
    error: string;
  }>;
  success_rate: number;
}

// API service for HMPI calculations
export const hmpiCalculationApi = {
  // Get all computed indices
  getComputedIndices: async (): Promise<PaginatedResponse<ComputedIndex>> => {
    try {
      const response = await axiosInstance.get('/computed-indices/');
      return response.data;
    } catch (error) {
      console.error('Error fetching computed indices:', error);
      throw error;
    }
  },

  // Calculate HMPI for a single sample
  calculateSingle: async (request: CalculationRequest): Promise<CalculationResult> => {
    try {
      const response = await axiosInstance.post('/computed-indices/calculate_single/', request);
      return response.data;
    } catch (error) {
      console.error('Error calculating single HMPI:', error);
      throw error;
    }
  },

  // Calculate HMPI for multiple samples
  calculateBatch: async (request: BatchCalculationRequest): Promise<BatchCalculationResult> => {
    try {
      const response = await axiosInstance.post('/computed-indices/calculate_batch/', request);
      return response.data;
    } catch (error) {
      console.error('Error calculating batch HMPI:', error);
      throw error;
    }
  },

  // Get calculation batch status
  getBatchStatus: async (batchId: string) => {
    try {
      const response = await axiosInstance.get(`/calculation-batches/?batch_id=${batchId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching batch status:', error);
      throw error;
    }
  },

  // Calculate HMPI for all samples from a specific year
  calculateByYear: async (request: YearCalculationRequest): Promise<YearCalculationResult> => {
    try {
      const response = await axiosInstance.post('/computed-indices/calculate_by_year/', request);
      return response.data;
    } catch (error) {
      console.error('Error calculating HMPI by year:', error);
      throw error;
    }
  },
};
