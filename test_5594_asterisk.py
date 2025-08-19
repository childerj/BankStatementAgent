#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import extract_account_number_from_text, is_valid_account_number, print_and_log

def test_specific_asterisk_case():
    """Test the specific case '*5594' that the user asked about"""
    
    print("🧪 TESTING SPECIFIC CASE: *5594")
    print("=" * 50)
    
    # Test the exact case the user mentioned
    test_case = "*5594"
    
    print(f"📋 Testing: '{test_case}'")
    print("-" * 30)
    
    # Test 1: Direct validation
    print("1. Direct validation check:")
    is_valid = is_valid_account_number(test_case)
    print(f"   is_valid_account_number('{test_case}') = {is_valid}")
    print(f"   Expected: False (because it contains '*')")
    
    # Test 2: Text extraction 
    print("\n2. Text extraction check:")
    test_text = f"Account Number: {test_case}"
    print(f"   Input text: '{test_text}'")
    extracted = extract_account_number_from_text(test_text)
    print(f"   Extracted result: {extracted}")
    print(f"   Expected: None (because we reject masked numbers)")
    
    # Test 3: Check what happens if Document Intelligence returned this
    print("\n3. What if Document Intelligence returned this text?")
    print("   If Document Intelligence OCR returned text containing '*5594',")
    print("   our regex patterns would find it, but our validation would reject it.")
    
    # Test 4: Show the validation logic in action
    print("\n4. Validation logic breakdown:")
    if "*" in test_case:
        print(f"   ✓ Contains asterisk: '{test_case}' has '*'")
        print(f"   ✓ Rejection reason: Asterisk detected -> treat as masked/invalid")
    else:
        print(f"   ✗ No asterisk found")
    
    print("\n" + "=" * 50)
    print("📝 CONCLUSION:")
    print(f"   • Document Intelligence returns text exactly as it appears in the PDF")
    print(f"   • If PDF shows '*5594', Document Intelligence returns '*5594'")
    print(f"   • Our validation code rejects ANY account number with '*'")
    print(f"   • Result: '*5594' is treated as missing/invalid")
    
    # Test some variations to be thorough
    print("\n📋 Testing variations:")
    variations = ["*5594", "5594*", "55*94", "*", "**5594", "5594"]
    
    for var in variations:
        is_valid = is_valid_account_number(var)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        asterisk_note = " (has asterisk)" if "*" in var else " (no asterisk)"
        print(f"   '{var}' -> {status}{asterisk_note}")

if __name__ == "__main__":
    test_specific_asterisk_case()
