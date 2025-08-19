#!/usr/bin/env python3
"""Test the fixed BAI generation with proper balance continuity"""

import json
import sys
import os

# Add the parent directory to the path to import function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2

def test_balance_continuity():
    """Test BAI generation with corrected balance continuity"""
    
    print("🧪 Testing Fixed BAI Generation - Balance Continuity")
    print("=" * 60)
    
    # Create test data similar to the failing case
    test_data = {
        "account_number": "1035012999",
        "opening_balance": {"amount": 11270.62},  # Starting balance
        "transactions": [
            # Day 1 (250721)
            {"date": "2025-07-21", "amount": 4027.95, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-21", "amount": 2022.02, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-21", "amount": -2204.78, "description": "Withdrawal", "type": "withdrawal"},
            {"date": "2025-07-21", "amount": -1403.68, "description": "Withdrawal", "type": "withdrawal"},
            
            # Day 2 (250722)
            {"date": "2025-07-22", "amount": 3549.27, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-22", "amount": 2330.15, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-22", "amount": -2022.02, "description": "Withdrawal", "type": "withdrawal"},
            {"date": "2025-07-22", "amount": -1311.55, "description": "Withdrawal", "type": "withdrawal"},
            
            # Day 3 (250723)
            {"date": "2025-07-23", "amount": 6324.86, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-23", "amount": 1249.71, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-23", "amount": -4027.95, "description": "Withdrawal", "type": "withdrawal"},
            {"date": "2025-07-23", "amount": -3549.27, "description": "Withdrawal", "type": "withdrawal"},
        ]
    }
    
    # Generate BAI content
    bai_content = convert_to_bai2(test_data, "test_balance_continuity.pdf")
    
    print("\n📄 Generated BAI Content:")
    lines = bai_content.split('\n')
    
    # Analyze the balance flow
    groups = []
    current_group = None
    
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        parts = line.split(',')
        if not parts:
            continue
            
        record_code = parts[0]
        
        # Group Header (02)
        if record_code == '02':
            if current_group:
                groups.append(current_group)
            current_group = {
                "line": line_num,
                "date": parts[4] if len(parts) >= 5 else "Unknown",
                "opening_balance": None,
                "closing_balance": None
            }
            print(f"   Line {line_num:2d}: {line}")
            
        # Account Identifier (03) - opening balance
        elif record_code == '03' and current_group:
            current_group["opening_balance"] = int(parts[4]) if len(parts) >= 5 and parts[4].lstrip('-').isdigit() else 0
            print(f"   Line {line_num:2d}: {line}")
            print(f"            Opening Balance: {current_group['opening_balance']:,} cents")
            
        # Account Trailer (49) - closing balance
        elif record_code == '49' and current_group:
            current_group["closing_balance"] = int(parts[1]) if len(parts) >= 2 and parts[1].lstrip('-').isdigit() else 0
            print(f"   Line {line_num:2d}: {line}")
            print(f"            Closing Balance: {current_group['closing_balance']:,} cents")
    
    if current_group:
        groups.append(current_group)
    
    # Analyze balance continuity
    print(f"\n🔍 Balance Continuity Analysis:")
    print(f"{'Group':<8} {'Date':<8} {'Opening':<12} {'Closing':<12} {'Continuity':<12}")
    print("-" * 60)
    
    continuity_ok = True
    for i, group in enumerate(groups):
        if i == 0:
            continuity = "✅ Start"
        else:
            prev_closing = groups[i-1]["closing_balance"]
            current_opening = group["opening_balance"]
            if prev_closing == current_opening:
                continuity = "✅ Good"
            else:
                continuity = f"❌ Gap ({prev_closing - current_opening:,})"
                continuity_ok = False
        
        print(f"{i+1:<8} {group['date']:<8} {group['opening_balance']:<12,} {group['closing_balance']:<12,} {continuity:<12}")
    
    print(f"\n🎯 Result:")
    if continuity_ok:
        print(f"   ✅ BALANCE CONTINUITY IS CORRECT!")
        print(f"   ✅ This BAI file should work in Workday!")
    else:
        print(f"   ❌ Balance continuity is broken")
        print(f"   ❌ This will still fail in Workday")
    
    print(f"\n📊 Summary:")
    print(f"   Total groups: {len(groups)}")
    print(f"   Total lines: {len([l for l in lines if l.strip()])}")
    
    # Save test file for manual inspection
    with open("test_balance_continuity_output.bai", "w") as f:
        f.write(bai_content)
    print(f"   💾 Saved test file: test_balance_continuity_output.bai")

if __name__ == "__main__":
    test_balance_continuity()
