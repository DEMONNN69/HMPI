# routers/calculations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..services.hmpi_calculator import calculate_hpi, calculate_hei, categorize_quality

router = APIRouter()

class SampleData(BaseModel):
    sample_id: str
    arsenic: float
    lead: float
    cadmium: float
    chromium: float

class BatchCalculationRequest(BaseModel):
    samples: List[SampleData]

@router.post("/hmpi")
async def calculate_hmpi_indices(request: BatchCalculationRequest):
    """Calculate HMPI indices for batch of samples"""
    
    try:
        results = []
        for sample in request.samples:
            hpi_value = calculate_hpi(sample.dict())
            hei_value = calculate_hei(sample.dict())
            quality = categorize_quality(hpi_value)
            
            results.append({
                "sample_id": sample.sample_id,
                "hpi_value": round(hpi_value, 2),
                "hei_value": round(hei_value, 2),
                "quality_category": quality
            })
        
        return {
            "calculated_indices": results,
            "total_processed": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
