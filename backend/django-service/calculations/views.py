import requests
import uuid
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from .models import ComputedIndex, CalculationBatch

# Simple inline serializers
class ComputedIndexSerializer(serializers.ModelSerializer):
    sample_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ComputedIndex
        fields = '__all__'
    
    def get_sample_display(self, obj):
        if hasattr(obj.sample, 's_no'):
            return f"Sample {obj.sample.s_no}"
        elif hasattr(obj.sample, 'sample_id'):
            return f"Sample {obj.sample.sample_id}"
        return f"Sample ID {obj.object_id}"
from data_management.models import GroundWaterSample
from samples.models import WaterSample

# FastAPI service URL
FASTAPI_BASE_URL = "http://localhost:8001"

class ComputedIndexViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing computed indices.
    Integrates with FastAPI service for calculations.
    """
    queryset = ComputedIndex.objects.all().order_by('-computed_at')
    serializer_class = ComputedIndexSerializer
    
    @action(detail=False, methods=['post'])
    def calculate_single(self, request):
        """
        Calculate indices for a single sample using FastAPI service
        """
        # Simple validation
        sample_type = request.data.get('sample_type', 'water_sample')
        sample_id = request.data.get('sample_id')
        force_recalculate = request.data.get('force_recalculate', False)
        
        if not sample_id:
            return Response({'error': 'sample_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the sample
            if sample_type == 'ground_water':
                sample = GroundWaterSample.objects.get(id=sample_id)
                content_type = ContentType.objects.get_for_model(GroundWaterSample)
                sample_data = self._prepare_ground_water_data(sample)
            else:
                sample = WaterSample.objects.get(id=sample_id)
                content_type = ContentType.objects.get_for_model(WaterSample)
                sample_data = self._prepare_water_sample_data(sample)
            
            # Check if calculation already exists
            existing = ComputedIndex.objects.filter(
                content_type=content_type,
                object_id=sample_id
            ).first()
            
            if existing and not force_recalculate:
                return Response({
                    'message': 'Calculation already exists',
                    'computed_index': ComputedIndexSerializer(existing).data
                })
            
            # Call FastAPI for calculation
            calculation_result = self._call_fastapi_calculation(sample_data)
            
            if not calculation_result['success']:
                return Response({
                    'error': calculation_result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Store results in Django
            computed_index = self._store_calculation_result(
                content_type, sample_id, calculation_result['data'], existing
            )
            
            return Response({
                'message': 'Calculation completed successfully',
                'computed_index': ComputedIndexSerializer(computed_index).data
            })
            
        except (GroundWaterSample.DoesNotExist, WaterSample.DoesNotExist):
            return Response({
                'error': 'Sample not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def calculate_batch(self, request):
        """
        Calculate indices for multiple samples using FastAPI service
        """
        # Simple validation
        sample_type = request.data.get('sample_type', 'water_sample')
        sample_ids = request.data.get('sample_ids', [])
        force_recalculate = request.data.get('force_recalculate', False)
        
        if not sample_ids:
            return Response({'error': 'sample_ids is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create batch tracking record
        batch = CalculationBatch.objects.create(
            batch_id=f"{sample_type}_{len(sample_ids)}_{self._generate_batch_id()}",
            total_samples=len(sample_ids),
            status='processing'
        )
        
        try:
            results = []
            for sample_id in sample_ids:
                try:
                    # Process each sample
                    if sample_type == 'ground_water':
                        sample = GroundWaterSample.objects.get(id=sample_id)
                        content_type = ContentType.objects.get_for_model(GroundWaterSample)
                        sample_data = self._prepare_ground_water_data(sample)
                    else:
                        sample = WaterSample.objects.get(id=sample_id)
                        content_type = ContentType.objects.get_for_model(WaterSample)
                        sample_data = self._prepare_water_sample_data(sample)
                    
                    # Check existing calculation
                    existing = ComputedIndex.objects.filter(
                        content_type=content_type,
                        object_id=sample_id
                    ).first()
                    
                    if existing and not force_recalculate:
                        results.append({
                            'sample_id': sample_id,
                            'status': 'skipped',
                            'message': 'Already calculated'
                        })
                        batch.processed_samples += 1
                        continue
                    
                    # Calculate via FastAPI
                    calculation_result = self._call_fastapi_calculation(sample_data)
                    
                    if calculation_result['success']:
                        computed_index = self._store_calculation_result(
                            content_type, sample_id, calculation_result['data'], existing
                        )
                        results.append({
                            'sample_id': sample_id,
                            'status': 'success',
                            'computed_index_id': computed_index.id
                        })
                        batch.processed_samples += 1
                    else:
                        results.append({
                            'sample_id': sample_id,
                            'status': 'failed',
                            'error': calculation_result['error']
                        })
                        batch.failed_samples += 1
                        
                except Exception as e:
                    results.append({
                        'sample_id': sample_id,
                        'status': 'failed',
                        'error': str(e)
                    })
                    batch.failed_samples += 1
            
            # Update batch status
            batch.status = 'completed'
            batch.save()
            
            return Response({
                'batch_id': batch.batch_id,
                'status': 'completed',
                'total_samples': batch.total_samples,
                'processed_samples': batch.processed_samples,
                'failed_samples': batch.failed_samples,
                'results': results
            })
            
        except Exception as e:
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
            
            return Response({
                'error': str(e),
                'batch_id': batch.batch_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _prepare_ground_water_data(self, sample):
        """Prepare ground water sample data for FastAPI calculation"""
        return {
            'sample_id': str(sample.s_no),
            'arsenic': float(sample.as_ppb or 0) / 1000,  # Convert ppb to mg/L
            'lead': 0,  # Not available in ground water model
            'cadmium': 0,  # Not available
            'chromium': 0,  # Not available
            'mercury': 0,  # Not available
            'iron': float(sample.fe_ppm or 0),  # ppm to mg/L
            'zinc': 0,  # Not available
            'copper': 0,  # Not available
        }
    
    def _prepare_water_sample_data(self, sample):
        """Prepare water sample data for FastAPI calculation"""
        return {
            'sample_id': sample.sample_id,
            'arsenic': float(sample.arsenic or 0),
            'lead': float(sample.lead or 0),
            'cadmium': float(sample.cadmium or 0),
            'chromium': float(sample.chromium or 0),
            'mercury': 0,  # Not available in water sample model
            'iron': 0,  # Not available
            'zinc': 0,  # Not available
            'copper': 0,  # Not available
        }
    
    def _call_fastapi_calculation(self, sample_data):
        """Call FastAPI service for calculation"""
        try:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/api/v1/calculations/single",
                json=sample_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"FastAPI returned {response.status_code}: {response.text}"
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Failed to connect to FastAPI service: {str(e)}"
            }
    
    def _store_calculation_result(self, content_type, object_id, calculation_data, existing=None):
        """Store calculation result in Django database"""
        data = {
            'content_type': content_type,
            'object_id': object_id,
            'hpi_value': calculation_data['hpi_value'],
            'hei_value': calculation_data.get('hei_value'),
            'cd_value': calculation_data.get('cd_value'),
            'mi_value': calculation_data.get('mi_value'),
            'quality_category': calculation_data['quality_category'],
            'calculation_method': calculation_data.get('calculation_method', 'WHO_2011'),
            'computed_by': 'FastAPI_HPICalculator',
            'notes': calculation_data.get('notes', '')
        }
        
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            existing.save()
            return existing
        else:
            return ComputedIndex.objects.create(**data)
    
    def _generate_batch_id(self):
        """Generate unique batch ID"""
        return str(uuid.uuid4())[:8]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def bulk_create(self, request):
        """
        Bulk create computed indices from FastAPI results
        
        Request body:
        {
            "results": [
                {
                    "sample_pk": 123,
                    "sample_type": "ground_water",
                    "hpi_value": 45.2,
                    "hei_value": 32.1,
                    "cd_value": 2.1,
                    "mi_value": 1.8,
                    "quality_category": "good",
                    "calculation_method": "WHO_2011",
                    "calculation_year": 2023,
                    "location_name": "Sample Location",
                    "latitude": 12.345,
                    "longitude": 67.890,
                    "state": "State Name",
                    "district": "District Name",
                    "notes": "Bulk calculation"
                }
            ]
        }
        """
        from django.db import transaction
        
        results = request.data.get('results', [])
        if not results:
            return Response({'error': 'No results provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                created_instances = []
                
                for result_data in results:
                    sample_pk = result_data.get('sample_pk')
                    sample_type = result_data.get('sample_type', 'ground_water')
                    
                    if not sample_pk:
                        continue
                    
                    # Get content type
                    if sample_type == 'ground_water':
                        content_type = ContentType.objects.get_for_model(GroundWaterSample)
                    else:
                        content_type = ContentType.objects.get_for_model(WaterSample)
                    
                    # Create ComputedIndex instance
                    instance_data = {
                        'content_type': content_type,
                        'object_id': sample_pk,
                        'hpi_value': result_data.get('hpi_value'),
                        'hei_value': result_data.get('hei_value'),
                        'cd_value': result_data.get('cd_value'),
                        'mi_value': result_data.get('mi_value'),
                        'quality_category': result_data.get('quality_category'),
                        'calculation_method': result_data.get('calculation_method', 'WHO_2011'),
                        'computed_by': 'FastAPI_HPICalculator_Bulk',
                        'notes': result_data.get('notes', ''),
                        'calculation_year': result_data.get('calculation_year'),
                        'location_name': result_data.get('location_name'),
                        'latitude': result_data.get('latitude'),
                        'longitude': result_data.get('longitude'),
                        'state': result_data.get('state'),
                        'district': result_data.get('district')
                    }
                    
                    created_instances.append(ComputedIndex(**instance_data))
                
                # Bulk create all instances
                ComputedIndex.objects.bulk_create(created_instances, ignore_conflicts=True)
                
                return Response({
                    'status': 'success',
                    'created': len(created_instances),
                    'message': f'Successfully created {len(created_instances)} computed indices'
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Bulk creation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def calculate_by_year(self, request):
        """
        Calculate HMPI indices for all samples from a specific year.
        
        Request body:
        {
            "year": 2023,
            "sample_type": "water_sample" or "ground_water",
            "force_recalculate": false
        }
        """
        year = request.data.get('year')
        sample_type = request.data.get('sample_type', 'water_sample')
        force_recalculate = request.data.get('force_recalculate', False)
        
        if not year:
            return Response({'error': 'year is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Call FastAPI to calculate for the entire year
            fastapi_url = f"{settings.FASTAPI_BASE_URL}/api/v1/calculations/calculate-by-year"
            payload = {
                "year": year,
                "sample_type": sample_type,
                "force_recalculate": force_recalculate
            }
            
            response = requests.post(fastapi_url, json=payload)
            
            if response.status_code == 200:
                calculation_data = response.json()
                
                # Prepare bulk data for storage
                bulk_results = []
                for calc_result in calculation_data.get('calculated_indices', []):
                    try:
                        # Add sample_type and calculation_year to each result
                        calc_result['sample_type'] = sample_type
                        calc_result['calculation_year'] = year
                        bulk_results.append(calc_result)
                    except Exception as e:
                        print(f"Error preparing result for bulk storage: {e}")
                
                # Use bulk_create endpoint for efficient storage
                if bulk_results:
                    try:
                        bulk_response = requests.post(
                            f"http://localhost:8000/api/v1/computed-indices/bulk_create/",
                            json={'results': bulk_results},
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if bulk_response.status_code == 201:
                            bulk_data = bulk_response.json()
                            stored_count = bulk_data.get('created', 0)
                            stored_indices = list(range(1, stored_count + 1))  # Placeholder IDs
                            failed_storage = []
                        else:
                            stored_indices = []
                            failed_storage = [{'error': f'Bulk storage failed: {bulk_response.status_code}'}]
                    except Exception as e:
                        stored_indices = []
                        failed_storage = [{'error': f'Bulk storage error: {str(e)}'}]
                else:
                    stored_indices = []
                    failed_storage = []
                
                return Response({
                    'message': f'Year {year} calculations completed',
                    'year': year,
                    'sample_type': sample_type,
                    'total_calculated': calculation_data.get('total_processed', 0),
                    'total_stored': len(stored_indices),
                    'total_failed_calculation': calculation_data.get('total_failed', 0),
                    'total_failed_storage': len(failed_storage),
                    'stored_indices': stored_indices,
                    'failed_calculations': calculation_data.get('failed_calculations', []),
                    'failed_storage': failed_storage,
                    'success_rate': calculation_data.get('success_rate', 0)
                })
            else:
                return Response({
                    'error': f'FastAPI calculation failed: {response.text}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'error': f'Year calculation error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CalculationBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing calculation batch status"""
    queryset = CalculationBatch.objects.all()
    
    def list(self, request):
        batches = self.queryset.all()
        data = []
        for batch in batches:
            data.append({
                'batch_id': batch.batch_id,
                'status': batch.status,
                'total_samples': batch.total_samples,
                'processed_samples': batch.processed_samples,
                'failed_samples': batch.failed_samples,
                'started_at': batch.started_at.isoformat() if batch.started_at else None
            })
        return Response(data)

