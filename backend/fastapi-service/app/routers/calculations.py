# routers/calculations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor
import asyncio
from ..services.hmpi_calculator import HPICalculator

router = APIRouter()
calculator = HPICalculator()

def calculate_hmpi_batch(samples_batch):
    """Calculate HMPI for a batch of samples in a separate process"""
    calculator = HPICalculator()
    results = []
    failed_calculations = []
    
    for sample in samples_batch:
        try:
            # Extract metal concentrations with proper field mapping and unit conversion
            # Convert ppb to mg/L: ppb = μg/L, so ppb/1000 = mg/L
            # Convert ppm to mg/L: ppm = mg/L (for water)
            
            # Helper function to safely convert to float
            def safe_float(value, default=0.0):
                if value is None:
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            sample_dict = {
                'arsenic': safe_float(sample.get('as_ppb', 0)) / 1000.0,  # ppb to mg/L
                'iron': safe_float(sample.get('fe_ppm', 0)),  # ppm = mg/L for water
                'uranium': safe_float(sample.get('u_ppb', 0)) / 1000.0,  # ppb to mg/L
                # Note: Other metals (lead, cadmium, etc.) not available in this dataset
                # Using 0 as default since they're not measured
                'lead': 0,
                'cadmium': 0,
                'chromium': 0,
                'mercury': 0,
                'zinc': 0,
                'copper': 0,
            }
            
            # Calculate indices
            hpi = calculator.calculate_hpi(sample_dict)
            hei = calculator.calculate_hei(sample_dict)
            cd = calculator.calculate_cd(sample_dict)
            mi = calculator.calculate_mi(sample_dict)
            
            quality = calculator.classify_water_quality(hpi)
            
            # Include location data for map visualization
            results.append({
                "sample_id": sample.get('sample_id', str(sample.get('id', ''))),
                "sample_pk": sample.get('id'),
                "location_name": sample.get('location', 'Unknown Location'),
                "state": sample.get('state', None),
                "district": sample.get('district', None),
                "latitude": sample.get('latitude', None),
                "longitude": sample.get('longitude', None),
                "hpi_value": hpi,
                "hei_value": hei,
                "cd_value": cd,
                "mi_value": mi,
                "quality_category": quality,
                "calculation_method": "WHO_2011",
                "notes": f"Parallel calculation using {len([k for k, v in sample_dict.items() if v])} metals"
            })
            
        except Exception as e:
            failed_calculations.append({
                "sample_id": sample.get('sample_id', str(sample.get('id', ''))),
                "error": str(e)
            })
    
    return results, failed_calculations

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
    # Location data for map visualization
    location_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BatchCalculationRequest(BaseModel):
    samples: List[SampleData]

class YearCalculationRequest(BaseModel):
    year: int
    sample_type: str  # 'water_sample' or 'ground_water'
    force_recalculate: Optional[bool] = False

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

@router.post("/calculate-by-year")
async def calculate_by_year(request: YearCalculationRequest):
    """
    Calculate HMPI for all samples from a specific year using parallel processing.
    Returns calculated indices with location data for map visualization.
    """
    try:
        from ..services.django_client import DjangoClient
        
        django_client = DjangoClient()
        
        # Fetch all samples for the given year (now using concurrent requests)
        samples_data = await django_client.get_samples_by_year(
            year=request.year,
            sample_type=request.sample_type
        )
        
        if not samples_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No {request.sample_type} samples found for year {request.year}"
            )
        
        # Split samples into batches for parallel processing
        batch_size = 100  # Process 100 samples per batch
        sample_batches = [samples_data[i:i + batch_size] for i in range(0, len(samples_data), batch_size)]
        
        # Use ProcessPoolExecutor for CPU-intensive calculations
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=4) as executor:  # Adjust based on CPU cores
            # Submit all batches for parallel processing
            futures = [
                loop.run_in_executor(executor, calculate_hmpi_batch, batch)
                for batch in sample_batches
            ]
            
            # Wait for all batches to complete
            batch_results = await asyncio.gather(*futures)
        
        # Flatten results
        all_results = []
        all_failed = []
        for batch_result, batch_failed in batch_results:
            all_results.extend(batch_result)
            all_failed.extend(batch_failed)
        
        # Add year to all results
        for result in all_results:
            result["year"] = request.year
        
        return {
            "year": request.year,
            "sample_type": request.sample_type,  
            "calculated_indices": all_results,
            "total_processed": len(all_results),
            "total_failed": len(all_failed),
            "failed_calculations": all_failed,
            "success_rate": (len(all_results) / len(samples_data) * 100) if samples_data else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Year-based calculation error: {str(e)}")

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
