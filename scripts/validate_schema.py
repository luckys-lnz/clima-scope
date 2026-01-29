#!/usr/bin/env python3
"""
Schema Validation Script

Validates county weather report JSON files against the official JSON Schema.
Usage:
    python validate_schema.py <json_file>
    python validate_schema.py --all  # Validate all sample files
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from file."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def load_json_file(json_path: Path) -> Dict[str, Any]:
    """Load JSON data file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def validate_json(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate JSON data against schema.
    
    Returns:
        tuple: (is_valid, errors_list)
    """
    validator = Draft7Validator(schema)
    errors = []
    
    for error in validator.iter_errors(data):
        # Build readable error message
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"  • {path}: {error.message}")
    
    return len(errors) == 0, errors


def validate_file(json_path: Path, schema_path: Path, verbose: bool = True) -> bool:
    """
    Validate a single JSON file against the schema.
    
    Args:
        json_path: Path to JSON file to validate
        schema_path: Path to JSON schema file
        verbose: Print validation details
        
    Returns:
        bool: True if valid, False otherwise
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Validating: {json_path.name}")
        print(f"{'='*60}")
    
    try:
        data = load_json_file(json_path)
        schema = load_schema(schema_path)
        
        is_valid, errors = validate_json(data, schema)
        
        if is_valid:
            if verbose:
                print("✅ VALID - JSON conforms to schema")
                
                # Print summary statistics
                print(f"\nSummary:")
                print(f"  County: {data.get('county_name', 'N/A')} ({data.get('county_id', 'N/A')})")
                period = data.get('period', {})
                print(f"  Period: {period.get('start', 'N/A')} to {period.get('end', 'N/A')}")
                
                wards = data.get('wards', [])
                print(f"  Wards: {len(wards)}")
                
                variables = data.get('variables', {})
                if 'temperature' in variables:
                    temp = variables['temperature']['weekly']
                    print(f"  Temperature: {temp.get('min', 0):.1f}°C - {temp.get('max', 0):.1f}°C (mean: {temp.get('mean', 0):.1f}°C)")
                
                if 'rainfall' in variables:
                    rain = variables['rainfall']['weekly']
                    print(f"  Rainfall: {rain.get('total', 0):.1f}mm (max daily: {rain.get('max_intensity', 0):.1f}mm)")
                
                if 'wind' in variables:
                    wind = variables['wind']['weekly']
                    print(f"  Wind: {wind.get('mean_speed', 0):.1f}km/h (max gust: {wind.get('max_gust', 0):.1f}km/h, direction: {wind.get('dominant_direction', 'N/A')})")
            
            return True
        else:
            if verbose:
                print("❌ INVALID - Validation errors:")
                for error in errors:
                    print(error)
            return False
            
    except FileNotFoundError:
        if verbose:
            print(f"❌ ERROR: File not found: {json_path}")
        return False
    except json.JSONDecodeError as e:
        if verbose:
            print(f"❌ ERROR: Invalid JSON: {e}")
        return False
    except Exception as e:
        if verbose:
            print(f"❌ ERROR: {e}")
        return False


def validate_all_samples(schema_path: Path, samples_dir: Path) -> Dict[str, bool]:
    """
    Validate all sample JSON files in a directory.
    
    Returns:
        dict: Mapping of filename to validation result
    """
    results = {}
    
    # Find all JSON files
    json_files = sorted(samples_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {samples_dir}")
        return results
    
    print(f"\n{'='*60}")
    print(f"Validating {len(json_files)} sample files")
    print(f"{'='*60}")
    
    for json_file in json_files:
        is_valid = validate_file(json_file, schema_path, verbose=True)
        results[json_file.name] = is_valid
    
    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    valid_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for filename, is_valid in results.items():
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"{status} - {filename}")
    
    print(f"\nTotal: {valid_count}/{total_count} valid")
    
    return results


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    schema_path = project_root / "schemas" / "county-weather-report.schema.json"
    samples_dir = project_root / "backend" / "resources" / "sample_data"
    
    if not schema_path.exists():
        print(f"❌ ERROR: Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <json_file>")
        print(f"  {sys.argv[0]} --all")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        # Validate all sample files
        if not samples_dir.exists():
            print(f"❌ ERROR: Samples directory not found: {samples_dir}")
            sys.exit(1)
        
        results = validate_all_samples(schema_path, samples_dir)
        
        # Exit with error code if any validation failed
        if not all(results.values()):
            sys.exit(1)
    else:
        # Validate single file
        json_path = Path(sys.argv[1])
        
        if not json_path.exists():
            print(f"❌ ERROR: File not found: {json_path}")
            sys.exit(1)
        
        is_valid = validate_file(json_path, schema_path, verbose=True)
        
        if not is_valid:
            sys.exit(1)
    
    print("\n✅ All validations passed!")


if __name__ == "__main__":
    main()
