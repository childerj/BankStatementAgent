#!/usr/bin/env python3
"""
Test the function directly by simulating file processing
"""

import os
import sys
from pathlib import Path
import json

# Add the current directory to Python path so we can import from function_app
sys.path.insert(0, str(Path(__file__).parent))

# Import the function components
from function_app import extract_fields_with_sdk, get_routing_number, load_local_settings

def test_direct_function():
    """Test the function processing directly"""
    
    # Load local settings
    load_local_settings()
    
    print("🧪 DIRECT FUNCTION TEST")
    print("=" * 50)
    
    # Test PDF path
    pdf_path = "Test Docs/8-1-25_Prosperity.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📄 Testing with: {pdf_path}")
    
    # Get environment variables
    endpoint = os.getenv('DOCINTELLIGENCE_ENDPOINT')
    key = os.getenv('DOCINTELLIGENCE_KEY')
    
    if not endpoint or not key:
        print("❌ Missing Document Intelligence configuration")
        return
    
    # Process the PDF
    try:
        with open(pdf_path, 'rb') as f:
            file_bytes = f.read()
        
        print("📤 Processing PDF with Document Intelligence...")
        parsed_data = extract_fields_with_sdk(file_bytes, pdf_path, endpoint, key)
        
        if not parsed_data:
            print("❌ No data extracted from PDF")
            return
        
        print(f"✅ Data extracted: {len(parsed_data)} fields")
        print(f"📊 Raw fields: {list(parsed_data.get('raw_fields', {}).keys())}")
        
        # Test routing number extraction
        print("\n🔍 Testing routing number extraction...")
        routing_number = get_routing_number(parsed_data)
        
        if routing_number:
            print(f"✅ FINAL ROUTING NUMBER: {routing_number}")
        else:
            print("❌ NO ROUTING NUMBER EXTRACTED")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_function()
