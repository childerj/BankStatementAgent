#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, fallback_bai2_conversion
from datetime import datetime
import json

def test_updates():
    """Test the updated File ID, transaction types, and reference numbers"""
    
    print("Testing updated BAI2 generation...")
    
    # Sample data for testing
    test_data = {
        "account_number": "1234567890",
        "opening_balance": {"amount": 1000.00},
        "closing_balance": {"amount": 1200.00},
        "transactions": [
            {
                "amount": "500.00",
                "description": "Commercial Deposit",
                "type": "deposit",
                "date": "2025-08-13"
            },
            {
                "amount": "-300.00",
                "description": "World Acceptance Corporation Payment",
                "type": "debit",
                "date": "2025-08-13"
            },
            {
                "amount": "-50.00",
                "description": "Check Return - NSF",
                "type": "debit",
                "date": "2025-08-13"
            }
        ],
        "ocr_text_lines": [
            "Account Number: 1234567890",
            "Opening Balance: $1,000.00",
            "Closing Balance: $1,200.00",
            "Commercial Deposit +$500.00",
            "World Acceptance Corporation Payment -$300.00"
        ]
    }
    
    filename = "test_updates.pdf"
    now = datetime.now()
    file_date = now.strftime('%y%m%d')
    file_time = now.strftime('%H%M')
    
    # Test comprehensive BAI2 generation
    print("\n1. Testing comprehensive BAI2 generation...")
    try:
        bai_content = convert_to_bai2(test_data, filename, None, "083000564")
        
        lines = bai_content.strip().split('\n')
        
        # Check File ID is dynamic (not hardcoded 31257)
        header_line = lines[0]
        print(f"Header line: {header_line}")
        
        if ",31257," in header_line:
            print("❌ FAIL: File ID is still hardcoded as 31257")
            return False
        else:
            # Extract file ID
            parts = header_line.split(',')
            file_id = parts[5]
            print(f"✅ PASS: File ID is now dynamic: {file_id}")
        
        # Check transaction type codes
        transaction_lines = [line for line in lines if line.startswith('16,')]
        print(f"Found {len(transaction_lines)} transaction lines:")
        
        for line in transaction_lines:
            print(f"  {line}")
            parts = line.split(',')
            txn_type = parts[1]
            if txn_type in ['301', '451', '555']:
                print(f"  ✅ PASS: Transaction type {txn_type} is correct")
            elif txn_type in ['174', '455', '400', '475']:
                print(f"  ❌ FAIL: Transaction type {txn_type} is old format (should be 301/451/555)")
                return False
            else:
                print(f"  ⚠️  WARNING: Unexpected transaction type {txn_type}")
        
        print("✅ Comprehensive BAI2 generation test passed!")
        
    except Exception as e:
        print(f"❌ FAIL: Comprehensive BAI2 generation failed: {e}")
        return False
    
    # Test fallback BAI2 conversion
    print("\n2. Testing fallback BAI2 conversion...")
    try:
        bai_content = fallback_bai2_conversion(test_data, filename, file_date, file_time, "083000564")
        
        lines = bai_content.strip().split('\n')
        
        # Check File ID is dynamic
        header_line = lines[0]
        print(f"Header line: {header_line}")
        
        if ",31257," in header_line:
            print("❌ FAIL: File ID is still hardcoded as 31257 in fallback")
            return False
        else:
            parts = header_line.split(',')
            file_id = parts[5]
            print(f"✅ PASS: Fallback File ID is now dynamic: {file_id}")
        
        # Check transaction type codes
        transaction_lines = [line for line in lines if line.startswith('16,')]
        print(f"Found {len(transaction_lines)} transaction lines:")
        
        for line in transaction_lines:
            print(f"  {line}")
            parts = line.split(',')
            txn_type = parts[1]
            if txn_type in ['301', '451', '555']:
                print(f"  ✅ PASS: Transaction type {txn_type} is correct")
            elif txn_type in ['174', '455', '400', '475']:
                print(f"  ❌ FAIL: Transaction type {txn_type} is old format (should be 301/451/555)")
                return False
        
        print("✅ Fallback BAI2 conversion test passed!")
        
    except Exception as e:
        print(f"❌ FAIL: Fallback BAI2 conversion failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED! Updates are working correctly.")
    
    # Show sample output
    print("\n📄 Sample BAI2 output:")
    print("=" * 50)
    print(bai_content[:500] + "..." if len(bai_content) > 500 else bai_content)
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_updates()
    sys.exit(0 if success else 1)
