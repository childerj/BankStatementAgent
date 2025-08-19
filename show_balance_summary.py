#!/usr/bin/env python3
"""
Show starting balance, debits, credits, and ending balance for both BAI2 files
"""

def analyze_bai2_balances(file1, file2):
    """Extract and display key balance information from both BAI2 files"""
    
    print("💰 BAI2 BALANCE SUMMARY COMPARISON")
    print("=" * 60)
    
    def extract_balance_info(filename):
        """Extract balance information from a BAI2 file"""
        balances = {}
        transactions = []
        
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            record_type = parts[0]
            
            # Extract balance records (88)
            if record_type == '88':
                if len(parts) >= 3:
                    code = parts[1]
                    amount = int(parts[2]) if parts[2] and parts[2].isdigit() else 0
                    balances[code] = amount
            
            # Extract transaction records (16)
            elif record_type == '16':
                if len(parts) >= 3:
                    txn_code = parts[1]
                    amount = int(parts[2]) if parts[2].isdigit() else 0
                    transactions.append({
                        'code': txn_code,
                        'amount': amount
                    })
        
        # Calculate credits and debits from transactions
        total_credits = 0
        total_debits = 0
        credit_count = 0
        debit_count = 0
        
        for txn in transactions:
            amount = txn['amount']
            code = txn['code']
            
            # Credit codes (deposits)
            if code in ['301', '302', '303', '304', '305', '306', '307', '308', '309']:
                total_credits += amount
                credit_count += 1
            # Debit codes (withdrawals)
            elif code in ['451', '452', '453', '454', '455', '555', '556', '557']:
                total_debits += amount
                debit_count += 1
        
        # Determine starting and ending balances from balance codes
        starting_balance = 0
        ending_balance = 0
        
        # Priority order for starting balance: 010 (opening), 040 (opening available)
        if '010' in balances and balances['010'] > 0:
            starting_balance = balances['010']
        elif '040' in balances and balances['040'] > 0:
            starting_balance = balances['040']
        
        # Priority order for ending balance: 015 (closing), 045 (closing available), 072 (current ledger)
        if '015' in balances and balances['015'] > 0:
            ending_balance = balances['015']
        elif '045' in balances and balances['045'] > 0:
            ending_balance = balances['045']
        elif '072' in balances and balances['072'] > 0:
            ending_balance = balances['072']
        
        # If no explicit ending balance, calculate it
        if ending_balance == 0 and starting_balance > 0:
            ending_balance = starting_balance + total_credits - total_debits
        
        return {
            'starting_balance': starting_balance,
            'ending_balance': ending_balance,
            'total_credits': total_credits,
            'total_debits': total_debits,
            'credit_count': credit_count,
            'debit_count': debit_count,
            'net_change': total_credits - total_debits,
            'balances': balances
        }
    
    # Analyze both files
    print(f"📄 File 1: {file1}")
    info1 = extract_balance_info(file1)
    
    print(f"📄 File 2: {file2}")
    info2 = extract_balance_info(file2)
    
    print(f"\n📊 BALANCE SUMMARY:")
    print("=" * 40)
    
    # Format and display results
    def format_amount(cents):
        return f"${cents/100:>12,.2f}"
    
    def format_count(count):
        return f"{count:>3d}"
    
    print(f"{'Metric':<25} {'File 1':>15} {'File 2':>15} {'Match':>8}")
    print("-" * 68)
    
    # Starting Balance
    start_match = "✅" if info1['starting_balance'] == info2['starting_balance'] else "❌"
    print(f"{'Starting Balance':<25} {format_amount(info1['starting_balance'])} {format_amount(info2['starting_balance'])} {start_match:>6}")
    
    # Credits
    credit_match = "✅" if info1['total_credits'] == info2['total_credits'] else "❌"
    print(f"{'+ Credits':<25} {format_amount(info1['total_credits'])} {format_amount(info2['total_credits'])} {credit_match:>6}")
    print(f"{'  Credit Count':<25} {format_count(info1['credit_count']):>12} {format_count(info2['credit_count']):>12}")
    
    # Debits
    debit_match = "✅" if info1['total_debits'] == info2['total_debits'] else "❌"
    print(f"{'- Debits':<25} {format_amount(info1['total_debits'])} {format_amount(info2['total_debits'])} {debit_match:>6}")
    print(f"{'  Debit Count':<25} {format_count(info1['debit_count']):>12} {format_count(info2['debit_count']):>12}")
    
    # Net Change
    net_match = "✅" if info1['net_change'] == info2['net_change'] else "❌"
    print(f"{'= Net Change':<25} {format_amount(info1['net_change'])} {format_amount(info2['net_change'])} {net_match:>6}")
    
    # Ending Balance
    end_match = "✅" if info1['ending_balance'] == info2['ending_balance'] else "❌"
    print(f"{'Ending Balance':<25} {format_amount(info1['ending_balance'])} {format_amount(info2['ending_balance'])} {end_match:>6}")
    
    print(f"\n🧮 BALANCE RECONCILIATION:")
    print("=" * 40)
    
    def check_reconciliation(info, file_name):
        start = info['starting_balance']
        credits = info['total_credits']
        debits = info['total_debits']
        end = info['ending_balance']
        
        calculated_end = start + credits - debits
        difference = abs(end - calculated_end)
        
        print(f"\n📄 {file_name}:")
        print(f"  Starting: {format_amount(start)}")
        print(f"  + Credits: {format_amount(credits)}")
        print(f"  - Debits: {format_amount(debits)}")
        print(f"  = Calculated: {format_amount(calculated_end)}")
        print(f"  Actual End: {format_amount(end)}")
        print(f"  Difference: {format_amount(difference)}")
        
        if difference <= 1:  # 1 cent tolerance
            print(f"  Status: ✅ BALANCED")
        else:
            print(f"  Status: ❌ UNBALANCED")
        
        return difference <= 1
    
    balanced1 = check_reconciliation(info1, "File 1")
    balanced2 = check_reconciliation(info2, "File 2")
    
    print(f"\n🎯 SUMMARY:")
    print("=" * 20)
    
    transactions_match = (info1['total_credits'] == info2['total_credits'] and 
                         info1['total_debits'] == info2['total_debits'])
    
    print(f"Transaction Data Match: {'✅ YES' if transactions_match else '❌ NO'}")
    print(f"File 1 Balanced: {'✅ YES' if balanced1 else '❌ NO'}")
    print(f"File 2 Balanced: {'✅ YES' if balanced2 else '❌ NO'}")
    
    if transactions_match:
        print(f"\n💡 ANALYSIS:")
        print("Both files have identical transaction data (credits and debits).")
        print("Any differences are in balance reporting or file structure, not core transaction amounts.")
    else:
        print(f"\n⚠️  WARNING:")
        print("Files have different transaction totals - this needs investigation.")
    
    return info1, info2

if __name__ == "__main__":
    analyze_bai2_balances("WACBAI2_20250813 (1).bai", "WACBAI2_20250813_6.bai")
