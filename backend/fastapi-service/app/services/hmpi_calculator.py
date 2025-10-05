import numpy as np
from typing import Dict, List

class HPICalculator:
    def __init__(self):
        # WHO/BIS Standard permissible limits (mg/L)
        self.standards = {
            'arsenic': 0.01,      # WHO guideline
            'lead': 0.01,         # WHO guideline
            'cadmium': 0.003,     # WHO guideline
            'chromium': 0.05,     # WHO guideline
            'mercury': 0.001,     # WHO guideline
            'iron': 0.3,          # WHO guideline
            'zinc': 3.0,          # WHO guideline
            'copper': 2.0,        # WHO guideline
            'uranium': 0.03,      # WHO guideline
        }
        
        # Unit weights (Wi = K/Si, where K=1)
        self.unit_weights = {}
        for metal, standard in self.standards.items():
            self.unit_weights[metal] = 1 / standard

    def calculate_hpi(self, sample_data: Dict) -> float:
        """
        Calculate Heavy Metal Pollution Index (HPI)
        HPI = Σ(Wi × Qi) / ΣWi
        Where: Qi = (Si/Standard) × 100 (NOT using ideal values)
        """
        total_weighted = 0
        total_weights = 0
        
        for metal, concentration in sample_data.items():
            if metal in self.standards and concentration is not None:
                # Unit weight (Wi = 1/Standard)
                wi = self.unit_weights[metal]
                
                # Sub-index (Qi = (Measured/Standard) × 100)
                qi = (concentration / self.standards[metal]) * 100
                
                total_weighted += wi * qi
                total_weights += wi
        
        return total_weighted / total_weights if total_weights > 0 else 0

# ----------------------------------------------------------------------
    
    def calculate_hei(self, sample_data: Dict) -> float:
        """
        Calculate Heavy Metal Evaluation Index (HEI)
        HEI = Σ(Ci/Si) / n
        """
        sum_ratio = 0
        count = 0
        
        for metal, concentration in sample_data.items():
            if metal in self.standards and concentration is not None:
                sum_ratio += concentration / self.standards[metal]
                count += 1
        
        return sum_ratio / count if count > 0 else 0

# ----------------------------------------------------------------------

    def calculate_cd(self, sample_data: Dict) -> float:
        """
        Calculate Degree of Contamination (Cd)
        Cd = Σ(Ci/Si - 1)
        """
        cd_sum = 0
        
        for metal, concentration in sample_data.items():
            if metal in self.standards and concentration is not None:
                cf = concentration / self.standards[metal]
                cd_sum += (cf - 1)
        
        return cd_sum

# ----------------------------------------------------------------------

    def calculate_mi(self, sample_data: Dict) -> float:
        """
        Calculate Metal Index (MI)
        MI = Σ(Ci/MACi) / n
        """
        return self.calculate_hei(sample_data)  # Same formula as HEI

# ----------------------------------------------------------------------

    def categorize_water_quality(self, hpi_value: float) -> str:
        """Categorize water quality based on HPI value"""
        if hpi_value < 25:
            return "excellent"
        elif hpi_value < 50:
            return "good" 
        elif hpi_value < 100:
            return "moderate"
        else:
            return "poor"
    
    def classify_water_quality(self, hpi_value: float) -> str:
        """Alias for categorize_water_quality - classify water quality based on HPI value"""
        return self.categorize_water_quality(hpi_value)

    def get_pollution_status(self, hpi_value: float) -> Dict:
        """
        Get detailed pollution status based on HPI
        """
        category = self.categorize_water_quality(hpi_value)
        
        if category == "excellent":
            description = "Very low heavy metal pollution level"
            risk_level = "Minimal"
        elif category == "good":
            description = "Low heavy metal pollution level"
            risk_level = "Low"
        elif category == "moderate":
            description = "Moderate heavy metal pollution level"
            risk_level = "Moderate"
        else:  # poor
            description = "High heavy metal pollution level"
            risk_level = "High"
        
        return {
            "hpi_value": round(hpi_value, 2),
            "category": category,
            "description": description,
            "risk_level": risk_level
        }