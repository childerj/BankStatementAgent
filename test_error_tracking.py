#!/usr/bin/env python3
"""
Test with detailed error tracking to find exactly where the 'float' object has no attribute 'get' error occurs
"""

import sys
import os
import traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, reconcile_transactions

def test_with_detailed_error_tracking():
    """Test with detailed error tracking"""
    
    print("🕵️ Testing with detailed error tracking...")
    
    # Test data with mixed types that previously caused the error
    mixed_transactions = [
        {"date": "2025-08-12", "amount": 1000.50, "description": "Deposit 1", "type": "deposit"},
        1234.56,  # This float would cause the 'get' error
        {"date": "2025-08-12", "amount": -500.25, "description": "Withdrawal 1", "type": "withdrawal"},
        789.01,   # Another problematic float
        {"date": "2025-08-12", "amount": 250.00, "description": "Deposit 2", "type": "deposit"}
    ]
    
    # Test data structure that would be passed to the functions
    test_data = {
        "transactions": mixed_transactions,
        "opening_balance": {"amount": 5000.00, "date": "2025-08-12"},
        "closing_balance": {"amount": 5950.25, "date": "2025-08-12"},
        "account_number": "2375133"
    }
    
    # Test reconcile_transactions with mixed data
    print("\n1️⃣ Testing reconcile_transactions...")
    try:
        reconciliation_result = reconcile_transactions(test_data)
        print(f"✅ reconcile_transactions completed successfully!")
    except Exception as e:
        print(f"❌ reconcile_transactions failed: {e}")
        traceback.print_exc()
        return False
    
    # Test convert_to_bai2 with mixed data
    print("\n2️⃣ Testing convert_to_bai2 with detailed error tracking...")
    try:
        bai2_content = convert_to_bai2(test_data, "test_mixed.pdf", reconciliation_result, "083000564")
        print(f"✅ convert_to_bai2 completed successfully!")
        print(f"   - Generated BAI2 content: {len(bai2_content)} characters")
    except Exception as e:
        print(f"❌ convert_to_bai2 failed: {e}")
        print(f"\n🔍 Full error traceback:")
        traceback.print_exc()
        
        # Try to identify the exact line where the error occurs
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        print(f"\n📍 Error details:")
        print(f"   - Error type: {exc_type.__name__}")
        print(f"   - Error message: {exc_value}")
        
        # Print the call stack
        print(f"\n📚 Call stack:")
        for frame in traceback.extract_tb(exc_traceback):
            print(f"   - File: {frame.filename}")
            print(f"     Line {frame.lineno}: {frame.line}")
            print(f"     Function: {frame.name}")
            print()
        
        return False
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_with_detailed_error_tracking()
    if success:
        print("\n🚀 VALIDATION COMPLETE!")
        sys.exit(0)
    else:
        print("\n💥 VALIDATION FAILED!")
        sys.exit(1)
