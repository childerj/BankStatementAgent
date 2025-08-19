#!/usr/bin/env python3
"""
Test OpenAI lookup directly
"""

import json
import os

def test_openai_lookup():
    """Test OpenAI lookup for Prosperity Bank"""
    
    print("🤖 Testing OpenAI Lookup for Prosperity Bank")
    print("=" * 60)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings['Values']
        
        # Get OpenAI config
        endpoint = values.get('AZURE_OPENAI_ENDPOINT')
        api_key = values.get('AZURE_OPENAI_KEY')
        deployment = values.get('AZURE_OPENAI_DEPLOYMENT')
        
        print(f"📋 Configuration:")
        print(f"   Endpoint: {endpoint}")
        print(f"   API Key: {'SET' if api_key else 'NOT SET'}")
        print(f"   Deployment: {deployment}")
        
        if not endpoint or not api_key or not deployment:
            print("❌ Missing OpenAI configuration")
            return
        
        # Test with modern OpenAI client
        from openai import AzureOpenAI
        
        print(f"\n🔧 Creating Azure OpenAI client...")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01"
        )
        
        bank_name = "Prosperity Bank"
        
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
        
        print(f"\n🤖 Making OpenAI API call...")
        print(f"📝 Bank: {bank_name}")
        print(f"📝 Deployment: {deployment}")
        
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
        
        print(f"\n📊 Results:")
        print(f"   Raw response: '{routing_number}'")
        print(f"   Length: {len(routing_number)}")
        print(f"   Is digit: {routing_number.isdigit()}")
        
        if routing_number == "NOT_FOUND":
            print(f"   ❌ OpenAI could not find routing number for {bank_name}")
        elif routing_number.isdigit() and len(routing_number) == 9:
            print(f"   ✅ Valid format: 9-digit number")
            
            # Basic routing number validation (checksum)
            def validate_routing_checksum(routing):
                digits = [int(d) for d in routing]
                checksum = (
                    3 * (digits[0] + digits[3] + digits[6]) +
                    7 * (digits[1] + digits[4] + digits[7]) +
                    1 * (digits[2] + digits[5] + digits[8])
                ) % 10
                return checksum == 0
            
            if validate_routing_checksum(routing_number):
                print(f"   ✅ Valid checksum")
                
                if routing_number.startswith('113'):
                    print(f"   ✅ SUCCESS! Matches Prosperity Bank pattern (113xxxxxx)")
                else:
                    print(f"   ⚠️ Unexpected routing number (expected 113xxxxxx)")
                    print(f"   💡 OpenAI may have found a different Prosperity Bank routing")
            else:
                print(f"   ❌ Invalid checksum")
        else:
            print(f"   ❌ Invalid format (expected 9 digits)")
        
        return routing_number
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_openai_lookup()
    
    print(f"\n🎉 Test Complete!")
    print(f"   Result: {result}")
    
    if result and result != "NOT_FOUND" and len(result) == 9 and result.isdigit():
        print(f"   ✅ SUCCESS! OpenAI integration is working")
    else:
        print(f"   ❌ OpenAI integration needs troubleshooting")
