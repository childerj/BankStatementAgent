#!/usr/bin/env python3
"""
Test script to debug WACBAI2_20250813.pdf processing
This will help us see exactly what Document Intelligence is extracting
"""

import os
import sys
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import json

def test_document_intelligence():
    """Test Document Intelligence with WACBAI2_20250813.pdf"""
    
    # Get credentials from environment
    endpoint = os.getenv('DOCINTELLIGENCE_ENDPOINT')
    key = os.getenv('DOCINTELLIGENCE_KEY')
    
    if not endpoint or not key:
        print("❌ ERROR: Document Intelligence credentials not found in environment")
        print("Make sure DOCINTELLIGENCE_ENDPOINT and DOCINTELLIGENCE_KEY are set")
        print("Trying to load from local.settings.json...")
        
        # Try to load from local.settings.json
        import json
        try:
            with open('local.settings.json', 'r') as f:
                settings = json.load(f)
                endpoint = settings['Values'].get('DOCINTELLIGENCE_ENDPOINT')
                key = settings['Values'].get('DOCINTELLIGENCE_KEY')
                if endpoint and key:
                    print("✅ Loaded credentials from local.settings.json")
                else:
                    print("❌ Credentials not found in local.settings.json")
                    return
        except Exception as e:
            print(f"❌ Error loading local.settings.json: {e}")
            return
    
    print(f"✅ Using Document Intelligence endpoint: {endpoint}")
    
    # Initialize client
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    
    # Test file path
    test_file = r"c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\WACBAI2_20250813.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ ERROR: Test file not found: {test_file}")
        return
    
    print(f"✅ Processing file: {test_file}")
    print(f"✅ File size: {os.path.getsize(test_file)} bytes")
    
    # Test 1: Try prebuilt-bankStatement.us model
    print("\n" + "="*60)
    print("TEST 1: prebuilt-bankStatement.us model")
    print("="*60)
    
    try:
        with open(test_file, "rb") as f:
            file_content = f.read()
        
        print("📤 Starting analysis with prebuilt-bankStatement.us model...")
        poller = client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            file_content
        )
        
        print("⏳ Waiting for analysis to complete...")
        result = poller.result()
        
        print("✅ bankStatement.us model SUCCESS!")
        print(f"✅ Number of pages: {len(result.pages) if result.pages else 0}")
        
        # Check for bank name in documents
        if result.documents:
            print(f"✅ Number of documents found: {len(result.documents)}")
            for i, doc in enumerate(result.documents):
                print(f"\n--- Document {i+1} ---")
                print(f"Document type: {doc.doc_type}")
                print(f"Confidence: {doc.confidence}")
                
                if doc.fields:
                    print("Fields found:")
                    for field_name, field in doc.fields.items():
                        if field_name.lower() in ['bankname', 'bank_name', 'bank']:
                            print(f"  🏦 {field_name}: {field.value} (confidence: {field.confidence})")
                        else:
                            print(f"  📄 {field_name}: {field.value}")
                else:
                    print("❌ No fields found in document")
        
        # Extract all text content
        all_text = ""
        if result.pages:
            for page in result.pages:
                if page.lines:
                    for line in page.lines:
                        all_text += line.content + "\n"
        
        print(f"\n📝 Total text extracted: {len(all_text)} characters")
        print(f"📝 First 500 characters:")
        print("-" * 40)
        print(all_text[:500])
        print("-" * 40)
        
        # Look for bank-related terms
        bank_terms = ['bank', 'prosperity', 'stock yards', 'stockyards', 'wacbai2', 'washington', 'cash']
        print(f"\n🔍 Searching for bank-related terms...")
        for term in bank_terms:
            if term.lower() in all_text.lower():
                print(f"  ✅ Found '{term}' in extracted text")
            else:
                print(f"  ❌ '{term}' not found")
        
        print(f"\n💾 Saving full text to debug file...")
        with open("wacbai2_extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(all_text)
        print(f"✅ Text saved to: wacbai2_extracted_text.txt")
        
    except Exception as e:
        print(f"❌ Error with prebuilt-bankStatement.us model: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Test 2: Try prebuilt-layout model as fallback
        print("\n" + "="*60)
        print("TEST 2: prebuilt-layout model (fallback)")
        print("="*60)
        
        try:
            with open(test_file, "rb") as f:
                file_content = f.read()
            
            print("📤 Starting analysis with prebuilt-layout model...")
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                file_content
            )
            
            print("⏳ Waiting for analysis to complete...")
            result = poller.result()
            
            print("✅ prebuilt-layout model SUCCESS!")
            print(f"✅ Number of pages: {len(result.pages) if result.pages else 0}")
            
            # Extract all text content from layout model
            all_text = ""
            if result.pages:
                for page in result.pages:
                    if page.lines:
                        for line in page.lines:
                            all_text += line.content + "\n"
            
            print(f"\n📝 Total text extracted: {len(all_text)} characters")
            print(f"📝 First 500 characters:")
            print("-" * 40)
            print(all_text[:500])
            print("-" * 40)
            
            # Look for bank-related terms
            bank_terms = ['bank', 'prosperity', 'stock yards', 'stockyards', 'wacbai2', 'washington', 'cash']
            print(f"\n🔍 Searching for bank-related terms...")
            for term in bank_terms:
                if term.lower() in all_text.lower():
                    print(f"  ✅ Found '{term}' in extracted text")
                else:
                    print(f"  ❌ '{term}' not found")
            
            print(f"\n💾 Saving layout model text to debug file...")
            with open("wacbai2_layout_text.txt", "w", encoding="utf-8") as f:
                f.write(all_text)
            print(f"✅ Text saved to: wacbai2_layout_text.txt")
            
        except Exception as e2:
            print(f"❌ Error with prebuilt-layout model: {str(e2)}")
            print(f"Error type: {type(e2).__name__}")

if __name__ == "__main__":
    print("🧪 WACBAI2 Document Intelligence Debug Test")
    print("=" * 50)
    test_document_intelligence()
    print("\n✅ Test completed!")
