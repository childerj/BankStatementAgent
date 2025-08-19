#!/usr/bin/env python3
"""
Compare monetary values between two BAI2 files to verify correctness
"""

def analyze_monetary_values(file1, file2):
    """Compare monetary values between two BAI2 files"""
    
    print("💰 MONETARY VALUE COMPARISON")
    print("=" * 50)
    
    def parse_bai2_file(filename):
        """Parse BAI2 file and extract monetary values"""
        balances = {}
        transactions = []
        control_totals = {}
        
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            record_type = parts[0]
            
            if record_type == '88':  # Balance records
                if len(parts) >= 3:
                    code = parts[1]
                    amount = parts[2] if parts[2] else "0"
                    count = parts[3] if len(parts) > 3 and parts[3] else "0"
                    balances[code] = {
                        'amount': int(amount) if amount.isdigit() else 0,
                        'count': int(count) if count.isdigit() else 0
                    }
            
            elif record_type == '16':  # Transaction records
                if len(parts) >= 3:
                    txn_code = parts[1]
                    amount = int(parts[2]) if parts[2].isdigit() else 0
                    description = parts[6] if len(parts) > 6 else ""
                    transactions.append({
                        'code': txn_code,
                        'amount': amount,
                        'description': description
                    })
            
            elif record_type in ['49', '98', '99']:  # Control totals
                if len(parts) >= 2:
                    total = int(parts[1]) if parts[1].isdigit() else 0
                    control_totals[record_type] = total
        
        return balances, transactions, control_totals
    
    # Parse both files
    print(f"📄 Analyzing File 1: {file1}")
    balances1, transactions1, control1 = parse_bai2_file(file1)
    
    print(f"📄 Analyzing File 2: {file2}")
    balances2, transactions2, control2 = parse_bai2_file(file2)
    
    print(f"\n🏦 BALANCE COMPARISON:")
    print("-" * 40)
    
    # Compare balance codes
    all_codes = set(balances1.keys()) | set(balances2.keys())
    
    differences_found = False
    
    for code in sorted(all_codes):
        val1 = balances1.get(code, {'amount': 0, 'count': 0})
        val2 = balances2.get(code, {'amount': 0, 'count': 0})
        
        amount1 = val1['amount']
        amount2 = val2['amount']
        count1 = val1['count']
        count2 = val2['count']
        
        status = "✅" if amount1 == amount2 and count1 == count2 else "❌"
        
        if amount1 != amount2 or count1 != count2:
            differences_found = True
        
        print(f"{status} Code {code}:")
        print(f"    File 1: ${amount1/100:>10.2f} (count: {count1})")
        print(f"    File 2: ${amount2/100:>10.2f} (count: {count2})")
        
        if amount1 != amount2:
            diff = abs(amount1 - amount2)
            print(f"    Difference: ${diff/100:.2f}")
    
    print(f"\n💳 TRANSACTION COMPARISON:")
    print("-" * 40)
    
    # Calculate transaction totals
    def calc_totals(transactions):
        credits = 0
        debits = 0
        credit_count = 0
        debit_count = 0
        
        for txn in transactions:
            amount = txn['amount']
            code = txn['code']
            
            # Credit codes (deposits)
            if code in ['301', '302', '303', '304', '305', '306', '307', '308', '309']:
                credits += amount
                credit_count += 1
            # Debit codes (withdrawals)
            elif code in ['451', '452', '453', '454', '455', '555', '556', '557']:
                debits += amount
                debit_count += 1
        
        return credits, debits, credit_count, debit_count
    
    credits1, debits1, cc1, dc1 = calc_totals(transactions1)
    credits2, debits2, cc2, dc2 = calc_totals(transactions2)
    
    print(f"📈 Credits:")
    print(f"    File 1: ${credits1/100:>10.2f} ({cc1} transactions)")
    print(f"    File 2: ${credits2/100:>10.2f} ({cc2} transactions)")
    print(f"    Match: {'✅' if credits1 == credits2 and cc1 == cc2 else '❌'}")
    
    print(f"📉 Debits:")
    print(f"    File 1: ${debits1/100:>10.2f} ({dc1} transactions)")
    print(f"    File 2: ${debits2/100:>10.2f} ({dc2} transactions)")
    print(f"    Match: {'✅' if debits1 == debits2 and dc1 == dc2 else '❌'}")
    
    print(f"\n🎯 CONTROL TOTAL COMPARISON:")
    print("-" * 40)
    
    for code in ['49', '98', '99']:
        total1 = control1.get(code, 0)
        total2 = control2.get(code, 0)
        
        status = "✅" if total1 == total2 else "❌"
        print(f"{status} Record {code}:")
        print(f"    File 1: ${total1/100:>10.2f}")
        print(f"    File 2: ${total2/100:>10.2f}")
        
        if total1 != total2:
            diff = abs(total1 - total2)
            print(f"    Difference: ${diff/100:.2f}")
    
    print(f"\n🔍 DETAILED TRANSACTION ANALYSIS:")
    print("-" * 40)
    
    # Group transactions by amount to find matches
    def group_by_amount(transactions):
        groups = {}
        for txn in transactions:
            amount = txn['amount']
            if amount not in groups:
                groups[amount] = []
            groups[amount].append(txn)
        return groups
    
    groups1 = group_by_amount(transactions1)
    groups2 = group_by_amount(transactions2)
    
    all_amounts = set(groups1.keys()) | set(groups2.keys())
    
    transaction_differences = False
    
    for amount in sorted(all_amounts):
        count1 = len(groups1.get(amount, []))
        count2 = len(groups2.get(amount, []))
        
        if count1 != count2:
            transaction_differences = True
            print(f"❌ Amount ${amount/100:.2f}:")
            print(f"    File 1: {count1} transactions")
            print(f"    File 2: {count2} transactions")
    
    if not transaction_differences:
        print("✅ All transaction amounts have matching counts")
    
    print(f"\n📊 FINAL ASSESSMENT:")
    print("=" * 30)
    
    # Overall assessment
    balance_match = not differences_found
    transaction_match = credits1 == credits2 and debits1 == debits2 and cc1 == cc2 and dc1 == dc2
    control_match = all(control1.get(code, 0) == control2.get(code, 0) for code in ['49', '98', '99'])
    
    print(f"Balance Records Match: {'✅ YES' if balance_match else '❌ NO'}")
    print(f"Transaction Totals Match: {'✅ YES' if transaction_match else '❌ NO'}")
    print(f"Control Totals Match: {'✅ YES' if control_match else '❌ NO'}")
    
    overall_match = balance_match and transaction_match and control_match
    print(f"\n🎯 OVERALL MONEY-WISE CORRECTNESS: {'✅ CORRECT' if overall_match else '❌ DIFFERENCES FOUND'}")
    
    if overall_match:
        print("💰 Both files are monetarily equivalent!")
        print("   The only differences are in balance code usage, not actual amounts.")
    else:
        print("⚠️  Files have monetary differences that need investigation.")
    
    return overall_match

if __name__ == "__main__":
    analyze_monetary_values("WACBAI2_20250813 (1).bai", "WACBAI2_20250813_6.bai")
