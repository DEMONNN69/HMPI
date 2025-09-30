# services/django_client.py
import requests
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime

DJANGO_BASE_URL = "http://localhost:8000"

class DjangoClient:
    """Client for communicating with Django service"""
    
    def __init__(self):
        self.base_url = DJANGO_BASE_URL
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_page_async(self, endpoint: str, year: int, page: int):
        """Fetch a single page asynchronously"""
        session = await self.get_session()
        try:
            async with session.get(
                f"{self.base_url}{endpoint}",
                params={"year": year, "page": page, "page_size": 100}
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"Page {page} not found (404) - likely beyond available data")
                    return None
                elif response.status == 500:
                    print(f"Server error on page {page} (500) - likely problematic data, skipping")
                    return None
                else:
                    print(f"Error on page {page}: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            return None
        
    async def get_samples_by_year(self, year: int, sample_type: str):
        """
        Fetch all samples for a specific year from Django using concurrent requests
        
        Args:
            year: The year to filter samples by
            sample_type: 'water_sample' or 'ground_water'
        """
        try:
            endpoint = "/api/v1/ground-water-samples/" if sample_type == "ground_water" else "/api/v1/samples/"
            
            # Start with first page
            all_samples = []
            page = 1
            consecutive_failures = 0
            max_consecutive_failures = 3  # Stop after 3 consecutive failures
            
            # Keep fetching pages until we hit consecutive failures
            while consecutive_failures < max_consecutive_failures:
                result = await self.fetch_page_async(endpoint, year, page)
                
                if result and 'results' in result and result['results']:
                    # Success - add samples and reset failure counter
                    all_samples.extend(result['results'])
                    consecutive_failures = 0
                    print(f"✓ Page {page}: {len(result['results'])} samples")
                elif result and 'results' in result and not result['results']:
                    # Empty page - we've reached the end
                    print(f"✓ Page {page}: Empty page - reached end of data")
                    break
                else:
                    # Failed page - increment failure counter but continue
                    consecutive_failures += 1
                    print(f"✗ Page {page}: Failed (consecutive failures: {consecutive_failures})")
                    
                    # If this is a single failure, continue to next page
                    if consecutive_failures < max_consecutive_failures:
                        print(f"  Continuing to page {page + 1}...")
                
                page += 1
                
                # Safety limit to prevent infinite loops
                if page > 200:  # Max 200 pages (20,000 records)
                    print("Safety limit reached - stopping at page 200")
                    break
            
            print(f"Final result: {len(all_samples)} samples collected from {page-1} page attempts")
            
            samples = all_samples
            
            # Filter by year if the API doesn't support year filtering (additional safety check)
            if isinstance(samples, list):
                year_filtered = []
                for sample in samples:
                    sample_year = None
                    
                    # Check if there's a direct year field first
                    if isinstance(sample, dict) and 'year' in sample:
                        sample_year = sample['year']
                    else:
                        # Try different date fields that might exist
                        date_fields = ['collection_date', 'date_collected', 'created_at', 'date']
                        
                        for field in date_fields:
                            if isinstance(sample, dict) and field in sample and sample[field]:
                                try:
                                    date_str = str(sample[field])
                                    if date_str:
                                        sample_year = datetime.fromisoformat(date_str.replace('Z', '+00:00')).year
                                        break
                                except:
                                    continue
                    
                    if sample_year == year:
                        year_filtered.append(sample)
                
                return year_filtered
            
            return samples
                
        except Exception as e:
            raise Exception(f"Error fetching samples by year: {str(e)}")
        finally:
            # Close the aiohttp session if it exists
            if self.session:
                await self.session.close()
                self.session = None
    
    async def check_existing_calculations(self, year: int, location_name: str, latitude: float, longitude: float):
        """
        Check if calculations already exist for a specific year and location
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/computed-indices/",
                params={
                    "calculation_year": year,
                    "location_name": location_name,
                    "latitude": latitude,
                    "longitude": longitude
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', data) if isinstance(data, dict) else data
                return len(results) > 0  # True if calculations exist
            
            return False
            
        except Exception as e:
            print(f"Error checking existing calculations: {str(e)}")
            return False

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