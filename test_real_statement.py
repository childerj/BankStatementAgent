#!/usr/bin/env python3
"""
Test OpenAI routing number lookup with a real bank statement
"""

import sys
import os

def test_with_real_statement():
    """Test routing number extraction with a real bank statement"""
    
    print("🧪 Testing OpenAI Routing with Real Bank Statement")
    print("=" * 65)
    
    from function_app import process_bank_statement_file
    
    # Test with the Prosperity bank statement
    test_file = "Test Docs/8-1-25_Prosperity.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📄 Processing: {test_file}")
    
    try:
        # Process the real bank statement
        result = process_bank_statement_file(test_file)
        
        if result and "routing_number" in result:
            routing_number = result["routing_number"]
            print(f"✅ Successfully extracted routing number: {routing_number}")
            
            # Validate the routing number
            if routing_number and len(routing_number) == 9 and routing_number.isdigit():
                print(f"✅ Routing number format is valid: {routing_number}")
            else:
                print(f"❌ Invalid routing number format: {routing_number}")
            
            # Check if it was extracted directly or via OpenAI
            if "extraction_method" in result:
                print(f"📊 Extraction method: {result['extraction_method']}")
            
            # Check if bank name was extracted
            if "bank_name" in result:
                print(f"🏦 Bank name: {result['bank_name']}")
        else:
            print("❌ No routing number found in result")
            if result:
                print(f"Available keys: {list(result.keys())}")
    
    except Exception as e:
        print(f"❌ Error processing bank statement: {e}")
        import traceback
        traceback.print_exc()

def test_routing_verification():
    """Test routing number verification logic"""
    
    print("\n🧪 Testing Routing Number Verification")
    print("=" * 50)
    
    from function_app import is_valid_routing_number
    
    test_routing_numbers = [
        ("121000248", True),   # Wells Fargo
        ("026009593", True),   # Bank of America
        ("021000021", True),   # Chase
        ("000000000", False),  # Invalid - all zeros
        ("111111111", False),  # Invalid - all ones
        ("123456789", False),  # Invalid - fake number
        ("12345678", False),   # Invalid - too short
        ("1234567890", False), # Invalid - too long
        ("", False),           # Invalid - empty
        ("abcdefghi", False),  # Invalid - not numeric
    ]
    
    for routing, expected in test_routing_numbers:
        result = is_valid_routing_number(routing)
        status = "✅" if result == expected else "❌"
        print(f"{status} {routing:12} | Valid: {result:5} | Expected: {expected}")

if __name__ == "__main__":
    test_routing_verification()
    test_with_real_statement()
