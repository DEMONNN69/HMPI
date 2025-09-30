from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import GroundWaterSample
from .serializers import GroundWaterSampleSerializer

class GroundWaterSampleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only ViewSet for displaying ground water samples.
    Supports flexible searching (state, district, location) and exact filtering (year).
    """
    # Order by S.No for deterministic pagination
    queryset = GroundWaterSample.objects.all().order_by('s_no')
    serializer_class = GroundWaterSampleSerializer
    
    # --- Filtering and Searching ---
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    # Fields available for exact filtering (e.g., ?year=2023)
    filterset_fields = ['year']
    
    # The 'search' parameter (e.g., ?search=Maharashtra) queries all these fields
    # across the WHOLE QUERYSET before pagination is applied.
    search_fields = ['state', 'district', 'location']
