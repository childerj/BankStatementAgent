#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to extract fields from a PDF bank statement using Azure Document Intelligence
and display them in a formatted table.
"""

import os
import requests
import time
import json
from datetime import datetime
from tabulate import tabulate

def load_env_from_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        with open("local.settings.json", "r") as f:
            settings = json.load(f)
            env_vars = settings.get("Values", {})
            for key, value in env_vars.items():
                os.environ[key] = value
        print("✅ Loaded environment variables from local.settings.json")
        return True
    except Exception as e:
        print(f"❌ Failed to load local.settings.json: {e}")
        return False

def extract_pdf_fields(pdf_path):
    """Extract fields from PDF using Azure Document Intelligence"""
    
    print("🔍 EXTRACTING FIELDS FROM PDF")
    print("=" * 60)
    
    # Load environment variables
    if not load_env_from_local_settings():
        return None
    
    # Get configuration
    endpoint = os.environ.get("DOCINTELLIGENCE_ENDPOINT")
    key = os.environ.get("DOCINTELLIGENCE_KEY")
    
    if not endpoint or not key:
        print("❌ Document Intelligence configuration missing!")
        return None
    
    print(f"📄 Processing file: {os.path.basename(pdf_path)}")
    print(f"🔗 Endpoint: {endpoint}")
    print("")
    
    # Read PDF file
    try:
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
        file_size = len(file_bytes)
        print(f"📊 File size: {file_size:,} bytes")
    except Exception as e:
        print(f"❌ Failed to read PDF file: {e}")
        return None
    
    # Headers for Document Intelligence
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/pdf"
    }
    
    # Use only OCR/Read model for cleaner text extraction
    model_name = "OCR/Read Model"
    url = f"{endpoint}/formrecognizer/documentModels/prebuilt-read:analyze?api-version=2023-07-31"
    
    print(f"🤖 Using {model_name} for optimal text extraction...")
    
    # Submit document
    response = requests.post(url, headers=headers, data=file_bytes)
    
    if response.status_code == 404:
        print(f"   ❌ {model_name} not available in this region")
        return None, None
    elif response.status_code != 202:
        print(f"   ❌ {model_name} failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None
    
    operation_location = response.headers.get("operation-location")
    if not operation_location:
        print(f"   ❌ No operation-location header from {model_name}")
        return None, None
    
    print(f"   ⏳ {model_name} processing...")
    
    # Poll for completion
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait_time:
            print(f"   ❌ {model_name} timed out")
            return None, None
            
        result = requests.get(operation_location, headers=headers).json()
        if result.get("status") == "succeeded":
            elapsed = int(time.time() - start_time)
            print(f"   ✅ {model_name} completed in {elapsed} seconds")
            return result.get("analyzeResult", {}), model_name
        elif result.get("status") == "failed":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"   ❌ {model_name} failed: {error_msg}")
            return None, None
        
        print(".", end="", flush=True)
        time.sleep(2)

def display_structured_fields(analyze_result, model_name):
    """Display structured document fields in tables"""
    
    print(f"\n📋 STRUCTURED FIELDS FROM {model_name.upper()}")
    print("=" * 80)
    
    documents = analyze_result.get("documents", [])
    if not documents:
        print("⚠️  No structured documents found")
        return
    
    doc = documents[0]
    fields = doc.get("fields", {})
    
    if not fields:
        print("⚠️  No fields found in document")
        return
    
    # Prepare data for main fields table
    field_data = []
    transaction_arrays = []
    object_fields = []
    
    for field_name, field_info in fields.items():
        content = field_info.get("content", "N/A")
        confidence = field_info.get("confidence", 0)
        field_type = field_info.get("type", "unknown")
        
        # Handle different field types
        if "valueArray" in field_info:
            # This is a transaction array or similar
            array_items = field_info["valueArray"]
            transaction_arrays.append({
                "field_name": field_name,
                "items": array_items,
                "confidence": confidence
            })
            content = f"Array with {len(array_items)} items"
        elif "valueObject" in field_info:
            # This is an object with sub-fields
            obj_fields = field_info["valueObject"]
            object_fields.append({
                "field_name": field_name,
                "fields": obj_fields,
                "confidence": confidence
            })
            content = f"Object with {len(obj_fields)} fields"
        
        # Add to main table
        confidence_icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        field_data.append([
            field_name,
            field_type,
            str(content)[:100] + ("..." if len(str(content)) > 100 else ""),
            f"{confidence:.1%}",
            confidence_icon
        ])
    
    # Display main fields table
    if field_data:
        print("\n📊 MAIN DOCUMENT FIELDS:")
        print("-" * 60)
        headers = ["Field Name", "Type", "Content", "Confidence", "Level"]
        print(tabulate(field_data, headers=headers, tablefmt="grid", maxcolwidths=[20, 12, 50, 10, 6]))
    
    # Display transaction arrays
    for array_info in transaction_arrays:
        print(f"\n📝 ARRAY FIELD: {array_info['field_name']}")
        print("-" * 60)
        
        if array_info['items']:
            array_data = []
            for i, item in enumerate(array_info['items'][:10], 1):  # Show first 10 items
                if "valueObject" in item:
                    # Transaction with sub-fields
                    obj_fields = item["valueObject"]
                    row = [f"Item {i}"]
                    
                    # Extract common transaction fields
                    amount = obj_fields.get("Amount", {}).get("content", "N/A")
                    description = obj_fields.get("Description", {}).get("content", "N/A")
                    date = obj_fields.get("Date", {}).get("content", "N/A")
                    
                    row.extend([date, amount, description])
                    array_data.append(row)
                elif "content" in item:
                    # Simple array item
                    array_data.append([f"Item {i}", "", "", item["content"]])
            
            if array_data:
                array_headers = ["Index", "Date", "Amount", "Description"]
                print(tabulate(array_data, headers=array_headers, tablefmt="grid"))
            
            if len(array_info['items']) > 10:
                print(f"   ... and {len(array_info['items']) - 10} more items")
    
    # Display object fields
    for obj_info in object_fields:
        print(f"\n📂 OBJECT FIELD: {obj_info['field_name']}")
        print("-" * 60)
        
        obj_data = []
        for sub_field_name, sub_field_info in obj_info['fields'].items():
            content = sub_field_info.get("content", "N/A")
            confidence = sub_field_info.get("confidence", 0)
            field_type = sub_field_info.get("type", "unknown")
            
            confidence_icon = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
            obj_data.append([
                sub_field_name,
                field_type,
                str(content),
                f"{confidence:.1%}",
                confidence_icon
            ])
        
        if obj_data:
            obj_headers = ["Sub-Field", "Type", "Content", "Confidence", "Level"]
            print(tabulate(obj_data, headers=obj_headers, tablefmt="grid"))
    
    # Document summary
    doc_type = doc.get("docType", "unknown")
    doc_confidence = doc.get("confidence", 0)
    
    print(f"\n📄 DOCUMENT SUMMARY:")
    print("-" * 30)
    summary_data = [
        ["Document Type", doc_type],
        ["Overall Confidence", f"{doc_confidence:.1%}"],
        ["Total Fields", len(fields)],
        ["Transaction Arrays", len(transaction_arrays)],
        ["Object Fields", len(object_fields)]
    ]
    print(tabulate(summary_data, headers=["Property", "Value"], tablefmt="grid"))

def display_ocr_text(analyze_result, model_name):
    """Display OCR text results"""
    
    print(f"\n📄 OCR TEXT FROM {model_name.upper()}")
    print("=" * 80)
    
    pages = analyze_result.get("pages", [])
    if not pages:
        print("⚠️  No pages found in OCR results")
        return
    
    all_lines = []
    for page_num, page in enumerate(pages, 1):
        print(f"\n📄 PAGE {page_num}:")
        print("-" * 40)
        
        lines = page.get("lines", [])
        page_lines = []
        
        for line_num, line in enumerate(lines, 1):
            line_text = line.get("content", "")
            if line_text.strip():
                page_lines.append([line_num, line_text.strip()])
                all_lines.append(line_text.strip())
        
        if page_lines:
            print(tabulate(page_lines, headers=["Line", "Text"], tablefmt="grid", maxcolwidths=[5, 80]))
    
    print(f"\n📊 OCR SUMMARY:")
    print(f"   Pages: {len(pages)}")
    print(f"   Total lines: {len(all_lines)}")
    print(f"   Total characters: {sum(len(line) for line in all_lines)}")
    
    return all_lines

def main():
    """Main function to test field extraction"""
    
    # PDF file path
    pdf_path = "Test Docs/811.pdf"
    
    print(f"⏰ Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Extract fields using Document Intelligence
    result = extract_pdf_fields(pdf_path)
    if not result:
        print("❌ Failed to extract fields from PDF")
        return
    
    analyze_result, model_name = result
    
    # Since we're using OCR/Read model, always display OCR text
    print(f"\n🔍 PROCESSING RESULTS FROM {model_name.upper()}")
    print("=" * 80)
    
    ocr_lines = display_ocr_text(analyze_result, model_name)
    
    # Show all extracted lines that will be sent to OpenAI
    if ocr_lines:
        print(f"\n📤 ALL EXTRACTED TEXT FOR AZURE OPENAI PARSING")
        print("=" * 60)
        print("Complete text that will be sent to Azure OpenAI:")
        print("-" * 60)
        
        # Show all lines
        for i, line in enumerate(ocr_lines, 1):
            print(f"{i:3d}: {line}")
        
        print("-" * 60)
        combined_text = '\n'.join(ocr_lines)
        print(f"Total text length: {len(combined_text):,} characters")
        print("This text will be analyzed by Azure OpenAI to extract:")
        print("  • Bank name and account number")
        print("  • Opening and closing balances")
        print("  • Individual transactions with dates, amounts, descriptions")
        print("  • Transaction types (deposits vs withdrawals)")
        print("  • All amounts converted to cents for BAI2 format")
    
    print("\n" + "="*80)
    print("✅ FIELD EXTRACTION TEST COMPLETED!")
    print("   Review the tables above to see what data was extracted")
    print("   This is the same data that will be sent to Azure OpenAI for parsing")
    print("="*80)

if __name__ == "__main__":
    main()
