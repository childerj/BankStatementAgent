#!/usr/bin/env python3
"""
Compare BAI2 file structures to analyze if they use the same logic
"""

def analyze_bai2_structure(file_path, file_name):
    """Analyze the structure of a BAI2 file"""
    print(f"\n📊 ANALYZING: {file_name}")
    print("=" * 60)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Parse file structure
    file_headers = []
    group_headers = []
    account_records = []
    balance_records = []
    transaction_records = []
    detail_records = []
    trailers = []
    
    current_group = None
    current_account = None
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        # Extract record type (first field before comma)
        record_type = line.split(',')[0]
        
        if record_type == '01':
            file_headers.append((line_num, line))
        elif record_type == '02':
            group_headers.append((line_num, line))
            current_group = line_num
        elif record_type == '03':
            account_records.append((line_num, line, current_group))
            current_account = line_num
        elif record_type == '88':
            if 'Z/' in line:  # Balance summary record
                balance_records.append((line_num, line, current_account))
            else:  # Detail/continuation record
                detail_records.append((line_num, line, current_account))
        elif record_type == '16':
            transaction_records.append((line_num, line, current_account))
        elif record_type in ['49', '98', '99']:
            trailers.append((line_num, line, record_type))
    
    # Print summary
    print(f"📋 STRUCTURE SUMMARY:")
    print(f"   • File Headers (01): {len(file_headers)}")
    print(f"   • Group Headers (02): {len(group_headers)}")
    print(f"   • Account Records (03): {len(account_records)}")
    print(f"   • Balance Records (88 with Z/): {len(balance_records)}")
    print(f"   • Transaction Records (16): {len(transaction_records)}")
    print(f"   • Detail Records (88 without Z/): {len(detail_records)}")
    print(f"   • Trailers (49/98/99): {len(trailers)}")
    
    # Analyze balance codes used
    balance_codes = {}
    for _, line, _ in balance_records:
        fields = line.split(',')
        if len(fields) >= 2:
            code = fields[1]
            balance_codes[code] = balance_codes.get(code, 0) + 1
    
    print(f"\n🏦 BALANCE CODES USED:")
    for code, count in sorted(balance_codes.items()):
        print(f"   • Code {code}: {count} times")
    
    # Analyze transaction codes
    transaction_codes = {}
    for _, line, _ in transaction_records:
        fields = line.split(',')
        if len(fields) >= 2:
            code = fields[1]
            transaction_codes[code] = transaction_codes.get(code, 0) + 1
    
    print(f"\n💳 TRANSACTION CODES USED:")
    for code, count in sorted(transaction_codes.items()):
        print(f"   • Code {code}: {count} times")
    
    # Check for multi-day structure
    unique_groups = len(set(g[2] for g in account_records))
    print(f"\n📅 MULTI-DAY STRUCTURE:")
    print(f"   • Number of groups/days: {len(group_headers)}")
    print(f"   • Accounts span groups: {unique_groups}")
    
    # Look for detailed transaction descriptions
    has_detailed_descriptions = any('WORLD ACCEPTANCE' in line for _, line, _ in detail_records)
    print(f"\n📝 TRANSACTION DETAILS:")
    print(f"   • Has detailed descriptions: {has_detailed_descriptions}")
    print(f"   • Detail continuation records: {len(detail_records)}")
    
    return {
        'file_headers': len(file_headers),
        'group_headers': len(group_headers),
        'account_records': len(account_records),
        'balance_records': len(balance_records),
        'transaction_records': len(transaction_records),
        'detail_records': len(detail_records),
        'trailers': len(trailers),
        'balance_codes': balance_codes,
        'transaction_codes': transaction_codes,
        'has_detailed_descriptions': has_detailed_descriptions,
        'multi_day': len(group_headers) > 1
    }

def compare_structures(struct1, struct2, name1, name2):
    """Compare two BAI2 structures and highlight differences"""
    print(f"\n🔍 STRUCTURE COMPARISON: {name1} vs {name2}")
    print("=" * 70)
    
    # Compare basic structure
    print("📊 RECORD COUNTS:")
    for key in ['file_headers', 'group_headers', 'account_records', 'balance_records', 'transaction_records', 'detail_records']:
        val1 = struct1[key]
        val2 = struct2[key]
        match = "✅" if val1 == val2 else "❌"
        print(f"   {match} {key.replace('_', ' ').title()}: {val1} vs {val2}")
    
    # Compare balance codes
    print("\n🏦 BALANCE CODES:")
    all_balance_codes = set(struct1['balance_codes'].keys()) | set(struct2['balance_codes'].keys())
    for code in sorted(all_balance_codes):
        count1 = struct1['balance_codes'].get(code, 0)
        count2 = struct2['balance_codes'].get(code, 0)
        match = "✅" if count1 == count2 else "❌"
        print(f"   {match} Code {code}: {count1} vs {count2}")
    
    # Compare transaction codes
    print("\n💳 TRANSACTION CODES:")
    all_transaction_codes = set(struct1['transaction_codes'].keys()) | set(struct2['transaction_codes'].keys())
    for code in sorted(all_transaction_codes):
        count1 = struct1['transaction_codes'].get(code, 0)
        count2 = struct2['transaction_codes'].get(code, 0)
        match = "✅" if count1 == count2 else "❌"
        print(f"   {match} Code {code}: {count1} vs {count2}")
    
    # Compare features
    print("\n🎯 KEY FEATURES:")
    features = [
        ('Multi-day structure', 'multi_day'),
        ('Detailed descriptions', 'has_detailed_descriptions')
    ]
    
    for feature_name, key in features:
        val1 = struct1[key]
        val2 = struct2[key]
        match = "✅" if val1 == val2 else "❌"
        print(f"   {match} {feature_name}: {val1} vs {val2}")
    
    # Overall similarity assessment
    print(f"\n🎯 SIMILARITY ASSESSMENT:")
    
    # Check if they follow the same pattern
    same_balance_codes = struct1['balance_codes'].keys() == struct2['balance_codes'].keys()
    same_transaction_codes = struct1['transaction_codes'].keys() == struct2['transaction_codes'].keys()
    same_multi_day = struct1['multi_day'] == struct2['multi_day']
    same_detailed = struct1['has_detailed_descriptions'] == struct2['has_detailed_descriptions']
    
    if same_balance_codes and same_transaction_codes and same_multi_day and same_detailed:
        print("   ✅ SAME LOGIC: Both files use identical BAI2 structure and logic")
    elif same_balance_codes and same_transaction_codes:
        print("   🟡 SIMILAR LOGIC: Same codes but different features")
    elif same_multi_day and same_detailed:
        print("   🟡 SIMILAR STRUCTURE: Same format but different codes")
    else:
        print("   ❌ DIFFERENT LOGIC: Files use different BAI2 approaches")
    
    return same_balance_codes and same_transaction_codes and same_multi_day and same_detailed

def main():
    print("🔍 BAI2 STRUCTURE COMPARISON TOOL")
    print("=" * 70)
    
    # File paths
    working_file = "WACBAI2_20250813 (1).bai"
    central_bank_file = "Central Bank 7-22-2025.bai2"
    
    # Copy working file to workspace if needed
    import os
    if not os.path.exists(working_file):
        import shutil
        shutil.copy(f"C:\\Users\\jeff.childers\\Downloads\\{working_file}", working_file)
    
    # Analyze both files
    struct1 = analyze_bai2_structure(working_file, "Working File (WACBAI2_20250813)")
    struct2 = analyze_bai2_structure(central_bank_file, "Central Bank File (7-22-2025)")
    
    # Compare structures
    same_logic = compare_structures(struct1, struct2, "Working File", "Central Bank File")
    
    print(f"\n🎯 FINAL ANSWER:")
    if same_logic:
        print("   ✅ YES - Both files use the SAME LOGIC and structure")
        print("   ➤ Your function would generate equivalent output for both")
        print("   ➤ Both follow the same BAI2 formatting approach")
    else:
        print("   ❌ NO - Files use DIFFERENT logic or structure")
        print("   ➤ Your function may need adjustments for equivalent output")
        print("   ➤ Different BAI2 formatting approaches detected")

if __name__ == "__main__":
    main()
