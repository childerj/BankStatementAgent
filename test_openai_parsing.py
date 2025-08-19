#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to extract fields from a PDF bank statement using Azure Document Intelligence
and then send the data to Azure OpenAI to parse and format it as a structured bank statement.
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
            
            return '\n'.join(all_lines)
        elif result.get("status") == "failed":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"   ❌ {model_name} failed: {error_msg}")
            return None
        
        print(".", end="", flush=True)
        time.sleep(2)

def send_to_openai(extracted_text):
    """Send extracted text to Azure OpenAI for structured parsing"""
    
    print("\n🤖 SENDING DATA TO AZURE OPENAI")
    print("=" * 60)
    
    # Get OpenAI configuration
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    if not openai_endpoint or not openai_key:
        print("❌ Azure OpenAI configuration missing!")
        return None
    
    print(f"🔗 OpenAI Endpoint: {openai_endpoint}")
    print(f"🚀 Deployment: {deployment_name}")
    print(f"📝 Text length: {len(extracted_text):,} characters")
    
    # Prepare the prompt
    prompt = f"""You are a bank statement parsing expert. I will provide you with raw OCR text extracted from a bank statement PDF, and I need you to parse and organize it into a structured bank statement format.

CRITICAL PARSING INSTRUCTIONS:
1. Look for transaction patterns where dates (like "6/02", "6/03") are followed by descriptions and amounts
2. DEPOSITS: "Deposit# 000000000000811" entries - find the corresponding dollar amounts on nearby lines
3. WITHDRAWALS: "WORLD ACCEPTANCE/CONC DEBIT" entries - find the corresponding dollar amounts on nearby lines
4. FEES: "MAINT FEE" or similar fee descriptions
5. Amounts appear as standalone numbers like "2,870.50", "1,211.00", "180.00", etc.
6. IGNORE: Lines that say "Ending Daily Balance" or similar balance reporting

AMOUNT MATCHING RULES:
- When you see a date like "6/04" followed by "Deposit# 000000000000811", look for the next standalone dollar amount
- When you see a date like "6/04" followed by "WORLD ACCEPTANCE/CONC DEBIT", look for the next standalone dollar amount
- Some transactions may have $0.00 amounts if no amount is listed nearby
- Match amounts carefully by examining the sequence of lines in the OCR text

Please analyze the following OCR text and create a properly formatted bank statement:

1. ACCOUNT INFORMATION (bank name, account holder, account number, statement period)
2. ACCOUNT SUMMARY (opening balance, closing balance, total deposits, total withdrawals)
3. TRANSACTION DETAILS in this format:

| Date       | Description                          | Amount      | Type       |
|------------|--------------------------------------|-------------|------------|

PARSING EXAMPLE:
If you see:
"6/04"
"Deposit# 000000000000811"
"2,870.50"
"6/04"
"WORLD ACCEPTANCE/CONC DEBIT"

Then parse as:
06/04/2025 | Deposit# 000000000000811 | +$2,870.50 | DEPOSIT
06/04/2025 | WORLD ACCEPTANCE/CONC DEBIT | -$2,870.50 | WITHDRAWAL

Here is the raw OCR text from the bank statement:

{extracted_text}

Please parse this data carefully, matching amounts to their corresponding transactions.""""""

    # Prepare the API request
    url = f"{openai_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-08-01-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that specializes in parsing and formatting bank statement data. You always provide clear, accurate, and well-organized responses."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.1,
        "top_p": 0.1
    }
    
    print("   ⏳ Sending request to Azure OpenAI...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            print(f"   ✅ OpenAI request successful!")
            print(f"   📊 Token usage: {prompt_tokens:,} prompt + {completion_tokens:,} completion = {total_tokens:,} total")
            
            return content
        else:
            print(f"   ❌ OpenAI request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ OpenAI request error: {e}")
        return None

def main():
    """Main function to test OpenAI parsing"""
    
    # PDF file path
    pdf_path = "Test Docs/811.pdf"
    
    print(f"⏰ Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Step 1: Extract text from PDF
    extracted_text = extract_pdf_fields(pdf_path)
    if not extracted_text:
        print("❌ Failed to extract text from PDF")
        return
    
    # Step 2: Send to OpenAI for parsing
    parsed_statement = send_to_openai(extracted_text)
    if not parsed_statement:
        print("❌ Failed to get parsed statement from OpenAI")
        return
    
    # Step 3: Display the results
    print("\n" + "="*80)
    print("🏦 AZURE OPENAI PARSED BANK STATEMENT")
    print("="*80)
    print(parsed_statement)
    print("="*80)
    print("✅ BANK STATEMENT PARSING COMPLETED!")
    print("   The statement above has been parsed and formatted by Azure OpenAI")
    print("="*80)

if __name__ == "__main__":
    main()
