#!/usr/bin/env python3
"""Test the enhanced reconciliation logic with unknown opening balance"""

import json
import sys
import os

# Add the parent directory to the path to import function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import reconcile_transactions

def test_reconciliation_scenarios():
    """Test different reconciliation scenarios"""
    
    print("🧪 Testing Enhanced Reconciliation Logic")
    print("=" * 60)
    
    # Test Case 1: Both balances known and match
    print("\n1️⃣  Test Case: Both balances known, perfect match")
    test_data_1 = {
        "opening_balance": {"amount": 1000.00},
        "closing_balance": {"amount": 1200.00},
        "transactions": [
            {"amount": 300.00, "description": "Deposit"},
            {"amount": -100.00, "description": "Withdrawal"}
        ]
    }
    
    try:
        result = reconcile_transactions(test_data_1)
        print(f"   Status: {result['reconciliation_status']}")
        print(f"   Error Codes: {result['error_codes']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Balanced: {result['balanced']}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Case 2: Opening balance unknown
    print("\n2️⃣  Test Case: Opening balance UNKNOWN")
    test_data_2 = {
        "closing_balance": {"amount": 1200.00},
        "transactions": [
            {"amount": 300.00, "description": "Deposit"},
            {"amount": -100.00, "description": "Withdrawal"}
        ]
    }
    
    try:
        result = reconcile_transactions(test_data_2)
        print(f"   Status: {result['reconciliation_status']}")
        print(f"   Error Codes: {result['error_codes']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Opening Balance Known: {result['opening_balance_known']}")
        print(f"   Calculated Opening: ${result['opening_balance']:,.2f}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Case 3: Closing balance unknown
    print("\n3️⃣  Test Case: Closing balance UNKNOWN")
    test_data_3 = {
        "opening_balance": {"amount": 1000.00},
        "transactions": [
            {"amount": 300.00, "description": "Deposit"},
            {"amount": -100.00, "description": "Withdrawal"}
        ]
    }
    
    try:
        result = reconcile_transactions(test_data_3)
        print(f"   Status: {result['reconciliation_status']}")
        print(f"   Error Codes: {result['error_codes']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Closing Balance Known: {result['closing_balance_known']}")
        print(f"   Calculated Closing: ${result['expected_closing']:,.2f}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Case 4: Both balances unknown
    print("\n4️⃣  Test Case: Both balances UNKNOWN")
    test_data_4 = {
        "transactions": [
            {"amount": 300.00, "description": "Deposit"},
            {"amount": -100.00, "description": "Withdrawal"}
        ]
    }
    
    try:
        result = reconcile_transactions(test_data_4)
        print(f"   Status: {result['reconciliation_status']}")
        print(f"   Error Codes: {result['error_codes']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Opening Balance Known: {result['opening_balance_known']}")
        print(f"   Closing Balance Known: {result['closing_balance_known']}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Case 5: Balances don't match
    print("\n5️⃣  Test Case: Balance mismatch")
    test_data_5 = {
        "opening_balance": {"amount": 1000.00},
        "closing_balance": {"amount": 1500.00},  # Should be 1200
        "transactions": [
            {"amount": 300.00, "description": "Deposit"},
            {"amount": -100.00, "description": "Withdrawal"}
        ]
    }
    
    try:
        result = reconcile_transactions(test_data_5)
        print(f"   Status: {result['reconciliation_status']}")
        print(f"   Error Codes: {result['error_codes']}")
        print(f"   Warnings: {result['warnings']}")
        print(f"   Difference: ${result['difference']:,.2f}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Reconciliation testing complete!")

if __name__ == "__main__":
    test_reconciliation_scenarios()
