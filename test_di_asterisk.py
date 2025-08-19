#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import extract_account_number_from_text, print_and_log

def test_asterisk_extraction():
    """Test how Document Intelligence handles asterisks in PDFs"""
    
    print("🧪 TESTING DOCUMENT INTELLIGENCE ASTERISK HANDLING")
    print("=" * 60)
    
    # Test text samples that might contain asterisks
    test_texts = [
        "Account Number: ****5594",
        "Account Number: 1234****",
        "Account Number: 12**5594", 
        "Account Number: *5594",
        "Account Number: 5594*",
        "Account Number: 1234567890",  # normal
        "Account: ************1234",
        "Acct #: ABC****DEF",
    ]
    
    print("📋 Testing account number extraction from text samples:")
    print("-" * 50)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Testing text: '{text}'")
        result = extract_account_number_from_text(text)
        print(f"   Extracted: {result}")
        
        # Also test if the text contains asterisks
        has_asterisk = "*" in text
        print(f"   Contains asterisk: {has_asterisk}")
    
    print("\n" + "=" * 60)
    print("📄 To see what Document Intelligence actually extracts from PDFs,")
    print("   we would need to process an actual PDF with masked account numbers.")
    print("   The extraction above shows how our regex patterns handle asterisks.")
    
    # Test if we can find any PDFs to analyze
    test_pdfs = [
        "Test Docs/8-1-25_Prosperity.pdf",
        "Test Docs/811.pdf",
        "Test Docs/841.pdf"
    ]
    
    for pdf_path in test_pdfs:
        if os.path.exists(pdf_path):
            print(f"\n🔍 Found test PDF: {pdf_path}")
            print("   To see actual Document Intelligence output, we could analyze this...")
            break
    else:
        print("\n❌ No test PDFs found for Document Intelligence analysis")

if __name__ == "__main__":
    test_asterisk_extraction()
