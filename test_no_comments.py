"""
Test that all comments (88 records) have been removed from BAI2 output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import (
    convert_to_bai2,
    fallback_bai2_conversion,
    create_error_bai2_file
)

def test_no_comments_in_bai2():
    """Test that no 88 records (comments) are in BAI2 output"""
    print("🧪 Testing that all comments have been removed from BAI2 output...")
    
    # Sample transaction data  
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
        }
    ]
    
    # Test data structure
    data = {
        "account_number": "12345678",
        "opening_balance": {"amount": 1500.00},
        "closing_balance": {"amount": 3875.50},
        "statement_date": "08/13/2025",
        "transactions": transactions,
        "ocr_text_lines": [
            "ACCOUNT NUMBER: 12345678",
            "OPENING BALANCE: $1,500.00",
            "CLOSING BALANCE: $3,875.50",
            "ACH CREDIT PAYROLL DEPOSIT +$2,500.00",
            "WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV -$125.50",
            "ONLINE TRANSFER FROM SAVINGS ACCOUNT +$1,000.00"
        ]
    }
    
    filename = "test_statement.pdf"
    
    # Test convert_to_bai2
    print(f"\n--- Testing convert_to_bai2 ---")
    
    try:
        bai2_content = convert_to_bai2(data, filename, None, "083000564")
        lines = bai2_content.split('\n')
        
        # Check for any 88 records
        comment_records = [line for line in lines if line.startswith('88,')]
        
        print(f"Total lines in BAI2 file: {len(lines)}")
        print(f"Comment records (88) found: {len(comment_records)}")
        
        if comment_records:
            print("❌ FOUND COMMENT RECORDS:")
            for record in comment_records:
                print(f"  {record}")
        else:
            print("✅ No comment records found - all comments successfully removed")
        
        # Show file structure
        record_types = {}
        for line in lines:
            if line.strip():
                record_type = line.split(',')[0]
                record_types[record_type] = record_types.get(record_type, 0) + 1
        
        print("\nFile structure (record types):")
        for record_type, count in sorted(record_types.items()):
            print(f"  {record_type}: {count} records")
    
    except Exception as e:
        print(f"❌ Error in convert_to_bai2: {e}")
        import traceback
        traceback.print_exc()
    
    # Test fallback_bai2_conversion
    print(f"\n--- Testing fallback_bai2_conversion ---")
    
    try:
        bai2_content = fallback_bai2_conversion(data, filename, "250813", "1200", "083000564")
        lines = bai2_content.split('\n')
        
        # Check for any 88 records
        comment_records = [line for line in lines if line.startswith('88,')]
        
        print(f"Total lines in BAI2 file: {len(lines)}")
        print(f"Comment records (88) found: {len(comment_records)}")
        
        if comment_records:
            print("❌ FOUND COMMENT RECORDS:")
            for record in comment_records:
                print(f"  {record}")
        else:
            print("✅ No comment records found - all comments successfully removed")
    
    except Exception as e:
        print(f"❌ Error in fallback_bai2_conversion: {e}")
        import traceback
        traceback.print_exc()
    
    # Test create_error_bai2_file
    print(f"\n--- Testing create_error_bai2_file ---")
    
    try:
        error_content = create_error_bai2_file("Test error message", filename, "250813", "1200")
        lines = error_content.split('\n')
        
        # Check for any 88 records
        comment_records = [line for line in lines if line.startswith('88,')]
        
        print(f"Total lines in error BAI2 file: {len(lines)}")
        print(f"Comment records (88) found: {len(comment_records)}")
        
        if comment_records:
            print("❌ FOUND COMMENT RECORDS:")
            for record in comment_records:
                print(f"  {record}")
        else:
            print("✅ No comment records found - all comments successfully removed")
    
    except Exception as e:
        print(f"❌ Error in create_error_bai2_file: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Comment removal test completed!")

if __name__ == "__main__":
    test_no_comments_in_bai2()
