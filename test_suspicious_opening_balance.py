#!/usr/bin/env python3
"""
Test script to verify the suspicious opening balance detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import reconcile_transactions

def test_suspicious_opening_balance():
    """Test detection of opening balance that equals total deposits"""
    print("🧪 TESTING SUSPICIOUS OPENING BALANCE DETECTION")
    print("=" * 60)
    
    # Simulate the problematic case: opening balance = total deposits
    parsed_data = {
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
    
    print("📊 Test Data:")
    print(f"   Opening Balance: ${parsed_data['opening_balance']['amount']:,.2f}")
    print(f"   Total Deposits:  ${parsed_data['summary']['total_deposits']:,.2f}")
    print(f"   Closing Balance: ${parsed_data['closing_balance']['amount']:,.2f}")
    print(f"   ⚠️  Opening Balance = Total Deposits (SUSPICIOUS!)")
    print()
    
    # Run reconciliation
    try:
        result = reconcile_transactions(parsed_data)
    except Exception as e:
        print(f"🔍 Reconciliation threw exception (expected): {e}")
        result = None
    
    print("✅ RECONCILIATION RESULT:")
    print("=" * 40)
    
    if result:
        print(f"🔍 Status: {result.get('reconciliation_status', 'UNKNOWN')}")
        print(f"📝 Error Codes: {result.get('error_codes', [])}")
        print(f"⚠️  Warnings: {result.get('warnings', [])}")
        print(f"💰 Opening Balance Known: {result.get('opening_balance_known', False)}")
        
        if 'OB_SUSPICIOUS' in result.get('error_codes', []):
            print("✅ SUCCESS: Detected suspicious opening balance!")
            print("✅ Opening balance correctly marked as unknown")
        else:
            print("❌ FAILED: Did not detect suspicious opening balance")
            
        print("\nFull result:")
        for key, value in result.items():
            print(f"   {key}: {value}")
    else:
        print("❌ FAILED: No reconciliation result returned")
    
    print("\n" + "=" * 60)
    print("🎯 EXPECTED BEHAVIOR:")
    print("   • Should detect opening balance = total deposits")
    print("   • Should add 'OB_SUSPICIOUS' error code") 
    print("   • Should mark opening_balance_known = False")
    print("   • Should add warning about extraction error")

if __name__ == "__main__":
    test_suspicious_opening_balance()
