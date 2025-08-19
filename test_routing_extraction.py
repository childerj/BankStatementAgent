#!/usr/bin/env python3
"""
Test the dynamic routing number extraction functionality
"""

import sys
import os
sys.path.append('.')

from function_app import extract_routing_number_from_text, extract_bank_name_from_text, is_valid_routing_number, get_routing_number, lookup_routing_number_by_bank_name

def test_routing_number_extraction():
    """Test routing number extraction from various text patterns"""
    print("=== Testing Routing Number Extraction ===")
    
    test_cases = [
        "Routing Number: 111903151",
        "RT#: 083000564", 
        "ABA# 121000248",
        "This is a statement with routing 026009593 for the account",
        "Your routing number is 021000021",
        "Transit Number: 111000025",
        "Some random text with no routing number",
        "Invalid routing 123456789",  # Invalid checksum
    ]
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        result = extract_routing_number_from_text(test_text)
        print(f"Result: {result}")

def test_bank_name_extraction():
    """Test bank name extraction"""
    print("\n\n=== Testing Bank Name Extraction ===")
    
    test_cases = [
        "Wells Fargo Bank Statement",
        "Bank of America - Account Summary",
        "Chase Bank Monthly Statement", 
        "First National Bank of Texas",
        "Navy Federal Credit Union",
        "Some text without bank name",
        "Random Bank text here",
    ]
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        result = extract_bank_name_from_text(test_text)
        print(f"Result: {result}")

def test_routing_validation():
    """Test routing number validation"""
    print("\n\n=== Testing Routing Number Validation ===")
    
    test_numbers = [
        "111903151",  # Valid
        "083000564",  # Valid
        "121000248",  # Valid (Wells Fargo)
        "026009593",  # Valid (Bank of America)
        "021000021",  # Valid (Chase)
        "111000025",  # Valid (Navy Federal)
        "123456789",  # Invalid checksum
        "12345678",   # Too short
        "1234567890", # Too long
        "abcdefghi",  # Not numeric
    ]
    
    for number in test_numbers:
        result = is_valid_routing_number(number)
        print(f"'{number}': {result}")

def test_openai_lookup():
    """Test OpenAI bank name lookup (requires API key)"""
    print("\n\n=== Testing OpenAI Bank Lookup ===")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set - skipping OpenAI test")
        return
    
    test_banks = [
        "Wells Fargo Bank",
        "Bank of America", 
        "Chase Bank",
        "Unknown Bank Name",
    ]
    
    for bank_name in test_banks:
        print(f"\nLooking up: {bank_name}")
        try:
            result = lookup_routing_number_by_bank_name(bank_name)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

def test_full_extraction():
    """Test the full get_routing_number function"""
    print("\n\n=== Testing Full Routing Number Extraction ===")
    
    # Mock data like what would come from document intelligence
    test_data = {
        "ocr_text_lines": [
            "WELLS FARGO BANK",
            "Monthly Statement",
            "Account Number: 1234567890",
            "Routing Number: 121000248",
            "Statement Period: July 2024",
        ],
        "raw_fields": {
            "bank_name": {"content": "Wells Fargo Bank", "confidence": 0.95},
            "account_info": {"content": "RT# 121000248", "confidence": 0.88}
        }
    }
    
    print("Testing with mock bank statement data...")
    result = get_routing_number(test_data)
    print(f"Extracted routing number: {result}")
    
    # Test with no routing number but bank name
    test_data2 = {
        "ocr_text_lines": [
            "BANK OF AMERICA",
            "Monthly Statement", 
            "Account Summary",
        ]
    }
    
    print("\nTesting with bank name only...")
    result2 = get_routing_number(test_data2)
    print(f"Extracted routing number: {result2}")

if __name__ == "__main__":
    test_routing_number_extraction()
    test_bank_name_extraction() 
    test_routing_validation()
    test_openai_lookup()
    test_full_extraction()
    
    print("\n✅ All tests completed!")
