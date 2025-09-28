# samples/serializers.py
from rest_framework import serializers
from .models import WaterSample, ComputedIndex

class WaterSampleSerializer(serializers.ModelSerializer):
    computed_index = serializers.SerializerMethodField()
    
    class Meta:
        model = WaterSample
        fields = '__all__'
        read_only_fields = ('uploaded_by', 'created_at', 'updated_at')
    
    def get_computed_index(self, obj):
        if hasattr(obj, 'computed_index'):
            return ComputedIndexSerializer(obj.computed_index).data
        return None

class ComputedIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComputedIndex
        fields = '__all__'
