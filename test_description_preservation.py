"""
Test that transaction descriptions from bank statements are preserved in BAI2 output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import (
    convert_to_bai2,
    fallback_bai2_conversion
)

def test_description_preservation():
    """Test that original descriptions are preserved"""
    print("🧪 Testing description preservation...")
    
    # Sample transaction data with original descriptions  
    transactions = [
        {
            "description": "ACH CREDIT PAYROLL DEPOSIT",
            "amount": 2500.00,
            "date": "08/13/2025",
            "routing_number": "083000564"
        },
        {
            "description": "WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV",
            "amount": -125.50,
            "date": "08/13/2025", 
            "routing_number": "083000564"
        },
        {
            "description": "ONLINE TRANSFER FROM SAVINGS ACCOUNT",
            "amount": 1000.00,
            "date": "08/13/2025",
            "routing_number": "083000564"
        },
        {
            "description": "CHECK #1234 TO LOCAL GROCERY STORE",
            "amount": -75.25,
            "date": "08/13/2025",
            "routing_number": "083000564"
        }
    ]
    
    # Test data structure matching function expectations
    data = {
        "account_number": "12345678",
        "opening_balance": {"amount": 1500.00},
        "closing_balance": {"amount": 4299.25},
        "statement_date": "08/13/2025",
        "transactions": transactions,
        "ocr_text_lines": [
            "ACCOUNT NUMBER: 12345678",
            "OPENING BALANCE: $1,500.00",
            "CLOSING BALANCE: $4,299.25",
            "ACH CREDIT PAYROLL DEPOSIT +$2,500.00",
            "WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV -$125.50",
            "ONLINE TRANSFER FROM SAVINGS ACCOUNT +$1,000.00", 
            "CHECK #1234 TO LOCAL GROCERY STORE -$75.25"
        ]
    }
    
    filename = "test_statement.pdf"
    
    # Test convert_to_bai2 first
    print(f"\n--- Testing convert_to_bai2 ---")
    
    try:
        bai2_content = convert_to_bai2(data, filename, None, "083000564")
        lines = bai2_content.split('\n')
        
        # Find transaction records (type 16)
        transaction_records = [line for line in lines if line.startswith('16,')]
        
        print(f"Found {len(transaction_records)} transaction records:")
        
        for i, record in enumerate(transaction_records):
            parts = record.split(',')
            if len(parts) >= 7:
                txn_type = parts[1]
                amount = parts[2] 
                text_desc = parts[6]
                
                # Find corresponding original transaction
                original_desc = transactions[i]["description"] if i < len(transactions) else "Unknown"
                
                print(f"  Transaction {i+1}:")
                print(f"    Type: {txn_type}")
                print(f"    Amount: {amount}")
                print(f"    Original Description: '{original_desc}'")
                print(f"    BAI2 Description: '{text_desc}'")
                
                # Check if description is preserved (truncated to 50 chars max)
                expected_desc = original_desc[:50]
                if text_desc not in [expected_desc, "Deposit"] and not text_desc.startswith(original_desc[:20]):
                    print(f"    ❌ MISMATCH: Expected something like '{expected_desc[:20]}...', got '{text_desc}'")
                else:
                    print(f"    ✅ Description preserved correctly")
            
            print()
        
        # Also check for 88 records (continuation records)
        continuation_records = [line for line in lines if line.startswith('88,')]
        if continuation_records:
            print(f"Found {len(continuation_records)} continuation records:")
            for record in continuation_records:
                parts = record.split(',')
                if len(parts) >= 2:
                    desc = parts[1]
                    print(f"  88 Record: '{desc}'")
    
    except Exception as e:
        print(f"❌ Error in convert_to_bai2: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Description preservation test completed!")

if __name__ == "__main__":
    test_description_preservation()
