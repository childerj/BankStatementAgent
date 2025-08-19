#!/usr/bin/env python3
"""
Test script to verify BAI2 error codes are correctly set
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import create_error_bai2_file

def test_error_codes():
    """Test that error codes are correctly assigned based on error messages"""
    
    test_cases = [
        # Test case: (error_message, expected_error_code, explicit_error_code)
        ("No routing number found on statement", "ERROR_NO_ROUTING", None),
        ("No account number found on statement", "ERROR_NO_ACCOUNT", None),
        ("OpenAI parsing failed - no transaction data available", "ERROR_PARSING_FAILED", None),
        ("Bank name extraction failed", "ERROR_NO_BANK_NAME", None),
        ("Document Intelligence failed to process", "ERROR_DOC_INTEL_FAILED", None),
        ("Unknown error occurred", "ERROR_UNKNOWN", None),
        ("Custom error", "ERROR_CUSTOM", "ERROR_CUSTOM"),  # Explicit override
    ]
    
    print("Testing BAI2 error code generation...\n")
    
    for i, (error_message, expected_code, explicit_code) in enumerate(test_cases, 1):
        print(f"Test {i}: {error_message}")
        
        # Generate BAI2 content
        bai2_content = create_error_bai2_file(
            error_message, 
            "test.pdf", 
            "20250108", 
            "1200",
            explicit_code
        )
        
        # Extract the error code from the diagnostic record (88 record)
        lines = bai2_content.strip().split('\n')
        diagnostic_line = None
        for line in lines:
            if line.startswith('88,999,'):
                diagnostic_line = line
                break
        
        if diagnostic_line:
            # Parse: 88,999,ERROR_CODE,,Z/
            parts = diagnostic_line.split(',')
            actual_code = parts[2] if len(parts) > 2 else "NOT_FOUND"
            
            if actual_code == expected_code:
                print(f"  ✅ PASS: {actual_code}")
            else:
                print(f"  ❌ FAIL: Expected {expected_code}, got {actual_code}")
        else:
            print(f"  ❌ FAIL: No diagnostic line found")
        
        print()

if __name__ == "__main__":
    test_error_codes()
