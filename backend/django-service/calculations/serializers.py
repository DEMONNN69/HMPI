from rest_framework import serializers
from .models import ComputedIndex, CalculationBatch

class ComputedIndexSerializer(serializers.ModelSerializer):
    """
    Serializer for the ComputedIndex model.
    Supports both GroundWaterSample and WaterSample through generic foreign key.
    """
    
    # Display fields from the related sample
    sample_display = serializers.SerializerMethodField()
    sample_location = serializers.SerializerMethodField()
    
    class Meta:
        model = ComputedIndex
        fields = [
            'id',
            'content_type',
            'object_id', 
            'sample_display',
            'sample_location',
            'hpi_value', 
            'hei_value', 
            'cd_value', 
            'mi_value',
            'quality_category',
            'calculation_method',
            'computed_at',
            'computed_by',
            'notes'
        ]
        read_only_fields = ['id', 'computed_at']
    
    def get_sample_display(self, obj):
        """Return appropriate display name for the sample"""
        if hasattr(obj.sample, 's_no'):
            return f"Sample {obj.sample.s_no}"
        elif hasattr(obj.sample, 'sample_id'):
            return f"Sample {obj.sample.sample_id}"
        return f"Sample ID {obj.object_id}"
    
    def get_sample_location(self, obj):
        """Return location from the sample"""
        if hasattr(obj.sample, 'location'):
            return obj.sample.location
        elif hasattr(obj.sample, 'latitude') and hasattr(obj.sample, 'longitude'):
            return f"Lat: {obj.sample.latitude}, Lon: {obj.sample.longitude}"
        return "Location not available"

class CalculationBatchSerializer(serializers.ModelSerializer):
    """Serializer for tracking batch calculation operations"""
    
    class Meta:
        model = CalculationBatch
        fields = '__all__'
        read_only_fields = ['started_at', 'completed_at']

class SampleCalculationRequestSerializer(serializers.Serializer):
    """Serializer for requesting calculations on a specific sample"""
    
    sample_type = serializers.ChoiceField(choices=['ground_water', 'water_sample'])
    sample_id = serializers.IntegerField()
    force_recalculate = serializers.BooleanField(default=False)

class BatchCalculationRequestSerializer(serializers.Serializer):
    """Serializer for requesting batch calculations"""
    
    sample_type = serializers.ChoiceField(choices=['ground_water', 'water_sample'])
    sample_ids = serializers.ListField(child=serializers.IntegerField())
    force_recalculate = serializers.BooleanField(default=False) 
