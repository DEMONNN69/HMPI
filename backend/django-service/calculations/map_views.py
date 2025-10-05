# calculations/map_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from data_management.models import GroundWaterSample
from .models import ComputedIndex
from django.db.models import Count, Q, Avg
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

class MapDataPagination(PageNumberPagination):
    page_size = 500  # Default page size
    page_size_query_param = 'limit'
    max_page_size = 2000

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_map_data(request):
    """Optimized API endpoint for map visualization data"""
    
    # Get query parameters
    limit = int(request.GET.get('limit', 500))
    page = int(request.GET.get('page', 1))
    fields_param = request.GET.get('fields', 'basic')  # basic, full, minimal
    
    # Limit the maximum number of records
    limit = min(limit, 2000)
    
    # Base queryset - only essential fields for performance
    base_queryset = ComputedIndex.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        hpi_value__isnull=False
    ).order_by('-computed_at')
    
    # Select only needed fields based on request
    if fields_param == 'minimal':
        # Only coordinates and HMPI for initial load
        queryset = base_queryset.values(
            'id', 'latitude', 'longitude', 'hpi_value'
        )
    elif fields_param == 'basic':
        # Add location name for popups
        queryset = base_queryset.values(
            'id', 'latitude', 'longitude', 'hpi_value', 
            'location_name', 'quality_category'
        )
    else:  # full
        # All data for detailed view
        queryset = base_queryset.values(
            'id', 'latitude', 'longitude', 'hpi_value',
            'location_name', 'quality_category', 'state', 'district',
            'computed_at', 'calculation_year'
        )
    
    # Apply pagination
    paginator = Paginator(queryset, limit)
    page_obj = paginator.get_page(page)
    
    # Convert to list and format data
    map_data = []
    for item in page_obj.object_list:
        data_point = {
            'id': item['id'],
            'latitude': float(item['latitude']),
            'longitude': float(item['longitude']),
            'hmpi_value': float(item['hpi_value']),
        }
        
        # Add fields based on request type
        if fields_param != 'minimal':
            data_point.update({
                'location_name': item.get('location_name', f"Site {item['id']}"),
                'quality_category': item.get('quality_category', 'Unknown')
            })
            
        if fields_param == 'full':
            data_point.update({
                'state': item.get('state', 'Unknown'),
                'district': item.get('district', 'Unknown'),
                'sample_date': item['computed_at'].strftime('%Y-%m-%d') if item.get('computed_at') else 'Unknown',
                'calculation_year': item.get('calculation_year', 2024)
            })
        
        map_data.append(data_point)
    
    # Calculate statistics from current page data
    if map_data:
        total_samples = len(map_data)
        avg_hmpi = sum(point['hmpi_value'] for point in map_data) / total_samples
        
        # Quality distribution for current page
        quality_dist = {'excellent': 0, 'good': 0, 'poor': 0, 'very_poor': 0, 'unsuitable': 0}
        for point in map_data:
            hmpi = point['hmpi_value']
            if hmpi < 25:
                quality_dist['excellent'] += 1
            elif hmpi < 50:
                quality_dist['good'] += 1
            elif hmpi < 75:
                quality_dist['poor'] += 1
            elif hmpi < 100:
                quality_dist['very_poor'] += 1
            else:
                quality_dist['unsuitable'] += 1
    else:
        total_samples = 0
        avg_hmpi = 0
        quality_dist = {'excellent': 0, 'good': 0, 'poor': 0, 'very_poor': 0, 'unsuitable': 0}
                
    
    # Response with pagination info
    response_data = {
        'data': map_data,
        'stats': {
            'total_samples': total_samples,
            'average_hmpi': round(avg_hmpi, 2),
            'quality_distribution': quality_dist
        },
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_records': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_size': limit
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pollution_hotspots(request):
    """Get pollution hotspots (areas with HPI > 100)"""
    
    hotspots = ComputedIndex.objects.filter(
        hpi_value__gt=100,
        latitude__isnull=False,
        longitude__isnull=False
    ).order_by('-hpi_value')
    
    hotspot_data = []
    for hotspot in hotspots:
        hotspot_data.append({
            'id': hotspot.id,
            'latitude': float(hotspot.latitude),
            'longitude': float(hotspot.longitude),
            'location_name': hotspot.location_name,
            'state': hotspot.state,
            'district': hotspot.district,
            'hpi_value': float(hotspot.hpi_value),
            'quality_category': hotspot.get_quality_category_display(),
            'computed_at': hotspot.computed_at.isoformat(),
            'calculation_year': hotspot.calculation_year,
        })
    
    return Response({
        'hotspots': hotspot_data,
        'count': len(hotspot_data),
        'success': True
    })