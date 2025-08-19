#!/usr/bin/env python3
"""Test the comprehensive BAI format generation"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, print_and_log

def test_comprehensive_bai():
    """Test the comprehensive BAI format with sample data"""
    
    print_and_log("🧪 Testing comprehensive BAI format generation...")
    
    # Sample data mimicking what OpenAI would extract
    test_data = {
        "account_number": "1035012999",
        "opening_balance": {"amount": 11270.62},
        "closing_balance": {"amount": 12204.62},
        "transactions": [
            {
                "date": "2025-07-21",
                "amount": 402.95,
                "description": "Commercial Deposit #413",
                "type": "deposit"
            },
            {
                "date": "2025-07-21", 
                "amount": 202.02,
                "description": "Commercial Deposit",
                "type": "deposit"
            },
            {
                "date": "2025-07-21",
                "amount": -220.78,
                "description": "World Acceptance Debit 0440 Marshall, TX",
                "type": "debit"
            },
            {
                "date": "2025-07-21",
                "amount": -140.68,
                "description": "World Acceptance Debit 0518 Palestine, TX", 
                "type": "debit"
            },
            {
                "date": "2025-07-22",
                "amount": 354.27,
                "description": "Commercial Deposit #414",
                "type": "deposit"
            },
            {
                "date": "2025-07-22",
                "amount": -202.02,
                "description": "World Acceptance Debit 0518 Palestine, TX",
                "type": "debit"
            }
        ]
    }
    
    # Generate BAI
    bai_content = convert_to_bai2(test_data, "test_statement")
    
    print_and_log("\n" + "="*60)
    print_and_log("📄 Generated Comprehensive BAI Content:")
    print_and_log("="*60)
    print(bai_content)
    print_and_log("="*60)
    
    # Analyze the structure
    lines = bai_content.strip().split('\n')
    print_and_log(f"📊 Structure Analysis:")
    print_and_log(f"   Total lines: {len(lines)}")
    
    # Count record types
    record_types = {}
    for line in lines:
        if line:
            record_type = line.split(',')[0]
            record_types[record_type] = record_types.get(record_type, 0) + 1
    
    print_and_log(f"   Record breakdown:")
    for record_type, count in sorted(record_types.items()):
        record_names = {
            '01': 'File Header',
            '02': 'Group Header', 
            '03': 'Account Identifier',
            '16': 'Transaction Detail',
            '49': 'Account Trailer',
            '88': 'Summary/Description',
            '98': 'Group Trailer',
            '99': 'File Trailer'
        }
        name = record_names.get(record_type, f'Unknown ({record_type})')
        print_and_log(f"     {record_type}: {count} ({name})")
    
    # Save to file for manual inspection
    output_file = "test_comprehensive_output.bai"
    with open(output_file, 'w') as f:
        f.write(bai_content)
    
    print_and_log(f"\n✅ Test complete! Output saved to: {output_file}")
    print_and_log("📋 You can compare this with Vera_baitest_20250728 (1) (1).bai")
    
    return bai_content

if __name__ == "__main__":
    test_comprehensive_bai()
