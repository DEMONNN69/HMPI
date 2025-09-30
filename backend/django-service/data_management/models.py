from django.db import models
from django.core.validators import MinValueValidator

class GroundWaterSample(models.Model):
    """
    Model representing a single ground water sample record, including 
    geolocation and 21 chemical/heavy metal parameters.
    """
    # Identification and Location
    s_no = models.IntegerField(verbose_name="Serial Number", unique=True, db_index=True)
    state = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, db_index=True)
    location = models.CharField(max_length=255)
    
    # Geolocation (Required fields)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    year = models.IntegerField(
        validators=[MinValueValidator(1900)], 
        help_text="Year of sample collection"
    )

    # Core Parameters (DecimalField for precision, allowing null/blank)
    ph = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ec_us_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="EC (µS/cm)")
    co3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="CO3 (mg/L)")
    hco3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="HCO3 (mg/L)")
    cl_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Cl (mg/L)")
    f_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="F (mg/L)")
    total_hardness_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Total Hardness (mg/L)")

    # Complete Chemical/Ion List
    so4_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="SO4 (mg/L)")
    no3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="NO3 (mg/L)")
    po4_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="PO4 (mg/L)")
    ca_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Ca (mg/L)")
    mg_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Mg (mg/L)")
    na_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Na (mg/L)")
    k_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="K (mg/L)")

    # Heavy Metals
    fe_ppm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Fe (ppm)")
    as_ppb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="As (ppb)")
    u_ppb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="U (ppb)")
    
    # Timestamps - FIX: Added null=True to allow migration without default
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.state} - {self.location} ({self.year})"

    class Meta:
        verbose_name = "Ground Water Sample"
        verbose_name_plural = "Ground Water Samples"
        ordering = ['s_no']
