#!/usr/bin/env python3
"""
Test the fixed OpenAI routing number lookup functionality
"""

import sys
import os

def test_routing_lookup_fixed():
    """Test that routing number lookup now works correctly"""
    
    print("🧪 Testing Fixed OpenAI Routing Number Lookup")
    print("=" * 60)
    
    # Import the function (this should now automatically load local settings)
    from function_app import lookup_routing_number_by_bank_name, extract_bank_name_from_text, get_routing_number
    
    # Test 1: Direct lookup function
    print("\n=== Test 1: Direct Lookup Function ===")
    test_banks = [
        "Wells Fargo Bank",
        "Bank of America", 
        "JPMorgan Chase Bank",
        "Unknown Bank XYZ123"
    ]
    
    for bank_name in test_banks:
        print(f"\nTesting: {bank_name}")
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        
        if routing_number:
            print(f"✅ Success: {routing_number}")
        else:
            print(f"❌ No routing number found")
    
    # Test 2: Bank name extraction from text
    print("\n\n=== Test 2: Bank Name Extraction ===")
    test_texts = [
        "Statement from Wells Fargo Bank for account ending in 1234",
        "Bank of America account summary for period ending 12/31/2024",
        "JPMorgan Chase Bank checking account statement",
        "Random bank text without clear bank name"
    ]
    
    for text in test_texts:
        print(f"\nText: {text[:50]}...")
        bank_name = extract_bank_name_from_text(text)
        print(f"Extracted bank: {bank_name}")
        
        if bank_name:
            routing_number = lookup_routing_number_by_bank_name(bank_name)
            print(f"Routing number: {routing_number}")
    
    # Test 3: Full routing number extraction pipeline
    print("\n\n=== Test 3: Full Pipeline Test ===")
    
    # Simulate documents with different routing number scenarios
    test_scenarios = [
        {
            "description": "Document with routing number in text",
            "document_text": "Wells Fargo Bank statement. Routing number: 121000248. Account: 1234567890",
            "expected_routing": "121000248",
            "should_use_openai": False
        },
        {
            "description": "Document with bank name but no routing number",
            "document_text": "Bank of America checking account statement. Account number: 9876543210",
            "expected_bank": "Bank of America",
            "should_use_openai": True
        },
        {
            "description": "Document with no routing or bank info",
            "document_text": "Generic bank statement with account 5555555555",
            "should_fail": True
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['description']} ---")
        print(f"Text: {scenario['document_text'][:80]}...")
        
        # Test the full get_routing_number function
        routing_number = get_routing_number(scenario['document_text'])
        
        if routing_number:
            print(f"✅ Found routing number: {routing_number}")
        else:
            print(f"❌ No routing number found")
            if scenario.get('should_fail'):
                print("✅ Expected failure - test passed")
    
    print("\n🎉 Fixed OpenAI routing number lookup test completed!")

if __name__ == "__main__":
    test_routing_lookup_fixed()
