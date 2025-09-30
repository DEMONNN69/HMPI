# test_integration.py - Simple integration test
import requests
import json

def test_fastapi_calculation():
    """Test FastAPI calculation endpoint"""
    print("Testing FastAPI calculation service...")
    
    # Test sample data
    sample_data = {
        "sample_id": "TEST_001",
        "arsenic": 0.02,
        "lead": 0.015,
        "cadmium": 0.005,
        "chromium": 0.03,
        "mercury": 0.001,
        "iron": 0.1,
        "zinc": 1.0,
        "copper": 0.5
    }
    
    try:
        # Call FastAPI calculation endpoint
        response = requests.post(
            "http://localhost:8001/api/v1/calculations/single",
            json=sample_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ FastAPI calculation successful!")
            print(f"   Sample ID: {result['sample_id']}")
            print(f"   HPI Value: {result['hpi_value']}")
            print(f"   Quality: {result['quality_category']}")
            print(f"   HEI Value: {result.get('hei_value', 'N/A')}")
            return True
        else:
            print(f"❌ FastAPI calculation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.ConnectionError:
        print("❌ Cannot connect to FastAPI service (http://localhost:8001)")
        print("   Make sure FastAPI service is running")
        return False
    except Exception as e:
        print(f"❌ Error testing FastAPI: {str(e)}")
        return False

def test_django_integration():
    """Test Django integration endpoint"""
    print("\nTesting Django integration service...")
    
    # Test calculation request
    request_data = {
        "sample_type": "water_sample",
        "sample_id": 1,  # Assuming sample with ID 1 exists
        "force_recalculate": True
    }
    
    try:
        # Call Django integration endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/computed-indices/calculate_single/",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Django integration successful!")
            print(f"   Message: {result['message']}")
            if 'computed_index' in result:
                idx = result['computed_index']
                print(f"   HPI Value: {idx['hpi_value']}")
                print(f"   Quality: {idx['quality_category']}")
            return True
        else:
            print(f"❌ Django integration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.ConnectionError:
        print("❌ Cannot connect to Django service (http://localhost:8000)")
        print("   Make sure Django service is running")
        return False
    except Exception as e:
        print(f"❌ Error testing Django integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 HMPI Integration Test Suite")
    print("=" * 50)
    
    # Test FastAPI service
    fastapi_ok = test_fastapi_calculation()
    
    # Test Django integration (only if FastAPI works)
    if fastapi_ok:
        django_ok = test_django_integration()
    else:
        print("\n⏭️  Skipping Django integration test (FastAPI not available)")
        django_ok = False
    
    print("\n" + "=" * 50)
    print("🏁 Test Results:")
    print(f"   FastAPI Service: {'✅ PASS' if fastapi_ok else '❌ FAIL'}")
    print(f"   Django Integration: {'✅ PASS' if django_ok else '❌ FAIL'}")
    
    if fastapi_ok and django_ok:
        print("\n🎉 All tests passed! Integration is working correctly.")
    else:
        print("\n🔧 Some tests failed. Check the services and try again.")