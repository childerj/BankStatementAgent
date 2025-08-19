"""
Test that all comment lines starting with '#' have been removed from BAI2 output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import (
    convert_to_bai2,
    fallback_bai2_conversion,
    create_error_bai2_file
)
from datetime import datetime

def test_no_comment_lines():
    """Test that no lines starting with '#' are present in BAI2 output"""
    print("🧪 Testing removal of all comment lines from BAI2 output...")
    
    # Test data structure
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
        }
    ]
    
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
            "WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV -$125.50"
        ]
    }
    
    filename = "test_statement.pdf"
    
    # Test 1: Main conversion function
    print(f"\n--- Testing convert_to_bai2 ---")
    
    try:
        bai2_content = convert_to_bai2(data, filename, None, "083000564")
        lines = bai2_content.split('\n')
        
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        
        print(f"Total lines in BAI2: {len(lines)}")
        print(f"Comment lines found: {len(comment_lines)}")
        
        if comment_lines:
            print("❌ FAILED: Found comment lines:")
            for line in comment_lines:
                print(f"  '{line}'")
        else:
            print("✅ SUCCESS: No comment lines found")
        
        # Show first few lines for verification
        print("\nFirst 10 lines of BAI2:")
        for i, line in enumerate(lines[:10]):
            if line.strip():
                print(f"  {i+1}: {line}")
    
    except Exception as e:
        print(f"❌ Error in convert_to_bai2: {e}")
    
    # Test 2: Fallback conversion function  
    print(f"\n--- Testing fallback_bai2_conversion ---")
    
    try:
        now = datetime.now()
        file_date = now.strftime("%y%m%d")
        file_time = now.strftime("%H%M")
        
        bai2_content = fallback_bai2_conversion(data, filename, file_date, file_time, "083000564")
        lines = bai2_content.split('\n')
        
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        
        print(f"Total lines in BAI2: {len(lines)}")
        print(f"Comment lines found: {len(comment_lines)}")
        
        if comment_lines:
            print("❌ FAILED: Found comment lines:")
            for line in comment_lines:
                print(f"  '{line}'")
        else:
            print("✅ SUCCESS: No comment lines found")
    
    except Exception as e:
        print(f"❌ Error in fallback_bai2_conversion: {e}")
    
    # Test 3: Error BAI2 file function
    print(f"\n--- Testing create_error_bai2_file ---")
    
    try:
        now = datetime.now()
        file_date = now.strftime("%y%m%d")
        file_time = now.strftime("%H%M")
        
        bai2_content = create_error_bai2_file("Test error message", filename, file_date, file_time)
        lines = bai2_content.split('\n')
        
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        
        print(f"Total lines in BAI2: {len(lines)}")
        print(f"Comment lines found: {len(comment_lines)}")
        
        if comment_lines:
            print("❌ FAILED: Found comment lines:")
            for line in comment_lines:
                print(f"  '{line}'")
        else:
            print("✅ SUCCESS: No comment lines found")
        
        # Show the error BAI2 content
        print("\nError BAI2 content:")
        for i, line in enumerate(lines):
            if line.strip():
                print(f"  {i+1}: {line}")
    
    except Exception as e:
        print(f"❌ Error in create_error_bai2_file: {e}")
    
    print("\n✅ Comment line removal test completed!")

if __name__ == "__main__":
    test_no_comment_lines()
