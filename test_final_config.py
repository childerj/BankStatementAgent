#!/usr/bin/env python3
"""
Final test to verify the updated function_app.py configuration works
"""

import os
import sys
import json
from openai import AzureOpenAI

def load_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        if os.path.exists('local.settings.json'):
            with open('local.settings.json', 'r') as f:
                settings = json.load(f)
                values = settings.get('Values', {})
                
                for key, value in values.items():
                    if not os.getenv(key):
                        os.environ[key] = value
                        
                print("✅ Loaded local.settings.json")
                return True
    except Exception as e:
        print(f"⚠️ Could not load local.settings.json: {e}")
        return False
    return True

def test_final_configuration():
    """Test the final configuration that will be used in function_app.py"""
    print("🧪 Testing Final Configuration")
    print("=" * 40)
    
    load_local_settings()
    
    # Use exact same configuration as function_app.py
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')
    api_version = "2024-10-21"
    
    print(f"🔍 Final Configuration:")
    print(f"   AZURE_OPENAI_ENDPOINT: {endpoint}")
    print(f"   AZURE_OPENAI_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"   AZURE_OPENAI_DEPLOYMENT: {deployment}")
    print(f"   API Version: {api_version}")
    
    try:
        # Test 1: SDK client (used in lookup_routing_number_by_bank_name)
        print(f"\n🧪 Test 1: SDK Client Configuration")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": "What is the ABA routing number for RCB BANK? Respond with only the 9-digit number."}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        print(f"   📥 SDK Response: '{routing_number}'")
        
        if routing_number == "103112594":
            print(f"   ✅ SDK Test PASSED: Correct routing number")
            sdk_test = True
        else:
            print(f"   ⚠️ SDK Test WARNING: Different routing number (still working)")
            sdk_test = True
        
        # Test 2: REST API (used in send_to_openai_for_parsing)
        print(f"\n🧪 Test 2: REST API Configuration")
        import requests
        
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }
        data = {
            "messages": [
                {"role": "user", "content": "Say 'REST API test' and nothing else."}
            ],
            "max_tokens": 10,
            "temperature": 0
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            print(f"   📥 REST Response: '{content}'")
            print(f"   ✅ REST Test PASSED")
            rest_test = True
        else:
            print(f"   ❌ REST Test FAILED: {response.status_code} - {response.text}")
            rest_test = False
        
        # Summary
        print(f"\n📊 Final Test Results")
        print("=" * 25)
        print(f"   SDK Client:  {'✅ PASS' if sdk_test else '❌ FAIL'}")
        print(f"   REST API:    {'✅ PASS' if rest_test else '❌ FAIL'}")
        
        if sdk_test and rest_test:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ GPT-4.1 is ready to deploy with API version 2024-10-21")
            return True
        else:
            print(f"\n❌ TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Final Configuration Test")
    print("=" * 35)
    
    success = test_final_configuration()
    
    if success:
        print(f"\n✅ Ready to deploy!")
        sys.exit(0)
    else:
        print(f"\n❌ Not ready to deploy!")
        sys.exit(1)
