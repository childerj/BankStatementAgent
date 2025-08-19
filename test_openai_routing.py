#!/usr/bin/env python3
"""
Test OpenAI routing number lookup for Stock Yards Bank & Trust
"""

import json
import openai
from openai import AzureOpenAI

def test_openai_routing_lookup():
    """Test OpenAI lookup for Stock Yards Bank routing number"""
    
    print("🧪 Testing OpenAI Routing Number Lookup")
    print("=" * 50)
    
    # Load OpenAI credentials
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        openai_endpoint = settings['Values']['AZURE_OPENAI_ENDPOINT']
        openai_key = settings['Values']['AZURE_OPENAI_KEY']
        deployment = settings['Values']['AZURE_OPENAI_DEPLOYMENT']
    
    print(f"🔗 OpenAI endpoint: {openai_endpoint}")
    print(f"🚀 Deployment: {deployment}")
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_key=openai_key,
        api_version="2024-02-01"
    )
    
    # Test bank name extraction
    bank_name = "Stock Yards Bank & Trust"
    print(f"🏦 Testing bank: {bank_name}")
    
    # Create the prompt exactly like the function does
    prompt = f"""
    You are a banking expert. I need the 9-digit routing number for this US bank: {bank_name}
    
    Please respond with ONLY the 9-digit routing number if you know it with certainty.
    If you're not certain or don't know the routing number, respond with exactly: UNKNOWN
    
    Bank: {bank_name}
    Routing number:"""
    
    print(f"\n📝 Prompt sent to OpenAI:")
    print(f"   '{prompt}'")
    
    try:
        print(f"\n🤖 Calling OpenAI...")
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )
        
        routing_response = response.choices[0].message.content.strip()
        print(f"✅ OpenAI response: '{routing_response}'")
        
        # Validate the response
        if routing_response == "UNKNOWN":
            print(f"❌ OpenAI doesn't know the routing number")
        elif len(routing_response) == 9 and routing_response.isdigit():
            print(f"✅ Valid routing number returned: {routing_response}")
            
            # Verify this routing number
            verify_prompt = f"Is {routing_response} the correct routing number for {bank_name}? Respond with YES or NO only."
            
            verify_response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "user", "content": verify_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            verification = verify_response.choices[0].message.content.strip()
            print(f"🔍 Verification: {verification}")
            
        else:
            print(f"❌ Invalid response format: '{routing_response}'")
        
        # Test some variations of the bank name
        variations = [
            "Stock Yards Bank",
            "Stockyards Bank",
            "Stock Yards Bank and Trust",
            "Stock Yards Bank & Trust Company"
        ]
        
        print(f"\n🔄 Testing bank name variations...")
        for variation in variations:
            var_prompt = f"""
            You are a banking expert. I need the 9-digit routing number for this US bank: {variation}
            
            Please respond with ONLY the 9-digit routing number if you know it with certainty.
            If you're not certain or don't know the routing number, respond with exactly: UNKNOWN
            
            Bank: {variation}
            Routing number:"""
            
            var_response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "user", "content": var_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            var_routing = var_response.choices[0].message.content.strip()
            print(f"   '{variation}' -> '{var_routing}'")
    
    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_openai_routing_lookup()
