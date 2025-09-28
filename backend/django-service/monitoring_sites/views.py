# monitoring_sites/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MonitoringSite
from .serializers import MonitoringSiteSerializer

class MonitoringSiteViewSet(viewsets.ModelViewSet):
    queryset = MonitoringSite.objects.all()
    serializer_class = MonitoringSiteSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active_sites(self, request):
        active_sites = MonitoringSite.objects.filter(is_active=True)
        serializer = self.get_serializer(active_sites, many=True)
        return Response(serializer.data)
