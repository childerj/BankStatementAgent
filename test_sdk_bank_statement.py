#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script using Azure Document Intelligence Python SDK with prebuilt-bankStatement.us model
"""

import os
import json
from datetime import datetime
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

def test_bank_statement_model(pdf_path):
    """Test the prebuilt-bankStatement.us model using Azure SDK"""
    
    print("🔍 TESTING AZURE DOCUMENT INTELLIGENCE SDK")
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
        # Simple method call with just model_id and document data
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
        
        # Print general information
        print("\n📊 ANALYSIS RESULTS")
        print("=" * 40)
        print(f"API Version: {analyze_result.get('api_version', 'Unknown')}")
        print(f"Model ID: {analyze_result.get('model_id', 'Unknown')}")
        
        # Check for documents (structured data)
        documents = analyze_result.get('documents', [])
        if documents:
            print(f"\n📋 Found {len(documents)} structured document(s)")
            
            for doc_idx, doc in enumerate(documents):
                print(f"\n--- DOCUMENT {doc_idx + 1} ---")
                doc_type = doc.get('doc_type', 'Unknown')
                confidence = doc.get('confidence', 0)
                print(f"Document Type: {doc_type}")
                print(f"Confidence: {confidence:.2f}")
                
                # Extract fields
                fields = doc.get('fields', {})
                print(f"Fields found: {len(fields)}")
                
                # Account Information
                print("\n🏦 ACCOUNT INFORMATION:")
                account_fields = ['BankName', 'AccountNumber', 'AccountHolderName', 'StatementStartDate', 'StatementEndDate']
                for field_name in account_fields:
                    if field_name in fields:
                        field = fields[field_name]
                        value = field.get('value_string') or field.get('content', 'N/A')
                        confidence = field.get('confidence', 0)
                        print(f"  {field_name}: {value} (confidence: {confidence:.2f})")
                
                # Balance Information
                print("\n💰 BALANCE INFORMATION:")
                balance_fields = ['BeginningBalance', 'EndingBalance']
                for field_name in balance_fields:
                    if field_name in fields:
                        field = fields[field_name]
                        if 'value_currency' in field:
                            currency_info = field['value_currency']
                            amount = currency_info.get('amount', 0)
                            currency_code = currency_info.get('currency_code', 'USD')
                            confidence = field.get('confidence', 0)
                            print(f"  {field_name}: {amount} {currency_code} (confidence: {confidence:.2f})")
                        else:
                            value = field.get('content', 'N/A')
                            confidence = field.get('confidence', 0)
                            print(f"  {field_name}: {value} (confidence: {confidence:.2f})")
                
                # Transaction Information
                if 'Transactions' in fields:
                    transactions_field = fields['Transactions']
                    if 'value_array' in transactions_field:
                        transactions = transactions_field['value_array']
                        print(f"\n💳 TRANSACTIONS ({len(transactions)} found):")
                        
                        for trans_idx, trans in enumerate(transactions[:10]):  # Show first 10
                            print(f"\n  Transaction {trans_idx + 1}:")
                            if 'value_object' in trans:
                                trans_obj = trans['value_object']
                                
                                # Date
                                if 'Date' in trans_obj:
                                    date_field = trans_obj['Date']
                                    date_value = date_field.get('value_date') or date_field.get('content', 'N/A')
                                    print(f"    Date: {date_value}")
                                
                                # Description
                                if 'Description' in trans_obj:
                                    desc_field = trans_obj['Description']
                                    desc_value = desc_field.get('value_string') or desc_field.get('content', 'N/A')
                                    print(f"    Description: {desc_value}")
                                
                                # Amount
                                if 'Amount' in trans_obj:
                                    amount_field = trans_obj['Amount']
                                    if 'value_currency' in amount_field:
                                        currency_info = amount_field['value_currency']
                                        amount = currency_info.get('amount', 0)
                                        currency_code = currency_info.get('currency_code', 'USD')
                                        print(f"    Amount: {amount} {currency_code}")
                                    else:
                                        amount_value = amount_field.get('content', 'N/A')
                                        print(f"    Amount: {amount_value}")
                                
                                # Transaction Type
                                if 'TransactionType' in trans_obj:
                                    type_field = trans_obj['TransactionType']
                                    type_value = type_field.get('value_string') or type_field.get('content', 'N/A')
                                    print(f"    Type: {type_value}")
                        
                        if len(transactions) > 10:
                            print(f"\n  ... and {len(transactions) - 10} more transactions")
                
                # Print all available fields for debugging
                print(f"\n🔍 ALL AVAILABLE FIELDS:")
                for field_name, field_data in fields.items():
                    field_type = type(field_data.get('value_string') or 
                                   field_data.get('value_currency') or 
                                   field_data.get('value_array') or 
                                   field_data.get('content', '')).__name__
                    confidence = field_data.get('confidence', 0)
                    print(f"  {field_name}: {field_type} (confidence: {confidence:.2f})")
        
        else:
            print("\n⚠️ No structured documents found")
        
        # Also show raw text as fallback
        pages = analyze_result.get('pages', [])
        if pages:
            print(f"\n📄 RAW TEXT (from {len(pages)} pages):")
            all_lines = []
            for page in pages:
                lines = page.get('lines', [])
                for line in lines:
                    content = line.get('content', '')
                    if content.strip():
                        all_lines.append(content.strip())
            
            print(f"Total lines extracted: {len(all_lines)}")
            if all_lines:
                print("First 10 lines:")
                for i, line in enumerate(all_lines[:10]):
                    print(f"  {i+1}: {line}")
                if len(all_lines) > 10:
                    print(f"  ... and {len(all_lines) - 10} more lines")
        
        return analyze_result
        
    except ServiceRequestError as e:
        print(f"   ❌ Service request error: {e}")
        return None
    except HttpResponseError as e:
        print(f"   ❌ HTTP response error: {e}")
        print(f"   Status code: {e.status_code}")
        print(f"   Error code: {e.error.code if hasattr(e, 'error') and e.error else 'Unknown'}")
        return None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return None

def main():
    """Main function to test the SDK"""
    
    # PDF file path
    pdf_path = "Test Docs/811.pdf"
    
    print(f"⏰ SDK Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    # Test the bank statement model
    result = test_bank_statement_model(pdf_path)
    
    if result:
        print("\n" + "="*80)
        print("✅ SDK TEST COMPLETED SUCCESSFULLY!")
        print("   The prebuilt-bankStatement.us model analysis is complete")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ SDK TEST FAILED!")
        print("   The prebuilt-bankStatement.us model could not analyze the document")
        print("="*80)

if __name__ == "__main__":
    main()
