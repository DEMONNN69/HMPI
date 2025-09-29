from django.db import models


class GroundWaterSample(models.Model):
    s_no = models.IntegerField(verbose_name="Serial Number", unique=True)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    so4_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="SO4 (mg/L)")
    no3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="NO3 (mg/L)")
    po4_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="PO4 (mg/L)")
    ca_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Ca (mg/L)")
    mg_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Mg (mg/L)")
    na_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Na (mg/L)")
    k_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="K (mg/L)")
    
    year = models.IntegerField()

    ph = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ec_us_cm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="EC (µS/cm)")
    co3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="CO3 (mg/L)")
    hco3_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="HCO3 (mg/L)")
    cl_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Cl (mg/L)")
    f_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="F (mg/L)")
    total_hardness_mg_l = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Total Hardness (mg/L)")
    fe_ppm = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Fe (ppm)")
    as_ppb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="As (ppb)")
    u_ppb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="U (ppb)")

    def __str__(self):
        return f"{self.state} - {self.location} ({self.year})"

    class Meta:
        verbose_name = "Ground Water Sample"
        verbose_name_plural = "Ground Water Samples"


