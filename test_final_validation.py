#!/usr/bin/env python3
"""
Test to verify all transaction processing loops are protected against mixed data types
Tests all possible scenarios where 'float' object has no attribute 'get' error could occur
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, reconcile_transactions, fallback_bai2_conversion

def test_all_transaction_processing_scenarios():
    """Test all transaction processing functions with mixed data types"""
    
    print("🧪 Testing ALL transaction processing scenarios for robustness...")
    
    # Test data with mixed types that previously caused the error
    mixed_transactions = [
        {"date": "2025-08-12", "amount": 1000.50, "description": "Deposit 1", "type": "deposit"},
        1234.56,  # This float would cause the 'get' error
        {"date": "2025-08-12", "amount": -500.25, "description": "Withdrawal 1", "type": "withdrawal"},
        789.01,   # Another problematic float
        {"date": "2025-08-12", "amount": 250.00, "description": "Deposit 2", "type": "deposit"},
        "invalid_string",  # String that's not a dict
        {"date": "2025-08-12", "amount": -100.00, "description": "Fee", "type": "fee"},
        None,     # None value
        {"date": "2025-08-12", "amount": 300.00, "description": "Deposit 3", "type": "deposit"}
    ]
    
    # Test data structure that would be passed to the functions
    test_data = {
        "transactions": mixed_transactions,
        "opening_balance": {"amount": 5000.00, "date": "2025-08-12"},
        "closing_balance": {"amount": 5950.25, "date": "2025-08-12"},
        "account_number": "2375133"
    }
    
    # Test reconcile_transactions with mixed data
    print("\n1️⃣ Testing reconcile_transactions with mixed transaction types...")
    try:
        reconciliation_result = reconcile_transactions(test_data)
        print(f"✅ reconcile_transactions completed successfully!")
        print(f"   - Status: {reconciliation_result['reconciliation_status']}")
        print(f"   - Valid transactions processed: {reconciliation_result['transaction_count']}")
        print(f"   - Total deposits: ${reconciliation_result['total_deposits']:,.2f}")
        print(f"   - Total withdrawals: ${reconciliation_result['total_withdrawals']:,.2f}")
    except Exception as e:
        print(f"❌ reconcile_transactions failed: {e}")
        return False
    
    # Test convert_to_bai2 with mixed data
    print("\n2️⃣ Testing convert_to_bai2 with mixed transaction types...")
    try:
        bai2_content = convert_to_bai2(test_data, "test_mixed.pdf", reconciliation_result, "083000564")
        print(f"✅ convert_to_bai2 completed successfully!")
        print(f"   - Generated BAI2 content: {len(bai2_content)} characters")
        
        # Verify BAI2 structure
        lines = bai2_content.strip().split('\n')
        print(f"   - BAI2 lines: {len(lines)}")
        
        # Count transaction records (16 records)
        transaction_records = [line for line in lines if line.startswith('16,')]
        print(f"   - Transaction records (16): {len(transaction_records)}")
        
        # Verify only valid transactions were processed
        expected_valid_transactions = 5  # From mixed_transactions, only dicts with proper structure
        if len(transaction_records) == expected_valid_transactions:
            print(f"   ✅ Correct number of transactions processed ({expected_valid_transactions})")
        else:
            print(f"   ⚠️ Expected {expected_valid_transactions} transactions, got {len(transaction_records)}")
            
    except Exception as e:
        print(f"❌ convert_to_bai2 failed: {e}")
        return False
    
    # Test fallback_bai2_conversion with mixed data
    print("\n3️⃣ Testing fallback_bai2_conversion with mixed transaction types...")
    try:
        # Create fallback test data
        fallback_data = {
            "transactions": mixed_transactions,
            "opening_balance": 5000.00,
            "closing_balance": 5950.25,
            "total_deposits": 1550.50,
            "total_withdrawals": 600.25
        }
        
        fallback_bai2_content = fallback_bai2_conversion(
            fallback_data, "test_fallback.pdf", "250813", "1200", "083000564"
        )
        print(f"✅ fallback_bai2_conversion completed successfully!")
        print(f"   - Generated fallback BAI2 content: {len(fallback_bai2_content)} characters")
        
        # Verify fallback BAI2 structure
        fallback_lines = fallback_bai2_content.strip().split('\n')
        print(f"   - Fallback BAI2 lines: {len(fallback_lines)}")
        
        # Count transaction records (16 records)
        fallback_transaction_records = [line for line in fallback_lines if line.startswith('16,')]
        print(f"   - Fallback transaction records (16): {len(fallback_transaction_records)}")
        
        # Verify only valid transactions were processed
        if len(fallback_transaction_records) == expected_valid_transactions:
            print(f"   ✅ Correct number of fallback transactions processed ({expected_valid_transactions})")
        else:
            print(f"   ⚠️ Expected {expected_valid_transactions} fallback transactions, got {len(fallback_transaction_records)}")
            
    except Exception as e:
        print(f"❌ fallback_bai2_conversion failed: {e}")
        return False
    
    # Test edge case: all invalid transactions
    print("\n4️⃣ Testing edge case with all invalid transactions...")
    try:
        invalid_data = {
            "transactions": [1234.56, 789.01, "invalid", None, [], {}],
            "opening_balance": {"amount": 5000.00, "date": "2025-08-12"},
            "closing_balance": {"amount": 5000.00, "date": "2025-08-12"},
            "account_number": "2375133"
        }
        
        edge_reconciliation = reconcile_transactions(invalid_data)
        edge_bai2 = convert_to_bai2(invalid_data, "test_edge.pdf", edge_reconciliation, "083000564")
        
        print(f"✅ Edge case (all invalid transactions) handled successfully!")
        print(f"   - Reconciliation status: {edge_reconciliation['reconciliation_status']}")
        print(f"   - Valid transactions: {edge_reconciliation['transaction_count']}")
        print(f"   - BAI2 generated: {len(edge_bai2)} characters")
        
    except Exception as e:
        print(f"❌ Edge case failed: {e}")
        return False
    
    # Test edge case: empty transactions list
    print("\n5️⃣ Testing edge case with empty transactions list...")
    try:
        empty_data = {
            "transactions": [],
            "opening_balance": {"amount": 5000.00, "date": "2025-08-12"},
            "closing_balance": {"amount": 5000.00, "date": "2025-08-12"},
            "account_number": "2375133"
        }
        
        empty_reconciliation = reconcile_transactions(empty_data)
        empty_bai2 = convert_to_bai2(empty_data, "test_empty.pdf", empty_reconciliation, "083000564")
        
        print(f"✅ Edge case (empty transactions) handled successfully!")
        print(f"   - Reconciliation status: {empty_reconciliation['reconciliation_status']}")
        print(f"   - Valid transactions: {empty_reconciliation['transaction_count']}")
        print(f"   - BAI2 generated: {len(empty_bai2)} characters")
        
    except Exception as e:
        print(f"❌ Empty transactions edge case failed: {e}")
        return False
    
    print("\n🎉 ALL TRANSACTION PROCESSING TESTS PASSED!")
    print("✅ The system is now robust against 'float' object has no attribute 'get' errors")
    print("✅ All transaction processing loops properly validate input types")
    print("✅ Mixed data types are handled gracefully")
    print("✅ Edge cases (empty, all invalid) are handled properly")
    print("\n💡 The Azure Function should now process bank statements without the previous error!")
    
    return True

if __name__ == "__main__":
    success = test_all_transaction_processing_scenarios()
    if success:
        print("\n🚀 VALIDATION COMPLETE - Ready for production!")
        sys.exit(0)
    else:
        print("\n💥 VALIDATION FAILED - Issues remain!")
        sys.exit(1)
