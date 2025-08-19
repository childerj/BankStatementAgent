#!/usr/bin/env python3
"""
Analyze the user's actual BAI files to confirm our fix will work
"""

def analyze_bai_file(filename):
    """Analyze a BAI file for balance continuity"""
    print(f"\n=== ANALYZING {filename} ===")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    groups = []
    current_group = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('02,'):  # Group header
            if current_group:
                groups.append(current_group)
            current_group = {
                'header': line,
                'opening_balance': None,
                'closing_balance': None,
                'date': line.split(',')[4] if len(line.split(',')) > 4 else 'unknown'
            }
        elif line.startswith('03,') and current_group:  # Account identifier
            parts = line.split(',')
            if len(parts) > 4:
                # Opening balance is in position 4
                balance_str = parts[4]
                if balance_str:
                    current_group['opening_balance'] = int(balance_str)
                else:
                    current_group['opening_balance'] = 0
        elif line.startswith('49,') and current_group:  # Group trailer
            parts = line.split(',')
            if len(parts) > 1:
                current_group['closing_balance'] = int(parts[1])
    
    if current_group:
        groups.append(current_group)
    
    print(f"Found {len(groups)} groups:")
    
    balance_continuity_good = True
    for i, group in enumerate(groups):
        print(f"  Group {i+1} (Date: {group['date']}): Opening=${group['opening_balance']:,}, Closing=${group['closing_balance']:,}")
        
        if i > 0:  # Check continuity from second group onwards
            prev_closing = groups[i-1]['closing_balance']
            current_opening = group['opening_balance']
            
            if current_opening != prev_closing:
                print(f"    ❌ CONTINUITY BROKEN: Previous closing (${prev_closing:,}) != Current opening (${current_opening:,})")
                balance_continuity_good = False
            else:
                print(f"    ✅ Continuity good: ${prev_closing:,} -> ${current_opening:,}")
    
    print(f"\nBalance Continuity: {'✅ GOOD' if balance_continuity_good else '❌ BROKEN'}")
    workday_status = '✅ YES' if balance_continuity_good else '❌ NO - Will fail with "finished with errors"'
    print(f"Workday Compatible: {workday_status}")
    
    return balance_continuity_good

def main():
    # Analyze the file that failed
    file1_path = r"C:\Users\jeff.childers\AppData\Local\Temp\StockYards_WACBAI2_20250804.bai"
    
    # Analyze the file that worked  
    file2_path = r"C:\Users\jeff.childers\AppData\Local\Temp\StockYards_WACBAI2_20250804 (1).bai"
    
    print("ANALYSIS OF USER'S ACTUAL BAI FILES")
    print("=" * 50)
    
    try:
        result1 = analyze_bai_file(file1_path)
        result2 = analyze_bai_file(file2_path)
        
        print(f"\n=== SUMMARY ===")
        print(f"File 1 (Failed in Workday): {'✅ Good' if result1 else '❌ Broken continuity'}")
        print(f"File 2 (Worked in Workday): {'✅ Good' if result2 else '❌ Broken continuity'}")
        
        print(f"\n=== WILL OUR FIX HELP? ===")
        if not result1 and result2:
            print("✅ YES! Our balance continuity fix will solve the problem.")
            print("   The failing file has broken continuity, which our fix addresses.")
            print("   The working file has good continuity, confirming this is the issue.")
        elif result1 and result2:
            print("🤔 Both files have good continuity - the issue might be elsewhere.")
        elif not result1 and not result2:
            print("❌ Both files have broken continuity - unexpected since file 2 worked.")
        else:
            print("🤔 Unexpected pattern - need further investigation.")
            
    except Exception as e:
        print(f"Error analyzing files: {e}")

if __name__ == "__main__":
    main()
