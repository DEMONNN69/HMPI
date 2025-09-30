# routers/calculations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..services.hmpi_calculator import HPICalculator

router = APIRouter()
calculator = HPICalculator()

class SampleData(BaseModel):
    sample_id: str
    arsenic: Optional[float] = 0
    lead: Optional[float] = 0
    cadmium: Optional[float] = 0
    chromium: Optional[float] = 0
    mercury: Optional[float] = 0
    iron: Optional[float] = 0
    zinc: Optional[float] = 0
    copper: Optional[float] = 0

class BatchCalculationRequest(BaseModel):
    samples: List[SampleData]

class CalculationResponse(BaseModel):
    sample_id: str
    hpi_value: float
    hei_value: Optional[float] = None
    cd_value: Optional[float] = None
    mi_value: Optional[float] = None
    quality_category: str
    calculation_method: str = "WHO_2011"
    notes: str = ""

@router.post("/single", response_model=CalculationResponse)
async def calculate_single_sample(sample: SampleData):
    """Calculate indices for a single water sample"""
    
    try:
        # Convert sample to dict for calculation
        sample_dict = sample.dict()
        
        # Calculate all indices
        hpi_value = calculator.calculate_hpi(sample_dict)
        hei_value = calculator.calculate_hei(sample_dict)
        cd_value = calculator.calculate_cd(sample_dict)
        mi_value = calculator.calculate_mi(sample_dict)
        quality = calculator.categorize_water_quality(hpi_value)
        
        return CalculationResponse(
            sample_id=sample.sample_id,
            hpi_value=round(hpi_value, 4),
            hei_value=round(hei_value, 4) if hei_value else None,
            cd_value=round(cd_value, 4) if cd_value else None,
            mi_value=round(mi_value, 4) if mi_value else None,
            quality_category=quality,
            calculation_method="WHO_2011",
            notes=f"Calculated using {len([k for k, v in sample_dict.items() if v and k != 'sample_id'])} metals"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

@router.post("/batch")
async def calculate_batch_samples(request: BatchCalculationRequest):
    """Calculate indices for multiple water samples"""
    
    try:
        results = []
        failed_calculations = []
        
        for sample in request.samples:
            try:
                # Convert sample to dict for calculation
                sample_dict = sample.dict()
                
                # Calculate all indices
                hpi_value = calculator.calculate_hpi(sample_dict)
                hei_value = calculator.calculate_hei(sample_dict)
                cd_value = calculator.calculate_cd(sample_dict)
                mi_value = calculator.calculate_mi(sample_dict)
                quality = calculator.categorize_water_quality(hpi_value)
                
                results.append({
                    "sample_id": sample.sample_id,
                    "hpi_value": round(hpi_value, 4),
                    "hei_value": round(hei_value, 4) if hei_value else None,
                    "cd_value": round(cd_value, 4) if cd_value else None,
                    "mi_value": round(mi_value, 4) if mi_value else None,
                    "quality_category": quality,
                    "calculation_method": "WHO_2011",
                    "notes": f"Calculated using {len([k for k, v in sample_dict.items() if v and k != 'sample_id'])} metals"
                })
                
            except Exception as e:
                failed_calculations.append({
                    "sample_id": sample.sample_id,
                    "error": str(e)
                })
        
        return {
            "calculated_indices": results,
            "total_processed": len(results),
            "total_failed": len(failed_calculations),
            "failed_calculations": failed_calculations,
            "success_rate": len(results) / len(request.samples) * 100 if request.samples else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch calculation error: {str(e)}")

@router.get("/standards")
async def get_calculation_standards():
    """Get the WHO standards and calculation parameters"""
    
    return {
        "standards": calculator.standards,
        "ideal_values": calculator.ideal_values,
        "quality_thresholds": {
            "excellent": "< 25",
            "good": "25 - 49",
            "poor": "50 - 74", 
            "very_poor": "≥ 75"
        },
        "calculation_method": "WHO_2011",
        "supported_metals": list(calculator.standards.keys())
    }
