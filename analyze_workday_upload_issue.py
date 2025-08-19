#!/usr/bin/env python3
"""Analyze BAI files for Workday upload differences"""

def analyze_bai_structure(file_path, file_name):
    """Analyze a BAI file structure for Workday compatibility issues"""
    
    print(f"\n🔍 Analyzing {file_name}:")
    print(f"   File: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"   ❌ Cannot read file: {e}")
        return
    
    # Clean lines
    lines = [line.strip() for line in lines if line.strip()]
    
    # Basic metrics
    print(f"\n📊 Basic Structure:")
    print(f"   Total lines: {len(lines)}")
    
    # Count record types
    record_counts = {}
    group_dates = []
    transaction_count = 0
    groups_with_transactions = 0
    groups_without_transactions = 0
    opening_balances = []
    
    current_group_date = None
    current_group_transactions = 0
    
    for i, line in enumerate(lines, 1):
        if not line:
            continue
            
        parts = line.split(',')
        if not parts:
            continue
            
        record_code = parts[0]
        record_counts[record_code] = record_counts.get(record_code, 0) + 1
        
        # Group Header (02)
        if record_code == '02':
            # Process previous group
            if current_group_date:
                if current_group_transactions > 0:
                    groups_with_transactions += 1
                else:
                    groups_without_transactions += 1
            
            # Start new group
            if len(parts) >= 5:
                current_group_date = parts[4]
                group_dates.append(current_group_date)
                current_group_transactions = 0
                print(f"   Group {current_group_date}: Line {i}")
                
        # Account Identifier (03) - check opening balance
        elif record_code == '03':
            if len(parts) >= 5:
                opening_bal = parts[4]
                opening_balances.append(opening_bal)
                if current_group_date:
                    print(f"      Opening balance: {opening_bal}")
                    
        # Transaction Detail (16)
        elif record_code == '16':
            transaction_count += 1
            current_group_transactions += 1
            
        # Account Trailer (49)
        elif record_code == '49':
            if current_group_date and current_group_transactions > 0:
                print(f"      Transactions: {current_group_transactions}")
    
    # Process final group
    if current_group_date:
        if current_group_transactions > 0:
            groups_with_transactions += 1
        else:
            groups_without_transactions += 1
    
    print(f"\n📈 Record Type Counts:")
    for record_type in sorted(record_counts.keys()):
        print(f"   {record_type}: {record_counts[record_type]} records")
    
    print(f"\n📅 Group Analysis:")
    print(f"   Total groups: {len(group_dates)}")
    print(f"   Groups with transactions: {groups_with_transactions}")
    print(f"   Groups without transactions: {groups_without_transactions}")
    print(f"   Total transactions: {transaction_count}")
    
    # Opening balance analysis
    unique_opening_balances = set(opening_balances)
    print(f"\n💰 Opening Balance Analysis:")
    print(f"   Unique opening balances: {unique_opening_balances}")
    
    # Check for potential issues
    issues = []
    warnings = []
    
    # Issue 1: Starting balance in first group
    if group_dates and opening_balances:
        first_opening = opening_balances[0] if opening_balances else "0"
        if first_opening == "0":
            warnings.append("First group has zero opening balance")
        else:
            print(f"   First group opening balance: {first_opening}")
    
    # Issue 2: Groups without transactions
    if groups_without_transactions > 0:
        warnings.append(f"{groups_without_transactions} groups have no transactions")
    
    # Issue 3: All subsequent groups starting at 0
    subsequent_openings = opening_balances[1:] if len(opening_balances) > 1 else []
    if subsequent_openings and all(bal == "0" for bal in subsequent_openings):
        issues.append("All groups after first start with zero balance (potential issue)")
    
    # Issue 4: Check for account trailer balances
    account_trailers = [line for line in lines if line.startswith('49,')]
    print(f"\n📋 Account Trailer Analysis:")
    for i, trailer in enumerate(account_trailers):
        parts = trailer.split(',')
        if len(parts) >= 2:
            balance = parts[1]
            print(f"   Group {i+1} ending balance: {balance}")
    
    # Report issues
    if issues:
        print(f"\n❌ CRITICAL ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not issues and not warnings:
        print(f"\n✅ No obvious structural issues found")
    
    return {
        "total_lines": len(lines),
        "total_groups": len(group_dates),
        "groups_with_transactions": groups_with_transactions,
        "groups_without_transactions": groups_without_transactions,
        "total_transactions": transaction_count,
        "opening_balances": opening_balances,
        "issues": issues,
        "warnings": warnings
    }

def compare_files():
    """Compare the two BAI files"""
    
    print("🏢 BAI File Workday Upload Analysis")
    print("=" * 70)
    
    # File paths
    file1 = r"c:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (4).bai"
    file2 = r"c:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (1) (3).bai"
    
    # Analyze both files
    result1 = analyze_bai_structure(file1, "FILE 1 (FAILS)")
    result2 = analyze_bai_structure(file2, "FILE 2 (WORKS)")
    
    # Compare key differences
    print(f"\n" + "=" * 70)
    print("🔄 COMPARISON SUMMARY:")
    
    print(f"\n📊 Structure Comparison:")
    print(f"   File 1 (Fails): {result1['total_groups']} groups, {result1['total_transactions']} transactions")
    print(f"   File 2 (Works): {result2['total_groups']} groups, {result2['total_transactions']} transactions")
    
    print(f"\n💰 Opening Balance Comparison:")
    print(f"   File 1 first opening: {result1['opening_balances'][0] if result1['opening_balances'] else 'None'}")
    print(f"   File 2 first opening: {result2['opening_balances'][0] if result2['opening_balances'] else 'None'}")
    
    print(f"\n📅 Group Activity:")
    print(f"   File 1: {result1['groups_with_transactions']} active, {result1['groups_without_transactions']} inactive")
    print(f"   File 2: {result2['groups_with_transactions']} active, {result2['groups_without_transactions']} inactive")
    
    # Key differences that could cause Workday issues
    print(f"\n🎯 POTENTIAL WORKDAY ISSUES:")
    
    if result1['groups_without_transactions'] == 0 and result2['groups_without_transactions'] > 0:
        print(f"   ✅ File 1 has NO inactive groups (good)")
        print(f"   ⚠️  File 2 has {result2['groups_without_transactions']} inactive groups")
    elif result1['groups_without_transactions'] > 0 and result2['groups_without_transactions'] == 0:
        print(f"   ❌ File 1 has {result1['groups_without_transactions']} inactive groups (potential issue)")
        print(f"   ✅ File 2 has NO inactive groups")
    
    # Check opening balance patterns
    if len(result1['opening_balances']) > 1:
        file1_pattern = "first non-zero" if result1['opening_balances'][0] != "0" else "all zero"
        if result1['opening_balances'][0] != "0" and all(bal == "0" for bal in result1['opening_balances'][1:]):
            file1_pattern = "first non-zero, rest zero"
    
    if len(result2['opening_balances']) > 1:
        file2_pattern = "mixed balances"
        if any(bal != "0" for bal in result2['opening_balances']):
            file2_pattern = "has non-zero balances"
    
    print(f"\n💡 RECOMMENDATION:")
    if result1['groups_without_transactions'] == 0 and result2['groups_without_transactions'] > 0:
        print(f"   File 1 should work better - no inactive groups")
        print(f"   File 2 might have compatibility issues with inactive groups")
    else:
        print(f"   Check other factors like opening balance consistency")
        print(f"   File 2 works, so use its pattern as reference")

if __name__ == "__main__":
    compare_files()
