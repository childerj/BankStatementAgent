#!/usr/bin/env python3
"""
Test program to send PDF to Document Intelligence and extract bank name
"""

import os
import sys
import re
import json
from pathlib import Path

def print_and_log(message):
    """Simple print function"""
    print(message)

def extract_bank_name_from_text(text):
    """Extract bank name from statement text"""
    print_and_log("🏦 Searching for bank name in statement text...")
    
    # Common bank name patterns - ordered by specificity (most specific first)
    bank_patterns = [
        r'(Stock\s+Yards\s+Bank(?:\s+&\s+Trust)?)',  # "Stock Yards Bank" or "Stock Yards Bank & Trust"
        r'(Wells\s+Fargo)',  # "Wells Fargo" - specific pattern first
        r'(Bank\s+of\s+[A-Z][a-z]+)',  # "Bank of America"
        r'(Chase)',  # "Chase"
        r'(Citibank)',  # "Citibank"
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+Bank(?:\s+&\s+Trust)?)',  # "First National Bank" or "Stock Yards Bank"
        r'([A-Z][a-z]+\s+National\s+Bank)',  # "First National Bank"
        r'([A-Z][a-z]+\s+Federal\s+Credit\s+Union)',  # "Navy Federal Credit Union"
        r'([A-Z][a-z]+\s+Credit\s+Union)',  # "First Credit Union"
        r'([A-Z][a-z]+\s+Trust)',  # "First Trust"
        r'([A-Z][a-z]+\s+Bank)',  # "First Bank" - more general pattern (last)
        r'([A-Z][a-z]+\s+Financial)',  # "Wells Financial"
        r'([A-Z][a-z]+\s+Federal)',  # "Navy Federal"
        r'([A-Z][a-z]+\s+Savings)',  # "First Savings"
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            bank_name = matches[0].strip()
            print_and_log(f"🏦 Found bank name: {bank_name}")
            return bank_name
    
    # Try to find bank name near common keywords
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if any(keyword in line.lower() for keyword in ['bank', 'financial', 'credit union', 'trust']):
            # Extract bank name from this line
            words = line.split()
            for i, word in enumerate(words):
                if word.lower() in ['bank', 'financial', 'trust']:
                    if i > 0:
                        potential_name = ' '.join(words[max(0, i-2):i+1])
                        print_and_log(f"🏦 Found potential bank name: {potential_name}")
                        return potential_name.strip()
    
    print_and_log("❌ No bank name found in statement text")
    return None

def parse_bankstatement_sdk_result(result):
    """Parse bankStatement.us model results using SDK format"""
    parsed_data = {
        "extraction_method": "bankStatement.us_sdk",
        "raw_fields": {},
        "ocr_text_lines": []
    }
    
    try:
        if result.documents:
            doc = result.documents[0]
            print_and_log(f"📄 Document fields found: {len(doc.fields) if doc.fields else 0}")
            
            if doc.fields:
                for field_name, field_value in doc.fields.items():
                    print_and_log(f"  • Field: {field_name}")
                    if hasattr(field_value, 'content') and field_value.content:
                        parsed_data["raw_fields"][field_name] = {
                            "content": field_value.content,
                            "confidence": getattr(field_value, 'confidence', 0)
                        }
                        print_and_log(f"    Content: {field_value.content[:100]}...")
                        print_and_log(f"    Confidence: {getattr(field_value, 'confidence', 0):.2f}")
        
        # Also extract text content for fallback processing
        if result.content:
            lines = result.content.split('\n')
            parsed_data["ocr_text_lines"] = [line.strip() for line in lines if line.strip()]
            print_and_log(f"📝 OCR text extracted: {len(parsed_data['ocr_text_lines'])} lines")
    
    except Exception as e:
        print_and_log(f"❌ Error parsing bankStatement SDK result: {str(e)}")
    
    return parsed_data

def parse_layout_sdk_result(result):
    """Parse layout model results using SDK format"""
    parsed_data = {
        "extraction_method": "layout_sdk", 
        "raw_fields": {},
        "ocr_text_lines": []
    }
    
    try:
        # Extract text content
        if result.content:
            lines = result.content.split('\n')
            parsed_data["ocr_text_lines"] = [line.strip() for line in lines if line.strip()]
            print_and_log(f"📝 OCR text extracted: {len(parsed_data['ocr_text_lines'])} lines")
        
        # Extract tables if present
        if result.tables:
            print_and_log(f"📊 Tables found: {len(result.tables)}")
            for i, table in enumerate(result.tables):
                print_and_log(f"  Table {i+1}: {table.row_count} rows, {table.column_count} columns")
    
    except Exception as e:
        print_and_log(f"❌ Error parsing layout SDK result: {str(e)}")
    
    return parsed_data

def test_document_intelligence(pdf_path):
    """Test Document Intelligence with the specified PDF file"""
    
    # Load environment variables from local.settings.json
    settings_path = Path(__file__).parent / "local.settings.json"
    if not settings_path.exists():
        print_and_log("❌ local.settings.json not found!")
        return
    
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    
    endpoint = settings["Values"]["DOCINTELLIGENCE_ENDPOINT"]
    key = settings["Values"]["DOCINTELLIGENCE_KEY"]
    
    print_and_log(f"🔗 Document Intelligence Endpoint: {endpoint}")
    print_and_log(f"🔑 Key configured: {'Yes' if key else 'No'}")
    
    # Check if PDF file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print_and_log(f"❌ PDF file not found: {pdf_path}")
        return
    
    print_and_log(f"📄 Testing with PDF: {pdf_file.name}")
    print_and_log(f"📊 File size: {pdf_file.stat().st_size:,} bytes")
    
    # Read the PDF file
    with open(pdf_file, 'rb') as f:
        file_bytes = f.read()
    
    print_and_log("=" * 60)
    print_and_log("🚀 STARTING DOCUMENT INTELLIGENCE TEST")
    print_and_log("=" * 60)
    
    # Test 1: Try bankStatement.us model
    parsed_data = None
    success = False
    
    try:
        print_and_log("🔄 TEST 1: Bank Statement Model (prebuilt-bankStatement.us)")
        print_and_log("-" * 50)
        
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        from io import BytesIO
        
        # Create client
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        print_and_log("📤 Starting analysis with bankStatement.us model...")
        
        # Analyze document
        poller = client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            BytesIO(file_bytes),
            content_type="application/pdf"
        )
        
        print_and_log("⏳ Waiting for analysis to complete...")
        result = poller.result()
        
        if result and result.documents:
            print_and_log("✅ Bank statement analysis completed successfully!")
            parsed_data = parse_bankstatement_sdk_result(result)
            success = True
        else:
            print_and_log("⚠️ No documents found in result")
    
    except Exception as e:
        print_and_log(f"❌ Error with bankStatement.us model: {str(e)}")
    
    # Test 2: If bankStatement failed, try layout model
    if not success:
        try:
            print_and_log("")
            print_and_log("🔄 TEST 2: Layout Model (prebuilt-layout)")
            print_and_log("-" * 50)
            
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            from io import BytesIO
            
            # Create client
            client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            
            print_and_log("📤 Starting analysis with layout model...")
            
            # Analyze document
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                document=BytesIO(file_bytes)
            )
            
            print_and_log("⏳ Waiting for OCR analysis to complete...")
            result = poller.result()
            
            if result:
                print_and_log("✅ OCR analysis completed successfully!")
                parsed_data = parse_layout_sdk_result(result)
                success = True
            else:
                print_and_log("⚠️ No result from OCR analysis")
        
        except Exception as e:
            print_and_log(f"❌ Error with layout model: {str(e)}")
    
    if not success:
        print_and_log("❌ Both extraction methods failed!")
        return
    
    print_and_log("")
    print_and_log("🔍 BANK NAME EXTRACTION TEST")
    print_and_log("=" * 60)
    
    # Try to extract bank name from different sources
    bank_name = None
    
    # Method 1: Check raw fields
    if parsed_data.get("raw_fields"):
        print_and_log("🔍 Method 1: Searching in raw fields...")
        for field_name, field_data in parsed_data["raw_fields"].items():
            print_and_log(f"  Checking field: {field_name}")
            if isinstance(field_data, dict) and "content" in field_data:
                content = field_data["content"].lower()
                if any(keyword in content for keyword in ['bank', 'financial', 'credit union', 'trust']):
                    potential_bank = extract_bank_name_from_text(field_data["content"])
                    if potential_bank:
                        bank_name = potential_bank
                        print_and_log(f"✅ Bank name found in field '{field_name}': {bank_name}")
                        break
    
    # Method 2: Check OCR text
    if not bank_name and parsed_data.get("ocr_text_lines"):
        print_and_log("")
        print_and_log("🔍 Method 2: Searching in OCR text...")
        full_text = '\n'.join(parsed_data["ocr_text_lines"])
        bank_name = extract_bank_name_from_text(full_text)
        if bank_name:
            print_and_log(f"✅ Bank name found in OCR text: {bank_name}")
    
    print_and_log("")
    print_and_log("📊 FINAL RESULTS")
    print_and_log("=" * 60)
    print_and_log(f"📄 PDF File: {pdf_file.name}")
    print_and_log(f"🔧 Extraction Method: {parsed_data.get('extraction_method', 'Unknown')}")
    print_and_log(f"📝 OCR Lines: {len(parsed_data.get('ocr_text_lines', []))}")
    print_and_log(f"🏷️  Raw Fields: {len(parsed_data.get('raw_fields', {}))}")
    
    if bank_name:
        print_and_log(f"🏦 BANK NAME FOUND: {bank_name}")
    else:
        print_and_log("❌ BANK NAME NOT FOUND")
    
    # Show first few lines of OCR text for debugging
    if parsed_data.get("ocr_text_lines"):
        print_and_log("")
        print_and_log("📝 First 10 lines of OCR text:")
        print_and_log("-" * 30)
        for i, line in enumerate(parsed_data["ocr_text_lines"][:10]):
            print_and_log(f"{i+1:2d}: {line}")
    
    # Show raw fields for debugging
    if parsed_data.get("raw_fields"):
        print_and_log("")
        print_and_log("🏷️  Raw fields detected:")
        print_and_log("-" * 30)
        for field_name, field_data in parsed_data["raw_fields"].items():
            if isinstance(field_data, dict) and "content" in field_data:
                content = field_data["content"][:100] + "..." if len(field_data["content"]) > 100 else field_data["content"]
                confidence = field_data.get("confidence", 0)
                print_and_log(f"• {field_name}: {content} (confidence: {confidence:.2f})")
    
    return bank_name

if __name__ == "__main__":
    # Test with the specified PDF file
    pdf_path = r"C:\Users\jeff.childers\Downloads\WACBAI2_20250813.pdf"
    
    print_and_log("🧪 DOCUMENT INTELLIGENCE BANK NAME EXTRACTION TEST")
    print_and_log("=" * 60)
    
    bank_name = test_document_intelligence(pdf_path)
    
    print_and_log("")
    print_and_log("🎯 TEST COMPLETE!")
    if bank_name:
        print_and_log(f"✅ Successfully extracted bank name: {bank_name}")
    else:
        print_and_log("❌ Could not extract bank name from document")
