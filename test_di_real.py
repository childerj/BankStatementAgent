#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import extract_data_from_pdf, print_and_log

def test_actual_pdf_with_di():
    """Test what Document Intelligence actually returns from a real PDF"""
    
    print("🧪 TESTING ACTUAL DOCUMENT INTELLIGENCE OUTPUT")
    print("=" * 60)
    
    # Use a test PDF to see what Document Intelligence actually extracts
    test_pdf = "Test Docs/8-1-25_Prosperity.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found: {test_pdf}")
        return
    
    print(f"📄 Analyzing: {test_pdf}")
    print("-" * 40)
    
    try:
        # Read the PDF file
        with open(test_pdf, 'rb') as f:
            pdf_bytes = f.read()
        
        # Extract data using Document Intelligence
        print("🔍 Running Document Intelligence extraction...")
        result = extract_data_from_pdf(pdf_bytes, test_pdf)
        
        if result:
            print("✅ Document Intelligence completed!")
            
            # Look at the raw OCR text to see if asterisks are preserved
            if "ocr_text_lines" in result:
                print(f"\n📝 OCR Text Lines ({len(result['ocr_text_lines'])} lines):")
                print("-" * 30)
                
                # Look for lines that might contain account numbers or asterisks
                for i, line in enumerate(result['ocr_text_lines'], 1):
                    line = line.strip()
                    if line and ("account" in line.lower() or "*" in line or "acct" in line.lower()):
                        print(f"Line {i:3}: {line}")
                        if "*" in line:
                            print(f"         ⚠️  CONTAINS ASTERISK!")
            
            # Look at structured fields
            if "raw_fields" in result:
                print(f"\n🏷️  Structured Fields:")
                print("-" * 20)
                for field_name, field_data in result["raw_fields"].items():
                    if isinstance(field_data, dict) and "content" in field_data:
                        content = field_data["content"]
                        print(f"{field_name}: {content}")
                        if "*" in str(content):
                            print(f"         ⚠️  CONTAINS ASTERISK!")
        else:
            print("❌ Document Intelligence failed or returned no data")
            
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")

if __name__ == "__main__":
    test_actual_pdf_with_di()
