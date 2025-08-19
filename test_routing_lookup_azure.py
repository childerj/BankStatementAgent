#!/usr/bin/env python3
"""
Test Bank Routing Number Lookup Functionality with Azure OpenAI
Tests the OpenAI-powered bank name to routing number lookup using Azure OpenAI
"""
import os
import json
from openai import AzureOpenAI
import re

def is_valid_routing_number(routing_number):
    """Basic validation of routing number using checksum algorithm"""
    if not routing_number or len(routing_number) != 9 or not routing_number.isdigit():
        return False
    
    # ABA routing number checksum validation
    digits = [int(d) for d in routing_number]
    checksum = (3 * (digits[0] + digits[3] + digits[6]) +
                7 * (digits[1] + digits[4] + digits[7]) +
                1 * (digits[2] + digits[5] + digits[8]))
    
    return checksum % 10 == 0

def load_local_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('Values', {})
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")
        return {}

def lookup_routing_number_by_bank_name(bank_name, client, deployment_name):
    """Use Azure OpenAI to lookup routing number for a given bank name"""
    print(f"🤖 Looking up routing number for bank: {bank_name}")
    
    try:
        prompt = f"""
        What is the primary ABA routing number for {bank_name}? 
        
        Please respond with ONLY the 9-digit routing number, no other text.
        If you're not certain or if the bank has multiple routing numbers, provide the most common one.
        If you cannot find a routing number for this bank, respond with "NOT_FOUND".
        
        Examples:
        - Wells Fargo Bank -> 121000248
        - Bank of America -> 026009593
        - Chase Bank -> 021000021
        """
        
        response = client.chat.completions.create(
            model=deployment_name,  # Use the actual deployment name
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        
        # Validate the response
        if routing_number == "NOT_FOUND":
            print(f"❌ OpenAI could not find routing number for: {bank_name}")
            return None
        
        # Check if it's a valid 9-digit number
        if routing_number.isdigit() and len(routing_number) == 9:
            if is_valid_routing_number(routing_number):
                print(f"✅ OpenAI found routing number: {routing_number} for {bank_name}")
                return routing_number
            else:
                print(f"❌ OpenAI returned invalid routing number: {routing_number}")
                return None
        else:
            print(f"❌ OpenAI returned invalid format: {routing_number}")
            return None
            
    except Exception as e:
        print(f"❌ Error looking up routing number with OpenAI: {str(e)}")
        return None

def extract_bank_name_from_text(text):
    """Extract bank name from statement text"""
    print(f"🏦 Searching for bank name in text: '{text[:100]}...'")
    
    # Common bank name patterns - ordered by specificity
    bank_patterns = [
        r'(Wells\s+Fargo)',  # "Wells Fargo" - specific pattern first
        r'(Bank\s+of\s+[A-Z][a-z]+)',  # "Bank of America"
        r'(Chase)',  # "Chase"
        r'(Citibank)',  # "Citibank"
        r'([A-Z][a-z]+\s+National\s+Bank)',  # "First National Bank"
        r'([A-Z][a-z]+\s+Federal\s+Credit\s+Union)',  # "Navy Federal Credit Union"
        r'([A-Z][a-z]+\s+Credit\s+Union)',  # "First Credit Union"
        r'([A-Z][a-z]+\s+Trust)',  # "First Trust"
        r'([A-Z][a-z]+\s+Bank)',  # "First Bank" - more general pattern
        r'([A-Z][a-z]+\s+Financial)',  # "Wells Financial"
        r'([A-Z][a-z]+\s+Federal)',  # "Navy Federal"
        r'([A-Z][a-z]+\s+Savings)',  # "First Savings"
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        if matches:
            bank_name = matches[0].strip()
            print(f"✅ Found bank name: {bank_name}")
            return bank_name
    
    print("❌ No bank name pattern found")
    return None

def test_bank_name_extraction():
    """Test bank name extraction from various text samples"""
    print("\n" + "="*50)
    print("TESTING BANK NAME EXTRACTION")
    print("="*50)
    
    test_texts = [
        "Wells Fargo Bank Statement for Account 123456789",
        "Bank of America Statement - Account #987654321",
        "Chase Bank Monthly Statement",
        "First National Bank - Account Summary",
        "Navy Federal Credit Union Statement",
        "Prosperity Bank - Account Information",
        "Stockyards Bank Statement",
        "Generic statement with no bank name mentioned"
    ]
    
    results = []
    for text in test_texts:
        print(f"\n📄 Testing: '{text}'")
        bank_name = extract_bank_name_from_text(text)
        results.append((text, bank_name))
    
    return results

def test_routing_number_lookup():
    """Test routing number lookup with real bank names"""
    print("\n" + "="*50)
    print("TESTING ROUTING NUMBER LOOKUP")
    print("="*50)
    
    # Load Azure OpenAI settings
    settings = load_local_settings()
    
    endpoint = settings.get('AZURE_OPENAI_ENDPOINT')
    api_key = settings.get('AZURE_OPENAI_KEY')
    deployment = settings.get('AZURE_OPENAI_DEPLOYMENT')
    
    if not endpoint or not api_key or not deployment:
        print("❌ Azure OpenAI configuration missing from local.settings.json")
        print(f"AZURE_OPENAI_ENDPOINT: {endpoint}")
        print(f"AZURE_OPENAI_KEY: {'***' if api_key else 'Not set'}")
        print(f"AZURE_OPENAI_DEPLOYMENT: {deployment}")
        return []
    
    print(f"✅ Azure OpenAI configured:")
    print(f"   Endpoint: {endpoint}")
    print(f"   Deployment: {deployment}")
    
    # Set up Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-01"
    )
    
    test_banks = [
        "Wells Fargo Bank",
        "Bank of America",
        "Chase Bank",
        "Prosperity Bank",
        "Navy Federal Credit Union"
    ]
    
    results = []
    for bank_name in test_banks:
        print(f"\n🏦 Testing: {bank_name}")
        routing_number = lookup_routing_number_by_bank_name(bank_name, client, deployment)
        results.append((bank_name, routing_number))
    
    return results

def test_routing_number_validation():
    """Test routing number validation"""
    print("\n" + "="*50)
    print("TESTING ROUTING NUMBER VALIDATION")
    print("="*50)
    
    test_numbers = [
        ("121000248", True),   # Valid Wells Fargo
        ("026009593", True),   # Valid Bank of America
        ("021000021", True),   # Valid Chase
        ("123456789", False),  # Invalid checksum
        ("12345678", False),   # Too short
        ("1234567890", False), # Too long
        ("abcdefghi", False),  # Not digits
        ("", False),           # Empty
        (None, False)          # None
    ]
    
    results = []
    for routing_number, expected in test_numbers:
        is_valid = is_valid_routing_number(routing_number)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} {routing_number}: {is_valid} (expected {expected})")
        results.append((routing_number, is_valid, expected))
    
    return results

def main():
    """Run all tests"""
    print("🧪 BANK ROUTING NUMBER LOOKUP TESTS")
    print("=" * 60)
    
    # Test 1: Bank name extraction
    extraction_results = test_bank_name_extraction()
    
    # Test 2: Routing number validation
    validation_results = test_routing_number_validation()
    
    # Test 3: OpenAI routing number lookup
    lookup_results = test_routing_number_lookup()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print(f"\n📊 Bank Name Extraction Results:")
    successful_extractions = sum(1 for _, name in extraction_results if name)
    print(f"   Successful: {successful_extractions}/{len(extraction_results)}")
    
    print(f"\n📊 Routing Number Validation Results:")
    correct_validations = sum(1 for _, actual, expected in validation_results if actual == expected)
    print(f"   Correct: {correct_validations}/{len(validation_results)}")
    
    print(f"\n📊 OpenAI Lookup Results:")
    successful_lookups = sum(1 for _, routing in lookup_results if routing)
    print(f"   Successful: {successful_lookups}/{len(lookup_results)}")
    
    # Overall result
    total_tests = len(extraction_results) + len(validation_results) + len(lookup_results)
    total_passed = successful_extractions + correct_validations + successful_lookups
    
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check output above")

if __name__ == "__main__":
    main()
