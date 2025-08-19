#!/usr/bin/env python3
"""
Test OpenAI routing number lookup for PROSPERITY BANK locally
"""

import os
import openai
import json

def test_openai_lookup():
    """Test OpenAI lookup for PROSPERITY BANK routing number"""
    print("🤖 Testing OpenAI routing number lookup for PROSPERITY BANK...")
    
    # Load environment variables from local.settings.json
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            for key, value in values.items():
                os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Could not load local.settings.json: {e}")
    
    # Get Azure OpenAI configuration
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_key = os.getenv('AZURE_OPENAI_KEY') 
    azure_openai_model = os.getenv('AZURE_OPENAI_MODEL', 'gpt-4o')
    
    print(f"🔧 Endpoint: {azure_openai_endpoint}")
    print(f"🔧 Model: {azure_openai_model}")
    print(f"🔧 Key present: {'Yes' if azure_openai_key else 'No'}")
    
    if not all([azure_openai_endpoint, azure_openai_key]):
        print("❌ Missing Azure OpenAI configuration")
        return
    
    try:
        # Create OpenAI client for Azure
        client = openai.AzureOpenAI(
            azure_endpoint=azure_openai_endpoint,
            api_key=azure_openai_key,
            api_version="2024-02-01"
        )
        
        bank_name = "PROSPERITY BANK"
        print(f"\n🏦 Looking up routing number for: {bank_name}")
        
        prompt = f"""You are a banking expert. I need the primary routing number (ABA number) for {bank_name}.

Please respond with ONLY the 9-digit routing number, nothing else.
If you cannot find a definitive routing number, respond with "UNKNOWN".

Bank name: {bank_name}"""

        print(f"\n📝 Sending prompt to OpenAI...")
        print(f"Prompt: {prompt}")
        
        response = client.chat.completions.create(
            model=azure_openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful banking assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        routing_number = response.choices[0].message.content.strip()
        print(f"\n✅ OpenAI Response: '{routing_number}'")
        
        # Validate the routing number
        if routing_number == "UNKNOWN":
            print("❌ OpenAI could not find routing number")
        elif len(routing_number) == 9 and routing_number.isdigit():
            print(f"✅ Valid routing number format: {routing_number}")
        else:
            print(f"❌ Invalid routing number format: '{routing_number}' (length: {len(routing_number)})")
            print("   Expected: 9 digits")
        
        return routing_number
        
    except Exception as e:
        print(f"❌ Error during OpenAI lookup: {e}")
        return None

if __name__ == "__main__":
    test_openai_lookup()
