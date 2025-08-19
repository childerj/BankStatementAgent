#!/usr/bin/env python3
"""
Test OpenAI routing number lookup with proper data structures
"""

import sys
import os

def test_routing_with_proper_data():
    """Test routing number extraction with proper parsed_data structure"""
    
    print("🧪 Testing OpenAI Routing with Proper Data Structures")
    print("=" * 70)
    
    # Import the functions
    from function_app import get_routing_number, lookup_routing_number_by_bank_name
    
    # Test 1: Document with routing number in OCR text
    print("\n=== Test 1: Document with Routing Number ===")
    parsed_data_with_routing = {
        "ocr_text_lines": [
            "Wells Fargo Bank",
            "Account Statement",
            "Routing Number: 121000248",
            "Account Number: 1234567890",
            "Statement Period: 01/01/2025 - 01/31/2025"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(parsed_data_with_routing)
    print(f"Result: {routing_number}")
    if routing_number == "121000248":
        print("✅ Successfully extracted routing number from OCR text")
    else:
        print("❌ Failed to extract routing number from OCR text")
    
    # Test 2: Document with bank name but no routing number
    print("\n=== Test 2: Document with Bank Name Only ===")
    parsed_data_bank_only = {
        "ocr_text_lines": [
            "Bank of America",
            "Checking Account Statement", 
            "Account Number: 9876543210",
            "Statement Period: 01/01/2025 - 01/31/2025",
            "Beginning Balance: $1,000.00"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(parsed_data_bank_only)
    print(f"Result: {routing_number}")
    if routing_number and len(routing_number) == 9 and routing_number.isdigit():
        print("✅ Successfully looked up routing number via OpenAI")
    else:
        print("❌ Failed to lookup routing number via OpenAI")
    
    # Test 3: Document with bank name in raw_fields
    print("\n=== Test 3: Document with Bank Name in Raw Fields ===")
    parsed_data_raw_fields = {
        "ocr_text_lines": [
            "Account Statement",
            "Account Number: 5555555555",
            "Statement Period: 01/01/2025 - 01/31/2025"
        ],
        "raw_fields": {
            "bank_name": {
                "content": "JPMorgan Chase Bank, N.A."
            },
            "account_number": {
                "content": "5555555555"
            }
        }
    }
    
    routing_number = get_routing_number(parsed_data_raw_fields)
    print(f"Result: {routing_number}")
    if routing_number and len(routing_number) == 9 and routing_number.isdigit():
        print("✅ Successfully looked up routing number from raw fields via OpenAI")
    else:
        print("❌ Failed to lookup routing number from raw fields via OpenAI")
    
    # Test 4: Document with no bank information
    print("\n=== Test 4: Document with No Bank Information ===")
    parsed_data_no_bank = {
        "ocr_text_lines": [
            "Account Statement",
            "Account Number: 1111111111",
            "Statement Period: 01/01/2025 - 01/31/2025",
            "Beginning Balance: $500.00"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(parsed_data_no_bank)
    print(f"Result: {routing_number}")
    if routing_number is None:
        print("✅ Correctly returned None for document with no bank info")
    else:
        print("❌ Should have returned None for document with no bank info")
    
    # Test 5: Direct OpenAI lookup tests
    print("\n=== Test 5: Direct OpenAI Lookup Tests ===")
    direct_tests = [
        ("Wells Fargo", "121000248"),
        ("Bank of America", "026009593"),
        ("Chase", "021000021"),
        ("CitiBank", "021000089"),
        ("Unknown Bank XYZ", None)
    ]
    
    for bank_name, expected in direct_tests:
        result = lookup_routing_number_by_bank_name(bank_name)
        print(f"Bank: {bank_name:20} | Result: {result:12} | Expected: {expected}")
        
        if expected is None and result is None:
            print("  ✅ Correctly returned None for unknown bank")
        elif result == expected:
            print("  ✅ Correct routing number returned")
        elif result and len(result) == 9 and result.isdigit():
            print(f"  ⚠️ Different but valid routing number (expected {expected}, got {result})")
        else:
            print("  ❌ Incorrect result")
    
    print("\n🎉 OpenAI routing number test with proper data structures completed!")

if __name__ == "__main__":
    test_routing_with_proper_data()
