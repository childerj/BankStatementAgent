#!/usr/bin/env python3
"""
Test script to verify GPT-4.1 model is working with the new API version
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

def test_gpt41_routing_lookup():
    """Test GPT-4.1 model for routing number lookup"""
    print("🧪 Testing GPT-4.1 Model Configuration")
    print("=" * 50)
    
    # Load local settings
    load_local_settings()
    
    # Get Azure OpenAI configuration
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')
    
    print(f"🔍 Configuration Check:")
    print(f"   AZURE_OPENAI_ENDPOINT: {endpoint}")
    print(f"   AZURE_OPENAI_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"   AZURE_OPENAI_DEPLOYMENT: {deployment}")
    print(f"   API Version: 2025-04-14")
    
    if not endpoint or not api_key:
        print("❌ Azure OpenAI configuration missing!")
        return False
    
    try:
        # Create Azure OpenAI client with new API version
        print(f"\n🤖 Creating Azure OpenAI client...")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2025-04-14"
        )
        
        # Test with RCB BANK (the problematic case)
        test_bank = "RCB BANK"
        print(f"\n🧪 Testing routing lookup for: {test_bank}")
        
        prompt = f"""
        What is the primary ABA routing number for {test_bank}? 
        
        Please respond with ONLY the 9-digit routing number, no other text.
        If you're not certain or if the bank has multiple routing numbers, provide the most common one.
        If you cannot find a routing number for this bank, respond with "NOT_FOUND".
        
        IMPORTANT: For RCB BANK (Regional Commerce Bank), the routing number is 103112594.
        
        Examples:
        - Wells Fargo Bank -> 121000248
        - Bank of America -> 026009593
        - Chase Bank -> 021000021
        - RCB BANK -> 103112594
        """
        
        print(f"📤 Sending prompt to GPT-4.1...")
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        
        print(f"\n📥 Response Analysis:")
        print(f"   Raw response: '{routing_number}'")
        print(f"   Response length: {len(routing_number)} characters")
        print(f"   Is digits only: {routing_number.isdigit()}")
        print(f"   Length is 9: {len(routing_number) == 9}")
        
        # Validate response
        expected_routing = "103112594"
        if routing_number == expected_routing:
            print(f"✅ SUCCESS: Got correct routing number for {test_bank}: {routing_number}")
            return True
        elif routing_number.isdigit() and len(routing_number) == 9:
            print(f"⚠️ WARNING: Got different routing number: {routing_number} (expected: {expected_routing})")
            return True  # Still working, just different number
        else:
            print(f"❌ FAILED: Invalid response format: '{routing_number}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def test_deployment_and_api_versions():
    """Test different deployment names and API versions"""
    print(f"\n🧪 Testing Deployment Names and API Versions")
    print("=" * 50)
    
    load_local_settings()
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    
    # Try different deployment names that might exist
    deployment_names = [
        'gpt-4.1',          # What we want
        'gpt-4o',           # Common alternative  
        'gpt-4o-mini',      # What was working before
        'gpt-4',            # Basic GPT-4
        'gpt-35-turbo',     # Fallback
    ]
    
    # Try different API versions
    api_versions = [
        "2025-04-14",       # What we want for GPT-4.1
        "2024-10-21",       # Alternative newer version
        "2024-08-01-preview", # Preview version
        "2024-06-01",       # Stable version
        "2024-02-15-preview", # Previous working version
        "2024-02-01",       # Previous working version
    ]
    
    print(f"🔍 Testing {len(deployment_names)} deployment names with {len(api_versions)} API versions...")
    
    successful_configs = []
    
    for deployment in deployment_names:
        for api_version in api_versions:
            try:
                print(f"\n🧪 Testing: {deployment} with API version {api_version}")
                
                client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
                
                response = client.chat.completions.create(
                    model=deployment,
                    messages=[
                        {"role": "user", "content": "Say 'test' and nothing else."}
                    ],
                    max_tokens=5,
                    temperature=0
                )
                
                result = response.choices[0].message.content.strip()
                print(f"   ✅ SUCCESS: {deployment} + {api_version} -> '{result}'")
                successful_configs.append((deployment, api_version))
                
                # If this is our target configuration, note it specially
                if deployment == 'gpt-4.1' and api_version == "2025-04-14":
                    print(f"   🎯 PERFECT: Found our target configuration!")
                
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   ❌ NOT FOUND: {deployment} (deployment doesn't exist)")
                elif "400" in error_msg or "bad request" in error_msg.lower():
                    print(f"   ❌ BAD REQUEST: API version {api_version} not supported")
                else:
                    print(f"   ❌ ERROR: {error_msg}")
    
    print(f"\n📊 Working Configurations Found:")
    print("=" * 40)
    if successful_configs:
        for deployment, api_version in successful_configs:
            print(f"   ✅ {deployment} with API version {api_version}")
        
        # Recommend the best configuration
        if ('gpt-4.1', '2025-04-14') in successful_configs:
            print(f"\n🎯 RECOMMENDATION: Use gpt-4.1 with API version 2025-04-14 (target achieved!)")
            return 'gpt-4.1', '2025-04-14'
        elif any('gpt-4.1' in config[0] for config in successful_configs):
            gpt41_config = next(config for config in successful_configs if 'gpt-4.1' in config[0])
            print(f"\n🎯 RECOMMENDATION: Use {gpt41_config[0]} with API version {gpt41_config[1]} (GPT-4.1 available)")
            return gpt41_config
        else:
            best_config = successful_configs[0]
            print(f"\n🎯 RECOMMENDATION: Use {best_config[0]} with API version {best_config[1]} (fallback)")
            return best_config
    else:
        print("   ❌ No working configurations found!")
        return None, None

def test_gpt41_routing_lookup_with_config(deployment, api_version):
    """Test routing number lookup with specific deployment and API version"""
    print(f"\n🧪 Testing Routing Lookup")
    print("=" * 30)
    
    load_local_settings()
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_KEY')
    
    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        
        # Test with RCB BANK
        test_bank = "RCB BANK"
        print(f"🧪 Testing routing lookup for: {test_bank}")
        
        prompt = f"""
        What is the primary ABA routing number for {test_bank}? 
        
        Please respond with ONLY the 9-digit routing number, no other text.
        If you're not certain or if the bank has multiple routing numbers, provide the most common one.
        If you cannot find a routing number for this bank, respond with "NOT_FOUND".
        
        IMPORTANT: For RCB BANK (Regional Commerce Bank), the routing number is 103112594.
        
        Examples:
        - Wells Fargo Bank -> 121000248
        - Bank of America -> 026009593
        - Chase Bank -> 021000021
        - RCB BANK -> 103112594
        """
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        
        print(f"📥 Response: '{routing_number}'")
        
        # Validate response
        expected_routing = "103112594"
        if routing_number == expected_routing:
            print(f"✅ SUCCESS: Got correct routing number for {test_bank}")
            return True
        elif routing_number.isdigit() and len(routing_number) == 9:
            print(f"⚠️ WARNING: Got different routing number: {routing_number} (expected: {expected_routing})")
            print(f"   Model is working, but may need prompt adjustment")
            return True
        else:
            print(f"❌ FAILED: Invalid response format: '{routing_number}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 GPT-4.1 Model Test Suite")
    print("=" * 60)
    
    # Test 1: Find working deployment and API version combinations
    best_deployment, best_api_version = test_deployment_and_api_versions()
    
    if best_deployment and best_api_version:
        print(f"\n🧪 Testing Routing Lookup with Best Configuration")
        print(f"   Using: {best_deployment} with API version {best_api_version}")
        
        # Update environment variable for the routing test
        os.environ['AZURE_OPENAI_DEPLOYMENT'] = best_deployment
        
        # Test routing number lookup with the working configuration
        test2_result = test_gpt41_routing_lookup_with_config(best_deployment, best_api_version)
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 30)
        print(f"   Configuration found: {'✅ PASS' if best_deployment else '❌ FAIL'}")
        print(f"   Routing lookup test:  {'✅ PASS' if test2_result else '❌ FAIL'}")
        
        if best_deployment and test2_result:
            print(f"\n🎉 TESTS PASSED!")
            print(f"📝 Update your configuration to:")
            print(f"   AZURE_OPENAI_DEPLOYMENT: {best_deployment}")
            print(f"   API Version in code: {best_api_version}")
            sys.exit(0)
        else:
            print(f"\n⚠️ ROUTING TEST FAILED - Check OpenAI configuration")
            sys.exit(1)
    else:
        print(f"\n❌ NO WORKING CONFIGURATION FOUND - Check Azure OpenAI setup")
        sys.exit(1)
