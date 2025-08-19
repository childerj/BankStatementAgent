#!/usr/bin/env python3
"""
Test the suspicious opening balance detection in full BAI2 generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, reconcile_transactions

def test_suspicious_opening_bai2():
    """Test BAI2 generation with suspicious opening balance detection"""
    print("🧪 TESTING SUSPICIOUS OPENING BALANCE IN BAI2 GENERATION")
    print("=" * 70)
    
    # Simulate the problematic case from the real statement
    data = {
        "account_number": "2375133",
        "opening_balance": {"amount": 17206.08, "date": "2025-08-04"},  # Same as total deposits!
        "closing_balance": {"amount": 17706.23, "date": "2025-08-04"},
        "transactions": [
            {"date": "2025-08-04", "amount": 10000.00, "description": "Large Deposit", "type": "deposit"},
            {"date": "2025-08-04", "amount": 7206.08, "description": "Another Deposit", "type": "deposit"},
            {"date": "2025-08-04", "amount": -14992.51, "description": "Large Withdrawal", "type": "withdrawal"}
        ],
        "summary": {
            "total_deposits": 17206.08,  # This equals the opening balance - SUSPICIOUS!
            "total_withdrawals": 14992.51,
            "transaction_count": 3
        }
    }
    
    print("📊 Simulating the real problematic statement:")
    print(f"   Opening Balance: ${data['opening_balance']['amount']:,.2f}")
    print(f"   Total Deposits:  ${data['summary']['total_deposits']:,.2f}")
    print(f"   Closing Balance: ${data['closing_balance']['amount']:,.2f}")
    print(f"   ⚠️  Opening Balance = Total Deposits (SUSPICIOUS!)")
    print()
    
    # First run reconciliation (this is where the validation happens)
    print("🔄 Running reconciliation to trigger validation...")
    try:
        reconciliation_result = reconcile_transactions(data)
        print("✅ Reconciliation completed successfully")
    except Exception as e:
        print(f"⚠️  Reconciliation had issues: {e}")
        reconciliation_result = None
    
    # Generate BAI2 with reconciliation data
    bai_content = convert_to_bai2(
        data=data,
        filename="StockYards_WACBAI2_20250804_suspicious.pdf",
        routing_number="113122655",
        reconciliation_data=reconciliation_result
    )
    
    print("✅ BAI2 COMMENTS WITH SUSPICIOUS OPENING BALANCE DETECTION:")
    print("=" * 80)
    
    # Extract and show comments
    lines = bai_content.split('\n')
    for line in lines:
        if line.startswith('#'):
            print(line)
    
    print("=" * 80)
    print()
    print("🎯 EXPECTED IMPROVEMENTS:")
    print("   ✅ Should show 'OB_SUSPICIOUS' error code")
    print("   ✅ Should mark opening balance as NOT_FOUND or show calculated value")
    print("   ✅ Should include explanation about extraction error")
    print("   ✅ Should provide more accurate reconciliation")

if __name__ == "__main__":
    test_suspicious_opening_bai2()
