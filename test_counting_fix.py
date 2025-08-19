#!/usr/bin/env python3
"""
Test the fixed BAI2 record counting logic locally
"""
import sys
import os

# Add the current directory to Python path to import function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2
from datetime import datetime

def test_record_counting():
    """Test BAI2 generation with mock data to verify record counting"""
    print("Testing BAI2 record counting fix...")
    print("=" * 50)
    
    # Create mock transaction data similar to what OpenAI would return
    mock_data = {
        'account_number': '2375133',
        'statement_period': '08/12/2025 - 08/13/2025',
        'opening_balance': 1498035,
        'closing_balance': 1498035,
        'transactions': [
            {
                'date': '08/12/2025',
                'amount': 137.07,
                'type': 'deposit',
                'description': 'Commercial Deposit, Serial Num: 1470',
                'reference_number': '478980340'
            },
            {
                'date': '08/12/2025',
                'amount': 325.10,
                'type': 'deposit', 
                'description': 'Commercial Deposit, Serial Num: 1449',
                'reference_number': '478980341'
            },
            {
                'date': '08/12/2025',
                'amount': -69.00,
                'type': 'withdrawal',
                'description': 'ACH Debit Received, WORLD ACCEPTANCE',
                'reference_number': '478980346'
            }
        ],
        'summary': {
            'total_deposits': 462.17,
            'total_withdrawals': 69.00,
            'transaction_count': 3
        },
        # Include the required fields for bank name detection
        'raw_fields': {},
        'ocr_text_lines': ['Stock Yards Bank & Trust', 'WACBAI2', 'Account: 2375133']
    }
    
    # Generate BAI2 file
    routing_number = "083000564"  # Stock Yards Bank routing number from OpenAI
    bai_content = convert_to_bai2(mock_data, "test.pdf", routing_number=routing_number)
    
    # Save to file for analysis
    with open("test_fixed_bai.bai", "w") as f:
        f.write(bai_content)
    
    print("✅ Generated test BAI2 file: test_fixed_bai.bai")
    print()
    
    # Analyze the generated file
    lines = [line.strip() for line in bai_content.strip().split('\n') if line.strip()]
    
    print("Generated BAI2 structure:")
    for i, line in enumerate(lines, 1):
        record_type = line.split(',')[0]
        print(f"{i:2d}: {record_type} - {line}")
    print()
    
    # Find trailer records and verify counts
    account_trailer = None
    group_trailer = None
    file_trailer = None
    
    file_header_idx = None
    group_header_idx = None
    account_header_idx = None
    account_trailer_idx = None
    group_trailer_idx = None
    file_trailer_idx = None
    
    for i, line in enumerate(lines):
        record_type = line.split(',')[0]
        if record_type == '01':
            file_header_idx = i
        elif record_type == '02':
            group_header_idx = i
        elif record_type == '03':
            account_header_idx = i
        elif record_type == '49':
            account_trailer_idx = i
            account_trailer = line
        elif record_type == '98':
            group_trailer_idx = i
            group_trailer = line
        elif record_type == '99':
            file_trailer_idx = i
            file_trailer = line
    
    # Verify record counts
    print("RECORD COUNT VERIFICATION:")
    print("-" * 30)
    
    # Account records (between 03 and 49)
    if account_header_idx is not None and account_trailer_idx is not None:
        account_records = lines[account_header_idx+1:account_trailer_idx]
        actual_account_count = len(account_records)
        expected_account_count = int(account_trailer.split(',')[2].rstrip('/'))
        
        print(f"Account records (between 03 and 49):")
        print(f"  Actual: {actual_account_count}")
        print(f"  Expected: {expected_account_count}")
        print(f"  Match: {'✅' if actual_account_count == expected_account_count else '❌'}")
        
        if actual_account_count != expected_account_count:
            print(f"  Record breakdown:")
            record_types = {}
            for line in account_records:
                rt = line.split(',')[0]
                record_types[rt] = record_types.get(rt, 0) + 1
            for rt, count in sorted(record_types.items()):
                print(f"    {rt}: {count} records")
    
    # Group records (between 02 and 98)
    if group_header_idx is not None and group_trailer_idx is not None:
        group_records = lines[group_header_idx+1:group_trailer_idx]
        actual_group_count = len(group_records)
        expected_group_count = int(group_trailer.split(',')[3].rstrip('/'))
        
        print(f"Group records (between 02 and 98):")
        print(f"  Actual: {actual_group_count}")
        print(f"  Expected: {expected_group_count}")
        print(f"  Match: {'✅' if actual_group_count == expected_group_count else '❌'}")
    
    # File records (between 01 and 99)
    if file_header_idx is not None and file_trailer_idx is not None:
        file_records = lines[file_header_idx+1:file_trailer_idx]
        actual_file_count = len(file_records)
        expected_file_count = int(file_trailer.split(',')[3].rstrip('/'))
        
        print(f"File records (between 01 and 99):")
        print(f"  Actual: {actual_file_count}")
        print(f"  Expected: {expected_file_count}")
        print(f"  Match: {'✅' if actual_file_count == expected_file_count else '❌'}")
    
    print()
    print("Trailer records:")
    print(f"  Account trailer (49): {account_trailer}")
    print(f"  Group trailer (98): {group_trailer}")
    print(f"  File trailer (99): {file_trailer}")
    
    return True

if __name__ == "__main__":
    test_record_counting()
