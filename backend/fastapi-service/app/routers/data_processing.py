# routers/data_processing.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
from ..services.hmpi_calculator import calculate_hmpi_batch
from ..services.django_client import send_to_django

router = APIRouter()

@router.post("/upload")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload and process CSV file with water sample data"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['sample_id', 'latitude', 'longitude', 'arsenic', 'lead']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Process data and calculate HMPI
        processed_data = calculate_hmpi_batch(df)
        
        # Send processed data to Django service
        django_response = await send_to_django(processed_data.to_dict('records'))
        
        return {
            "message": "File processed successfully",
            "processed_samples": len(processed_data),
            "results": processed_data.to_dict('records')[:10],  # First 10 for preview
            "django_sync": django_response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

