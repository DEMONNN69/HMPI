from rest_framework import serializers
from .models import GroundWaterSample 

class GroundWaterSampleSerializer(serializers.ModelSerializer):
    """
    Serializer for the GroundWaterSample model, exporting all fields 
    for use by the React frontend.
    """
    
    class Meta:
        model = GroundWaterSample
        # Include all fields to match the TypeScript interface
        fields = '__all__' 
