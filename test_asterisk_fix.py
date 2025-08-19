#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import extract_account_number_from_text, is_valid_account_number, print_and_log

def test_asterisk_capture_fix():
    """Test that we now properly capture and reject *5594"""
    
    print("🧪 TESTING ASTERISK CAPTURE FIX")
    print("=" * 50)
    
    test_cases = [
        {
            "input": "Account Number: *5594",
            "expected_extract": None,     # Should be rejected as invalid
            "expected_valid": "N/A",      # N/A because it should not be extracted
            "description": "Leading asterisk case"
        },
        {
            "input": "Account Number: 5594*",
            "expected_extract": None,     # Should be rejected as invalid
            "expected_valid": "N/A",      # N/A because it should not be extracted
            "description": "Trailing asterisk case"
        },
        {
            "input": "Account Number: 55*94",
            "expected_extract": None,     # Should be rejected as invalid
            "expected_valid": "N/A",      # N/A because it should not be extracted
            "description": "Middle asterisk case"
        },
        {
            "input": "Account Number: 1234567890",
            "expected_extract": "1234567890",  # Should capture normal account number
            "expected_valid": True,             # Should be valid (no asterisk)
            "description": "Normal account number"
        },
        {
            "input": "Account Number: ****5594",
            "expected_extract": None,    # Should be rejected as invalid
            "expected_valid": "N/A",     # N/A because it should not be extracted
            "description": "Multiple asterisks case"
        }
    ]
    
    print("📋 Testing extraction and validation:")
    print("-" * 50)
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['description']}")
        print(f"   Input: '{case['input']}'")
        
        # Test extraction
        extracted = extract_account_number_from_text(case['input'])
        print(f"   Extracted: {extracted}")
        print(f"   Expected:  {case['expected_extract']}")
        
        if extracted == case['expected_extract']:
            print("   ✅ Extraction: PASS")
        else:
            print("   ❌ Extraction: FAIL")
            all_passed = False
        
        # Test validation (only if we got something)
        if extracted is not None:
            is_valid = is_valid_account_number(extracted)
            print(f"   Valid: {is_valid}")
            print(f"   Expected Valid: {case['expected_valid']}")
            
            if is_valid == case['expected_valid']:
                print("   ✅ Validation: PASS")
            else:
                print("   ❌ Validation: FAIL")
                all_passed = False
        else:
            if case['expected_valid'] == "N/A":
                print("   ✅ Validation: PASS (correctly rejected)")
            else:
                print("   ⚠️  No extraction - validation skipped")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The fix correctly captures asterisks and rejects masked account numbers")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 The regex patterns may need further adjustment")

if __name__ == "__main__":
    test_asterisk_capture_fix()
