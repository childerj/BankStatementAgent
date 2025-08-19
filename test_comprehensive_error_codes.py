#!/usr/bin/env python3
"""
Test script to verify BAI2 error codes are correctly set in all scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import create_error_bai2_file

def test_comprehensive_error_codes():
    """Test that error codes are correctly assigned in all scenarios"""
    
    test_cases = [
        # Standard error mappings
        ("No routing number found on statement", "ERROR_NO_ROUTING"),
        ("No account number found on statement", "ERROR_NO_ACCOUNT"),
        ("OpenAI parsing failed - no transaction data available", "ERROR_PARSING_FAILED"),
        ("Bank name extraction failed", "ERROR_NO_BANK_NAME"),
        ("Document Intelligence failed to process", "ERROR_DOC_INTEL_FAILED"),
        ("Unknown error occurred", "ERROR_UNKNOWN"),
        
        # Processing error mappings  
        ("Processing failed: Document Intelligence connection error", "ERROR_DOC_INTEL_FAILED"),
        ("Processing failed: OpenAI timeout", "ERROR_PARSING_FAILED"),
        ("Processing failed: Network connection failed", "ERROR_NETWORK_FAILED"),
        ("Processing failed: Request timeout", "ERROR_TIMEOUT"),
        ("Processing failed: General exception", "ERROR_PROCESSING_FAILED"),
        
        # Edge case variations
        ("ROUTING number is missing from document", "ERROR_NO_ROUTING"),
        ("Account Number could not be found", "ERROR_NO_ACCOUNT"),
        ("Bank Name detection failed", "ERROR_NO_BANK_NAME"),
        ("openai service returned empty", "ERROR_PARSING_FAILED"),
        ("document intelligence service error", "ERROR_DOC_INTEL_FAILED"),
        
        # Custom overrides
        ("Custom message", "ERROR_CUSTOM", "ERROR_CUSTOM"),
        ("Special case", "ERROR_SPECIAL", "ERROR_SPECIAL"),
    ]
    
    print("Testing comprehensive BAI2 error code generation...\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        if len(test_case) == 3:
            error_message, expected_code, explicit_code = test_case
        else:
            error_message, expected_code = test_case
            explicit_code = None
            
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
                passed += 1
            else:
                print(f"  ❌ FAIL: Expected {expected_code}, got {actual_code}")
                failed += 1
        else:
            print(f"  ❌ FAIL: No diagnostic line found")
            failed += 1
        
        print()
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"Success rate: {(passed / (passed + failed)) * 100:.1f}%")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = test_comprehensive_error_codes()
    sys.exit(0 if success else 1)
