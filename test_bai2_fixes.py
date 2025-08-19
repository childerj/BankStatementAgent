#!/usr/bin/env python3
"""
Test the updated BAI2 generation to fix key issues identified in comparison
"""

def test_fixed_bai2_generation():
    """Test BAI2 generation with fixes applied"""
    
    print("🔧 TESTING FIXED BAI2 GENERATION")
    print("=" * 60)
    
    # Simulate realistic transaction data matching the working file
    test_data = {
        "account_number": "2375133",
        "opening_balance": {
            "amount": 1498035,  # $14,980.35 in the working file
            "date": "2025-08-12"
        },
        "closing_balance": {
            "amount": 1498035,  # Same as opening in working file for first group
            "date": "2025-08-12"
        },
        "transactions": [
            {
                "date": "2025-08-12",
                "amount": 137.07,
                "description": "Commercial Deposit, Serial Num: 1470",
                "type": "deposit",
                "reference_number": "478980340"
            },
            {
                "date": "2025-08-12", 
                "amount": 325.10,
                "description": "Commercial Deposit, Serial Num: 1449",
                "type": "deposit",
                "reference_number": "478980341"
            },
            {
                "date": "2025-08-12",
                "amount": 1334.74,
                "description": "Commercial Deposit, Serial Num: 1486", 
                "type": "deposit",
                "reference_number": "478980342"
            },
            {
                "date": "2025-08-12",
                "amount": 2135.48,
                "description": "Commercial Deposit, Serial Num: 1459",
                "type": "deposit", 
                "reference_number": "478980343"
            },
            {
                "date": "2025-08-12",
                "amount": -185.00,
                "description": "RETURNED DEPOSITED ITEM Check 192",
                "type": "withdrawal",
                "reference_number": "478980344"
            },
            {
                "date": "2025-08-12",
                "amount": -69.00,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV",
                "type": "withdrawal",
                "reference_number": "478980346"
            },
            {
                "date": "2025-08-12",
                "amount": -92.00,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1479 NICHOLASVI",
                "type": "withdrawal",
                "reference_number": "478980347"
            },
            {
                "date": "2025-08-12",
                "amount": -333.60,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1486 GEORGETOWN",
                "type": "withdrawal",
                "reference_number": "478980348"
            },
            {
                "date": "2025-08-12",
                "amount": -343.19,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1470 PARIS,KY",
                "type": "withdrawal",
                "reference_number": "478980349"
            },
            {
                "date": "2025-08-12",
                "amount": -550.00,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1432 SHELBYVILL",
                "type": "withdrawal",
                "reference_number": "478980350"
            },
            {
                "date": "2025-08-12",
                "amount": -712.34,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1459 CYNTHIANA",
                "type": "withdrawal",
                "reference_number": "478980351"
            },
            {
                "date": "2025-08-12",
                "amount": -834.60,
                "description": "WORLD ACCEPTANCE CONC DEBIT 1449 WINCHESTER",
                "type": "withdrawal",
                "reference_number": "478980352"
            }
        ]
    }
    
    # Calculate expected totals
    total_deposits = sum(txn["amount"] for txn in test_data["transactions"] if txn["amount"] > 0)
    total_withdrawals = sum(abs(txn["amount"]) for txn in test_data["transactions"] if txn["amount"] < 0)
    
    print(f"📊 Test Data Summary:")
    print(f"   Opening Balance: ${test_data['opening_balance']['amount']:,.2f}")
    print(f"   Total Deposits: ${total_deposits:,.2f}")
    print(f"   Total Withdrawals: ${total_withdrawals:,.2f}")
    print(f"   Transactions: {len(test_data['transactions'])}")
    
    # Expected working file format
    expected_balance_codes = [
        "88,015,1498035,,Z/",  # Opening balance
        "88,040,,,Z/",         # Credits (should be empty in working file first group)
        "88,045,1498035,,Z/",  # Opening ledger balance
        "88,072,225962,,Z/",   # Total debits
        "88,074,000,,Z/",      # Rejected credits
        "88,100,393239,4,Z/",  # Credit summary
        "88,400,311973,8,Z/",  # Debit summary  
        "88,075,,,Z/",         # Rejected debits
        "88,079,,,Z/"          # Rejected transactions
    ]
    
    print(f"\n🎯 Expected Balance Codes (from working file):")
    for code in expected_balance_codes:
        print(f"   {code}")
    
    return test_data

if __name__ == "__main__":
    test_data = test_fixed_bai2_generation()
    
    print(f"\n💡 Key Fixes Needed:")
    print(f"1. ✅ Match transaction descriptions to working file format")
    print(f"2. ✅ Fix balance code 88,015 (opening balance)")
    print(f"3. ✅ Fix balance code 88,040 (should be empty in first group)")
    print(f"4. ✅ Fix balance code 88,045 (opening ledger balance)")
    print(f"5. ✅ Fix balance code 88,072 (total debits)")
    print(f"6. ✅ Fix control totals in account/group/file trailers")
    print(f"7. ✅ Use working file format for File ID (simpler: 168262 vs 202508131626)")
    
    print(f"\n🔧 Ready to apply fixes to convert_to_bai2 function...")
