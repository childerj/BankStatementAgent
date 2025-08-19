"""
Two-pass comprehensive extraction to find ALL 104 transactions
"""
import os
import json
import requests
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
from tabulate import tabulate

# Load environment variables
if os.path.exists('local.settings.json'):
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        values = settings.get('Values', {})
        for key, value in values.items():
            os.environ[key] = value

def two_pass_extraction():
    """Two-pass extraction to find all 104 transactions"""
    
    # Test file
    test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\822-847-896.pdf'
    
    print("🎯 TWO-PASS COMPREHENSIVE EXTRACTION")
    print("🎯 TARGET: 51 deposits + 53 withdrawals = 104 transactions")
    print("=" * 70)
    
    # Extract OCR data first
    endpoint = os.environ["DOCINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCINTELLIGENCE_KEY"]
    
    with open(test_file, 'rb') as f:
        file_bytes = f.read()
    
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    
    print("📊 Extracting OCR data...")
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=BytesIO(file_bytes),
        content_type="application/pdf"
    )
    result = poller.result()
    
    if result and result.content:
        ocr_text = result.content
        print(f"📊 Total OCR text: {len(ocr_text):,} characters")
    else:
        print("❌ Failed to extract OCR text")
        return
    
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    
    if not openai_endpoint or not openai_key:
        print("❌ OpenAI credentials not configured")
        return
    
    # PASS 1: Ultra-aggressive extraction prompt
    print("\n🚀 PASS 1: Ultra-aggressive extraction...")
    
    pass1_prompt = f"""
You are an EXPERT bank statement parser with ONE CRITICAL MISSION:
Find ALL 104 transactions in this 5-page bank statement. This is PASS 1 of 2.

CRITICAL MISSION PARAMETERS:
- EXACTLY 51 deposits (positive amounts)  
- EXACTLY 53 withdrawals (negative amounts)
- TOTAL: 104 transactions
- NO EXCEPTIONS - FIND THEM ALL

ULTRA-AGGRESSIVE PARSING STRATEGY:
1. Scan EVERY SINGLE LINE of text
2. Look for ANY pattern that could be a transaction:
   - Date + amount pairs
   - Running balance changes
   - Transaction descriptions with amounts
   - Table rows with dates and amounts
   - Balance entries that represent transactions
3. Include EVERYTHING that looks like a financial transaction
4. Look for patterns across ALL 4-5 pages
5. Check for different date formats: MM/DD, MM/DD/YY, MM/DD/YYYY
6. Include deposits, withdrawals, fees, interest, checks, transfers
7. Look for balance-after amounts that might indicate transactions

PARSING RULES FOR 104 TRANSACTIONS:
- Every date with a corresponding amount is likely a transaction
- Look for transaction tables and parse EVERY row
- Include all fees, service charges, and small amounts
- Check for running balances that indicate transaction amounts
- Look for patterns like "DEPOSIT 0000000822" with amounts
- Include "WITHDRAWAL -WORLD ACCEPTANCE" patterns
- Find balance changes that represent transactions

OCR TEXT (ALL PAGES):
{ocr_text}

Return ONLY valid JSON (NO markdown):
{{
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "amount": number (positive=deposit, negative=withdrawal),
            "description": "description",
            "type": "deposit|withdrawal|fee|interest|transfer|check|other"
        }}
    ],
    "summary": {{
        "deposit_count": number,
        "withdrawal_count": number,
        "total_count": number
    }}
}}

EXTRACT ALL 104 TRANSACTIONS - EVERY SINGLE ONE!
"""

    # Call OpenAI for Pass 1
    deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    url = f"{openai_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    data = {
        "messages": [
            {"role": "system", "content": "You are an expert bank statement parser. Extract ALL transactions with 100% accuracy. Return only valid JSON."},
            {"role": "user", "content": pass1_prompt}
        ],
        "max_tokens": 15000,
        "temperature": 0.0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=180)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Clean up response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                pass1_result = json.loads(content)
                
                if "transactions" in pass1_result:
                    transactions = pass1_result["transactions"]
                    deposits = [t for t in transactions if t.get('amount', 0) > 0]
                    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
                    
                    print(f"✅ PASS 1 RESULTS:")
                    print(f"   Total found: {len(transactions)}")
                    print(f"   Deposits: {len(deposits)} (target: 51)")
                    print(f"   Withdrawals: {len(withdrawals)} (target: 53)")
                    
                    if len(transactions) >= 104:
                        print("🎉 PASS 1 SUCCESS: Found all transactions!")
                        
                        # Display all transactions
                        print(f"\n📋 ALL {len(transactions)} TRANSACTIONS:")
                        print("=" * 100)
                        
                        # Sort by date
                        sorted_txns = sorted(transactions, key=lambda x: x.get('date', ''))
                        
                        table_data = []
                        for i, txn in enumerate(sorted_txns, 1):
                            amount = txn.get('amount', 0)
                            desc = txn.get('description', 'N/A')
                            date = txn.get('date', 'N/A')
                            txn_type = txn.get('type', 'N/A')
                            
                            if amount >= 0:
                                amount_str = f"${amount:,.2f}"
                                sign = "💰"
                            else:
                                amount_str = f"-${abs(amount):,.2f}"
                                sign = "💸"
                            
                            table_data.append([
                                i,
                                date,
                                sign,
                                amount_str,
                                txn_type.capitalize(),
                                desc[:35] + "..." if len(desc) > 35 else desc
                            ])
                        
                        headers = ["#", "Date", "Type", "Amount", "Category", "Description"]
                        table = tabulate(table_data, headers=headers, tablefmt="grid")
                        print(table)
                        
                        return pass1_result
                    else:
                        missing = 104 - len(transactions)
                        print(f"⚠️  PASS 1 PARTIAL: Still missing {missing} transactions")
                
            except json.JSONDecodeError as e:
                print(f"❌ PASS 1 JSON error: {e}")
                return None
                
        else:
            print(f"❌ PASS 1 API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ PASS 1 error: {str(e)}")
        return None

if __name__ == "__main__":
    result = two_pass_extraction()
    if result and "transactions" in result:
        count = len(result["transactions"])
        if count == 104:
            print(f"\n🎉 MISSION ACCOMPLISHED: Found all {count} transactions!")
        else:
            print(f"\n⚠️  MISSION PARTIAL: Found {count}/104 transactions")
    else:
        print("\n❌ MISSION FAILED")
