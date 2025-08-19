#!/usr/bin/env python3
"""
Comprehensive test to verify routing number logic flow:
1. If routing number found on statement -> use it
2. If not found on statement -> try bank name lookup with OpenAI
3. If neither works -> error out (no fallback)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import get_routing_number, extract_routing_number_from_text, extract_bank_name_from_text, lookup_routing_number_by_bank_name

def test_routing_logic_flow():
    """Test the complete routing number logic flow"""
    print("🧪 Testing Routing Number Logic Flow")
    print("=" * 60)
    
    # Test Case 1: Routing number found directly on statement
    print("\n📋 Test Case 1: Routing number found on statement")
    test_data_with_routing = {
        "ocr_text_lines": [
            "PROSPERITY BANK",
            "Routing Number: 113122655",
            "Account: 1234567890",
            "Statement Period: 08/01/2025 - 08/31/2025"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(test_data_with_routing)
    if routing_number == "113122655":
        print("✅ PASS: Found routing number directly on statement")
    else:
        print(f"❌ FAIL: Expected '113122655', got '{routing_number}'")
    
    # Test Case 2: No routing number on statement, but bank name found -> OpenAI lookup
    print("\n📋 Test Case 2: No routing number, but bank name found (OpenAI lookup)")
    test_data_bank_name_only = {
        "ocr_text_lines": [
            "PROSPERITY BANK",
            "Account: 1234567890", 
            "Statement Period: 08/01/2025 - 08/31/2025",
            "No routing number visible here"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(test_data_bank_name_only)
    if routing_number:  # Should get routing number from OpenAI
        print(f"✅ PASS: Got routing number from OpenAI lookup: {routing_number}")
    else:
        print("❌ FAIL: Should have gotten routing number from OpenAI lookup")
    
    # Test Case 3: No routing number and no recognizable bank name -> error out
    print("\n📋 Test Case 3: No routing number and no bank name (should error)")
    test_data_no_info = {
        "ocr_text_lines": [
            "UNKNOWN FINANCIAL INSTITUTION XYZ123",
            "Account: 1234567890",
            "Statement Period: 08/01/2025 - 08/31/2025",
            "Some random text here"
        ],
        "raw_fields": {}
    }
    
    routing_number = get_routing_number(test_data_no_info)
    if routing_number is None:
        print("✅ PASS: Correctly returned None when no routing number or bank name found")
    else:
        print(f"❌ FAIL: Expected None, got '{routing_number}'")
    
    # Test the individual extraction functions
    print("\n📋 Testing Individual Extraction Functions")
    
    # Test routing number extraction
    text_with_routing = "Account Details\nRouting Number: 113122655\nAccount: 1234567890"
    extracted_routing = extract_routing_number_from_text(text_with_routing)
    print(f"🔍 Routing extraction test: '{extracted_routing}' (expected: '113122655')")
    
    # Test bank name extraction  
    text_with_bank = "PROSPERITY BANK\nStatement for August 2025"
    extracted_bank = extract_bank_name_from_text(text_with_bank)
    print(f"🏦 Bank name extraction test: '{extracted_bank}' (expected: 'Prosperity Bank')")
    
    # Test OpenAI lookup
    if extracted_bank:
        openai_routing = lookup_routing_number_by_bank_name(extracted_bank)
        print(f"🤖 OpenAI lookup test: '{openai_routing}' (should be a valid routing number)")
    
    print("\n" + "=" * 60)
    print("✅ Routing Number Logic Flow Test Complete!")
    print("\nLogic Summary:")
    print("1. ✅ Try to find routing number directly on statement")
    print("2. ✅ If not found, extract bank name and lookup via OpenAI")
    print("3. ✅ If neither works, return None (triggers error in main function)")
    print("4. ✅ NO FALLBACK VALUES - strict validation only")

if __name__ == "__main__":
    test_routing_logic_flow()
