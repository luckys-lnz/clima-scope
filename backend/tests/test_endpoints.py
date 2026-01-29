#!/usr/bin/env python3
"""
Test Script for API Endpoints

Tests all the API endpoints to verify they work correctly.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

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
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    return response.status_code == 200


def test_counties():
    """Test county endpoints."""
    print("\n" + "="*60)
    print("Testing County Endpoints")
    print("="*60)
    
    # List counties
    print("\n1. Listing counties...")
    response = requests.get(f"{BASE_URL}/counties")
    print_response(response, "List Counties")
    
    # Create county
    print("\n2. Creating a test county...")
    county_data = {
        "id": "99",
        "name": "Test County",
        "region": "Test Region",
        "notes": "This is a test county for API testing"
    }
    response = requests.post(
        f"{BASE_URL}/counties",
        json=county_data
    )
    print_response(response, "Create County")
    
    if response.status_code == 201:
        county_id = response.json()["id"]
        
        # Get county
        print("\n3. Getting county by ID...")
        response = requests.get(f"{BASE_URL}/counties/{county_id}")
        print_response(response, "Get County")
        
        # Update county
        print("\n4. Updating county...")
        update_data = {
            "notes": "Updated test county notes"
        }
        response = requests.put(
            f"{BASE_URL}/counties/{county_id}",
            json=update_data
        )
        print_response(response, "Update County")
        
        # Delete county
        print("\n5. Deleting county...")
        response = requests.delete(f"{BASE_URL}/counties/{county_id}")
        print_response(response, "Delete County")
    
    return True


def test_weather_reports():
    """Test weather report endpoints."""
    print("\n" + "="*60)
    print("Testing Weather Report Endpoints")
    print("="*60)
    
    # First, create a county if it doesn't exist
    county_data = {
        "id": "98",
        "name": "Test County for Reports",
        "region": "Test Region"
    }
    try:
        requests.post(f"{BASE_URL}/counties", json=county_data)
    except:
        pass  # County might already exist
    
    # List weather reports
    print("\n1. Listing weather reports...")
    response = requests.get(f"{BASE_URL}/reports/weather")
    print_response(response, "List Weather Reports")
    
    # Create a test weather report
    print("\n2. Creating a test weather report...")
    period_start = datetime.now()
    period_end = period_start + timedelta(days=7)
    
    weather_report_data = {
        "county_id": "98",
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "week_number": 1,
        "year": 2026,
        "schema_version": "1.0",
        "raw_data": {
            "county_id": "98",
            "county_name": "Test County for Reports",
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
    
    response = requests.post(
        f"{BASE_URL}/reports/weather",
        json=weather_report_data
    )
    print_response(response, "Create Weather Report")
    
    if response.status_code == 201:
        report_id = response.json()["id"]
        
        # Get weather report
        print("\n3. Getting weather report by ID...")
        response = requests.get(f"{BASE_URL}/reports/weather/{report_id}")
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
    response = requests.get(f"{BASE_URL}/reports/complete")
    print_response(response, "List Complete Reports")
    
    return True


def test_pdf_endpoints():
    """Test PDF endpoints."""
    print("\n" + "="*60)
    print("Testing PDF Endpoints")
    print("="*60)
    
    # List PDF reports
    print("\n1. Listing PDF reports...")
    response = requests.get(f"{BASE_URL}/pdf")
    print_response(response, "List PDF Reports")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("API Endpoint Testing")
    print("="*60)
    print(f"\nTesting endpoints at: {BASE_URL}")
    print("\nMake sure the server is running at http://localhost:8000")
    print("="*60)
    
    try:
        # Test health
        if not test_health():
            print("❌ Health check failed. Is the server running?")
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
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the server is running:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  python run.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
