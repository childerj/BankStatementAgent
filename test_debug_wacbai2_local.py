#!/usr/bin/env python3
"""
Local test to debug bank name extraction from WACBAI2_20250813.pdf
This mimics the exact logic in function_app.py but runs locally with detailed debugging.
"""

import os
import re
import sys

# Load environment variables from local.settings.json
import json

def load_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            for key, value in values.items():
                os.environ[key] = value
            print(f"✅ Loaded {len(values)} environment variables from local.settings.json")
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")

def extract_bank_name_from_text(text):
    """Extract bank name from text using regex patterns"""
    print(f"🔍 Extracting bank name from text: {text[:200]}...")
    
    # Common bank name patterns
    patterns = [
        r'([A-Za-z\s&]+)\s+bank',  # "First National Bank"
        r'bank\s+of\s+([A-Za-z\s&]+)',  # "Bank of America"
        r'([A-Za-z\s&]+)\s+credit\s+union',  # "Navy Federal Credit Union"
        r'([A-Za-z\s&]+)\s+trust\s+company',  # "Northern Trust Company"
        r'([A-Za-z\s&]+)\s+financial',  # "Wells Fargo Financial"
        r'([A-Za-z\s&]{3,})\s+(?:n\.?a\.?|national\s+association)',  # "JPMorgan Chase N.A."
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Clean up the match
            bank_name = match.strip().title()
            # Filter out common false positives
            if len(bank_name) >= 3 and not any(word in bank_name.lower() for word in ['page', 'statement', 'account', 'balance', 'transaction']):
                print(f"✅ Found bank name with pattern '{pattern}': {bank_name}")
                return bank_name
    
    print(f"❌ No bank name found in text")
    return None

def analyze_document_intelligence():
    """Run Document Intelligence on the test file locally"""
    load_local_settings()
    
    # Import Azure Form Recognizer
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
    
    # Get credentials from environment
    endpoint = os.getenv("DOCINTELLIGENCE_ENDPOINT")
    key = os.getenv("DOCINTELLIGENCE_KEY")
    
    print(f"🔍 Document Intelligence Endpoint: {endpoint}")
    print(f"🔍 Document Intelligence Key: {'SET' if key else 'NOT SET'}")
    
    if not endpoint or not key:
        print("❌ Document Intelligence credentials not found")
        return None
    
    # Initialize client
    client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    
    # Process the test file
    file_path = "Test Docs/WACBAI2_20250813.pdf"
    print(f"🔍 Processing file: {file_path}")
    
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", document=f)
        result = poller.result()
    
    print(f"✅ Document Intelligence completed")
    
    # Extract bank name from Document Intelligence results
    bank_name = None
    print(f"\n🏦 DOCUMENT INTELLIGENCE FIELD ANALYSIS:")
    print(f"=========================================")
    
    # Check if we have structured documents (like with bank statement model)
    if result.documents and len(result.documents) > 0:
        document = result.documents[0]
        if hasattr(document, 'fields') and document.fields:
            # Check all fields
            for field_name, field in document.fields.items():
                print(f"🔍 Field '{field_name}': {field.value} (confidence: {field.confidence:.2%})")
                if field_name == "BankName" and field.value:
                    bank_name = field.value.strip()
                    print(f"✅ Found bank name from Document Intelligence: {bank_name}")
        else:
            print(f"🔍 No structured fields found - using layout model, will rely on OCR text")
    else:
        print(f"🔍 No documents found in result")
    
    # Extract OCR text for fallback
    ocr_text_lines = []
    for page in result.pages:
        for line in page.lines:
            ocr_text_lines.append(line.content)
    
    full_text = '\n'.join(ocr_text_lines)
    print(f"\n🔍 OCR TEXT ANALYSIS:")
    print(f"====================")
    print(f"Total OCR text length: {len(full_text)} characters")
    print(f"Number of lines: {len(ocr_text_lines)}")
    print(f"First 500 characters: {full_text[:500]}")
    print(f"Last 200 characters: {full_text[-200:]}")
    
    # Normalize text for bank name searching
    normalized_text = full_text.replace('\n', ' ').replace('\r', ' ')
    normalized_text = ' '.join(normalized_text.split())
    print(f"\n🔍 NORMALIZED TEXT (first 500 chars): {normalized_text[:500]}")
    
    # Check for specific known banks
    print(f"\n🏦 SPECIFIC BANK PATTERN ANALYSIS:")
    print(f"===================================")
    
    if not bank_name:
        if "PROSPERITY" in normalized_text.upper():
            bank_name = "PROSPERITY BANK"
            print(f"✅ Found PROSPERITY BANK in OCR text")
        elif "STOCK YARDS" in normalized_text.upper() or "STOCKYARDS" in normalized_text.upper():
            bank_name = "STOCK YARDS BANK"
            print(f"✅ Found STOCK YARDS BANK in normalized OCR text")
        elif "WACBAI2" in normalized_text.upper():
            # This might be a Washington State CASH file - could be multiple banks
            if "STOCK YARDS" in normalized_text.upper():
                bank_name = "STOCK YARDS BANK"
                print(f"✅ Found STOCK YARDS BANK in WACBAI2 file")
            else:
                bank_name = "WA CASH MANAGEMENT"
                print(f"✅ Found WA CASH MANAGEMENT (WACBAI2) in OCR text")
        else:
            # Use regex pattern extraction as fallback
            print(f"🔍 No specific bank patterns found, trying regex extraction...")
            bank_name = extract_bank_name_from_text(normalized_text)
    
    print(f"\n🏦 FINAL BANK NAME RESULT:")
    print(f"===========================")
    if bank_name:
        print(f"✅ BANK NAME FOUND: '{bank_name}'")
    else:
        print(f"❌ BANK NAME NOT FOUND")
    
    # Get document fields if available
    document_fields = {}
    if result.documents and len(result.documents) > 0:
        document = result.documents[0]
        if hasattr(document, 'fields') and document.fields:
            document_fields = {field_name: field.value for field_name, field in document.fields.items() if field.value}
    
    return {
        'bank_name': bank_name,
        'full_text': full_text,
        'normalized_text': normalized_text,
        'document_intelligence_fields': document_fields
    }

def test_openai_lookup(bank_name):
    """Test OpenAI routing number lookup"""
    if not bank_name:
        print(f"❌ Cannot test OpenAI lookup - no bank name provided")
        return None
    
    load_local_settings()
    
    try:
        # Get Azure OpenAI configuration from environment
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        print(f"\n🤖 OPENAI LOOKUP TEST:")
        print(f"======================")
        print(f"🔍 AZURE_OPENAI_ENDPOINT: {endpoint}")
        print(f"🔍 AZURE_OPENAI_KEY: {'SET' if api_key else 'NOT SET'}")
        print(f"🔍 AZURE_OPENAI_DEPLOYMENT: {deployment}")
        
        if not endpoint or not api_key or not deployment:
            print("❌ Azure OpenAI configuration missing from environment variables")
            return None
        
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
        
        print(f"🤖 PROMPT BEING SENT:")
        print(f"=====================")
        print(prompt)
        print(f"=====================")
        
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
        print(f"🤖 OPENAI RESPONSE:")
        print(f"==================")
        print(f"Raw response: '{routing_number}'")
        print(f"Response length: {len(routing_number)} characters")
        print(f"Is digits only: {routing_number.isdigit()}")
        
        return routing_number
        
    except Exception as e:
        print(f"❌ Error with OpenAI lookup: {str(e)}")
        import traceback
        print(f"❌ Full error traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    print("🔍 DEBUGGING BANK NAME EXTRACTION FOR WACBAI2_20250813.pdf")
    print("=" * 60)
    
    # Step 1: Analyze with Document Intelligence
    analysis_result = analyze_document_intelligence()
    
    if analysis_result:
        bank_name = analysis_result['bank_name']
        
        # Step 2: Test OpenAI lookup if bank name found
        if bank_name:
            routing_number = test_openai_lookup(bank_name)
            
            print(f"\n🏁 FINAL RESULTS:")
            print(f"=================")
            print(f"Bank Name: {bank_name}")
            print(f"Routing Number: {routing_number}")
        else:
            print(f"\n❌ Cannot proceed to OpenAI lookup - no bank name found")
    else:
        print(f"❌ Document Intelligence analysis failed")
