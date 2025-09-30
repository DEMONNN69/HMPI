import numpy as np
from typing import Dict, List

class HPICalculator:
    def __init__(self):
        # Standard permissible limits (WHO/BIS standards)
        self.standards = {
            'arsenic': 0.01,       # mg/L (WHO)
            'lead': 0.01,          # mg/L (WHO) 
            'cadmium': 0.003,      # mg/L (WHO)
            'chromium': 0.05,      # mg/L (WHO)
            'mercury': 0.001,      # mg/L (WHO)
            'iron': 0.3,           # mg/L (WHO)
            'zinc': 3.0,           # mg/L (WHO)
            'copper': 2.0,         # mg/L (WHO)
            'uranium': 0.03,       # mg/L (WHO)
        }
        
        # Ideal values (usually 0 for most metals)
        self.ideal_values = {
            'arsenic': 0,
            'lead': 0, 
            'cadmium': 0,
            'chromium': 0,
            'mercury': 0,
            'iron': 0,
            'zinc': 0,
            'copper': 0,
            'uranium': 0,
        }
    
    def calculate_hpi(self, sample_data: Dict) -> float:
        """
        Calculate Heavy Metal Pollution Index (HPI)
        HPI = Σ(Wi × Qi) / ΣWi
        """
        total_weighted = 0
        total_weights = 0
        
        for metal, concentration in sample_data.items():
            if metal in self.standards and concentration is not None:
                # Unit weight (Wi)
                wi = 1 / self.standards[metal]
                
                # Sub-index (Qi)
                si = concentration  # Measured value
                ii = self.ideal_values[metal]  # Ideal value
                std = self.standards[metal]  # Standard value
                
                # Check to prevent division by zero, though std > ii in this case
                if (std - ii) != 0:
                    qi = abs((si - ii) / (std - ii)) * 100
                else:
                    # Handle case where standard and ideal values are the same (shouldn't happen with these standards)
                    qi = 0 

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
        elif hpi_value < 75:
            return "poor"
        else:
            return "very_poor"
    
    def classify_water_quality(self, hpi_value: float) -> str:
        """Alias for categorize_water_quality - classify water quality based on HPI value"""
        return self.categorize_water_quality(hpi_value)