"""
Use Document Intelligence structured results to find transactions
"""
import os
import json
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
import re
from tabulate import tabulate

# Load environment variables
if os.path.exists('local.settings.json'):
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        values = settings.get('Values', {})
        for key, value in values.items():
            os.environ[key] = value

def extract_using_structured_analysis():
    """Use Document Intelligence structured analysis to find transactions"""
    
    test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\822-847-896.pdf'
    
    print("🏗️  STRUCTURED DOCUMENT ANALYSIS")
    print("🎯 TARGET: 104 transactions (51 deposits + 53 withdrawals)")
    print("=" * 70)
    
    endpoint = os.environ["DOCINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCINTELLIGENCE_KEY"]
    
    with open(test_file, 'rb') as f:
        file_bytes = f.read()
    
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    
    print("📊 Using Document Intelligence structured analysis...")
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=BytesIO(file_bytes),
        content_type="application/pdf"
    )
    result = poller.result()
    
    if not result:
        print("❌ Failed to get Document Intelligence results")
        return
    
    print(f"✅ Document Intelligence analysis complete")
    
    transactions = []
    
    # Method 1: Extract from tables
    if result.tables:
        print(f"📋 Found {len(result.tables)} tables")
        
        for table_idx, table in enumerate(result.tables):
            print(f"   Table {table_idx + 1}: {table.row_count} rows x {table.column_count} columns")
            
            # Look for table headers that indicate transaction data
            headers = []
            if table.cells:
                # Get first row as potential headers
                first_row_cells = [cell for cell in table.cells if cell.row_index == 0]
                headers = [cell.content.lower() for cell in first_row_cells]
                print(f"   Headers: {headers}")
                
                # Process each row looking for transaction patterns
                for row_idx in range(1, table.row_count):  # Skip header row
                    row_cells = [cell for cell in table.cells if cell.row_index == row_idx]
                    row_data = [cell.content for cell in row_cells]
                    
                    # Look for date and amount patterns in this row
                    dates_in_row = []
                    amounts_in_row = []
                    
                    for cell_content in row_data:
                        # Find dates
                        date_matches = re.findall(r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', cell_content)
                        dates_in_row.extend(date_matches)
                        
                        # Find amounts
                        amount_matches = re.findall(r'\$?([\d,]+\.\d{2})', cell_content)
                        amounts_in_row.extend(amount_matches)
                    
                    # If we found dates and amounts in this row, it's likely a transaction
                    if dates_in_row and amounts_in_row:
                        for date in dates_in_row:
                            for amount in amounts_in_row:
                                # Convert amount to float
                                try:
                                    amount_val = float(amount.replace(',', ''))
                                    
                                    # Determine if it's a deposit or withdrawal based on context
                                    row_text = ' '.join(row_data).lower()
                                    if 'withdrawal' in row_text or 'debit' in row_text:
                                        amount_val = -amount_val
                                    
                                    transactions.append({
                                        'date': date,
                                        'amount': amount_val,
                                        'description': ' '.join(row_data),
                                        'source': f'Table {table_idx + 1}, Row {row_idx + 1}',
                                        'type': 'withdrawal' if amount_val < 0 else 'deposit'
                                    })
                                except ValueError:
                                    continue
    
    # Method 2: Extract from paragraphs
    if result.paragraphs:
        print(f"📄 Found {len(result.paragraphs)} paragraphs")
        
        for para_idx, paragraph in enumerate(result.paragraphs):
            content = paragraph.content
            
            # Look for transaction patterns in paragraphs
            if any(keyword in content.lower() for keyword in ['deposit', 'withdrawal', 'balance', 'transaction']):
                # Find dates and amounts in this paragraph
                dates = re.findall(r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', content)
                amounts = re.findall(r'\$?([\d,]+\.\d{2})', content)
                
                if dates and amounts:
                    for date in dates:
                        for amount in amounts:
                            try:
                                amount_val = float(amount.replace(',', ''))
                                
                                # Determine sign based on context
                                if any(keyword in content.lower() for keyword in ['withdrawal', 'debit', 'fee', 'charge']):
                                    amount_val = -amount_val
                                
                                transactions.append({
                                    'date': date,
                                    'amount': amount_val,
                                    'description': content,
                                    'source': f'Paragraph {para_idx + 1}',
                                    'type': 'withdrawal' if amount_val < 0 else 'deposit'
                                })
                            except ValueError:
                                continue
    
    # Method 3: Raw text pattern matching on the content
    ocr_text = result.content if result.content else ""
    if ocr_text:
        print(f"📝 Analyzing raw OCR text ({len(ocr_text)} characters)")
        
        lines = ocr_text.split('\n')
        for line_idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for specific transaction patterns
            
            # Pattern 1: "DEPOSIT 0000000XXX" followed by amount
            deposit_pattern = re.search(r'DEPOSIT\s+(\d+).*?([\d,]+\.\d{2})', line)
            if deposit_pattern:
                try:
                    amount_val = float(deposit_pattern.group(2).replace(',', ''))
                    # Look for date in nearby lines
                    date = None
                    for nearby_line in lines[max(0, line_idx-2):line_idx+3]:
                        date_match = re.search(r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', nearby_line)
                        if date_match:
                            date = date_match.group(1)
                            break
                    
                    if date:
                        transactions.append({
                            'date': date,
                            'amount': amount_val,
                            'description': line,
                            'source': f'Raw text line {line_idx + 1}',
                            'type': 'deposit'
                        })
                except ValueError:
                    continue
            
            # Pattern 2: "WITHDRAWAL -" followed by description and amount
            withdrawal_pattern = re.search(r'WITHDRAWAL\s+-.*?([\d,]+\.\d{2})', line)
            if withdrawal_pattern:
                try:
                    amount_val = -float(withdrawal_pattern.group(1).replace(',', ''))
                    # Look for date in nearby lines
                    date = None
                    for nearby_line in lines[max(0, line_idx-2):line_idx+3]:
                        date_match = re.search(r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', nearby_line)
                        if date_match:
                            date = date_match.group(1)
                            break
                    
                    if date:
                        transactions.append({
                            'date': date,
                            'amount': amount_val,
                            'description': line,
                            'source': f'Raw text line {line_idx + 1}',
                            'type': 'withdrawal'
                        })
                except ValueError:
                    continue
    
    # Remove duplicates based on date and amount
    unique_transactions = []
    seen = set()
    
    for txn in transactions:
        key = (txn['date'], txn['amount'])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(txn)
    
    transactions = unique_transactions
    
    # Sort by date and amount for better organization
    transactions.sort(key=lambda x: (x['date'], x['amount']))
    
    # Count deposits and withdrawals
    deposits = [t for t in transactions if t['amount'] > 0]
    withdrawals = [t for t in transactions if t['amount'] < 0]
    
    print(f"\n📊 STRUCTURED ANALYSIS RESULTS:")
    print(f"   Total unique transactions: {len(transactions)}")
    print(f"   Deposits: {len(deposits)} (target: 51)")
    print(f"   Withdrawals: {len(withdrawals)} (target: 53)")
    print(f"   Missing: {104 - len(transactions)} transactions")
    
    if transactions:
        print(f"\n📋 ALL {len(transactions)} EXTRACTED TRANSACTIONS:")
        print("=" * 120)
        
        table_data = []
        for i, txn in enumerate(transactions, 1):
            amount = txn['amount']
            desc = txn['description'][:50] + "..." if len(txn['description']) > 50 else txn['description']
            
            if amount >= 0:
                amount_str = f"${amount:,.2f}"
                sign = "💰"
            else:
                amount_str = f"-${abs(amount):,.2f}"
                sign = "💸"
            
            table_data.append([
                i,
                txn['date'],
                sign,
                amount_str,
                txn['type'].capitalize(),
                desc,
                txn['source']
            ])
        
        headers = ["#", "Date", "Type", "Amount", "Category", "Description", "Source"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        print(table)
    
    return transactions

if __name__ == "__main__":
    transactions = extract_using_structured_analysis()
    if transactions:
        count = len(transactions)
        if count >= 100:
            print(f"\n🎉 EXCELLENT: Found {count} transactions!")
        elif count >= 80:
            print(f"\n👍 GOOD: Found {count} transactions (missing {104-count})")
        else:
            print(f"\n⚠️  NEEDS WORK: Found {count} transactions (missing {104-count})")
    else:
        print("\n❌ NO TRANSACTIONS FOUND")
