import requests
import uuid
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
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

