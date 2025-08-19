#!/usr/bin/env python3
"""
Debug the WACBAI2 PDF bank name extraction issue
"""

import json
import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

def debug_wacbai2_extraction():
    """Debug what's happening with the WACBAI2 PDF"""
    
    print("🐛 Debugging WACBAI2 PDF Bank Name Extraction")
    print("=" * 60)
    
    # Check if the PDF exists locally first
    pdf_path = r"C:\Users\jeff.childers\Downloads\WACBAI2_20250813.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found at: {pdf_path}")
        print("Let me check for similar files...")
        
        downloads_dir = r"C:\Users\jeff.childers\Downloads"
        if os.path.exists(downloads_dir):
            pdf_files = [f for f in os.listdir(downloads_dir) if f.endswith('.pdf')]
            print(f"PDF files in Downloads:")
            for pdf in pdf_files:
                print(f"   {pdf}")
        return
    
    try:
        # Load Azure AI credentials
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            ai_endpoint = settings['Values']['DOCINTELLIGENCE_ENDPOINT']
            ai_key = settings['Values']['DOCINTELLIGENCE_KEY']
        
        print(f"📋 Processing: {pdf_path}")
        print(f"🔗 Azure AI endpoint: {ai_endpoint}")
        print()
        
        # Initialize Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=ai_endpoint,
            credential=AzureKeyCredential(ai_key)
        )
        
        # Analyze the document
        print("🔍 Analyzing document...")
        with open(pdf_path, "rb") as f:
            poller = client.begin_analyze_document(
                "prebuilt-bankStatement.us", 
                f,
                content_type="application/pdf"
            )
        
        result = poller.result()
        print("✅ Document analysis complete!")
        
        # Get the full text content
        all_text = result.content if result.content else ""
        
        print(f"\n=== Document Text Analysis ===")
        print(f"Total characters: {len(all_text)}")
        
        # Show first 1000 characters
        print(f"\n=== First 1000 characters ===")
        print(f"'{all_text[:1000]}'")
        
        # Look for routing numbers (9 digits)
        print(f"\n=== Routing Number Search ===")
        import re
        routing_pattern = r'\b[0-9]{9}\b'
        routing_matches = re.findall(routing_pattern, all_text)
        
        if routing_matches:
            print(f"✅ Found routing numbers: {set(routing_matches)}")
        else:
            print(f"❌ No 9-digit routing numbers found")
        
        # Look for bank-related text
        print(f"\n=== Bank Name Search ===")
        bank_keywords = [
            'bank', 'BANK', 'Bank',
            'credit union', 'financial', 'trust',
            'Wells', 'Chase', 'America', 'Capital',
            'Prosperity', 'PROSPERITY',
            'Federal', 'National', 'Community'
        ]
        
        found_bank_lines = []
        lines = all_text.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in bank_keywords):
                found_bank_lines.append(f"Line {i+1}: {line.strip()}")
        
        if found_bank_lines:
            print(f"✅ Found {len(found_bank_lines)} lines with bank keywords:")
            for line in found_bank_lines[:10]:  # First 10 matches
                print(f"   {line}")
        else:
            print(f"❌ No bank-related keywords found")
        
        # Test the bank name extraction function from the Azure Function
        print(f"\n=== Testing Function Logic ===")
        
        def test_bank_extraction(text):
            """Replicate the bank name extraction logic from function_app.py"""
            
            # Look for common bank patterns
            bank_patterns = [
                r'([A-Za-z\s]+)\s*BANK',
                r'([A-Za-z\s]+)\s*CREDIT\s*UNION',
                r'([A-Za-z\s]+)\s*FINANCIAL',
                r'BANK\s*OF\s*([A-Za-z\s]+)',
                r'FIRST\s*([A-Za-z\s]+)\s*BANK'
            ]
            
            extracted_names = []
            
            for pattern in bank_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    
                    # Clean up the match
                    bank_name = match.strip()
                    if len(bank_name) > 2:  # Skip very short matches
                        extracted_names.append(bank_name)
            
            return extracted_names
        
        extracted_banks = test_bank_extraction(all_text)
        
        if extracted_banks:
            print(f"✅ Extracted bank names:")
            for bank in set(extracted_banks):  # Remove duplicates
                print(f"   '{bank}'")
        else:
            print(f"❌ No bank names extracted with pattern matching")
        
        # Final diagnosis
        print(f"\n=== DIAGNOSIS ===")
        
        if not routing_matches and not extracted_banks:
            print(f"🔍 ROOT CAUSE IDENTIFIED:")
            print(f"   • No routing numbers found in document text")
            print(f"   • No bank names extracted for OpenAI lookup")
            print(f"   • This explains why an ERROR BAI file was generated")
            print(f"\n💡 POTENTIAL SOLUTIONS:")
            print(f"   1. Check if document contains machine-readable text")
            print(f"   2. Look for routing/bank info in different document areas")
            print(f"   3. Enhance bank name extraction patterns")
            print(f"   4. Add manual routing number mapping for known banks")
        
        elif routing_matches:
            print(f"✅ Routing numbers found - this should have worked!")
            print(f"   Check why routing extraction failed in the function")
        
        elif extracted_banks:
            print(f"✅ Bank names found - OpenAI lookup should have been attempted")
            print(f"   Check OpenAI integration and API response")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_wacbai2_extraction()
