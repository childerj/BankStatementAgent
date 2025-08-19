"""
Test the comprehensive OpenAI parsing for all transactions - optimized for large documents
"""
import os
import json
import sys
import time
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

def test_comprehensive_parsing(pdf_file_path=None):
    """Test comprehensive parsing to find all transactions"""
    
    # Test file - use command line argument if provided
    if pdf_file_path:
        test_file = pdf_file_path
        filename = os.path.basename(test_file)
    else:
        test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\Stockyards_20250806.pdf'
        filename = "Stockyards_20250806.pdf"
    
    print("🎯 COMPREHENSIVE TRANSACTION EXTRACTION (OPTIMIZED)")
    print(f"🎯 STATEMENT: {filename}")
    print("=" * 70)
    
    # Extract OCR data first
    endpoint = os.environ["DOCINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCINTELLIGENCE_KEY"]
    
    with open(test_file, 'rb') as f:
        file_bytes = f.read()
    
    # Get OCR data using SDK
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
        
        # Show OCR text statistics
        word_count = len(ocr_text.split())
        print(f"📊 Total OCR text: {len(ocr_text):,} characters ({word_count:,} words)")
        
        # For very large documents, implement smart truncation
        if len(ocr_text) > 12000:  # OpenAI context limit consideration
            print(f"⚠️  Large document detected - implementing smart processing...")
            
            # Focus on transaction-rich sections
            lines = ocr_text.split('\n')
            transaction_lines = []
            balance_lines = []
            
            for line in lines:
                line_lower = line.lower()
                # Look for lines that likely contain transactions
                if any(keyword in line_lower for keyword in [
                    'deposit', 'withdrawal', 'debit', 'credit', 'check', 'transfer', 
                    'fee', 'charge', 'payment', 'world acceptance', 'ach', 'atm'
                ]) or any(char.isdigit() and '$' in line for char in line):
                    transaction_lines.append(line)
                # Also capture balance/summary lines
                elif any(keyword in line_lower for keyword in [
                    'balance', 'total', 'beginning', 'ending', 'summary'
                ]):
                    balance_lines.append(line)
            
            # Create focused text
            focused_text = '\n'.join(balance_lines[:10] + transaction_lines + balance_lines[-10:])
            
            if len(focused_text) < len(ocr_text) * 0.8:  # If we filtered significantly
                ocr_text = focused_text
                print(f"📊 Focused on transactions: {len(ocr_text):,} characters ({len(ocr_text.split()):,} words)")
            else:
                print(f"📊 Using full text (filtering didn't reduce significantly)")
        else:
            print(f"📊 Sending FULL TEXT to OpenAI")
    else:
        print("❌ Failed to extract OCR text")
        return
    
    # Test the comprehensive OpenAI parsing
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    
    if not openai_endpoint or not openai_key:
        print("❌ OpenAI credentials not configured")
        return
    
    # Ultra-comprehensive prompt designed to find ALL transactions
    prompt = f"""
You are an expert bank statement parser. Extract ALL financial transactions from this bank statement with complete accuracy.

SCANNING STRATEGY:
1. Scan EVERY SINGLE LINE of the OCR text below
2. Look for transaction patterns throughout ALL pages
3. Find dates in MM/DD, MM/DD/YY, or MM-DD-YYYY formats
4. Find corresponding dollar amounts ($X.XX or X.XX)
5. Include ALL transaction types: deposits, withdrawals, checks, fees, transfers, interest, ATM transactions
6. Parse transaction tables row by row completely
7. Look for balance columns that might indicate transaction amounts

CRITICAL PARSING RULES:
- Scan from the very beginning to the very end of the text
- Every date + amount combination is likely a transaction
- Include even small amounts (fees, interest, etc.)
- Check for negative amounts (withdrawals/debits)
- Check for positive amounts (deposits/credits)
- Look for check numbers, reference numbers, descriptions
- Don't miss transactions at page breaks

FULL OCR TEXT:
{ocr_text}

Return ONLY valid JSON with this structure (NO markdown, NO explanations):
{{
    "account_number": "extracted account number",
    "statement_period": {{
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }},
    "opening_balance": {{
        "amount": number,
        "date": "YYYY-MM-DD"
    }},
    "closing_balance": {{
        "amount": number,
        "date": "YYYY-MM-DD"
    }},
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "amount": number (positive for deposits, negative for withdrawals),
            "description": "transaction description",
            "type": "deposit|withdrawal|fee|interest|transfer|check|other",
            "balance_after": number
        }}
    ],
    "summary": {{
        "total_deposits": number,
        "total_withdrawals": number,
        "transaction_count": number,
        "deposit_count": number,
        "withdrawal_count": number
    }}
}}

EXTRACT ALL TRANSACTIONS - FIND EVERY ONE!
"""

    try:
        print("🤖 Sending comprehensive prompt to OpenAI...")
        
        deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        url = f"{openai_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": openai_key
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are an expert bank statement parser. Extract ALL transactions with 100% accuracy. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 16000,  # Increased token limit
            "temperature": 0.0
        }
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Sending to OpenAI (attempt {attempt + 1}/{max_retries})...")
                
                # Increase timeout for large documents
                timeout = 180 if len(ocr_text) > 10000 else 120
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                
                break  # Success, exit retry loop
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                    print(f"⏱️  Request timed out. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("❌ Final timeout after all retries")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    print(f"⚠️  Request failed: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Final error after all retries: {e}")
                    return None
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            print(f"📥 Response length: {len(content):,} characters")
            
            # Clean up the response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                parsed_result = json.loads(content)
                print("✅ Successfully parsed JSON response!")
                
                # Detailed analysis
                if "transactions" in parsed_result:
                    transactions = parsed_result["transactions"]
                    
                    # Count by type
                    deposits = [t for t in transactions if t.get('amount', 0) > 0]
                    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
                    
                    print(f"\n🎯 EXTRACTION RESULTS:")
                    print(f"   📊 Total found: {len(transactions)} transactions")
                    print(f"   💰 Deposits: {len(deposits)}")
                    print(f"   💸 Withdrawals: {len(withdrawals)}")
                    
                    if len(transactions) >= 100:
                        print("   ✅ HIGH VOLUME STATEMENT!")
                    elif len(transactions) >= 50:
                        print("   👍 GOOD VOLUME STATEMENT!")
                    elif len(transactions) >= 20:
                        print("   📊 MODERATE VOLUME STATEMENT")
                    else:
                        print("   ⚠️  LOW VOLUME STATEMENT")
                    
                    if transactions:
                        print(f"\n📋 ALL {len(transactions)} TRANSACTIONS:")
                        print("=" * 100)
                        
                        # Sort by date for better review
                        sorted_txns = sorted(transactions, key=lambda x: x.get('date', ''))
                        
                        # Prepare table data
                        table_data = []
                        for i, txn in enumerate(sorted_txns, 1):
                            amount = txn.get('amount', 0)
                            desc = txn.get('description', 'N/A')
                            date = txn.get('date', 'N/A')
                            txn_type = txn.get('type', 'N/A')
                            
                            # Format amount with proper sign and currency
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
                        
                        # Create and display the table
                        headers = ["#", "Date", "Type", "Amount", "Category", "Description"]
                        table = tabulate(table_data, headers=headers, tablefmt="grid")
                        print(table)
                
                if "summary" in parsed_result:
                    summary = parsed_result["summary"]
                    print(f"\n💰 FINANCIAL SUMMARY:")
                    print(f"   Deposits: ${summary.get('total_deposits', 0):,.2f}")
                    print(f"   Withdrawals: ${abs(summary.get('total_withdrawals', 0)):,.2f}")
                    print(f"   Net change: ${summary.get('total_deposits', 0) + summary.get('total_withdrawals', 0):,.2f}")
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"📄 Response length: {len(content)} characters")
                print(f"📄 Response preview (first 500): {content[:500]}...")
                print(f"📄 Response preview (last 500): ...{content[-500:]}")
                
                # Try to extract partial JSON array for transactions
                try:
                    print("\n🔧 Attempting to extract partial transaction data...")
                    
                    # Look for transaction array pattern
                    array_start = content.find('"transactions": [')
                    if array_start >= 0:
                        print("   Found transactions array start")
                        
                        # Find the content within the array
                        bracket_start = content.find('[', array_start) + 1
                        bracket_count = 0
                        array_end = -1
                        
                        for i, char in enumerate(content[bracket_start:], bracket_start):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                if bracket_count == 0:
                                    array_end = i
                                    break
                                bracket_count -= 1
                        
                        if array_end > bracket_start:
                            # Extract the transaction array content
                            array_content = content[bracket_start:array_end]
                            partial_json = f'{{"transactions": [{array_content}]}}'
                            
                            try:
                                parsed_result = json.loads(partial_json)
                                print("   ✅ Successfully extracted partial transaction data!")
                                
                                transactions = parsed_result.get("transactions", [])
                                print(f"   📊 Recovered {len(transactions)} transactions")
                                
                                # Display the recovered transactions
                                if transactions:
                                    print(f"\n📋 RECOVERED {len(transactions)} TRANSACTIONS:")
                                    print("=" * 100)
                                    
                                    # Sort by date for better review
                                    try:
                                        sorted_txns = sorted(transactions, key=lambda x: x.get('date', ''))
                                    except:
                                        sorted_txns = transactions
                                    
                                    # Prepare table data
                                    table_data = []
                                    for i, txn in enumerate(sorted_txns[:50], 1):  # Limit to first 50 for display
                                        amount = txn.get('amount', 0)
                                        desc = txn.get('description', 'N/A')
                                        date = txn.get('date', 'N/A')
                                        txn_type = txn.get('type', 'N/A')
                                        
                                        # Format amount with proper sign and currency
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
                                            str(txn_type).capitalize(),
                                            str(desc)[:35] + "..." if len(str(desc)) > 35 else str(desc)
                                        ])
                                    
                                    # Create and display the table
                                    headers = ["#", "Date", "Type", "Amount", "Category", "Description"]
                                    table = tabulate(table_data, headers=headers, tablefmt="grid")
                                    print(table)
                                    
                                    if len(transactions) > 50:
                                        print(f"\n... and {len(transactions) - 50} more transactions")
                                
                                return {"transactions": transactions}
                                
                            except json.JSONDecodeError as parse_error:
                                print(f"   ❌ Partial parsing also failed: {parse_error}")
                        else:
                            print("   ❌ Could not find complete transaction array")
                    else:
                        print("   ❌ Could not find transactions array in response")
                        
                except Exception as fallback_e:
                    print(f"   ❌ Fallback extraction failed: {fallback_e}")
                
                return None
                
        else:
            print(f"❌ OpenAI API error: {response.status_code}")
            print(f"Error: {response.text[:500]}...")
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    # Check for command line argument
    pdf_file = None
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        # Convert relative path to absolute if needed
        if not os.path.isabs(pdf_file):
            pdf_file = os.path.abspath(pdf_file)
    
    result = test_comprehensive_parsing(pdf_file)
    if result and "transactions" in result:
        txn_count = len(result["transactions"])
        if txn_count >= 100:
            print(f"\n🎉 HIGH VOLUME: Found {txn_count} transactions!")
        elif txn_count >= 50:
            print(f"\n✅ GOOD VOLUME: Found {txn_count} transactions!")
        elif txn_count >= 20:
            print(f"\n👍 MODERATE: Found {txn_count} transactions")
        else:
            print(f"\n⚠️  LOW VOLUME: Found {txn_count} transactions")
    else:
        print("\n❌ FAILED: Could not extract transactions")
