from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from data_management.models import GroundWaterSample
from samples.models import WaterSample

class ComputedIndex(models.Model):
    """
    Stores the Heavy Metal Pollution Indices (HPI, HEI, Cd, MI) 
    calculated by the FastAPI service. Uses generic foreign key to support
    both GroundWaterSample and WaterSample models.
    """
    
    # Generic foreign key to support multiple sample types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    sample = GenericForeignKey('content_type', 'object_id')
    
    # Year and Location data for map visualization
    calculation_year = models.IntegerField(verbose_name="Calculation Year")
    location_name = models.CharField(max_length=200, verbose_name="Location Name")
    state = models.CharField(max_length=100, null=True, blank=True, verbose_name="State")
    district = models.CharField(max_length=100, null=True, blank=True, verbose_name="District")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Latitude")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Longitude")
    
    # Calculated Index Values
    hpi_value = models.FloatField(verbose_name="Heavy Metal Pollution Index (HPI)")
    hei_value = models.FloatField(null=True, blank=True, verbose_name="Heavy Metal Evaluation Index (HEI)")
    cd_value = models.FloatField(null=True, blank=True, verbose_name="Degree of Contamination (Cd)")
    mi_value = models.FloatField(null=True, blank=True, verbose_name="Metal Index (MI)")
    
    # Quality Categories
    QUALITY_CHOICES = [
        ('excellent', 'Excellent (HPI < 25)'),
        ('good', 'Good (25 ≤ HPI < 50)'),
        ('poor', 'Poor (50 ≤ HPI < 75)'),
        ('very_poor', 'Very Poor (HPI ≥ 75)'),
    ]
    
    quality_category = models.CharField(
        max_length=20, 
        choices=QUALITY_CHOICES,
        verbose_name="Water Quality Category"
    )
    
    # Metadata
    calculation_method = models.CharField(max_length=50, default="WHO_2011", verbose_name="Calculation Method")
    computed_at = models.DateTimeField(auto_now_add=True)
    computed_by = models.CharField(max_length=100, default="FastAPI_HPICalculator", verbose_name="Computed By")
    
    # Additional context
    notes = models.TextField(blank=True, null=True, verbose_name="Calculation Notes")

    def __str__(self):
        if hasattr(self.sample, 's_no'):
            return f"Index for Sample {self.sample.s_no} - Quality: {self.quality_category}"
        elif hasattr(self.sample, 'sample_id'):
            return f"Index for Sample {self.sample.sample_id} - Quality: {self.quality_category}"
        else:
            return f"Index for Sample ID {self.object_id} - Quality: {self.quality_category}"

    class Meta:
        verbose_name = "Computed Index"
        verbose_name_plural = "Computed Indices"
        ordering = ['-computed_at']
        unique_together = [
            ['calculation_year', 'location_name', 'latitude', 'longitude'],  # Prevent duplicate calculations for same year/location
            ['content_type', 'object_id']  # Ensure one calculation per sample
        ]
        indexes = [
            models.Index(fields=['calculation_year']),
            models.Index(fields=['location_name']),
            models.Index(fields=['quality_category']),
            models.Index(fields=['hpi_value']),
            models.Index(fields=['computed_at']),
            models.Index(fields=['calculation_year', 'location_name']),
            models.Index(fields=['calculation_year', 'quality_category']),
            models.Index(fields=['state', 'district']),
        ]

class CalculationBatch(models.Model):
    """
    Groups multiple calculations together for batch processing tracking
    """
    batch_id = models.CharField(max_length=100, unique=True)
    total_samples = models.IntegerField()
    processed_samples = models.IntegerField(default=0)
    failed_samples = models.IntegerField(default=0)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.status} ({self.processed_samples}/{self.total_samples})"
    
    class Meta:
        verbose_name = "Calculation Batch"
        verbose_name_plural = "Calculation Batches"
        ordering = ['-started_at']
