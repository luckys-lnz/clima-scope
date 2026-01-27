/**
 * Schema Validation Script
 * 
 * Validates Person B's schema implementations
 * Run with: npx tsx scripts/validate-schemas.ts
 */

import { KENYA_COUNTIES, validateCountyList, generateMockCountyReport } from "../lib/weather-schemas"
import {
  isValidCountyReport,
  flattenReportForCSV,
  EXAMPLE_REPORT,
  type CountyWeatherReportData,
} from "../lib/json-schema"

console.log("=".repeat(60))
console.log("SCHEMA VALIDATION TEST")
console.log("=".repeat(60))

// Test 1: County List Validation
console.log("\n1. Testing County List...")
const countyValidation = validateCountyList()
if (countyValidation.isValid) {
  console.log("✅ County list is valid")
  console.log(`   - Total counties: ${KENYA_COUNTIES.length}`)
  
  // Check for duplicates
  const ids = KENYA_COUNTIES.map((c) => c.id)
  const names = KENYA_COUNTIES.map((c) => c.name)
  const uniqueIds = new Set(ids)
  const uniqueNames = new Set(names)
  
  console.log(`   - Unique IDs: ${uniqueIds.size}`)
  console.log(`   - Unique names: ${uniqueNames.size}`)
  
  if (uniqueIds.size === 47 && uniqueNames.size === 47) {
    console.log("   ✅ No duplicates found")
  } else {
    console.log("   ❌ Duplicates detected!")
  }
} else {
  console.log("❌ County list validation failed:")
  countyValidation.errors.forEach((error) => console.log(`   - ${error}`))
}

// Test 2: Mock Report Generation
console.log("\n2. Testing Mock Report Generation...")
try {
  const mockReport = generateMockCountyReport("31", "Nairobi")
  
  console.log("✅ Mock report generated successfully")
  console.log(`   - County: ${mockReport.county_name} (${mockReport.county_id})`)
  console.log(`   - Period: ${mockReport.period.start} to ${mockReport.period.end}`)
  console.log(`   - Temperature daily values: ${mockReport.variables.temperature.daily.length}`)
  console.log(`   - Rainfall daily values: ${mockReport.variables.rainfall.daily.length}`)
  console.log(`   - Wind daily values: ${mockReport.variables.wind.daily_peak.length}`)
  console.log(`   - Wards: ${mockReport.wards.length}`)
  
  // Validate data ranges
  const temp = mockReport.variables.temperature
  if (temp.weekly.mean >= -50 && temp.weekly.mean <= 50) {
    console.log("   ✅ Temperature values in valid range")
  } else {
    console.log("   ❌ Temperature out of range!")
  }
  
  const rain = mockReport.variables.rainfall
  if (rain.weekly.total >= 0 && rain.daily.every((v) => v >= 0)) {
    console.log("   ✅ Rainfall values valid (>= 0)")
  } else {
    console.log("   ❌ Invalid rainfall values!")
  }
} catch (error) {
  console.log(`❌ Mock report generation failed: ${error}`)
}

// Test 3: JSON Schema Validation
console.log("\n3. Testing JSON Schema Validation...")
try {
  const isValid = isValidCountyReport(EXAMPLE_REPORT)
  if (isValid) {
    console.log("✅ Example report passes validation")
    console.log(`   - County: ${EXAMPLE_REPORT.county_name}`)
    console.log(`   - Schema version: ${EXAMPLE_REPORT.schema_version || "not set"}`)
    console.log(`   - Wards: ${EXAMPLE_REPORT.wards?.length || 0}`)
  } else {
    console.log("❌ Example report failed validation")
  }
  
  // Test invalid data
  const invalidTests = [
    { name: "null", data: null },
    { name: "empty object", data: {} },
    { name: "missing county_id", data: { county_name: "Test" } },
  ]
  
  console.log("\n   Testing invalid data rejection:")
  invalidTests.forEach((test) => {
    const result = isValidCountyReport(test.data)
    if (!result) {
      console.log(`   ✅ Correctly rejected: ${test.name}`)
    } else {
      console.log(`   ❌ Incorrectly accepted: ${test.name}`)
    }
  })
} catch (error) {
  console.log(`❌ JSON schema validation failed: ${error}`)
}

// Test 4: CSV Flattening
console.log("\n4. Testing CSV Flattening...")
try {
  const flat = flattenReportForCSV(EXAMPLE_REPORT)
  
  if (flat.length > 0) {
    console.log(`✅ Flattened ${flat.length} ward(s) to CSV format`)
    const firstRow = flat[0]
    console.log(`   - Sample row:`)
    console.log(`     County: ${firstRow.county_name}`)
    console.log(`     Ward: ${firstRow.ward_name} (${firstRow.ward_id})`)
    console.log(`     Rainfall: ${firstRow.rainfall_total} mm`)
    console.log(`     Temp: ${firstRow.temp_mean}°C`)
    
    // Verify all required fields present
    const requiredFields = [
      "schema_version",
      "county_id",
      "county_name",
      "ward_id",
      "ward_name",
      "rainfall_total",
      "temp_mean",
      "temp_max",
      "temp_min",
      "wind_max",
    ]
    
    const missingFields = requiredFields.filter((field) => !(field in firstRow))
    if (missingFields.length === 0) {
      console.log("   ✅ All required fields present")
    } else {
      console.log(`   ❌ Missing fields: ${missingFields.join(", ")}`)
    }
  } else {
    console.log("⚠️  No wards to flatten (empty wards array)")
  }
} catch (error) {
  console.log(`❌ CSV flattening failed: ${error}`)
}

// Test 5: Schema Consistency
console.log("\n5. Testing Schema Consistency...")
try {
  const mockReport = generateMockCountyReport("31", "Nairobi")
  
  // Check if mock report can be used as CountyWeatherReportData
  const reportData: CountyWeatherReportData = {
    schema_version: mockReport.schema_version || "1.0",
    county_id: mockReport.county_id,
    county_name: mockReport.county_name,
    period: mockReport.period,
    variables: mockReport.variables,
    wards: mockReport.wards.map((w) => ({
      ward_id: w.ward_id,
      ward_name: w.ward_name,
      rainfall_total: w.rainfall_total,
      temp_max: w.temp_max,
      temp_min: w.temp_min,
      temp_mean: w.temp_mean,
      wind_max: w.wind_max,
      wind_mean: w.wind_mean,
      grid_points_used: w.grid_points_used,
      quality_flag: w.quality_flag,
    })),
    extremes: mockReport.extremes,
    metadata: mockReport.metadata,
    disclaimer: mockReport.disclaimer,
    quality_flags: mockReport.quality_flags,
  }
  
  console.log("✅ Schema types are compatible")
  console.log("   - Mock report can be converted to CountyWeatherReportData")
  
  // Validate the converted report
  if (isValidCountyReport(reportData)) {
    console.log("   ✅ Converted report passes validation")
  } else {
    console.log("   ⚠️  Converted report has validation issues")
  }
} catch (error) {
  console.log(`❌ Schema consistency check failed: ${error}`)
}

console.log("\n" + "=".repeat(60))
console.log("VALIDATION COMPLETE")
console.log("=".repeat(60))
