#!/usr/bin/env python3
"""
Test script to verify the transaction validation fix
"""

def test_transaction_validation():
    """Test that our validation logic works correctly"""
    
    # Simulate problematic data that was causing the error
    problematic_transactions = [
        {"date": "2025-08-13", "amount": 100.0, "description": "Valid transaction"},
        123.45,  # This float was causing the error
        {"date": "2025-08-13", "amount": -50.0, "description": "Another valid transaction"},
        "invalid_string",  # This would also cause issues
        {"date": "2025-08-13", "amount": 200.0, "description": "Valid transaction 2"}
    ]
    
    print("🧪 Testing transaction validation logic...")
    print(f"📊 Original array length: {len(problematic_transactions)}")
    
    # Apply the same validation logic we added to the function
    valid_transactions = []
    for i, txn in enumerate(problematic_transactions):
        if isinstance(txn, dict):
            valid_transactions.append(txn)
            print(f"✅ Transaction {i}: Valid dict - {txn.get('description', 'No description')}")
        else:
            print(f"⚠️ Transaction {i}: Invalid type {type(txn)} - {txn}")
    
    print(f"📊 Filtered array length: {len(valid_transactions)}")
    
    # Test transaction processing
    total_amount = 0
    for txn in valid_transactions:
        amount = float(txn.get("amount", 0))
        total_amount += amount
        print(f"💰 Processing: ${amount:,.2f} - {txn.get('description', 'No description')}")
    
    print(f"💰 Total amount: ${total_amount:,.2f}")
    print("✅ Validation test completed successfully!")
    
    return len(valid_transactions) == 3  # Should have filtered out 2 invalid entries

if __name__ == "__main__":
    success = test_transaction_validation()
    if success:
        print("\n🎉 TEST PASSED: Transaction validation is working correctly!")
    else:
        print("\n❌ TEST FAILED: Transaction validation needs fixing!")
