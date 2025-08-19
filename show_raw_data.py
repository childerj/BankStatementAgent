#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to show raw OCR data around specific transaction dates
"""

import os
import requests
import time
import json
from datetime import datetime

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
    """Extract fields from PDF using Azure Document Intelligence OCR/Read model"""
    
    print("🔍 EXTRACTING TEXT FROM PDF")
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
    
    # Use OCR/Read model
    model_name = "OCR/Read Model"
    url = f"{endpoint}/formrecognizer/documentModels/prebuilt-read:analyze?api-version=2023-07-31"
    
    print(f"🤖 Using {model_name} for text extraction...")
    
    # Submit document
    response = requests.post(url, headers=headers, data=file_bytes)
    
    if response.status_code != 202:
        print(f"   ❌ {model_name} failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    operation_location = response.headers.get("operation-location")
    if not operation_location:
        print(f"   ❌ No operation-location header from {model_name}")
        return None
    
    print(f"   ⏳ {model_name} processing...")
    
    # Poll for completion
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while True:
        if time.time() - start_time > max_wait_time:
            print(f"   ❌ {model_name} timed out")
            return None
            
        result = requests.get(operation_location, headers=headers).json()
        if result.get("status") == "succeeded":
            elapsed = int(time.time() - start_time)
            print(f"   ✅ {model_name} completed in {elapsed} seconds")
            
            # Extract all text lines
            analyze_result = result.get("analyzeResult", {})
            pages = analyze_result.get("pages", [])
            
            all_lines = []
            for page in pages:
                lines = page.get("lines", [])
                for line in lines:
                    line_text = line.get("content", "")
                    if line_text.strip():
                        all_lines.append(line_text.strip())
            
            return all_lines
        elif result.get("status") == "failed":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"   ❌ {model_name} failed: {error_msg}")
            return None
        
        print(".", end="", flush=True)
        time.sleep(2)

def show_raw_data_around_date(lines, target_date):
    """Show raw OCR data around a specific date"""
    
    print(f"\n📋 RAW OCR DATA AROUND DATE: {target_date}")
    print("=" * 80)
    
    # Find all occurrences of the target date
    date_indices = []
    for i, line in enumerate(lines):
        if target_date in line:
            date_indices.append(i)
    
    if not date_indices:
        print(f"❌ Date '{target_date}' not found in OCR data")
        return
    
    print(f"✅ Found {len(date_indices)} occurrence(s) of date '{target_date}' at line(s): {date_indices}")
    print("")
    
    # Show context around each occurrence
    for idx, line_num in enumerate(date_indices):
        print(f"📍 OCCURRENCE {idx + 1} - Line {line_num + 1}:")
        print("-" * 40)
        
        # Show 10 lines before and after the target date
        start_line = max(0, line_num - 10)
        end_line = min(len(lines), line_num + 11)
        
        for i in range(start_line, end_line):
            marker = " ➤ " if i == line_num else "   "
            print(f"{marker}{i + 1:3d}: {lines[i]}")
        
        print("")

def main():
    """Main function to show raw data around 6/2"""
    
    # PDF file path
    pdf_path = "Test Docs/811.pdf"
    
    print(f"⏰ Analysis started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Extract all lines from PDF
    lines = extract_pdf_fields(pdf_path)
    if not lines:
        print("❌ Failed to extract lines from PDF")
        return
    
    print(f"\n📊 TOTAL LINES EXTRACTED: {len(lines)}")
    
    # Show raw data around 6/02
    show_raw_data_around_date(lines, "6/02")
    
    # Also show around 6/2 (without leading zero)
    show_raw_data_around_date(lines, "6/2")
    
    print("\n" + "="*80)
    print("✅ RAW DATA ANALYSIS COMPLETED!")
    print("="*80)

if __name__ == "__main__":
    main()
