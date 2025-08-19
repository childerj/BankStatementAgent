#!/usr/bin/env python3
"""
Test to verify the complete BAI2 error file structure and format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import create_error_bai2_file

def test_bai2_error_file_structure():
    """Test that the complete BAI2 error file structure is correct"""
    
    # Test routing number error
    error_message = "No routing number found on statement"
    bai2_content = create_error_bai2_file(
        error_message, 
        "test_bank_statement.pdf", 
        "20250108", 
        "1200",
        "ERROR_NO_ROUTING"
    )
    
    print("Sample ERROR BAI2 file for routing number issue:")
    print("=" * 60)
    print(bai2_content)
    print("=" * 60)
    
    # Verify the structure
    lines = bai2_content.strip().split('\n')
    
    expected_patterns = [
        ("01", "File Header", lambda line: line.startswith("01,ERROR,WORKDAY,20250108,1200,")),
        ("02", "Group Header", lambda line: line.startswith("02,ERROR,000000000,1,20250108,,USD,")),
        ("03", "Account Identifier", lambda line: line.startswith("03,ERROR,,010,0,")),
        ("88", "Error Diagnostic", lambda line: line.startswith("88,999,ERROR_NO_ROUTING,")),
        ("49", "Account Trailer", lambda line: line.startswith("49,0,3/")),
        ("98", "Group Trailer", lambda line: line.startswith("98,0,1,5/")),
        ("99", "File Trailer", lambda line: line.startswith("99,0,1,7/")),
    ]
    
    print("\nStructure validation:")
    all_valid = True
    
    for i, (record_type, description, validator) in enumerate(expected_patterns):
        if i < len(lines) and validator(lines[i]):
            print(f"  ✅ {record_type} {description}: {lines[i]}")
        else:
            print(f"  ❌ {record_type} {description}: Expected pattern not found")
            if i < len(lines):
                print(f"     Actual: {lines[i]}")
            all_valid = False
    
    # Test different error codes
    print("\nTesting different error codes:")
    error_scenarios = [
        ("ERROR_NO_ROUTING", "No routing number found"),
        ("ERROR_NO_ACCOUNT", "No account number found"),
        ("ERROR_PARSING_FAILED", "OpenAI parsing failed"),
        ("ERROR_DOC_INTEL_FAILED", "Document Intelligence failed"),
        ("ERROR_NETWORK_FAILED", "Network connection failed"),
    ]
    
    for error_code, error_msg in error_scenarios:
        bai2_content = create_error_bai2_file(error_msg, "test.pdf", "20250108", "1200", error_code)
        diagnostic_line = None
        for line in bai2_content.split('\n'):
            if line.startswith('88,999,'):
                diagnostic_line = line
                break
        
        if diagnostic_line and error_code in diagnostic_line:
            print(f"  ✅ {error_code}: {diagnostic_line}")
        else:
            print(f"  ❌ {error_code}: Diagnostic record not found or incorrect")
            all_valid = False
    
    return all_valid

if __name__ == "__main__":
    success = test_bai2_error_file_structure()
    print(f"\nOverall test result: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)
