#!/usr/bin/env python3
"""
Test with balanced data to find the exact location of the 'float' object has no attribute 'get' error
"""

import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, reconcile_transactions

def test_to_find_float_error():
    """Test with balanced data to find the float error"""
    
    print("🕵️ Testing to find the exact location of the 'float' error...")
    
    # Test data with mixed types - balanced to avoid reconciliation errors
    mixed_transactions = [
        {"date": "2025-08-12", "amount": 1000.50, "description": "Deposit 1", "type": "deposit"},
        1234.56,  # This float would cause the 'get' error
        {"date": "2025-08-12", "amount": -500.25, "description": "Withdrawal 1", "type": "withdrawal"},
        789.01,   # Another problematic float
        {"date": "2025-08-12", "amount": 250.00, "description": "Deposit 2", "type": "deposit"},
        {"date": "2025-08-12", "amount": -100.00, "description": "Fee", "type": "fee"}
    ]
    
    # Calculate balanced amounts: 1000.50 + 250.00 - 500.25 - 100.00 = 650.25
    opening_amount = 5000.00
    closing_amount = opening_amount + 650.25  # 5650.25
    
    # Test data structure that would be passed to the functions
    test_data = {
        "transactions": mixed_transactions,
        "opening_balance": {"amount": opening_amount, "date": "2025-08-12"},
        "closing_balance": {"amount": closing_amount, "date": "2025-08-12"},
        "account_number": "2375133"
    }
    
    # Create a mock reconciliation result to avoid reconciliation exception
    mock_reconciliation_result = {
        "opening_balance": opening_amount,
        "opening_balance_known": True,
        "closing_balance": closing_amount,
        "closing_balance_known": True,
        "total_deposits": 1250.50,
        "total_withdrawals": 600.25,
        "expected_closing": closing_amount,
        "difference": 0.0,
        "balanced": True,
        "transaction_count": 4,  # Only valid dict transactions
        "reconciliation_status": "COMPLETE",
        "warnings": [],
        "transactions": [txn for txn in mixed_transactions if isinstance(txn, dict)]  # Only pass valid transactions
    }
    
    print("\n🧪 Testing convert_to_bai2 with mock reconciliation data...")
    try:
        bai2_content = convert_to_bai2(test_data, "test_mixed.pdf", mock_reconciliation_result, "083000564")
        print(f"✅ convert_to_bai2 completed successfully!")
        print(f"   - Generated BAI2 content: {len(bai2_content)} characters")
        return True
    except Exception as e:
        print(f"❌ convert_to_bai2 failed: {e}")
        print(f"\n🔍 Full error traceback:")
        traceback.print_exc()
        
        # Try to identify the exact line where the error occurs
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        print(f"\n📍 Error details:")
        print(f"   - Error type: {exc_type.__name__}")
        print(f"   - Error message: {exc_value}")
        
        # Print the call stack
        print(f"\n📚 Call stack:")
        for frame in traceback.extract_tb(exc_traceback):
            print(f"   - File: {os.path.basename(frame.filename)}")
            print(f"     Line {frame.lineno}: {frame.line}")
            print(f"     Function: {frame.name}")
            print()
        
        return False

if __name__ == "__main__":
    success = test_to_find_float_error()
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Error found!")
        sys.exit(1)
