# File: c:\Users\Harsh tiwari\Desktop\SIH\hmpi\backend\django-service\data_management\admin.py

from django.contrib import admin
from .models import GroundWaterSample

@admin.register(GroundWaterSample)
class GroundWaterSampleAdmin(admin.ModelAdmin):
    list_display = ('s_no', 'state', 'district', 'location', 'year', 'as_ppb', 'fe_ppm', 'u_ppb')
    list_filter = ('state', 'district', 'year')
    search_fields = ('state', 'district', 'location')
    readonly_fields = ('id',)
    fieldsets = (
        ('Location Information', {
            'fields': ('s_no', 'state', 'district', 'location', 'latitude', 'longitude', 'year')
        }),
        ('Water Quality Parameters', {
            'fields': ('ph', 'ec_us_cm', 'co3_mg_l', 'hco3_mg_l', 'cl_mg_l', 'f_mg_l', 
                      'total_hardness_mg_l', 'fe_ppm', 'as_ppb', 'u_ppb')
        }),
    )
    list_per_page = 20