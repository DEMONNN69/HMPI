# services/django_client.py
import requests
import asyncio
from typing import List, Dict

DJANGO_BASE_URL = "http://localhost:8000"

async def send_to_django(sample_data: List[Dict]):
    """Send processed data to Django service"""
    
    try:
        # In production, you'd handle authentication properly
        response = requests.post(
            f"{DJANGO_BASE_URL}/api/v1/samples/",
            json={"bulk_data": sample_data},
            headers={"Content-Type": "application/json"}
        )
        
        return {
            "status": "success" if response.status_code == 201 else "error",
            "django_response": response.status_code
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

async def get_from_django(endpoint: str):
    """Get data from Django service"""
    
    try:
        response = requests.get(
            f"{DJANGO_BASE_URL}{endpoint}",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "data": response.json()
            }
        else:
            return {
                "status": "error",
                "message": f"Django service returned {response.status_code}"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }