#!/usr/bin/env python3
"""
Direct test of Prosperity PDF with Document Intelligence
"""

import json
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import openai

def test_prosperity_direct():
    """Test Prosperity PDF directly with Document Intelligence"""
    
    print("🏦 Direct Prosperity PDF Analysis")
    print("=" * 50)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings['Values']
        
        test_file = "Test Docs/8-1-25_Prosperity.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return
        
        print(f"📄 Analyzing: {test_file}")
        
        # Document Intelligence
        doc_intel_endpoint = values.get('DOCINTELLIGENCE_ENDPOINT')
        doc_intel_key = values.get('DOCINTELLIGENCE_KEY')
        
        client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=AzureKeyCredential(doc_intel_key)
        )
        
        print("📊 Running Document Intelligence analysis...")
        
        with open(test_file, "rb") as f:
            poller = client.begin_analyze_document(
                "prebuilt-layout", 
                body=f, 
                content_type="application/octet-stream"
            )
            result = poller.result()
        
        # Extract content
        full_text = result.content if result.content else ""
        print(f"✅ Extracted {len(full_text)} characters")
        
        # Show text sample
        print(f"\n📄 OCR Text Sample (first 500 chars):")
        print(f"{'='*50}")
        print(full_text[:500])
        print(f"{'='*50}")
        
        # Look for routing numbers in text
        import re
        routing_patterns = [
            r'\b(\d{9})\b',
            r'routing[:\s]*(\d{9})',
            r'aba[:\s]*(\d{9})',
            r'transit[:\s]*(\d{9})',
        ]
        
        print(f"\n🔍 Searching for routing numbers...")
        found_numbers = []
        
        for i, pattern in enumerate(routing_patterns, 1):
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            print(f"   Pattern {i} ({pattern}): {matches}")
            for match in matches:
                if len(match) == 9 and match.isdigit():
                    found_numbers.append(match)
        
        unique_numbers = list(dict.fromkeys(found_numbers))
        print(f"📋 Unique routing numbers found: {unique_numbers}")
        
        # Look for bank name
        bank_patterns = [
            r'(Prosperity\s+Bank)',
            r'(PROSPERITY\s+BANK)', 
            r'([A-Z][a-z]+\s+Bank)',
        ]
        
        print(f"\n🏦 Searching for bank names...")
        found_banks = []
        
        for pattern in bank_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            print(f"   Pattern ({pattern}): {matches}")
            found_banks.extend(matches)
        
        unique_banks = list(dict.fromkeys(found_banks))
        print(f"📋 Unique bank names found: {unique_banks}")
        
        # Check key-value pairs
        print(f"\n🔍 Checking key-value pairs...")
        if result.key_value_pairs:
            print(f"   Found {len(result.key_value_pairs)} key-value pairs")
            
            for kv_pair in result.key_value_pairs[:10]:  # Show first 10
                if kv_pair.key and kv_pair.value:
                    key_content = kv_pair.key.content if kv_pair.key.content else ""
                    value_content = kv_pair.value.content if kv_pair.value.content else ""
                    print(f"   '{key_content}' -> '{value_content}'")
        else:
            print(f"   No key-value pairs found")
        
        # Test OpenAI if we found a bank name but no routing number
        if unique_banks and not unique_numbers:
            print(f"\n🤖 Testing OpenAI lookup...")
            bank_name = unique_banks[0]
            print(f"   Bank name: {bank_name}")
            
            # Setup OpenAI
            openai_endpoint = values.get('AZURE_OPENAI_ENDPOINT')
            openai_key = values.get('AZURE_OPENAI_KEY')
            
            if openai_endpoint and openai_key:
                print(f"   OpenAI endpoint: {openai_endpoint}")
                
                # Initialize Azure OpenAI
                import openai
                openai.api_key = openai_key
                openai.api_base = openai_endpoint
                openai.api_type = "azure"
                openai.api_version = "2024-02-01"
                
                try:
                    response = openai.ChatCompletion.create(
                        engine="gpt-4.1",  # Based on your settings
                        messages=[
                            {
                                "role": "system", 
                                "content": "You are a banking expert. When given a bank name, return ONLY the primary 9-digit ABA routing number for that bank. Return only the number, no explanations."
                            },
                            {
                                "role": "user",
                                "content": f"What is the primary ABA routing number for {bank_name}?"
                            }
                        ],
                        max_tokens=50,
                        temperature=0
                    )
                    
                    openai_routing = response.choices[0].message.content.strip()
                    print(f"   ✅ OpenAI response: {openai_routing}")
                    
                    # Validate
                    if len(openai_routing) == 9 and openai_routing.isdigit():
                        print(f"   ✅ Valid routing number format")
                        if openai_routing.startswith('113'):
                            print(f"   ✅ Matches Prosperity Bank pattern!")
                        else:
                            print(f"   ⚠️ Unexpected routing number for Prosperity")
                    else:
                        print(f"   ❌ Invalid format: {openai_routing}")
                    
                except Exception as e:
                    print(f"   ❌ OpenAI error: {e}")
            else:
                print(f"   ❌ OpenAI not configured")
        
        # Summary
        print(f"\n📊 Analysis Summary:")
        print(f"   • Text extracted: {len(full_text)} characters")
        print(f"   • Routing numbers found: {len(unique_numbers)} ({unique_numbers})")
        print(f"   • Bank names found: {len(unique_banks)} ({unique_banks})")
        print(f"   • Key-value pairs: {len(result.key_value_pairs) if result.key_value_pairs else 0}")
        
        if unique_numbers:
            print(f"   ✅ SUCCESS: Direct routing extraction worked")
        elif unique_banks:
            print(f"   ✅ SUCCESS: Bank name found, can use OpenAI")
        else:
            print(f"   ❌ FAILURE: No routing number or bank name found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prosperity_direct()
