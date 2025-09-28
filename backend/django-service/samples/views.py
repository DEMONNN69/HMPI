# samples/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import WaterSample, ComputedIndex
from .serializers import WaterSampleSerializer, ComputedIndexSerializer

class WaterSampleViewSet(viewsets.ModelViewSet):
    queryset = WaterSample.objects.all()
    serializer_class = WaterSampleSerializer
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary_stats(self, request):
        total = WaterSample.objects.count()
        with_indices = ComputedIndex.objects.count()
        
        return Response({
            'total_samples': total,
            'processed_samples': with_indices,
            'pending_processing': total - with_indices
        })
