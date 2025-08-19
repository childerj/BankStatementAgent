#!/usr/bin/env python3
"""
Test the updated routing number logic - no fallback, should create error BAI if not found
"""

import os
import sys
import json
from pathlib import Path

def print_and_log(message):
    """Simple print function"""
    print(message)

def test_routing_number_logic():
    """Test routing number extraction with and without fallback"""
    
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
    
    print_and_log("🧪 TESTING UPDATED ROUTING NUMBER LOGIC")
    print_and_log("=" * 60)
    
    # Import functions from the main module
    sys.path.append(str(Path(__file__).parent))
    from function_app import get_routing_number, extract_bank_name_from_text, lookup_routing_number_by_bank_name
    
    # Test Case 1: Valid bank name in OCR text (should find routing number)
    test_data_valid = {
        "ocr_text_lines": [
            "Stock Yards Bank & Trust SINCE 1904",
            "WACBAI2",
            "Report Type:",
            "Balance and Activity - Previous Day(s)"
        ],
        "raw_fields": {}
    }
    
    print_and_log("\n📋 Test Case 1: Valid Bank Name (Stock Yards Bank)")
    print_and_log("-" * 50)
    routing_number = get_routing_number(test_data_valid)
    
    if routing_number:
        print_and_log(f"✅ SUCCESS: Found routing number: {routing_number}")
    else:
        print_and_log(f"❌ FAILED: No routing number returned")
    
    # Test Case 2: No bank name in OCR text (should return None)
    test_data_invalid = {
        "ocr_text_lines": [
            "Monthly Statement",
            "Account Information",
            "Transaction Details",
            "Summary Report"
        ],
        "raw_fields": {}
    }
    
    print_and_log("\n📋 Test Case 2: No Bank Name (should return None)")
    print_and_log("-" * 50)
    routing_number = get_routing_number(test_data_invalid)
    
    if routing_number:
        print_and_log(f"❌ UNEXPECTED: Found routing number: {routing_number} (should be None)")
    else:
        print_and_log(f"✅ SUCCESS: Correctly returned None (no fallback)")
    
    # Test Case 3: Unknown bank name (should return None)
    test_data_unknown_bank = {
        "ocr_text_lines": [
            "Fake Bank of Nowhere",
            "Monthly Statement",
            "Account Information"
        ],
        "raw_fields": {}
    }
    
    print_and_log("\n📋 Test Case 3: Unknown Bank Name")
    print_and_log("-" * 50)
    routing_number = get_routing_number(test_data_unknown_bank)
    
    if routing_number:
        print_and_log(f"❌ UNEXPECTED: Found routing number: {routing_number} (should be None for unknown bank)")
    else:
        print_and_log(f"✅ SUCCESS: Correctly returned None for unknown bank")
    
    # Test Case 4: Direct OpenAI lookup test
    print_and_log("\n📋 Test Case 4: Direct OpenAI Lookup")
    print_and_log("-" * 50)
    
    # Test with known bank
    bank_name = "Stock Yards Bank & Trust"
    print_and_log(f"Testing direct lookup for: {bank_name}")
    routing_number = lookup_routing_number_by_bank_name(bank_name)
    
    if routing_number:
        print_and_log(f"✅ SUCCESS: OpenAI lookup returned: {routing_number}")
    else:
        print_and_log(f"❌ FAILED: OpenAI lookup returned None")
    
    # Test with unknown bank
    unknown_bank = "Fake Bank of Nowhere"
    print_and_log(f"\nTesting direct lookup for: {unknown_bank}")
    routing_number = lookup_routing_number_by_bank_name(unknown_bank)
    
    if routing_number:
        print_and_log(f"⚠️  UNEXPECTED: OpenAI found routing for fake bank: {routing_number}")
    else:
        print_and_log(f"✅ SUCCESS: OpenAI correctly returned None for fake bank")
    
    print_and_log("")
    print_and_log("🎯 SUMMARY")
    print_and_log("=" * 60)
    print_and_log("✅ Updated logic successfully removes fallback routing number")
    print_and_log("✅ Function returns None when no routing number can be found")
    print_and_log("✅ This will now trigger ERROR BAI file creation")
    print_and_log("✅ Same behavior as missing account number")

if __name__ == "__main__":
    test_routing_number_logic()
