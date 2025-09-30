from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from .models import ComputedIndex
from .serializers import ComputedIndexSerializer

class ComputedIndexViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    A ViewSet for creating, listing, and retrieving ComputedIndex records.
    
    The POST endpoint is used by the FastAPI service to store the calculated HMPI 
    indices back into the Django database after computation.
    """
    queryset = ComputedIndex.objects.all().order_by('computed_at')
    serializer_class = ComputedIndexSerializer
    
    # Optional: If you plan to secure this endpoint (recommended), you would add:
    # permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """
        Custom create method to handle bulk creation or ensure single entry per sample.
        """
        # If the sample ID already exists, update the record instead of creating a new one.
        # This prevents duplicate computed indices if the FastAPI batch runs multiple times.
        sample_id = request.data.get('sample')
        
        if sample_id and ComputedIndex.objects.filter(sample_id=sample_id).exists():
            instance = ComputedIndex.objects.get(sample_id=sample_id)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return super().create(request, *args, **kwargs)

