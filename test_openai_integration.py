#!/usr/bin/env python3
"""
Test OpenAI Integration with proper environment setup
"""

import os
import json
import sys

def load_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            
            # Set environment variables
            for key, value in values.items():
                os.environ[key] = value
                
            print("✅ Loaded local.settings.json successfully")
            return True
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")
        return False

def test_openai_config():
    """Test OpenAI configuration"""
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    print("\n=== OpenAI Configuration Test ===")
    print(f"AZURE_OPENAI_ENDPOINT: {endpoint}")
    print(f"AZURE_OPENAI_KEY: {'***' if api_key else 'Not set'}")
    print(f"AZURE_OPENAI_DEPLOYMENT: {deployment}")
    
    if not endpoint or not api_key or not deployment:
        print("❌ Missing required OpenAI configuration")
        return False
    
    print("✅ All OpenAI configuration present")
    return True

def test_openai_connection():
    """Test actual OpenAI connection"""
    print("\n=== OpenAI Connection Test ===")
    
    try:
        from openai import AzureOpenAI
        
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01"
        )
        
        # Simple test request
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' in one word."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI connection successful. Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_routing_lookup():
    """Test routing number lookup function"""
    print("\n=== Routing Number Lookup Test ===")
    
    # Import the function after setting environment variables
    sys.path.append('.')
    from function_app import lookup_routing_number_by_bank_name
    
    # Test banks
    test_banks = [
        "Wells Fargo Bank",
        "Bank of America",
        "JPMorgan Chase Bank",
        "Citibank",
        "Invalid Bank Name XYZ123"
    ]
    
    for bank_name in test_banks:
        print(f"\nTesting: {bank_name}")
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        
        if routing_number:
            print(f"✅ Found routing number: {routing_number}")
        else:
            print(f"❌ No routing number found")

if __name__ == "__main__":
    print("🧪 OpenAI Integration Test")
    print("=" * 50)
    
    # Load local settings
    if not load_local_settings():
        print("❌ Cannot proceed without local.settings.json")
        sys.exit(1)
    
    # Test configuration
    if not test_openai_config():
        print("❌ Cannot proceed without proper OpenAI configuration")
        sys.exit(1)
    
    # Test connection
    if not test_openai_connection():
        print("❌ OpenAI connection failed")
        sys.exit(1)
    
    # Test routing lookup
    test_routing_lookup()
    
    print("\n✅ OpenAI integration test completed!")
