#!/usr/bin/env python3
"""
Test program to lookup routing number for Stock Yards Bank & Trust using OpenAI
"""

import os
import sys
import json
from pathlib import Path

def print_and_log(message):
    """Simple print function"""
    print(message)

def is_valid_routing_number(routing_number):
    """Validate routing number using ABA checksum algorithm"""
    if not routing_number or len(routing_number) != 9 or not routing_number.isdigit():
        return False
        
    # ABA routing number checksum validation
    digits = [int(d) for d in routing_number]
    checksum = (3 * (digits[0] + digits[3] + digits[6]) +
                7 * (digits[1] + digits[4] + digits[7]) +
                1 * (digits[2] + digits[5] + digits[8]))
    
    return checksum % 10 == 0

def lookup_routing_number_by_bank_name(bank_name):
    """Use Azure OpenAI to lookup routing number for a given bank name"""
    print_and_log(f"🤖 Looking up routing number for bank: {bank_name}")
    
    try:
        # Get Azure OpenAI configuration from environment
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        if not endpoint or not api_key or not deployment:
            print_and_log("❌ Azure OpenAI configuration missing from environment variables")
            print_and_log(f"AZURE_OPENAI_ENDPOINT: {endpoint}")
            print_and_log(f"AZURE_OPENAI_KEY: {'***' if api_key else 'Not set'}")
            print_and_log(f"AZURE_OPENAI_DEPLOYMENT: {deployment}")
            return None
        
        print_and_log(f"🔗 OpenAI Endpoint: {endpoint}")
        print_and_log(f"🚀 Using deployment: {deployment}")
        
        # Set up Azure OpenAI client
        from openai import AzureOpenAI
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
        
        print_and_log("📤 Sending request to OpenAI...")
        
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
        print_and_log(f"📥 OpenAI response: '{routing_number}'")
        
        # Validate the response
        if routing_number == "NOT_FOUND":
            print_and_log(f"❌ OpenAI could not find routing number for: {bank_name}")
            return None
        
        # Check if it's a valid 9-digit number
        if routing_number.isdigit() and len(routing_number) == 9:
            if is_valid_routing_number(routing_number):
                print_and_log(f"✅ OpenAI found routing number: {routing_number} for {bank_name}")
                return routing_number
            else:
                print_and_log(f"❌ OpenAI returned invalid routing number: {routing_number}")
                print_and_log(f"   Checksum validation failed")
                return None
        else:
            print_and_log(f"❌ OpenAI returned invalid format: {routing_number}")
            print_and_log(f"   Expected 9 digits, got: {len(routing_number)} characters")
            return None
            
    except Exception as e:
        print_and_log(f"❌ Error looking up routing number with OpenAI: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_routing_lookup():
    """Test routing number lookup for various banks"""
    
    # Load environment variables from local.settings.json
    settings_path = Path(__file__).parent / "local.settings.json"
    if not settings_path.exists():
        print_and_log("❌ local.settings.json not found!")
        return
    
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    
    # Set environment variables
    for key, value in settings["Values"].items():
        os.environ[key] = value
    
    print_and_log("🧪 OPENAI ROUTING NUMBER LOOKUP TEST")
    print_and_log("=" * 60)
    
    # Test cases
    test_banks = [
        "Stock Yards Bank & Trust",
        "Stock Yards Bank",
        "Wells Fargo Bank", 
        "Bank of America",
        "Chase Bank"
    ]
    
    results = {}
    
    for bank_name in test_banks:
        print_and_log(f"\n🏦 Testing: {bank_name}")
        print_and_log("-" * 40)
        
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        results[bank_name] = routing_number
        
        if routing_number:
            print_and_log(f"✅ SUCCESS: {bank_name} -> {routing_number}")
        else:
            print_and_log(f"❌ FAILED: Could not get routing number for {bank_name}")
    
    # Summary
    print_and_log("")
    print_and_log("📊 RESULTS SUMMARY")
    print_and_log("=" * 60)
    
    for bank_name, routing_number in results.items():
        status = "✅" if routing_number else "❌"
        print_and_log(f"{status} {bank_name:<30} -> {routing_number or 'NOT FOUND'}")
    
    # Focus on Stock Yards Bank
    stock_yards_routing = results.get("Stock Yards Bank & Trust") or results.get("Stock Yards Bank")
    
    print_and_log("")
    print_and_log("🎯 STOCK YARDS BANK RESULT")
    print_and_log("-" * 30)
    
    if stock_yards_routing:
        print_and_log(f"🏦 Bank: Stock Yards Bank & Trust")
        print_and_log(f"🔢 Routing Number: {stock_yards_routing}")
        print_and_log(f"✅ Status: Valid ABA routing number")
        
        # Verify checksum
        if is_valid_routing_number(stock_yards_routing):
            print_and_log(f"✅ Checksum: Valid")
        else:
            print_and_log(f"❌ Checksum: Invalid")
    else:
        print_and_log(f"❌ Could not retrieve routing number for Stock Yards Bank")

if __name__ == "__main__":
    test_routing_lookup()
