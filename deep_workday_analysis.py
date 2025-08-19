#!/usr/bin/env python3
"""Deep dive analysis into the Workday upload failure"""

def analyze_opening_balance_flow(file_path, file_name):
    """Analyze the opening balance flow between groups"""
    
    print(f"\n🔍 Deep Analysis: {file_name}")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"   ❌ Cannot read file: {e}")
        return
    
    lines = [line.strip() for line in lines if line.strip()]
    
    groups = []
    current_group = None
    
    for line in lines:
        parts = line.split(',')
        if not parts:
            continue
            
        record_code = parts[0]
        
        # Group Header (02)
        if record_code == '02':
            if current_group:
                groups.append(current_group)
            current_group = {
                "date": parts[4] if len(parts) >= 5 else "Unknown",
                "opening_balance": None,
                "closing_balance": None,
                "transactions": 0,
                "credit_total": 0,
                "debit_total": 0
            }
            
        # Account Identifier (03)
        elif record_code == '03' and current_group:
            current_group["opening_balance"] = int(parts[4]) if len(parts) >= 5 and parts[4].isdigit() else 0
            
        # Transaction Detail (16)
        elif record_code == '16' and current_group:
            current_group["transactions"] += 1
            if len(parts) >= 3:
                amount = int(parts[2]) if parts[2].isdigit() else 0
                txn_type = parts[1]
                if txn_type == "174":  # Credit
                    current_group["credit_total"] += amount
                elif txn_type == "455":  # Debit
                    current_group["debit_total"] += amount
                    
        # Account Trailer (49)
        elif record_code == '49' and current_group:
            current_group["closing_balance"] = int(parts[1]) if len(parts) >= 2 and parts[1].lstrip('-').isdigit() else 0
    
    if current_group:
        groups.append(current_group)
    
    print(f"\n📊 Group-by-Group Balance Flow:")
    print(f"{'Date':<8} {'Opening':<12} {'Credits':<12} {'Debits':<12} {'Expected':<12} {'Actual':<12} {'Match':<6}")
    print("-" * 80)
    
    total_issues = 0
    
    for i, group in enumerate(groups):
        opening = group["opening_balance"]
        credits = group["credit_total"]
        debits = group["debit_total"]
        closing = group["closing_balance"]
        expected = opening + credits - debits
        match = "✅" if expected == closing else "❌"
        
        if expected != closing:
            total_issues += 1
        
        print(f"{group['date']:<8} {opening:<12,} {credits:<12,} {debits:<12,} {expected:<12,} {closing:<12,} {match:<6}")
        
        if expected != closing:
            diff = closing - expected
            print(f"         ⚠️  Difference: {diff:,}")
    
    print(f"\n🎯 Balance Flow Analysis:")
    print(f"   Total groups: {len(groups)}")
    print(f"   Groups with balance issues: {total_issues}")
    
    # Check for the specific issue: zero opening balances after first group
    if len(groups) > 1:
        subsequent_openings = [g["opening_balance"] for g in groups[1:]]
        if all(opening == 0 for opening in subsequent_openings):
            print(f"   ❌ CRITICAL ISSUE: All groups after first have zero opening balance")
            print(f"      This breaks the balance continuity that Workday expects!")
            
            # Calculate what the opening balances SHOULD be
            print(f"\n💡 What the opening balances SHOULD be:")
            running_balance = groups[0]["opening_balance"]
            for i, group in enumerate(groups):
                if i == 0:
                    print(f"      {group['date']}: {running_balance:,} (correct)")
                else:
                    print(f"      {group['date']}: {running_balance:,} (currently {group['opening_balance']:,}) ❌")
                
                # Update running balance for next group
                running_balance = running_balance + group["credit_total"] - group["debit_total"]
        else:
            print(f"   ✅ Opening balances maintain continuity")
    
    return groups

def main():
    """Main analysis function"""
    
    print("🏢 Deep Dive: Workday Upload Failure Analysis")
    print("=" * 70)
    
    # File paths
    file1 = r"c:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (4).bai"
    file2 = r"c:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (1) (3).bai"
    
    # Analyze both files
    groups1 = analyze_opening_balance_flow(file1, "FILE 1 (FAILS IN WORKDAY)")
    groups2 = analyze_opening_balance_flow(file2, "FILE 2 (WORKS IN WORKDAY)")
    
    print(f"\n" + "=" * 70)
    print("🎯 ROOT CAUSE ANALYSIS:")
    
    # Check opening balance continuity
    file1_continuity = True
    file2_continuity = True
    
    if len(groups1) > 1:
        for i in range(1, len(groups1)):
            if groups1[i]["opening_balance"] == 0:
                file1_continuity = False
                break
    
    if len(groups2) > 1:
        # File 2 has inactive groups, so check only active groups
        active_groups2 = [g for g in groups2 if g["transactions"] > 0]
        if len(active_groups2) > 1:
            for i in range(1, len(active_groups2)):
                if active_groups2[i]["opening_balance"] == 0:
                    file2_continuity = False
                    break
    
    print(f"\n📊 Continuity Analysis:")
    print(f"   File 1 balance continuity: {'✅' if file1_continuity else '❌'}")
    print(f"   File 2 balance continuity: {'✅' if file2_continuity else '❌'}")
    
    print(f"\n🎯 LIKELY CAUSE OF WORKDAY FAILURE:")
    if not file1_continuity:
        print(f"   ❌ File 1 breaks balance continuity between groups")
        print(f"   ❌ Each group after the first starts with zero opening balance")
        print(f"   ❌ Workday expects each group's opening = previous group's closing")
        print(f"   ❌ This creates impossible balance reconciliation")
    
    if file2_continuity or len([g for g in groups2 if g["transactions"] > 0]) == 1:
        print(f"   ✅ File 2 maintains balance continuity (or has different structure)")
        print(f"   ✅ Workday can reconcile the balance flow")
    
    print(f"\n💡 SOLUTION:")
    print(f"   🔧 Modify the BAI generation to maintain balance continuity:")
    print(f"      • Group 1 opening balance: actual opening balance")
    print(f"      • Group 2 opening balance: Group 1 closing balance")
    print(f"      • Group 3 opening balance: Group 2 closing balance")
    print(f"      • And so on...")
    print(f"   🔧 This will make Workday accept the file!")

if __name__ == "__main__":
    main()
