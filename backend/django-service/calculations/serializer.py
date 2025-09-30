from rest_framework import serializers
from .models import ComputedIndex

class ComputedIndexSerializer(serializers.ModelSerializer):
    """
    Serializer for the ComputedIndex model.
    Used by FastAPI to POST computed results and by React to GET them.
    
    We include fields from the related GroundWaterSample for display purposes.
    """
    
    # Field to display the S.No from the related raw sample
    sample_s_no = serializers.ReadOnlyField(source='sample.s_no')
    
    # Field to display the Location from the related raw sample
    sample_location = serializers.ReadOnlyField(source='sample.location')

    class Meta:
        model = ComputedIndex
        fields = [
            'id', 
            'sample',              # Writable: FastAPI sends the sample ID here (FK)
            'sample_s_no',         # Read-Only: Display only
            'sample_location',     # Read-Only: Display only
            'hpi_value', 
            'hei_value', 
            'cd_value', 
            'mi_value',
            'quality_category',
            'computed_at'
        ]
        # 'sample' must remain writable for FastAPI's POST request to link the computed result.
        read_only_fields = ['id', 'sample_s_no', 'sample_location', 'computed_at'] 
