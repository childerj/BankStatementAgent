#!/usr/bin/env python3
"""
Test the exact bank name extraction logic from function_app.py
"""

import re
import os
import json
from openai import AzureOpenAI

def print_and_log(message):
    """Print with logging prefix"""
    print(f"[TEST] {message}")

def extract_bank_name_from_text(text):
    """Extract bank name from statement text - exact copy from function_app.py"""
    print_and_log("🏦 Searching for bank name in statement text...")
    
    # Common bank name patterns - ordered by specificity (most specific first)
    bank_patterns = [
        r'(Stock\s+Yards\s+Bank(?:\s+&\s+Trust)?)',  # "Stock Yards Bank" or "Stock Yards Bank & Trust"
        r'(Wells\s+Fargo)',  # "Wells Fargo" - specific pattern first
        r'(Bank\s+of\s+[A-Z][a-z]+)',  # "Bank of America"
        r'(Chase)',  # "Chase"
        r'(Citibank)',  # "Citibank"
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+Bank(?:\s+&\s+Trust)?)',  # "First National Bank" or "Stock Yards Bank"
        r'([A-Z][a-z]+\s+National\s+Bank)',  # "First National Bank"
        r'([A-Z][a-z]+\s+Federal\s+Credit\s+Union)',  # "Navy Federal Credit Union"
        r'([A-Z][a-z]+\s+Credit\s+Union)',  # "First Credit Union"
        r'([A-Z][a-z]+\s+Trust)',  # "First Trust"
        r'([A-Z][a-z]+\s+Bank)',  # "First Bank" - more general pattern (last)
        r'([A-Z][a-z]+\s+Financial)',  # "Wells Financial"
        r'([A-Z][a-z]+\s+Federal)',  # "Navy Federal"
        r'([A-Z][a-z]+\s+Savings)',  # "First Savings"
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            bank_name = matches[0].strip()
            print_and_log(f"🏦 Found bank name: {bank_name}")
            return bank_name
    
    # Try to find bank name near common keywords
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if any(keyword in line.lower() for keyword in ['bank', 'financial', 'credit union', 'trust']):
            # Extract bank name from this line
            words = line.split()
            for i, word in enumerate(words):
                if word.lower() in ['bank', 'financial', 'trust']:
                    if i > 0:
                        potential_name = ' '.join(words[max(0, i-2):i+1])
                        print_and_log(f"🏦 Found potential bank name: {potential_name}")
                        return potential_name.strip()
    
    print_and_log("❌ No bank name found in statement text")
    return None

def lookup_routing_number_by_bank_name(bank_name):
    """Use Azure OpenAI to lookup routing number for a given bank name"""
    print_and_log(f"🤖 Looking up routing number for bank: {bank_name}")
    
    try:
        # Load from local settings 
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            endpoint = settings['Values']['AZURE_OPENAI_ENDPOINT']
            api_key = settings['Values']['AZURE_OPENAI_KEY']
            deployment = settings['Values']['AZURE_OPENAI_DEPLOYMENT']
        
        if not endpoint or not api_key or not deployment:
            print_and_log("❌ Azure OpenAI configuration missing")
            return None
        
        # Set up Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01"
        )
        
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
            model=deployment,  # Use the deployment name from environment
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        print_and_log(f"🤖 OpenAI response: '{routing_number}'")
        
        # Validate the response
        if routing_number == "NOT_FOUND":
            print_and_log(f"❌ OpenAI could not find routing number for: {bank_name}")
            return None
        
        # Check if it's a valid 9-digit number
        if routing_number.isdigit() and len(routing_number) == 9:
            print_and_log(f"✅ OpenAI found routing number: {routing_number} for {bank_name}")
            return routing_number
        else:
            print_and_log(f"❌ OpenAI returned invalid format: {routing_number}")
            return None
            
    except Exception as e:
        print_and_log(f"❌ Error looking up routing number with OpenAI: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_exact_function_logic():
    """Test the exact logic from the Azure Function"""
    
    print("🧪 Testing Exact Function Logic")
    print("=" * 50)
    
    # Use the same text that was extracted from the document
    document_text = """Stock Yards Bank & Trust SINCE 1904
WACBAI2
Report Type:
Balance and Activity - Previous Day(s)
Currency:
USD
Customer:
World Finance Company of Kentucky LLC
Created By:
Timothy Sullivan
Created Date/Time:
08/13/2025 09:36 AM
Report Date(s):
08/12/2025 - 08/13/2025
Frequency:
Manual
Account(s) Requested:
2375133 (This report is missing some balance information)"""
    
    print(f"📄 Document text preview:")
    print(f"'{document_text[:200]}...'")
    print()
    
    # Test bank name extraction
    print(f"=== Testing Bank Name Extraction ===")
    bank_name = extract_bank_name_from_text(document_text)
    
    if bank_name:
        print(f"✅ Bank name extracted: '{bank_name}'")
        
        # Test OpenAI lookup
        print(f"\n=== Testing OpenAI Lookup ===")
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        
        if routing_number:
            print(f"✅ SUCCESS! Routing number found: {routing_number}")
        else:
            print(f"❌ OpenAI lookup failed")
    else:
        print(f"❌ No bank name extracted")
    
    print(f"\n=== Summary ===")
    print(f"Bank name extraction: {'✅' if bank_name else '❌'}")
    print(f"OpenAI lookup: {'✅' if bank_name and routing_number else '❌'}")
    
    if bank_name and routing_number:
        print(f"🎉 The function logic SHOULD work!")
        print(f"   Bank: {bank_name}")
        print(f"   Routing: {routing_number}")
        print(f"\n❓ The Azure Function must have failed for a different reason...")
    else:
        print(f"🔍 This explains why the Azure Function failed")

if __name__ == "__main__":
    test_exact_function_logic()
