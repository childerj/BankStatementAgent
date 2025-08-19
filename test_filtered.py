"""
Extract actual transactions by filtering out balance duplicates
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

def extract_actual_transactions():
    """Extract actual transactions by filtering out balance summary duplicates"""
    
    test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\8-1-25_Prosperity.pdf'
    
    print("🎯 EXTRACTING ACTUAL TRANSACTIONS")
    print("🎯 NEW STATEMENT: 8-1-25_Prosperity.pdf (no target)")
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
    
    # Focus only on actual transaction tables (not balance summaries)
    if result.tables:
        print(f"📋 Found {len(result.tables)} tables")
        
        for table_idx, table in enumerate(result.tables):
            print(f"   Table {table_idx + 1}: {table.row_count} rows x {table.column_count} columns")
            
            # Get headers to identify table type
            headers = []
            if table.cells:
                first_row_cells = [cell for cell in table.cells if cell.row_index == 0]
                headers = [cell.content.lower() for cell in first_row_cells]
                print(f"   Headers: {headers}")
                
                # Look for different transaction table patterns
                header_text = ' '.join(headers).lower()
                is_transaction_table = any(keyword in header_text for keyword in [
                    'account history', 
                    'posted date', 
                    'transaction',
                    'debit',
                    'credit',
                    'description',
                    'check number'
                ])
                
                if is_transaction_table:
                    print(f"   ✅ Processing transaction table {table_idx + 1}")
                    
                    # Process each row looking for actual transactions
                    for row_idx in range(1, table.row_count):  # Skip header row
                        row_cells = [cell for cell in table.cells if cell.row_index == row_idx]
                        row_data = [cell.content for cell in row_cells]
                        row_text = ' '.join(row_data)
                        
                        # Skip if this looks like a balance summary or duplicate
                        if 'daily balance' in row_text.lower() or len(row_data) < 2:
                            continue
                        
                        # Look for broader transaction patterns
                        if (any(pattern in row_text.upper() for pattern in [
                            'DEPOSIT', 'WITHDRAWAL', 'SERVICE CHARGE', 'FEE', 'DEBIT', 'CREDIT',
                            'CHECK', 'ATM', 'TRANSFER', 'PAYMENT'
                        ]) or 
                        # Or if the row has a date and an amount
                        (dates and amounts)):
                            # Find dates and amounts in this row
                            if not dates:
                                dates = re.findall(r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b', row_text)
                            if not amounts:
                                amounts = re.findall(r'\$?([\d,]+\.\d{2})', row_text)
                            
                            if dates and amounts:
                                date = dates[0]  # Take the first date
                                for amount_str in amounts:
                                    try:
                                        amount_val = float(amount_str.replace(',', ''))
                                        
                                        # Determine transaction type and sign
                                        transaction_type = "other"
                                        if 'WITHDRAWAL' in row_text.upper():
                                            amount_val = -amount_val
                                            transaction_type = "withdrawal"
                                        elif 'DEPOSIT' in row_text.upper():
                                            transaction_type = "deposit"
                                        elif 'FEE' in row_text.upper() or 'CHARGE' in row_text.upper():
                                            amount_val = -amount_val
                                            transaction_type = "fee"
                                        
                                        # Clean up description
                                        description = row_text.strip()
                                        
                                        transactions.append({
                                            'date': date,
                                            'amount': amount_val,
                                            'description': description,
                                            'type': transaction_type,
                                            'source': f'Table {table_idx + 1} (Account History)'
                                        })
                                        break  # Only take the first amount per transaction
                                    except ValueError:
                                        continue
                else:
                    print(f"   ⏭️  Skipping table {table_idx + 1} (not account history)")
    
    # Remove duplicates based on date, amount, and description
    unique_transactions = []
    seen = set()
    
    for txn in transactions:
        # Create a unique key based on date, amount, and first 20 chars of description
        key = (txn['date'], txn['amount'], txn['description'][:20])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(txn)
    
    transactions = unique_transactions
    
    # Sort by date and amount
    transactions.sort(key=lambda x: (x['date'], x['amount']))
    
    # Count deposits and withdrawals
    deposits = [t for t in transactions if t['amount'] > 0]
    withdrawals = [t for t in transactions if t['amount'] < 0]
    
    print(f"\n📊 ACTUAL TRANSACTION RESULTS:")
    print(f"   Total unique transactions: {len(transactions)}")
    print(f"   Deposits: {len(deposits)}")
    print(f"   Withdrawals: {len(withdrawals)}")
    print(f"   Total found: {len(transactions)} transactions")
    
    if len(transactions) >= 100:
        print("   ✅ HIGH VOLUME!")
    elif len(transactions) >= 50:
        print("   👍 GOOD VOLUME!")
    elif len(transactions) >= 20:
        print("   � MODERATE VOLUME")
    else:
        print("   ⚠️  LOW VOLUME")
    
    if transactions:
        print(f"\n📋 ALL {len(transactions)} ACTUAL TRANSACTIONS:")
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
                desc
            ])
        
        headers = ["#", "Date", "Type", "Amount", "Category", "Description"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        print(table)
        
        # Summary statistics
        total_deposits = sum(t['amount'] for t in deposits)
        total_withdrawals = sum(abs(t['amount']) for t in withdrawals)
        net_change = total_deposits - total_withdrawals
        
        print(f"\n💰 FINANCIAL SUMMARY:")
        print(f"   Total deposits: ${total_deposits:,.2f}")
        print(f"   Total withdrawals: ${total_withdrawals:,.2f}")
        print(f"   Net change: ${net_change:,.2f}")
    
    return transactions

if __name__ == "__main__":
    transactions = extract_actual_transactions()
    if transactions:
        count = len(transactions)
        if count >= 100:
            print(f"\n🎉 HIGH VOLUME: Found {count} transactions!")
        elif count >= 50:
            print(f"\n✅ GOOD VOLUME: Found {count} transactions!")
        elif count >= 20:
            print(f"\n👍 MODERATE: Found {count} transactions")
        else:
            print(f"\n⚠️  LOW VOLUME: Found {count} transactions")
    else:
        print("\n❌ NO TRANSACTIONS FOUND")
