#!/usr/bin/env python3
"""
Test the BAI2 record counting logic to ensure trailer records have correct counts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2

def test_record_counting():
    """Test BAI2 record counting logic"""
    print("🧪 Testing BAI2 Record Counting Logic")
    print("=" * 60)
    
    # Create test data similar to the working file
    test_data = {
        "ocr_text_lines": [
            "STOCKYARDS EXCHANGE BANK",
            "2375 WEST AIRLINE ROAD",
            "Routing Number: 083000564",
            "Account Number: 2375133",
            "Statement Period: 08/12/2025 - 08/12/2025",
            "Beginning Balance: $1,186,062.00",
            "Ending Balance: $1,498,035.00",
            "08/12/2025    Commercial Deposit         $13,707.00",
            "08/12/2025    Commercial Deposit         $32,510.00", 
            "08/12/2025    Commercial Deposit         $133,474.00",
            "08/12/2025    Commercial Deposit         $213,548.00",
            "08/12/2025    Deposited Item Returned    -$18,500.00",
            "08/12/2025    ACH Debit Received         -$6,900.00",
            "08/12/2025    ACH Debit Received         -$9,200.00",
            "08/12/2025    ACH Debit Received         -$33,360.00",
            "08/12/2025    ACH Debit Received         -$34,319.00",
            "08/12/2025    ACH Debit Received         -$55,000.00",
            "08/12/2025    ACH Debit Received         -$71,234.00",
            "08/12/2025    ACH Debit Received         -$83,460.00"
        ],
        "raw_fields": {},
        "bank_data": {
            "transactions": [
                {"date": "2025-08-12", "description": "Commercial Deposit", "amount": 13707.00, "type": "credit"},
                {"date": "2025-08-12", "description": "Commercial Deposit", "amount": 32510.00, "type": "credit"},
                {"date": "2025-08-12", "description": "Commercial Deposit", "amount": 133474.00, "type": "credit"},
                {"date": "2025-08-12", "description": "Commercial Deposit", "amount": 213548.00, "type": "credit"},
                {"date": "2025-08-12", "description": "Deposited Item Returned", "amount": -18500.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -6900.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -9200.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -33360.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -34319.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -55000.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -71234.00, "type": "debit"},
                {"date": "2025-08-12", "description": "ACH Debit Received", "amount": -83460.00, "type": "debit"}
            ],
            "beginning_balance": 1186062.00,
            "ending_balance": 1498035.00
        }
    }
    
    print("📋 Input Summary:")
    print(f"  💰 Beginning Balance: ${test_data['bank_data']['beginning_balance']:,.2f}")
    print(f"  💰 Ending Balance: ${test_data['bank_data']['ending_balance']:,.2f}")
    print(f"  📊 Transactions: {len(test_data['bank_data']['transactions'])}")
    
    print("\n🔄 Generating BAI2...")
    
    result = convert_to_bai2(
        data=test_data,
        filename="test-stockyards.pdf"
    )
    
    if result:
        lines = [line.strip() for line in result.split('\n') if line.strip()]
        
        print(f"\n📄 Generated BAI2 ({len(lines)} lines):")
        print("=" * 50)
        
        # Analyze record structure
        record_counts = {}
        account_section_records = 0
        group_section_records = 0
        total_records = len(lines)
        
        in_account_section = False
        in_group_section = False
        
        for i, line in enumerate(lines, 1):
            record_type = line.split(',')[0]
            
            # Count record types
            if record_type not in record_counts:
                record_counts[record_type] = 0
            record_counts[record_type] += 1
            
            # Track account section (03 until 49, exclusive)
            if record_type == '03':
                in_account_section = True
                account_section_records += 1
            elif record_type == '49':
                in_account_section = False
            elif in_account_section:
                account_section_records += 1
            
            # Track group section (02 until 98, exclusive)
            if record_type == '02':
                in_group_section = True 
                group_section_records += 1
            elif record_type == '98':
                in_group_section = False
            elif in_group_section:
                group_section_records += 1
                
            print(f"Line {i:2d}: {line}")
        
        print(f"\n📊 Record Analysis:")
        print("-" * 30)
        for record_type, count in sorted(record_counts.items()):
            print(f"Record {record_type}: {count:2d}")
        
        print(f"\nAccount section records: {account_section_records}")
        print(f"Group section records: {group_section_records}")
        print(f"Total records: {total_records}")
        
        # Extract trailer values
        trailer_49 = None
        trailer_98 = None
        trailer_99 = None
        
        for line in lines:
            if line.startswith('49,'):
                trailer_49 = line.split(',')[2].rstrip('/')
            elif line.startswith('98,'):
                trailer_98 = line.split(',')[3].rstrip('/')
            elif line.startswith('99,'):
                trailer_99 = line.split(',')[3].rstrip('/')
        
        print(f"\n📋 Trailer Record Counts:")
        print("-" * 30)
        print(f"49 record count: {trailer_49}")
        print(f"98 record count: {trailer_98}")
        print(f"99 record count: {trailer_99}")
        
        print(f"\n✅ Expected Values:")
        print("-" * 30)
        print(f"49 should be: {account_section_records} (account section records)")
        print(f"98 should be: {group_section_records} (group section records)")
        print(f"99 should be: {total_records - 1} (all records except 99)")
        
        # Validation
        success = True
        if str(trailer_49) != str(account_section_records):
            print(f"❌ 49 record count mismatch: {trailer_49} vs {account_section_records}")
            success = False
        else:
            print(f"✅ 49 record count correct: {trailer_49}")
            
        if str(trailer_98) != str(group_section_records):
            print(f"❌ 98 record count mismatch: {trailer_98} vs {group_section_records}")
            success = False
        else:
            print(f"✅ 98 record count correct: {trailer_98}")
            
        if str(trailer_99) != str(total_records - 1):
            print(f"❌ 99 record count mismatch: {trailer_99} vs {total_records - 1}")
            success = False
        else:
            print(f"✅ 99 record count correct: {trailer_99}")
        
        if success:
            print(f"\n🎉 All record counts are correct!")
        else:
            print(f"\n❌ Record count issues found!")
            
        return success
    else:
        print("❌ No result returned")
        return False

if __name__ == "__main__":
    test_record_counting()
