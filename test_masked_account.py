#!/usr/bin/env python3
"""
Test script to verify masked account numbers with asterisks are properly rejected
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import extract_account_number_from_text, is_valid_account_number

def test_masked_account_numbers():
    """Test various scenarios with masked account numbers"""
    print("🧪 TESTING MASKED ACCOUNT NUMBER DETECTION")
    print("=" * 60)
    
    test_cases = [
        {
            "description": "Account number with asterisks at end",
            "text": "Account Number: 1234****",
            "expected": None
        },
        {
            "description": "Account number with asterisks at beginning", 
            "text": "Account #: ****5678",
            "expected": None
        },
        {
            "description": "Account number with asterisks in middle",
            "text": "Account: 12**5678",
            "expected": None
        },
        {
            "description": "Normal valid numeric account number",
            "text": "Account Number: 1234567890",
            "expected": "1234567890"
        },
        {
            "description": "Valid alphanumeric account number",
            "text": "Account Number: ABC123456789",
            "expected": "abc123456789"
        },
        {
            "description": "Valid account with dashes",
            "text": "Account: 123-456-789",
            "expected": "123-456-789"
        },
        {
            "description": "Alphanumeric with asterisks (masked)",
            "text": "Account: ABC****123",
            "expected": None
        },
        {
            "description": "Multiple asterisks pattern",
            "text": "Account: **********1234",
            "expected": None
        },
        {
            "description": "Single asterisk",
            "text": "Account Number: 123456789*",
            "expected": None
        },
        {
            "description": "Normal account without asterisks",
            "text": "For account 9876543210 ending balance",
            "expected": "9876543210"
        },
        {
            "description": "Alphanumeric account in sentence",
            "text": "For account XYZ987654 ending balance",
            "expected": "xyz987654"
        }
    ]
    
    print("📋 Testing account number extraction:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Text: '{test_case['text']}'")
        
        result = extract_account_number_from_text(test_case['text'])
        expected = test_case['expected']
        
        if result == expected:
            print(f"   ✅ PASS: Got {result} (expected {expected})")
        else:
            print(f"   ❌ FAIL: Got {result} (expected {expected})")
    
    print("\n📋 Testing direct validation:")
    validation_tests = [
        ("1234567890", True),     # Normal numeric account
        ("ABC123456", True),      # Alphanumeric account
        ("123-456-789", True),    # Account with dashes
        ("XY1234Z", True),        # Mixed alphanumeric
        ("****1234", False),      # Masked with asterisks
        ("123*567", False),       # Asterisk in middle
        ("1234****", False),      # Asterisks at end
        ("**1234**", False),      # Asterisks both sides
        ("ABC*123", False),       # Alphanumeric with asterisk
        ("123456", True),         # Short but valid
        ("AB", False),            # Too short (less than 4 chars)
        ("123456789012345678901", True),  # Very long - now allowed
        ("", False),              # Empty
        ("!@#$%", False),         # Special characters only
        ("number", False),        # Common word exclusion
        ("account", False),       # Common word exclusion
        ("balance", False),       # Common word exclusion
    ]
    
    for account_num, expected in validation_tests:
        result = is_valid_account_number(account_num)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"   {status}: '{account_num}' -> {result} (expected {expected})")

if __name__ == "__main__":
    test_masked_account_numbers()
