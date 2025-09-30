from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator
from decimal import InvalidOperation
import logging
from .models import GroundWaterSample
from .serializers import GroundWaterSampleSerializer

logger = logging.getLogger(__name__)

class GroundWaterSampleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only ViewSet for displaying ground water samples.
    Supports flexible searching (state, district, location) and exact filtering (year).
    Includes error handling for problematic decimal records.
    """
    # Order by S.No for deterministic pagination
    queryset = GroundWaterSample.objects.all().order_by('s_no')
    serializer_class = GroundWaterSampleSerializer
    permission_classes = [AllowAny]
    
    # --- Filtering and Searching ---
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    # Fields available for exact filtering (e.g., ?year=2023)
    filterset_fields = ['year']
    
    # The 'search' parameter (e.g., ?search=Maharashtra) queries all these fields
    # across the WHOLE QUERYSET before pagination is applied.
    search_fields = ['state', 'district', 'location']
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to handle decimal conversion errors at record level
        """
        try:
            # Try normal list first
            return super().list(request, *args, **kwargs)
        except (InvalidOperation, Exception) as e:
            if "decimal.InvalidOperation" in str(e) or "InvalidOperation" in str(type(e).__name__):
                logger.warning(f"Decimal conversion error in pagination, switching to safe mode: {e}")
                return self._safe_paginated_list(request)
            else:
                # Re-raise if it's not a decimal error
                raise
    
    def _safe_paginated_list(self, request):
        """
        Safe pagination that skips problematic records one by one
        """
        # Get filtered queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get page parameters
        page_size = int(request.query_params.get('page_size', 100))
        page_number = int(request.query_params.get('page', 1))
        
        # Calculate offset
        offset = (page_number - 1) * page_size
        
        valid_records = []
        skipped_count = 0
        current_offset = offset
        
        # Try to collect page_size valid records
        while len(valid_records) < page_size and current_offset < queryset.count():
            try:
                # Get next batch to try (get more to account for skipped records)
                batch_size = min(page_size * 2, queryset.count() - current_offset)
                batch = list(queryset[current_offset:current_offset + batch_size])
                
                for record in batch:
                    if len(valid_records) >= page_size:
                        break
                    try:
                        # Try to access decimal fields to trigger any conversion errors
                        _ = record.longitude
                        _ = record.latitude  
                        _ = record.ph
                        _ = record.ec_us_cm
                        valid_records.append(record)
                    except (InvalidOperation, Exception) as e:
                        logger.warning(f"Skipping problematic record s_no={record.s_no}: {e}")
                        skipped_count += 1
                        continue
                
                current_offset += batch_size
                
            except (InvalidOperation, Exception) as e:
                logger.warning(f"Skipping batch at offset {current_offset}: {e}")
                current_offset += 1
                skipped_count += 1
        
        # Serialize valid records
        serializer = self.get_serializer(valid_records, many=True)
        
        # Create pagination-like response
        total_count = max(0, queryset.count() - skipped_count)  # Approximate
        has_next = current_offset < queryset.count()
        has_previous = page_number > 1
        
        response_data = {
            'count': total_count,
            'next': f"?page={page_number + 1}&page_size={page_size}" if has_next else None,
            'previous': f"?page={page_number - 1}&page_size={page_size}" if has_previous else None,
            'results': serializer.data,
            'skipped_records': skipped_count
        }
        
        if skipped_count > 0:
            logger.info(f"Page {page_number}: Returned {len(valid_records)} valid records, skipped {skipped_count} problematic records")
        
        return Response(response_data)
