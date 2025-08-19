#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Azure OpenAI endpoint configuration
"""

import os
import requests
import json
import sys
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

def test_azure_openai():
    """Test Azure OpenAI endpoint with a simple request"""
    
    print("🧪 TESTING AZURE OPENAI CONFIGURATION")
    print("=" * 60)
    
    # Load environment variables
    if not load_env_from_local_settings():
        return False
    
    # Get configuration
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    print(f"🔗 Endpoint: {openai_endpoint}")
    print(f"🚀 Deployment: {openai_deployment}")
    print(f"🔑 Key: {openai_key[:10]}...{openai_key[-5:] if openai_key else 'NOT SET'}")
    print("")
    
    # Validate configuration
    if not openai_endpoint or not openai_key:
        print("❌ Missing Azure OpenAI configuration!")
        print("   Please check your local.settings.json file")
        return False
    
    # Build URL
    url = f"{openai_endpoint}/openai/deployments/{openai_deployment}/chat/completions?api-version=2025-01-01-preview"
    print(f"🌐 Full URL: {url}")
    print("")
    
    # Prepare test request
    headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    test_payload = {
        "messages": [
            {
                "role": "user",
                "content": "Hello! Please respond with a simple JSON object containing your model name and the current status."
            }
        ],
        "max_tokens": 100,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    print("📤 Sending test request...")
    print(f"   Message: {test_payload['messages'][0]['content']}")
    print("")
    
    try:
        # Make the request
        response = requests.post(url, headers=headers, json=test_payload, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Azure OpenAI is working correctly")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print("")
            print("📋 RESPONSE DETAILS:")
            print("-" * 40)
            print(f"Content: {content}")
            
            # Try to parse as JSON
            try:
                parsed_content = json.loads(content)
                print("\n📊 Parsed JSON Response:")
                for key, value in parsed_content.items():
                    print(f"   {key}: {value}")
            except json.JSONDecodeError:
                print("⚠️  Response is not valid JSON (but that's okay for this test)")
            
            print("")
            print("🎉 Azure OpenAI integration is ready for bank statement processing!")
            return True
            
        else:
            print("❌ FAILED! Azure OpenAI request failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # Common error diagnostics
            if response.status_code == 401:
                print("\n🛠️  DIAGNOSIS: Authentication failed")
                print("   • Check if your API key is correct")
                print("   • Verify the key hasn't expired")
                
            elif response.status_code == 404:
                print("\n🛠️  DIAGNOSIS: Endpoint or deployment not found")
                print("   • Check if the endpoint URL is correct")
                print("   • Verify the deployment name exists")
                print("   • Confirm the deployment is in the same region")
                
            elif response.status_code == 429:
                print("\n🛠️  DIAGNOSIS: Rate limit exceeded")
                print("   • Wait a moment and try again")
                print("   • Check your quota limits")
                
            else:
                print(f"\n🛠️  DIAGNOSIS: Unexpected error ({response.status_code})")
                print("   • Check Azure OpenAI service status")
                print("   • Verify your subscription is active")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌ NETWORK ERROR!")
        print(f"   Error: {str(e)}")
        print("\n🛠️  TROUBLESHOOTING:")
        print("   • Check your internet connection")
        print("   • Verify the endpoint URL is accessible")
        print("   • Check if there are any firewall restrictions")
        return False
    
    except Exception as e:
        print("❌ UNEXPECTED ERROR!")
        print(f"   Error: {str(e)}")
        return False

def test_sample_bank_statement_parsing():
    """Test with a sample bank statement text"""
    
    print("\n" + "=" * 60)
    print("🏦 TESTING BANK STATEMENT PARSING")
    print("=" * 60)
    
    # Load environment variables
    if not load_env_from_local_settings():
        return False
    
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    
    if not openai_endpoint or not openai_key:
        print("❌ Azure OpenAI not configured")
        return False
    
    # Sample bank statement text
    sample_text = """
FIRST NATIONAL BANK
Account Statement
Account Number: 1234567890
Statement Period: 08/01/2025 - 08/06/2025

Previous Balance: $1,250.00
Current Balance: $1,485.50

TRANSACTIONS:
08/02/2025  DEPOSIT - PAYROLL           +$2,500.00
08/03/2025  WITHDRAWAL - ATM CASH       -$100.00
08/04/2025  CHECK #1234                 -$75.25
08/05/2025  ONLINE TRANSFER OUT         -$2,089.25
08/06/2025  INTEREST EARNED             +$0.50
"""
    
    prompt = f"""You are an expert at parsing bank statements and converting them to BAI2 format. 
    
Please analyze the following bank statement text and extract the key information needed for BAI2 conversion:

BANK STATEMENT TEXT:
{sample_text}

Please provide a JSON response with the following structure:
{{
    "bank_name": "Name of the bank (max 10 characters)",
    "account_number": "Account number (numbers only, max 20 digits)",
    "currency": "Currency code (usually USD)",
    "opening_balance": "Opening balance amount in cents (integer)",
    "closing_balance": "Closing balance amount in cents (integer)", 
    "transactions": [
        {{
            "date": "Transaction date in YYMMDD format",
            "amount": "Amount in cents (positive for credits, negative for debits)",
            "description": "Transaction description (max 50 chars)",
            "type": "Transaction type code (108 for deposit, 495 for withdrawal)"
        }}
    ],
    "statement_date": "Statement date in YYMMDD format"
}}

IMPORTANT GUIDELINES:
- Convert all monetary amounts to cents (multiply by 100)
- Use positive amounts for credits/deposits and negative for debits/withdrawals
- Keep bank name to 10 characters max
- Keep account number to 20 digits max
- Keep transaction descriptions to 50 characters max
- Use transaction type 108 for deposits/credits, 495 for withdrawals/debits
"""

    url = f"{openai_endpoint}/openai/deployments/{openai_deployment}/chat/completions?api-version=2025-01-01-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
        "response_format": {"type": "json_object"}
    }
    
    print("📤 Sending bank statement parsing test...")
    print("📄 Sample statement includes:")
    print("   • Bank: First National Bank")
    print("   • Account: 1234567890")
    print("   • 5 transactions")
    print("   • Balance: $1,250.00 → $1,485.50")
    print("")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            print("✅ Bank statement parsing test SUCCESSFUL!")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                parsed_data = json.loads(content)
                
                print("\n🧠 PARSED BANKING DATA:")
                print("-" * 40)
                print(f"🏦 Bank: {parsed_data.get('bank_name', 'N/A')}")
                print(f"🔢 Account: {parsed_data.get('account_number', 'N/A')}")
                print(f"💱 Currency: {parsed_data.get('currency', 'N/A')}")
                print(f"💰 Opening Balance: ${parsed_data.get('opening_balance', 0)/100:.2f}")
                print(f"💰 Closing Balance: ${parsed_data.get('closing_balance', 0)/100:.2f}")
                
                transactions = parsed_data.get('transactions', [])
                print(f"📝 Transactions: {len(transactions)}")
                
                if transactions:
                    print("\n📋 TRANSACTION DETAILS:")
                    for i, txn in enumerate(transactions, 1):
                        amount = txn.get('amount', 0)
                        desc = txn.get('description', 'N/A')
                        date = txn.get('date', 'N/A')
                        txn_type = txn.get('type', 'N/A')
                        
                        sign = "+" if amount >= 0 else ""
                        print(f"   {i}. {date} | ${sign}{amount/100:.2f} | {desc} | Type: {txn_type}")
                
                print("\n🎉 Azure OpenAI successfully parsed the bank statement!")
                print("   The function is ready for real bank statement processing.")
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {content}")
                return False
                
        else:
            print(f"❌ Bank statement parsing test FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during bank statement parsing test: {e}")
        return False

if __name__ == "__main__":
    print(f"⏰ Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Test basic connectivity
    basic_test_passed = test_azure_openai()
    
    if basic_test_passed:
        # Test bank statement parsing
        parsing_test_passed = test_sample_bank_statement_parsing()
        
        if parsing_test_passed:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("🚀 Your Azure OpenAI integration is ready for production use!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️  BASIC TEST PASSED but PARSING TEST FAILED")
            print("   Azure OpenAI works but may need prompt adjustments")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ BASIC TEST FAILED")
        print("   Fix configuration issues before proceeding")
        print("=" * 60)
        sys.exit(1)
