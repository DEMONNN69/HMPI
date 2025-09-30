from django.contrib import admin
from .models import ComputedIndex, CalculationBatch

@admin.register(ComputedIndex)
class ComputedIndexAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'hpi_value', 'quality_category', 'computed_at', 'computed_by']
    list_filter = ['quality_category', 'computed_at', 'calculation_method']
    search_fields = ['quality_category', 'notes']
    readonly_fields = ['computed_at']
    ordering = ['-computed_at']

@admin.register(CalculationBatch)
class CalculationBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'status', 'total_samples', 'processed_samples', 'failed_samples', 'started_at']
    list_filter = ['status', 'started_at']
    search_fields = ['batch_id']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']
