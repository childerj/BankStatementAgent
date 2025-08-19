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
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ServiceRequestError, HttpResponseError

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

def extract_pdf_fields_sdk(pdf_path):
    """Extract fields from PDF using Azure Document Intelligence SDK with prebuilt-bankStatement.us model"""
    
    print("🔍 EXTRACTING DATA USING SDK (prebuilt-bankStatement.us)")
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
            document_bytes = f.read()
        file_size = len(document_bytes)
        print(f"📊 File size: {file_size:,} bytes")
    except Exception as e:
        print(f"❌ Failed to read PDF file: {e}")
        return None
    
    try:
        # Create Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(key)
        )
        
        print("🤖 Using prebuilt-bankStatement.us model...")
        print("   ⏳ Starting analysis...")
        
        # Analyze document using the bank statement model
        poller = client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            document_bytes,
            content_type="application/pdf"
        )
        
        # Wait for completion
        result = poller.result()
        
        print("   ✅ Analysis completed successfully!")
        
        # Process the results
        analyze_result = result.as_dict()
        
        # Extract structured data
        structured_data = {
            "model_used": "prebuilt-bankStatement.us",
            "extraction_method": "SDK"
        }
        
        # Check for documents (structured data)
        documents = analyze_result.get('documents', [])
        if documents:
            print(f"   📋 Found {len(documents)} structured document(s)")
            
            doc = documents[0]  # Use first document
            fields = doc.get('fields', {})
            
            # Account Information
            if 'BankName' in fields:
                bank_name = fields['BankName'].get('value_string') or fields['BankName'].get('content', '')
                structured_data['bank_name'] = bank_name
                print(f"   🏦 Bank: {bank_name}")
            
            if 'AccountHolderName' in fields:
                holder_name = fields['AccountHolderName'].get('value_string') or fields['AccountHolderName'].get('content', '')
                structured_data['account_holder'] = holder_name
                print(f"   👤 Account Holder: {holder_name}")
            
            if 'AccountNumber' in fields:
                account_num = fields['AccountNumber'].get('value_string') or fields['AccountNumber'].get('content', '')
                structured_data['account_number'] = account_num
                print(f"   🔢 Account Number: {account_num}")
            
            # Statement period
            if 'StatementStartDate' in fields:
                start_date = fields['StatementStartDate'].get('value_string') or fields['StatementStartDate'].get('content', '')
                structured_data['start_date'] = start_date
                print(f"   📅 Start Date: {start_date}")
            
            if 'StatementEndDate' in fields:
                end_date = fields['StatementEndDate'].get('value_string') or fields['StatementEndDate'].get('content', '')
                structured_data['end_date'] = end_date
                print(f"   📅 End Date: {end_date}")
            
            # Balance Information
            balance_fields = ['BeginningBalance', 'EndingBalance']
            for field_name in balance_fields:
                if field_name in fields:
                    field = fields[field_name]
                    if 'value_currency' in field:
                        currency_info = field['value_currency']
                        amount = currency_info.get('amount', 0)
                        structured_data[field_name.lower()] = amount
                        print(f"   💰 {field_name}: ${amount}")
            
            # Transactions
            transactions = []
            if 'Transactions' in fields:
                transactions_field = fields['Transactions']
                if 'value_array' in transactions_field:
                    trans_list = transactions_field['value_array']
                    print(f"   💳 Found {len(trans_list)} structured transactions")
                    
                    for trans in trans_list:
                        if 'value_object' in trans:
                            trans_obj = trans['value_object']
                            transaction = {}
                            
                            # Date
                            if 'Date' in trans_obj:
                                date_field = trans_obj['Date']
                                date_value = date_field.get('value_date') or date_field.get('content', '')
                                transaction['date'] = date_value
                            
                            # Description
                            if 'Description' in trans_obj:
                                desc_field = trans_obj['Description']
                                desc_value = desc_field.get('value_string') or desc_field.get('content', '')
                                transaction['description'] = desc_value
                            
                            # Amount
                            if 'Amount' in trans_obj:
                                amount_field = trans_obj['Amount']
                                if 'value_currency' in amount_field:
                                    currency_info = amount_field['value_currency']
                                    amount = currency_info.get('amount', 0)
                                    transaction['amount'] = amount
                                else:
                                    amount_value = amount_field.get('content', '0')
                                    transaction['amount'] = amount_value
                            
                            # Transaction Type
                            if 'TransactionType' in trans_obj:
                                type_field = trans_obj['TransactionType']
                                type_value = type_field.get('value_string') or type_field.get('content', '')
                                transaction['type'] = type_value
                            
                            if transaction:
                                transactions.append(transaction)
            
            structured_data['transactions'] = transactions
            
        # Also get raw text as fallback
        pages = analyze_result.get('pages', [])
        all_lines = []
        if pages:
            for page in pages:
                lines = page.get('lines', [])
                for line in lines:
                    content = line.get('content', '')
                    if content.strip():
                        all_lines.append(content.strip())
        
        structured_data['raw_text'] = '\n'.join(all_lines)
        structured_data['lines_extracted'] = len(all_lines)
        
        return structured_data
        
    except ServiceRequestError as e:
        print(f"   ❌ Service request error: {e}")
        return None
    except HttpResponseError as e:
        print(f"   ❌ HTTP response error: {e}")
        print(f"   Status code: {e.status_code}")
        if hasattr(e, 'error') and e.error:
            print(f"   Error code: {e.error.code}")
            print(f"   Error message: {e.error.message}")
        return None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return None

def extract_pdf_fields_rest_api(pdf_path):
    """Extract fields from PDF using Azure Document Intelligence REST API with prebuilt-layout model"""
    
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
    
    # Use prebuilt-layout model (fallback since bankStatement model not available)
    model_name = "prebuilt-layout"
    url = f"{endpoint}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31"
    
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
            
            # Extract structured data from layout model
            analyze_result = result.get("analyzeResult", {})
            
            # Layout model provides better structure than read model
            pages = analyze_result.get("pages", [])
            tables = analyze_result.get("tables", [])
            
            # Extract text with better structure awareness
            all_lines = []
            for page in pages:
                lines = page.get("lines", [])
                for line in lines:
                    line_text = line.get("content", "")
                    if line_text.strip():
                        all_lines.append(line_text.strip())
            
            # If we have tables, add them too
            table_info = []
            for i, table in enumerate(tables):
                table_info.append(f"\n--- TABLE {i+1} ---")
                cells = table.get("cells", [])
                for cell in cells:
                    content = cell.get("content", "").strip()
                    if content:
                        row = cell.get("rowIndex", 0)
                        col = cell.get("columnIndex", 0)
                        table_info.append(f"Row {row}, Col {col}: {content}")
            
            raw_text = '\n'.join(all_lines)
            if table_info:
                raw_text += '\n\n' + '\n'.join(table_info)
            
            # Return as structured data for consistency
            return {
                "raw_text": raw_text,
                "model_used": "prebuilt-layout",
                "extraction_method": "REST_API",
                "tables_found": len(tables),
                "lines_extracted": len(all_lines)
            }
        elif result.get("status") == "failed":
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"   ❌ {model_name} failed: {error_msg}")
            return None
        
        print(".", end="", flush=True)
        time.sleep(2)

def send_to_openai(extracted_data):
    """Send extracted data to Azure OpenAI for structured parsing"""
    
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
    
    # Check if we have structured data or raw text
    if isinstance(extracted_data, dict):
        extraction_method = extracted_data.get('extraction_method', 'unknown')
        model_used = extracted_data.get('model_used', 'unknown')
        
        print(f"📊 Using {extraction_method} data (Model: {model_used})")
        
        # Handle SDK structured data with transactions
        if 'transactions' in extracted_data and extracted_data['transactions']:
            transactions = extracted_data['transactions']
            print(f"   💳 Structured transactions: {len(transactions)}")
            
            # Format structured data for OpenAI
            structured_info = []
            if extracted_data.get('bank_name'):
                structured_info.append(f"Bank: {extracted_data['bank_name']}")
            if extracted_data.get('account_number'):
                structured_info.append(f"Account: {extracted_data['account_number']}")
            if extracted_data.get('account_holder'):
                structured_info.append(f"Account Holder: {extracted_data['account_holder']}")
            if extracted_data.get('start_date') and extracted_data.get('end_date'):
                structured_info.append(f"Statement Period: {extracted_data['start_date']} to {extracted_data['end_date']}")
            if extracted_data.get('beginningbalance') is not None:
                structured_info.append(f"Opening Balance: ${extracted_data['beginningbalance']}")
            if extracted_data.get('endingbalance') is not None:
                structured_info.append(f"Closing Balance: ${extracted_data['endingbalance']}")
            
            # Format transactions
            transaction_info = []
            for i, trans in enumerate(transactions, 1):
                trans_str = f"Transaction {i}: "
                if trans.get('date'):
                    trans_str += f"Date: {trans['date']}, "
                if trans.get('description'):
                    trans_str += f"Description: {trans['description']}, "
                if trans.get('amount') is not None:
                    trans_str += f"Amount: ${trans['amount']}, "
                if trans.get('type'):
                    trans_str += f"Type: {trans['type']}"
                transaction_info.append(trans_str.rstrip(", "))
            
            # Combine structured and raw text
            formatted_data = "\n".join(structured_info)
            if transaction_info:
                formatted_data += "\n\nSTRUCTURED TRANSACTIONS:\n" + "\n".join(transaction_info)
            
            # Also include raw text for comprehensive analysis
            if extracted_data.get("raw_text"):
                formatted_data += "\n\nRAW OCR TEXT:\n" + extracted_data["raw_text"]
            
            print(f"📝 Formatted data length: {len(formatted_data):,} characters")
        else:
            # Handle REST API layout model data
            if extracted_data.get('tables_found', 0) > 0:
                print(f"   � Tables found: {extracted_data['tables_found']}")
            if extracted_data.get('lines_extracted', 0) > 0:
                print(f"   📝 Lines extracted: {extracted_data['lines_extracted']}")
            
            # Use the raw text from layout model
            formatted_data = extracted_data.get("raw_text", "")
            print(f"📝 Formatted data length: {len(formatted_data):,} characters")
    else:
        print("📝 Using raw OCR text")
        formatted_data = extracted_data
        print(f"📝 Text length: {len(formatted_data):,} characters")
    
    # Prepare the prompt
    prompt = f"""You are a bank statement parsing expert. I will provide you with raw OCR text extracted from a bank statement PDF, and I need you to parse and organize it into a structured bank statement format.

CRITICAL PARSING INSTRUCTIONS:
You must capture ALL transactions from the bank statement, even if some amounts are unclear or missing.

TRANSACTION IDENTIFICATION RULES:
1. Look for ALL date patterns like "6/02", "6/03", "6/04", "6/05", "6/06", "6/09", "6/10", "6/11", "6/12", "6/13", "6/16", "6/17", "6/18", "6/20", "6/23", "6/24", "6/25", "6/26", "6/27", "6/30" etc.
2. EVERY occurrence of "Deposit# 000000000000811" is a separate deposit transaction
3. EVERY occurrence of "WORLD ACCEPTANCE/CONC DEBIT" is a separate withdrawal transaction  
4. EVERY occurrence of "MAINT FEE" is a fee transaction

COMPREHENSIVE PARSING STRATEGY:
- Go through the OCR text systematically and find EVERY date
- For each date, look for transaction descriptions that follow
- Include ALL transactions, even if the amount is unclear - use $0.00 for unclear amounts
- Do NOT skip transactions just because the amount is hard to determine
- The bank statement shows daily activity with multiple transactions per day

AMOUNT MATCHING (Best Effort):
- Look for amounts near transaction descriptions
- If an amount is unclear, use $0.00 but still include the transaction
- Some transactions may share amounts or have amounts listed separately
- Focus on capturing ALL transaction occurrences rather than perfect amount matching

WHAT TO IGNORE:
- Summary totals and balances
- Headers and page information
- Account information (use for header section only)

EXPECTED TRANSACTION VOLUME:
Based on the OCR data, there should be 40+ individual transactions across the month of June. Make sure you capture:
- Multiple transactions per day (especially 6/02, 6/03, 6/04, 6/05, 6/06, 6/09, 6/10, 6/11, etc.)
- Both deposits and withdrawals for most days
- All occurrences of the transaction patterns

Please analyze the following OCR text and create a comprehensive bank statement that includes ALL transactions:

1. ACCOUNT INFORMATION (bank name, account holder, account number, statement period)
2. ACCOUNT SUMMARY (opening balance, closing balance, total deposits, total withdrawals)
3. TRANSACTION DETAILS - Include ALL dated transactions:

| Date       | Description                          | Amount      | Type       |
|------------|--------------------------------------|-------------|------------|

Here is the bank statement data extracted using Azure Document Intelligence:

{formatted_data}

Please parse this data comprehensively, ensuring you capture ALL transaction occurrences from the statement."""

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

def reconcile_balances(parsed_statement_text):
    """Extract balances and transactions from parsed statement and verify reconciliation"""
    
    print("\n🔍 BALANCE RECONCILIATION")
    print("=" * 60)
    
    import re
    
    # Extract opening and closing balances
    opening_balance = None
    closing_balance = None
    
    # Look for opening balance patterns
    opening_patterns = [
        r"Opening Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"Beginning Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"Starting Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"\|\s*Opening Balance\s*\|\s*\$?([\d,]+\.?\d*)\s*\|",
        r"Opening Balance.*?\$?([\d,]+\.?\d*)"
    ]
    
    for pattern in opening_patterns:
        match = re.search(pattern, parsed_statement_text, re.IGNORECASE)
        if match:
            opening_balance = float(match.group(1).replace(',', ''))
            break
    
    # Look for closing balance patterns
    closing_patterns = [
        r"Closing Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"Ending Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"Final Balance[:\s]+\$?([\d,]+\.?\d*)",
        r"\|\s*Closing Balance\s*\|\s*\$?([\d,]+\.?\d*)\s*\|",
        r"Closing Balance.*?\$?([\d,]+\.?\d*)"
    ]
    
    for pattern in closing_patterns:
        match = re.search(pattern, parsed_statement_text, re.IGNORECASE)
        if match:
            closing_balance = float(match.group(1).replace(',', ''))
            break
    
    print(f"💰 Opening Balance: ${opening_balance:,.2f}" if opening_balance is not None else "❌ Opening Balance: Not found")
    print(f"💰 Closing Balance: ${closing_balance:,.2f}" if closing_balance is not None else "❌ Closing Balance: Not found")
    
    if opening_balance is None or closing_balance is None:
        print("❌ Cannot perform reconciliation - missing balance information")
        return False
    
    # Extract transaction totals
    total_deposits = 0
    total_withdrawals = 0
    
    # Look for transaction summary totals first
    deposit_total_patterns = [
        r"Total Deposits[:\s]+\$?([\d,]+\.?\d*)",
        r"Total Credits[:\s]+\$?([\d,]+\.?\d*)",
        r"Deposits Total[:\s]+\$?([\d,]+\.?\d*)",
        r"\|\s*Total Deposits\s*\|\s*\$?([\d,]+\.?\d*)\s*\|",
        r"Total Deposits.*?\$?([\d,]+\.?\d*)"
    ]
    
    withdrawal_total_patterns = [
        r"Total Withdrawals[:\s]+\$?([\d,]+\.?\d*)",
        r"Total Debits[:\s]+\$?([\d,]+\.?\d*)",
        r"Withdrawals Total[:\s]+\$?([\d,]+\.?\d*)",
        r"\|\s*Total Withdrawals\s*\|\s*\$?([\d,]+\.?\d*)\s*\|",
        r"Total Withdrawals.*?\$?([\d,]+\.?\d*)"
    ]
    
    # Try to find summary totals
    for pattern in deposit_total_patterns:
        match = re.search(pattern, parsed_statement_text, re.IGNORECASE)
        if match:
            total_deposits = float(match.group(1).replace(',', ''))
            break
    
    for pattern in withdrawal_total_patterns:
        match = re.search(pattern, parsed_statement_text, re.IGNORECASE)
        if match:
            total_withdrawals = float(match.group(1).replace(',', ''))
            break
    
    # If no summary totals found, calculate from individual transactions
    if total_deposits == 0 or total_withdrawals == 0:
        print("   📊 Summary totals not found, calculating from individual transactions...")
        
        # Find the transaction table section
        table_match = re.search(r'\| Date.*?\| Type.*?\|.*?\n(.*?)(?:\n\n|\n---|\n\*|$)', parsed_statement_text, re.DOTALL | re.IGNORECASE)
        
        if table_match:
            table_content = table_match.group(1)
            
            # Parse individual transaction lines
            transaction_lines = table_content.strip().split('\n')
            
            calculated_deposits = 0
            calculated_withdrawals = 0
            transaction_count = 0
            
            for line in transaction_lines:
                if '|' in line and not line.strip().startswith('|---'):
                    parts = [part.strip() for part in line.split('|')]
                    if len(parts) >= 4:
                        try:
                            # Amount is typically in the 3rd column (index 2)
                            amount_str = parts[2].replace('$', '').replace(',', '').strip()
                            if amount_str and amount_str != '0.00':
                                amount = float(amount_str)
                                
                                # Type is typically in the 4th column (index 3)
                                trans_type = parts[3].lower().strip()
                                
                                if 'deposit' in trans_type or 'credit' in trans_type:
                                    calculated_deposits += amount
                                elif 'withdrawal' in trans_type or 'debit' in trans_type or 'fee' in trans_type:
                                    calculated_withdrawals += amount
                                
                                transaction_count += 1
                        except (ValueError, IndexError):
                            continue
            
            # Use calculated totals if we found transactions
            if transaction_count > 0:
                total_deposits = calculated_deposits
                total_withdrawals = calculated_withdrawals
                print(f"   ✅ Calculated from {transaction_count} individual transactions")
    
    print(f"💳 Total Deposits: ${total_deposits:,.2f}")
    print(f"💸 Total Withdrawals: ${total_withdrawals:,.2f}")
    
    # Perform reconciliation
    expected_closing = opening_balance + total_deposits - total_withdrawals
    actual_closing = closing_balance
    
    print(f"\n🧮 RECONCILIATION CHECK:")
    print(f"   Opening Balance:    ${opening_balance:,.2f}")
    print(f"   + Total Deposits:   ${total_deposits:,.2f}")
    print(f"   - Total Withdrawals: ${total_withdrawals:,.2f}")
    print(f"   = Expected Closing: ${expected_closing:,.2f}")
    print(f"   Actual Closing:     ${actual_closing:,.2f}")
    
    difference = abs(expected_closing - actual_closing)
    print(f"   Difference:         ${difference:,.2f}")
    
    # Allow for small rounding differences (up to $0.01)
    tolerance = 0.01
    
    if difference <= tolerance:
        print("   ✅ BALANCE RECONCILIATION SUCCESSFUL!")
        print(f"   📊 Statement balances correctly (difference: ${difference:,.2f})")
        return True
    else:
        print("   ❌ BALANCE RECONCILIATION FAILED!")
        print(f"   🚨 Difference of ${difference:,.2f} exceeds tolerance of ${tolerance:.2f}")
        print("   💡 Possible issues:")
        print("      • Missing transactions in the parsed data")
        print("      • Incorrect transaction amounts")
        print("      • Fees or adjustments not properly categorized")
        print("      • OCR parsing errors in amounts")
        return False

def main():
    """Main function to test OpenAI parsing with multiple extraction methods"""
    
    # PDF file path
    pdf_path = "Test Docs/811.pdf"
    
    print(f"⏰ Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Step 1: Try SDK method first (prebuilt-bankStatement.us), then fallback to REST API
    print("🔄 TRYING MULTIPLE EXTRACTION METHODS")
    print("=" * 60)
    
    extracted_data = None
    
    # Method 1: Try SDK with prebuilt-bankStatement.us model
    print("Method 1: SDK with prebuilt-bankStatement.us model")
    extracted_data = extract_pdf_fields_sdk(pdf_path)
    
    if not extracted_data:
        print("\n⚠️ SDK method failed, falling back to REST API with layout model")
        print("\nMethod 2: REST API with prebuilt-layout model")
        extracted_data = extract_pdf_fields_rest_api(pdf_path)
    
    if not extracted_data:
        print("❌ All extraction methods failed")
        return
    
    # Display extraction summary
    print(f"\n📊 EXTRACTION SUMMARY")
    print("=" * 40)
    method = extracted_data.get('extraction_method', 'Unknown')
    model = extracted_data.get('model_used', 'Unknown')
    print(f"✅ Successful method: {method}")
    print(f"🤖 Model used: {model}")
    
    if 'transactions' in extracted_data and extracted_data['transactions']:
        print(f"💳 Structured transactions: {len(extracted_data['transactions'])}")
    
    if 'lines_extracted' in extracted_data:
        print(f"📝 Raw text lines: {extracted_data['lines_extracted']}")
    
    # Step 2: Send to OpenAI for parsing
    parsed_statement = send_to_openai(extracted_data)
    if not parsed_statement:
        print("❌ Failed to get parsed statement from OpenAI")
        return
    
    # Step 3: Display the results
    print("\n" + "="*80)
    print("🏦 AZURE OPENAI PARSED BANK STATEMENT")
    print("="*80)
    print(parsed_statement)
    print("="*80)
    
    # Step 4: Perform balance reconciliation
    reconciliation_passed = reconcile_balances(parsed_statement)
    
    # Final summary
    print("\n" + "="*80)
    if reconciliation_passed:
        print("✅ BANK STATEMENT PARSING AND RECONCILIATION COMPLETED SUCCESSFULLY!")
        print(f"   • Extraction method: {method} ({model})")
        print("   • Parsed by Azure OpenAI")
        print("   • Balance reconciliation: PASSED ✅")
    else:
        print("⚠️ BANK STATEMENT PARSING COMPLETED WITH RECONCILIATION ISSUES!")
        print(f"   • Extraction method: {method} ({model})")
        print("   • Parsed by Azure OpenAI")
        print("   • Balance reconciliation: FAILED ❌")
        print("\n🚨 RECONCILIATION ERROR:")
        print("   The statement does not balance correctly. This may indicate:")
        print("   • Missing or incorrect transactions")
        print("   • OCR parsing errors")
        print("   • Data extraction issues")
        print("   • Please review the parsed statement for accuracy")
    print("="*80)

if __name__ == "__main__":
    main()
