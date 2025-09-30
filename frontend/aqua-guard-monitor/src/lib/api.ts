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
