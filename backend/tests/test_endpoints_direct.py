#!/usr/bin/env python3
"""
Direct Test Script for API Endpoints using FastAPI TestClient

Tests all the API endpoints directly without HTTP connection.
"""

from fastapi.testclient import TestClient
from app.main import app
import json
from datetime import datetime, timedelta

# Create test client
client = TestClient(app)

def print_response(response, title=""):
    """Print formatted response."""
    print(f"\n{'='*60}")
    if title:
        print(f"{title}")
        print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")


def test_health():
    """Test health endpoint."""
    print("Testing Health Endpoint...")
    response = client.get("/api/v1/health")
    print_response(response, "Health Check")
    return response.status_code == 200


def test_counties():
    """Test county endpoints (read-only reference data)."""
    print("\n" + "="*60)
    print("Testing County Endpoints (Reference Data - Read-Only)")
    print("="*60)
    
    # List counties
    print("\n1. Listing counties...")
    response = client.get("/api/v1/counties")
    print_response(response, "List Counties")
    
    # Get a specific county (use Nairobi - ID 31)
    print("\n2. Getting county by ID (Nairobi - 31)...")
    response = client.get("/api/v1/counties/31")
    print_response(response, "Get County")
    
    if response.status_code == 200:
        county_id = response.json()["id"]
        
        # Update county notes (only field that can be updated)
        print("\n3. Updating county notes (metadata only)...")
        update_data = {
            "notes": "Test notes update - counties are reference data"
        }
        response = client.patch(
            f"/api/v1/counties/{county_id}",
            json=update_data
        )
        print_response(response, "Update County Notes")
        
        # Verify notes were updated
        if response.status_code == 200:
            print("\n4. Verifying notes update...")
            response = client.get(f"/api/v1/counties/{county_id}")
            updated_notes = response.json().get("notes")
            print(f"   Updated notes: {updated_notes}")
        
        # Test that name/region cannot be updated
        print("\n5. Testing that name/region cannot be updated...")
        invalid_update = {
            "name": "Invalid Name",
            "notes": "Should fail"
        }
        response = client.patch(
            f"/api/v1/counties/{county_id}",
            json=invalid_update
        )
        print_response(response, "Attempt Invalid Update (should fail)")
    
    # Test that POST (create) is not allowed
    print("\n6. Testing that county creation is not allowed...")
    county_data = {
        "id": "99",
        "name": "Test County",
        "region": "Test Region"
    }
    response = client.post(
        "/api/v1/counties",
        json=county_data
    )
    print_response(response, "Attempt Create County (should fail - 405)")
    
    return True


def test_weather_reports():
    """Test weather report endpoints."""
    print("\n" + "="*60)
    print("Testing Weather Report Endpoints")
    print("="*60)
    
    # Use an existing county (Nairobi - 31) for testing
    # Counties are reference data and must be seeded first
    test_county_id = "31"  # Nairobi
    
    # List weather reports
    print("\n1. Listing weather reports...")
    response = client.get("/api/v1/reports/weather")
    print_response(response, "List Weather Reports")
    
    # Create a test weather report
    print("\n2. Creating a test weather report...")
    period_start = datetime.now()
    period_end = period_start + timedelta(days=7)
    
    weather_report_data = {
        "county_id": test_county_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "week_number": 1,
        "year": 2026,
        "schema_version": "1.0",
        "raw_data": {
            "county_id": test_county_id,
            "county_name": "Nairobi",
            "period": {
                "start": period_start.strftime("%Y-%m-%d"),
                "end": period_end.strftime("%Y-%m-%d"),
                "week_number": 1,
                "year": 2026
            },
            "variables": {
                "temperature": {
                    "weekly": {"mean": 25.0, "max": 30.0, "min": 20.0},
                    "daily": [],
                    "units": "celsius"
                },
                "rainfall": {
                    "weekly": {"total": 50.0, "max": 15.0},
                    "daily": [],
                    "units": "mm"
                },
                "wind": {
                    "weekly": {"mean_speed": 10.0, "max_speed": 20.0, "dominant_direction": "NE"},
                    "daily": [],
                    "units": "km/h"
                }
            },
            "metadata": {
                "model_run_timestamp": datetime.now().isoformat(),
                "data_source": "Test Data",
                "generated_at": datetime.now().isoformat()
            },
            "schema_version": "1.0"
        }
    }
    
    response = client.post(
        "/api/v1/reports/weather",
        json=weather_report_data
    )
    print_response(response, "Create Weather Report")
    
    if response.status_code == 201:
        report_id = response.json()["id"]
        
        # Get weather report
        print("\n3. Getting weather report by ID...")
        response = client.get(f"/api/v1/reports/weather/{report_id}")
        print_response(response, "Get Weather Report")
        
        return report_id
    
    return None


def test_complete_reports():
    """Test complete report endpoints."""
    print("\n" + "="*60)
    print("Testing Complete Report Endpoints")
    print("="*60)
    
    # List complete reports
    print("\n1. Listing complete reports...")
    response = client.get("/api/v1/reports/complete")
    print_response(response, "List Complete Reports")
    
    return True


def test_pdf_endpoints():
    """Test PDF endpoints."""
    print("\n" + "="*60)
    print("Testing PDF Endpoints")
    print("="*60)
    
    # List PDF reports
    print("\n1. Listing PDF reports...")
    response = client.get("/api/v1/pdf")
    print_response(response, "List PDF Reports")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("API Endpoint Testing (Direct TestClient)")
    print("="*60)
    print("\nTesting endpoints using FastAPI TestClient")
    print("="*60)
    
    try:
        # Test health
        if not test_health():
            print("❌ Health check failed.")
            return
        
        # Test counties
        test_counties()
        
        # Test weather reports
        report_id = test_weather_reports()
        
        # Test complete reports
        test_complete_reports()
        
        # Test PDF endpoints
        test_pdf_endpoints()
        
        print("\n" + "="*60)
        print("Testing Complete!")
        print("="*60)
        print("\nNote: Some endpoints (like generating complete reports and PDFs)")
        print("require AI API keys to be configured in the .env file.")
        print("\nTo test those endpoints, ensure:")
        print("1. OPENAI_API_KEY or ANTHROPIC_API_KEY is set in .env")
        print("2. The pdf_generator package is installed")
        print("3. Database migrations have been applied")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
