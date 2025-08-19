#!/usr/bin/env python3
"""
Simple analysis of date groups in working BAI2 file
"""

def analyze_date_groups():
    """Analyze date groups in working BAI2 file"""
    
    try:
        # Read working BAI2 file
        with open('WACBAI2_20250813 (1).bai', 'r') as f:
            working_lines = f.readlines()
    except FileNotFoundError:
        # Try alternative name
        try:
            with open('WACBAI2_20250813_1.bai', 'r') as f:
                working_lines = f.readlines()
        except FileNotFoundError:
            print("Working BAI2 file not found")
            return
    
    print("DATE GROUP ANALYSIS")
    print("=" * 50)
    
    # Find all group headers (02 records)
    group_headers = []
    for i, line in enumerate(working_lines):
        line = line.strip()
        if line.startswith('02,'):
            parts = line.split(',')
            if len(parts) >= 4:
                date = parts[4]  # Group date is 5th field
                group_headers.append((i+1, date, line))
                print(f"Group {len(group_headers)}: Line {i+1}, Date {date}")
                print(f"  Full line: {line}")
    
    print(f"\nFound {len(group_headers)} date groups")
    
    # Analyze transactions between groups
    if len(group_headers) >= 2:
        print("\nTRANSACTION ANALYSIS BY GROUP:")
        
        # First group transactions
        start_line = group_headers[0][0]
        end_line = group_headers[1][0] - 1
        
        first_group_txns = []
        for i in range(start_line, min(end_line, len(working_lines))):
            line = working_lines[i].strip()
            if line.startswith('16,'):
                first_group_txns.append(line)
        
        print(f"\nGroup 1 (Date {group_headers[0][1]}):")
        print(f"  {len(first_group_txns)} transactions")
        for j, txn in enumerate(first_group_txns[:3]):  # Show first 3
            print(f"    {j+1}: {txn}")
        if len(first_group_txns) > 3:
            print(f"    ... and {len(first_group_txns)-3} more")
        
        # Second group transactions
        start_line = group_headers[1][0]
        end_line = len(working_lines)
        
        second_group_txns = []
        for i in range(start_line, end_line):
            line = working_lines[i].strip()
            if line.startswith('16,'):
                second_group_txns.append(line)
        
        print(f"\nGroup 2 (Date {group_headers[1][1]}):")
        print(f"  {len(second_group_txns)} transactions")
        for j, txn in enumerate(second_group_txns[:3]):  # Show first 3
            print(f"    {j+1}: {txn}")
        if len(second_group_txns) > 3:
            print(f"    ... and {len(second_group_txns)-3} more")
    
    # Look for actual transaction dates in descriptions
    print("\nTRANSACTION DATE PATTERNS:")
    all_transactions = [line.strip() for line in working_lines if line.strip().startswith('16,')]
    
    date_patterns = set()
    for txn in all_transactions:
        # Look for date patterns in transaction descriptions
        parts = txn.split(',')
        if len(parts) >= 7:
            desc = parts[6]  # Description field
            # Look for date patterns like 08/12, 08/13, etc.
            import re
            dates = re.findall(r'\d{2}/\d{2}', desc)
            for date in dates:
                date_patterns.add(date)
    
    if date_patterns:
        print(f"  Found date patterns in descriptions: {sorted(date_patterns)}")
    else:
        print("  No obvious date patterns in transaction descriptions")
    
    # Summary
    print(f"\nSUMMARY:")
    print(f"  Total groups: {len(group_headers)}")
    if len(group_headers) >= 2:
        print(f"  Group dates: {group_headers[0][1]} and {group_headers[1][1]}")
        print(f"  This suggests the BAI2 spans multiple business days")
        print(f"  or uses separate groups for different transaction types/processing dates")

if __name__ == "__main__":
    analyze_date_groups()
