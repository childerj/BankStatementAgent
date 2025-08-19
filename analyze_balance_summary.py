#!/usr/bin/env python3
"""
Analyze the balance summary approach used in the WACBAI2_20250813_6.bai file
"""

def analyze_bai2_balance_summary(filename):
    """Analyze the balance summary approach in a BAI2 file"""
    
    print(f"📊 ANALYZING BALANCE SUMMARY APPROACH: {filename}")
    print("=" * 60)
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Parse records
    file_header = None
    group_header = None
    account_header = None
    balance_records = []
    transaction_records = []
    account_trailer = None
    group_trailer = None
    file_trailer = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(',')
        record_type = parts[0]
        
        if record_type == '01':
            file_header = parts
        elif record_type == '02':
            group_header = parts
        elif record_type == '03':
            account_header = parts
        elif record_type == '88':
            balance_records.append(parts)
        elif record_type == '16':
            transaction_records.append(parts)
        elif record_type == '49':
            account_trailer = parts
        elif record_type == '98':
            group_trailer = parts
        elif record_type == '99':
            file_trailer = parts
    
    print("\n🏦 FILE STRUCTURE:")
    print(f"  File Header (01): {file_header[1:4] if file_header else 'None'}")
    print(f"  Group Header (02): {group_header[1:4] if group_header else 'None'}")
    print(f"  Account Header (03): Account {account_header[1]} Opening Balance ${account_header[2] if account_header[2] else '0'}")
    print(f"  Balance Records (88): {len(balance_records)} records")
    print(f"  Transaction Records (16): {len(transaction_records)} records")
    print(f"  Account Trailer (49): Control total ${account_trailer[1] if account_trailer else 'None'}")
    print(f"  Group Trailer (98): Control total ${group_trailer[1] if group_trailer else 'None'}")
    print(f"  File Trailer (99): Control total ${file_trailer[1] if file_trailer else 'None'}")
    
    print("\n💰 BALANCE SUMMARY ANALYSIS:")
    print("=" * 40)
    
    if balance_records:
        print(f"📋 Found {len(balance_records)} balance summary records (88 records):")
        
        # Analyze each balance record
        balance_codes = {}
        for i, record in enumerate(balance_records):
            if len(record) >= 3:
                code = record[1]
                amount = record[2] if record[2] else "0"
                count = record[3] if len(record) > 3 and record[3] else "0"
                
                balance_codes[code] = {
                    'amount': amount,
                    'count': count,
                    'position': i + 1
                }
                
                # Decode the balance code
                code_meaning = decode_balance_code(code)
                print(f"  #{i+1:2d}: Code {code:3s} = {code_meaning:30s} Amount: ${amount:>10s} Count: {count}")
        
        print(f"\n🔍 BALANCE CODE SUMMARY:")
        print(f"  Total balance codes used: {len(balance_codes)}")
        
        # Check for specific patterns
        has_opening = '010' in balance_codes
        has_closing = '015' in balance_codes
        has_credit_summary = '040' in balance_codes
        has_debit_summary = '045' in balance_codes
        has_ledger_balance = '072' in balance_codes
        has_available_balance = '074' in balance_codes
        has_total_credits = '100' in balance_codes
        has_total_debits = '400' in balance_codes
        
        print(f"  Opening Balance (010): {'✅ Present' if has_opening else '❌ Missing'}")
        print(f"  Closing Balance (015): {'✅ Present' if has_closing else '❌ Missing'}")
        print(f"  Credit Summary (040): {'✅ Present' if has_credit_summary else '❌ Missing'}")
        print(f"  Debit Summary (045): {'✅ Present' if has_debit_summary else '❌ Missing'}")
        print(f"  Ledger Balance (072): {'✅ Present' if has_ledger_balance else '❌ Missing'}")
        print(f"  Available Balance (074): {'✅ Present' if has_available_balance else '❌ Missing'}")
        print(f"  Total Credits (100): {'✅ Present' if has_total_credits else '❌ Missing'}")
        print(f"  Total Debits (400): {'✅ Present' if has_total_debits else '❌ Missing'}")
    
    else:
        print("❌ NO BALANCE SUMMARY RECORDS FOUND")
        print("   This file does not use balance summary records (88 records)")
    
    print(f"\n💳 TRANSACTION ANALYSIS:")
    print("=" * 30)
    
    if transaction_records:
        credit_total = 0
        debit_total = 0
        credit_count = 0
        debit_count = 0
        
        transaction_codes = {}
        
        for record in transaction_records:
            if len(record) >= 3:
                txn_code = record[1]
                amount = float(record[2]) if record[2] else 0
                
                # Track transaction codes
                if txn_code not in transaction_codes:
                    transaction_codes[txn_code] = {'count': 0, 'total': 0}
                transaction_codes[txn_code]['count'] += 1
                transaction_codes[txn_code]['total'] += amount
                
                # Categorize as credit or debit based on common BAI2 codes
                if txn_code in ['301', '302', '303', '304', '305', '306', '307', '308', '309']:  # Credit codes
                    credit_total += amount
                    credit_count += 1
                elif txn_code in ['451', '452', '453', '454', '455', '555', '556', '557']:  # Debit codes
                    debit_total += amount
                    debit_count += 1
        
        print(f"📊 Transaction Totals:")
        print(f"  Total Credits: ${credit_total:,.2f} ({credit_count} transactions)")
        print(f"  Total Debits: ${debit_total:,.2f} ({debit_count} transactions)")
        print(f"  Net Amount: ${credit_total - debit_total:,.2f}")
        
        print(f"\n📋 Transaction Code Breakdown:")
        for code, data in sorted(transaction_codes.items()):
            code_meaning = decode_transaction_code(code)
            print(f"  Code {code}: {code_meaning:25s} Count: {data['count']:2d} Total: ${data['total']:>10,.2f}")
    
    else:
        print("❌ NO TRANSACTION RECORDS FOUND")
    
    print(f"\n🏗️ BALANCE SUMMARY APPROACH:")
    print("=" * 35)
    
    if balance_records:
        print("✅ COMPREHENSIVE BALANCE SUMMARY APPROACH")
        print("   This file uses detailed balance summary records (88 records)")
        print("   Benefits:")
        print("   • Provides multiple balance types for validation")
        print("   • Includes credit/debit summaries separate from transactions")
        print("   • Enables robust reconciliation checking")
        print("   • Follows full BAI2 specification")
        
        # Check for empty vs populated summaries
        empty_summaries = []
        populated_summaries = []
        
        for code, data in balance_codes.items():
            if data['amount'] == '' or data['amount'] == '0':
                empty_summaries.append(code)
            else:
                populated_summaries.append(code)
        
        if empty_summaries:
            print(f"\n⚠️  EMPTY SUMMARY CODES: {', '.join(empty_summaries)}")
            print("   These codes are present but have no values")
            print("   This indicates reserved placeholders or unused balance types")
        
        if populated_summaries:
            print(f"\n✅ POPULATED SUMMARY CODES: {', '.join(populated_summaries)}")
            print("   These codes contain actual balance/summary data")
    
    else:
        print("❌ MINIMAL BALANCE APPROACH")
        print("   This file does not use balance summary records")
        print("   Only transaction-based totals available")
    
    print("\n" + "=" * 60)
    return balance_codes if balance_records else None

def decode_balance_code(code):
    """Decode BAI2 balance codes to human-readable descriptions"""
    codes = {
        '010': 'Opening Ledger Balance',
        '015': 'Closing Ledger Balance',
        '040': 'Opening Available Balance',
        '045': 'Closing Available Balance',
        '072': 'Current Ledger Balance',
        '074': 'Current Available Balance',
        '075': 'Total Credits',
        '079': 'Total Debits',
        '100': 'Total Credits (Alt)',
        '400': 'Total Debits (Alt)',
        '450': 'Aggregate Balance',
        '500': 'Target Balance',
        '890': 'Book Balance'
    }
    return codes.get(code, f'Unknown Code {code}')

def decode_transaction_code(code):
    """Decode BAI2 transaction codes to human-readable descriptions"""
    codes = {
        '301': 'Commercial Deposit',
        '302': 'Consumer Deposit',
        '303': 'ATM Deposit',
        '304': 'Loan Deposit',
        '305': 'Check Deposit',
        '306': 'Wire Transfer Credit',
        '307': 'ACH Credit',
        '308': 'Interest Credit',
        '309': 'Dividend Credit',
        '451': 'ACH Debit',
        '452': 'Wire Transfer Debit',
        '453': 'Check Paid',
        '454': 'ATM Withdrawal',
        '455': 'Service Charge',
        '555': 'Returned Item',
        '556': 'NSF Item',
        '557': 'Stop Payment'
    }
    return codes.get(code, f'Code {code}')

if __name__ == "__main__":
    analyze_bai2_balance_summary("WACBAI2_20250813_6.bai")
