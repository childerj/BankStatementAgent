"""
Document Intelligence Analysis for 402_507_528.pdf
Analyze account number extraction issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
import re

def analyze_402_507_528_document():
    """Analyze 402_507_528.pdf with Document Intelligence to see account number extraction"""
    
    # Load environment variables
    from function_app import load_local_settings
    load_local_settings()
    
    # Get Document Intelligence credentials
    doc_intel_endpoint = os.environ.get("DOCINTELLIGENCE_ENDPOINT")
    doc_intel_key = os.environ.get("DOCINTELLIGENCE_KEY")
    
    if not doc_intel_endpoint or not doc_intel_key:
        print("❌ Document Intelligence credentials not found")
        return
    
    print("✅ Document Intelligence credentials loaded")
    
    # Initialize client
    client = DocumentIntelligenceClient(
        endpoint=doc_intel_endpoint,
        credential=AzureKeyCredential(doc_intel_key)
    )
    
    # Read the PDF file
    pdf_path = r"New Test Docs\402_507_528.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📄 Reading file: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    
    print(f"📊 File size: {len(file_bytes):,} bytes")
    
    try:
        # Analyze with bankStatement model
        print("\n🔍 Analyzing with prebuilt-bankStatement.us model...")
        
        poller = client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            BytesIO(file_bytes),
            content_type="application/pdf"
        )
        
        print("⏳ Waiting for analysis to complete...")
        result = poller.result()
        
        if result:
            print("✅ Analysis completed successfully!")
            
            # Extract all fields with focus on account numbers
            print("\n📋 EXTRACTED FIELDS:")
            print("=" * 50)
            
            account_fields = []
            if result.documents:
                doc = result.documents[0]
                if hasattr(doc, 'fields') and doc.fields:
                    for field_name, field_data in doc.fields.items():
                        if hasattr(field_data, 'content') and field_data.content:
                            confidence = getattr(field_data, 'confidence', 0.0)
                            print(f"Field: {field_name}")
                            print(f"Content: '{field_data.content}'")
                            print(f"Confidence: {confidence:.2%}")
                            
                            # Check if this looks like an account number
                            if 'account' in field_name.lower() or re.search(r'\b\d{4,}\b', field_data.content):
                                account_fields.append((field_name, field_data.content, confidence))
                            
                            print("-" * 30)
                        else:
                            print(f"Field: {field_name} (no content)")
                            print("-" * 30)
            
            # Highlight potential account number fields
            if account_fields:
                print("\n🏦 POTENTIAL ACCOUNT NUMBER FIELDS:")
                print("=" * 50)
                for field_name, content, confidence in account_fields:
                    print(f"Field: {field_name}")
                    print(f"Content: '{content}'")
                    print(f"Confidence: {confidence:.2%}")
                    print("-" * 30)
            
            # Extract OCR text and search for account patterns
            print("\n📝 OCR TEXT ANALYSIS - SEARCHING FOR ACCOUNT NUMBERS:")
            print("=" * 50)
            
            if result.content:
                lines = result.content.split('\n')
                print(f"Total lines extracted: {len(lines)}")
                
                # Search for account-related content
                print("\n🔍 Searching for account number patterns...")
                account_patterns = [
                    r'account\s*(?:number|no\.?|#)?\s*:?\s*(\d+)',
                    r'acct\s*(?:number|no\.?|#)?\s*:?\s*(\d+)',
                    r'ending\s+(\d+)',
                    r'xxxx\s*(\d+)',
                    r'\*{4}\s*(\d+)',
                    r'\b\d{4,}\b',  # Any sequence of 4+ digits
                ]
                
                found_accounts = []
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    if any(keyword in line_lower for keyword in ['account', 'acct', 'ending']):
                        print(f"Line {i+1}: {line}")
                        
                        # Try to extract account numbers from this line
                        for pattern in account_patterns:
                            matches = re.finditer(pattern, line_lower)
                            for match in matches:
                                if match.groups():
                                    account_num = match.group(1)
                                else:
                                    account_num = match.group(0)
                                
                                if len(account_num) >= 4:  # Only consider 4+ digit numbers
                                    found_accounts.append((account_num, line, pattern))
                                    print(f"  → Found account pattern: '{account_num}' using pattern: {pattern}")
                
                print(f"\n📊 Found {len(found_accounts)} potential account numbers:")
                for account_num, source_line, pattern in found_accounts:
                    print(f"  • '{account_num}' from: '{source_line.strip()}'")
                
                # Also search for partial account patterns like "Ending 0327"
                print("\n🔍 Searching for partial account patterns...")
                partial_patterns = [
                    r'ending\s+(\d{4})',
                    r'last\s+four\s+(\d{4})',
                    r'xxxx\s*(\d{4})',
                    r'\*{4}\s*(\d{4})',
                ]
                
                found_partials = []
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    for pattern in partial_patterns:
                        matches = re.finditer(pattern, line_lower)
                        for match in matches:
                            partial_num = match.group(1)
                            found_partials.append((partial_num, line, pattern))
                            print(f"Line {i+1}: {line}")
                            print(f"  → Found partial account: '{partial_num}' using pattern: {pattern}")
                
                print(f"\n📊 Found {len(found_partials)} potential partial account numbers:")
                for partial_num, source_line, pattern in found_partials:
                    print(f"  • '{partial_num}' from: '{source_line.strip()}'")
                
                # Show first 20 lines of OCR text for manual inspection
                print(f"\n📝 FIRST 20 LINES OF OCR TEXT:")
                print("=" * 50)
                for i, line in enumerate(lines[:20]):
                    print(f"{i+1:2d}: {line}")
                
                # Show lines containing numbers for pattern analysis
                print(f"\n🔢 LINES CONTAINING NUMBERS:")
                print("=" * 50)
                number_lines = []
                for i, line in enumerate(lines):
                    if re.search(r'\d', line):
                        number_lines.append((i+1, line))
                
                # Show first 30 lines with numbers
                for line_num, line in number_lines[:30]:
                    print(f"{line_num:2d}: {line}")
                    
                if len(number_lines) > 30:
                    print(f"... and {len(number_lines) - 30} more lines with numbers")
        
        else:
            print("❌ No analysis result returned")
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_402_507_528_document()
