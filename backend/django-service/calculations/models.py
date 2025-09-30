from django.db import models
# Assuming GroundWaterSample is correctly defined in your data_management app
from data_management.models import GroundWaterSample 

class ComputedIndex(models.Model):
    """
    Stores the Heavy Metal Pollution Indices (HPI, HEI, Cd, MI) 
    calculated by the FastAPI service, linking back to the raw water sample.
    """
    # Link to the raw data sample. One-to-one ensures only one result per sample.
    sample = models.OneToOneField(
        GroundWaterSample, 
        on_delete=models.CASCADE,
        related_name='computed_index',
        verbose_name="Related Water Sample"
    )
    
    # Calculated Index Values (stored as FloatField)
    hpi_value = models.FloatField(verbose_name="Heavy Metal Pollution Index (HPI)")
    hei_value = models.FloatField(null=True, blank=True, verbose_name="Heavy Metal Evaluation Index (HEI)")
    cd_value = models.FloatField(null=True, blank=True, verbose_name="Degree of Contamination (Cd)")
    mi_value = models.FloatField(null=True, blank=True, verbose_name="Metal Index (MI)")
    
    # Categorization based on HPI value (e.g., "excellent", "poor")
    quality_category = models.CharField(max_length=50, verbose_name="Water Quality Category")
    
    # Timestamp
    computed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Index for Sample {self.sample.s_no} - Quality: {self.quality_category}"

    class Meta:
        verbose_name = "Computed Index"
        verbose_name_plural = "Computed Indices"
