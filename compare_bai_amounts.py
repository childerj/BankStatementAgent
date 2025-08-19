#!/usr/bin/env python3
"""Compare transaction amounts between the two BAI files"""

def extract_transactions_from_bai(file_path):
    """Extract all transaction amounts from a BAI file"""
    transactions = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except:
        print(f"Could not read file: {file_path}")
        return []
    
    current_date = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(',')
        
        # Group header (02) - extract date
        if parts[0] == '02' and len(parts) >= 5:
            current_date = parts[4]
            
        # Transaction detail (16) - extract amount
        elif parts[0] == '16' and len(parts) >= 3:
            txn_type = parts[1]
            amount = int(parts[2]) if parts[2].isdigit() else 0
            
            # Convert type codes to readable format
            if txn_type == '174':
                txn_type_name = 'Credit/Deposit'
            elif txn_type == '455':
                txn_type_name = 'Debit'
            else:
                txn_type_name = f'Type_{txn_type}'
                
            transactions.append({
                'date': current_date,
                'type': txn_type_name,
                'amount': amount,
                'line': line
            })
    
    return transactions

def compare_amounts():
    """Compare amounts between the two files"""
    
    # File paths (adjust as needed)
    converted_file = r"C:\Users\jeff.childers\Downloads\Vera_baitest_20250728 converted.bai"
    original_file = r"C:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (1) (2).bai"
    
    print("🔍 Extracting transactions from both files...")
    
    converted_txns = extract_transactions_from_bai(converted_file)
    original_txns = extract_transactions_from_bai(original_file)
    
    print(f"\n📊 Transaction counts:")
    print(f"   Converted file: {len(converted_txns)} transactions")
    print(f"   Original file: {len(original_txns)} transactions")
    
    # Group by date for easier comparison
    converted_by_date = {}
    original_by_date = {}
    
    for txn in converted_txns:
        date = txn['date']
        if date not in converted_by_date:
            converted_by_date[date] = []
        converted_by_date[date].append(txn)
    
    for txn in original_txns:
        date = txn['date']
        if date not in original_by_date:
            original_by_date[date] = []
        original_by_date[date].append(txn)
    
    print(f"\n📅 Date coverage:")
    print(f"   Converted file dates: {sorted(converted_by_date.keys())}")
    print(f"   Original file dates: {sorted(original_by_date.keys())}")
    
    # Compare amounts for overlapping dates
    overlapping_dates = set(converted_by_date.keys()) & set(original_by_date.keys())
    print(f"\n🔄 Overlapping dates: {sorted(overlapping_dates)}")
    
    amounts_identical = True
    
    for date in sorted(overlapping_dates):
        print(f"\n📋 Comparing {date}:")
        
        converted_amounts = sorted([txn['amount'] for txn in converted_by_date[date]])
        original_amounts = sorted([txn['amount'] for txn in original_by_date[date]])
        
        print(f"   Converted: {len(converted_amounts)} amounts: {converted_amounts}")
        print(f"   Original:  {len(original_amounts)} amounts: {original_amounts}")
        
        if converted_amounts == original_amounts:
            print(f"   ✅ IDENTICAL amounts for {date}")
        else:
            print(f"   ❌ DIFFERENT amounts for {date}")
            amounts_identical = False
            
            # Show differences
            missing_in_converted = [amt for amt in original_amounts if amt not in converted_amounts]
            extra_in_converted = [amt for amt in converted_amounts if amt not in original_amounts]
            
            if missing_in_converted:
                print(f"      Missing in converted: {missing_in_converted}")
            if extra_in_converted:
                print(f"      Extra in converted: {extra_in_converted}")
    
    # Overall summary
    print(f"\n" + "="*60)
    if amounts_identical:
        print("✅ CONCLUSION: Transaction amounts are IDENTICAL for overlapping dates")
    else:
        print("❌ CONCLUSION: Transaction amounts are DIFFERENT")
    
    # Check total amounts
    converted_total = sum(txn['amount'] for txn in converted_txns)
    original_active_txns = [txn for txn in original_txns if txn['date'] in overlapping_dates]
    original_active_total = sum(txn['amount'] for txn in original_active_txns)
    
    print(f"\n💰 Total amounts for overlapping periods:")
    print(f"   Converted file total: {converted_total:,} cents (${converted_total/100:,.2f})")
    print(f"   Original file (active days): {original_active_total:,} cents (${original_active_total/100:,.2f})")
    
    if converted_total == original_active_total:
        print("✅ Total amounts MATCH for active transaction days")
    else:
        print("❌ Total amounts DO NOT MATCH")
        print(f"   Difference: {abs(converted_total - original_active_total):,} cents")

if __name__ == "__main__":
    compare_amounts()
