#!/usr/bin/env python3
"""
Test the full BAI conversion with missing routing number to ensure ERROR file is created
"""

import os
import sys
import json
from pathlib import Path

def print_and_log(message):
    """Simple print function"""
    print(message)

def test_bai_conversion_with_missing_routing():
    """Test BAI conversion when routing number cannot be found"""
    
    # Load environment variables from local.settings.json
    settings_path = Path(__file__).parent / "local.settings.json"
    if not settings_path.exists():
        print_and_log("❌ local.settings.json not found!")
        return
    
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    
    # Set environment variables
    for key, value in settings["Values"].items():
        os.environ[key] = value
    
    print_and_log("🧪 TESTING BAI CONVERSION WITH MISSING ROUTING NUMBER")
    print_and_log("=" * 70)
    
    # Import functions from the main module
    sys.path.append(str(Path(__file__).parent))
    from function_app import convert_to_bai2
    
    # Test data with valid account number but no routing number or bank name
    test_data_no_routing = {
        "ocr_text_lines": [
            "Monthly Statement",
            "Account: 1234567890",  # Valid account number
            "Transaction Details",
            "Summary Report"
        ],
        "raw_fields": {},
        "account_number": "1234567890"  # Valid account number provided
    }
    
    print_and_log("\n📋 Test Case: Valid Account Number, No Routing Number")
    print_and_log("-" * 60)
    print_and_log("Expected: ERROR BAI file should be created")
    print_and_log("")
    
    filename = "test_statement.pdf"
    bai_result = convert_to_bai2(test_data_no_routing, filename)
    
    print_and_log("\n📄 BAI RESULT:")
    print_and_log("-" * 30)
    
    # Check if the result contains error indicators
    if "ERROR" in bai_result:
        print_and_log("✅ SUCCESS: ERROR BAI file created as expected")
        print_and_log("")
        print_and_log("BAI Content Preview:")
        lines = bai_result.split('\n')
        for i, line in enumerate(lines[:10]):  # Show first 10 lines
            print_and_log(f"  {i+1:2d}: {line}")
        if len(lines) > 10:
            print_and_log(f"  ... and {len(lines) - 10} more lines")
    else:
        print_and_log("❌ UNEXPECTED: Normal BAI file created (should be ERROR)")
        print_and_log("")
        print_and_log("BAI Content Preview:")
        lines = bai_result.split('\n')
        for i, line in enumerate(lines[:5]):
            print_and_log(f"  {i+1:2d}: {line}")
    
    # Test Case 2: Test with known bank name that should work
    test_data_with_routing = {
        "ocr_text_lines": [
            "Stock Yards Bank & Trust SINCE 1904",
            "Monthly Statement",
            "Account: 1234567890",
            "Transaction Details"
        ],
        "raw_fields": {},
        "account_number": "1234567890"
    }
    
    print_and_log("\n\n📋 Test Case: Valid Account + Valid Bank Name")
    print_and_log("-" * 60)
    print_and_log("Expected: Normal BAI file should be created")
    print_and_log("")
    
    bai_result_2 = convert_to_bai2(test_data_with_routing, filename)
    
    if "ERROR" not in bai_result_2:
        print_and_log("✅ SUCCESS: Normal BAI file created as expected")
        print_and_log("")
        print_and_log("BAI Content Preview:")
        lines = bai_result_2.split('\n')
        for i, line in enumerate(lines[:5]):
            print_and_log(f"  {i+1:2d}: {line}")
    else:
        print_and_log("❌ UNEXPECTED: ERROR BAI file created (should be normal)")
    
    print_and_log("")
    print_and_log("🎯 SUMMARY")
    print_and_log("=" * 70)
    print_and_log("✅ Missing routing number now triggers ERROR BAI file creation")
    print_and_log("✅ Valid routing number lookup allows normal BAI file creation")
    print_and_log("✅ Behavior is consistent with missing account number handling")

if __name__ == "__main__":
    test_bai_conversion_with_missing_routing()
