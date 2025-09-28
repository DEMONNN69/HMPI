# samples/models.py
from django.db import models
from django.contrib.auth.models import User

class WaterSample(models.Model):
    sample_id = models.CharField(max_length=50, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    arsenic = models.FloatField(null=True, blank=True)
    lead = models.FloatField(null=True, blank=True)
    cadmium = models.FloatField(null=True, blank=True)
    chromium = models.FloatField(null=True, blank=True)
    collection_date = models.DateTimeField()
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sample {self.sample_id}"

class ComputedIndex(models.Model):
    QUALITY_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('poor', 'Poor'),
        ('very_poor', 'Very Poor'),
    ]
    
    sample = models.OneToOneField(WaterSample, on_delete=models.CASCADE, related_name='computed_index')
    hpi_value = models.FloatField()
    hei_value = models.FloatField(null=True, blank=True)
    mi_value = models.FloatField(null=True, blank=True)
    quality_category = models.CharField(max_length=20, choices=QUALITY_CHOICES)
    computed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Index for {self.sample.sample_id} - {self.quality_category}"

