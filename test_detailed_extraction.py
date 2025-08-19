#!/usr/bin/env python3
"""
Enhanced test program to show detailed Document Intelligence results
"""

import os
import sys
import re
import json
from pathlib import Path

def print_and_log(message):
    """Simple print function"""
    print(message)

def test_document_intelligence_detailed(pdf_path):
    """Detailed test of Document Intelligence with the specified PDF file"""
    
    # Load environment variables from local.settings.json
    settings_path = Path(__file__).parent / "local.settings.json"
    if not settings_path.exists():
        print_and_log("❌ local.settings.json not found!")
        return
    
    with open(settings_path, 'r') as f:
        settings = json.load(f)
    
    endpoint = settings["Values"]["DOCINTELLIGENCE_ENDPOINT"]
    key = settings["Values"]["DOCINTELLIGENCE_KEY"]
    
    # Check if PDF file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print_and_log(f"❌ PDF file not found: {pdf_path}")
        return
    
    print_and_log(f"📄 Analyzing PDF: {pdf_file.name}")
    print_and_log(f"📊 File size: {pdf_file.stat().st_size:,} bytes")
    
    # Read the PDF file
    with open(pdf_file, 'rb') as f:
        file_bytes = f.read()
    
    print_and_log("=" * 80)
    print_and_log("🚀 DETAILED DOCUMENT INTELLIGENCE ANALYSIS")
    print_and_log("=" * 80)
    
    try:
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
        
        if not result or not result.documents:
            print_and_log("❌ No documents found in result")
            return
        
        print_and_log("✅ Analysis completed successfully!")
        print_and_log("")
        
        # Show detailed document structure
        print_and_log("📄 DOCUMENT STRUCTURE")
        print_and_log("-" * 40)
        print_and_log(f"Number of documents: {len(result.documents)}")
        
        for doc_idx, doc in enumerate(result.documents):
            print_and_log(f"\n📋 Document {doc_idx + 1}:")
            print_and_log(f"  Document type: {getattr(doc, 'doc_type', 'Unknown')}")
            print_and_log(f"  Confidence: {getattr(doc, 'confidence', 0):.2f}")
            
            if doc.fields:
                print_and_log(f"  Fields found: {len(doc.fields)}")
                print_and_log("")
                
                # Show all fields in detail
                for field_name, field_value in doc.fields.items():
                    print_and_log(f"  🏷️  Field: {field_name}")
                    print_and_log(f"    Type: {type(field_value).__name__}")
                    confidence = getattr(field_value, 'confidence', 0)
                    if confidence is not None:
                        print_and_log(f"    Confidence: {confidence:.2f}")
                    else:
                        print_and_log(f"    Confidence: None")
                    
                    # Handle different field types
                    if hasattr(field_value, 'content') and field_value.content:
                        content = field_value.content
                        if len(content) > 100:
                            content = content[:100] + "..."
                        print_and_log(f"    Content: {content}")
                    
                    elif hasattr(field_value, 'value'):
                        if isinstance(field_value.value, list):
                            print_and_log(f"    Value: List with {len(field_value.value)} items")
                            for i, item in enumerate(field_value.value[:3]):  # Show first 3 items
                                if hasattr(item, 'content'):
                                    print_and_log(f"      [{i}]: {item.content[:50]}...")
                                elif hasattr(item, 'value') and hasattr(item.value, 'fields'):
                                    print_and_log(f"      [{i}]: Object with {len(item.value.fields)} fields")
                                    # Show account-specific fields
                                    if hasattr(item.value, 'fields'):
                                        for sub_field_name, sub_field_value in item.value.fields.items():
                                            if hasattr(sub_field_value, 'content'):
                                                sub_content = sub_field_value.content
                                                if len(sub_content) > 50:
                                                    sub_content = sub_content[:50] + "..."
                                                print_and_log(f"        {sub_field_name}: {sub_content}")
                                else:
                                    print_and_log(f"      [{i}]: {str(item)[:50]}...")
                        else:
                            value_str = str(field_value.value)
                            if len(value_str) > 100:
                                value_str = value_str[:100] + "..."
                            print_and_log(f"    Value: {value_str}")
                    
                    print_and_log("")
        
        # Show OCR content
        if result.content:
            print_and_log("📝 OCR CONTENT")
            print_and_log("-" * 40)
            lines = result.content.split('\n')
            clean_lines = [line.strip() for line in lines if line.strip()]
            print_and_log(f"Total OCR lines: {len(clean_lines)}")
            print_and_log("")
            print_and_log("First 20 lines:")
            for i, line in enumerate(clean_lines[:20]):
                print_and_log(f"{i+1:2d}: {line}")
            
            if len(clean_lines) > 20:
                print_and_log(f"... and {len(clean_lines) - 20} more lines")
        
        # Extract and highlight bank name specifically
        print_and_log("")
        print_and_log("🏦 BANK NAME ANALYSIS")
        print_and_log("-" * 40)
        
        # Look for bank-related text in OCR
        if result.content:
            bank_keywords = ['bank', 'trust', 'financial', 'credit union', 'federal']
            bank_lines = []
            
            for i, line in enumerate(clean_lines):
                if any(keyword in line.lower() for keyword in bank_keywords):
                    bank_lines.append((i+1, line))
            
            if bank_lines:
                print_and_log(f"Found {len(bank_lines)} lines containing bank-related keywords:")
                for line_num, line in bank_lines:
                    print_and_log(f"  Line {line_num}: {line}")
                
                # Apply regex patterns to find bank name
                full_text = '\n'.join(clean_lines)
                bank_patterns = [
                    r'(Stock\s+Yards\s+Bank)',
                    r'(Wells\s+Fargo)',
                    r'(Bank\s+of\s+[A-Z][a-z]+)',
                    r'(Chase)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+Bank)',
                    r'([A-Z][a-z]+\s+Bank)',
                ]
                
                print_and_log("")
                print_and_log("Bank name pattern matching:")
                for pattern in bank_patterns:
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        print_and_log(f"  Pattern '{pattern}' found: {matches}")
            else:
                print_and_log("No lines with bank-related keywords found")
    
    except Exception as e:
        print_and_log(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with the specified PDF file
    pdf_path = r"C:\Users\jeff.childers\Downloads\WACBAI2_20250813.pdf"
    
    print_and_log("🔍 DETAILED DOCUMENT INTELLIGENCE ANALYSIS")
    print_and_log("=" * 80)
    
    test_document_intelligence_detailed(pdf_path)
