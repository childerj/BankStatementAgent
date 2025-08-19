#!/usr/bin/env python3
"""
Analyze the BAI2 file structure and record counts to identify the counting issue.
"""

def analyze_bai2_file():
    """Analyze the BAI2 file structure and counts"""
    
    bai2_content = """01,083000564,323809,250813,1858,202508131858,,,2/
02,323809,083000564,1,250812,,USD,2/
03,2375133,,010,,,Z/
88,015,1498035,,Z/
88,040,,,Z/
88,045,1498035,,Z/
88,072,311973,,Z/
88,074,000,,Z/
88,100,393239,4,Z/
88,400,311973,8,Z/
88,075,,,Z/
88,079,,,Z/
16,301,13707,Z,478980340,0000001470,Commercial Deposit, Serial Num: 1470, Ref Num: 478,/
16,301,32510,Z,478980341,0000001471,Commercial Deposit, Serial Num: 1449, Ref Num: 478,/
16,301,133474,Z,478980342,0000001472,Commercial Deposit, Serial Num: 1486, Ref Num: 478,/
16,301,213548,Z,478980343,0000001473,Commercial Deposit, Serial Num: 1459, Ref Num: 478,/
16,555,18500,Z,478980344,,Deposited Item Returned, Ref Num: 478980344, RETUR,/
16,451,6900,Z,478980346,,ACH Debit Received, Ref Num: 478980346, WORLD ACCE,/
16,451,9200,Z,478980347,,ACH Debit Received, Ref Num: 478980347, WORLD ACCE,/
16,451,33360,Z,478980348,,ACH Debit Received, Ref Num: 478980348, WORLD ACCE,/
16,451,34319,Z,478980349,,ACH Debit Received, Ref Num: 478980349, WORLD ACCE,/
16,451,55000,Z,478980350,,ACH Debit Received, Ref Num: 478980350, WORLD ACCE,/
16,451,71234,Z,478980351,,ACH Debit Received, Ref Num: 478980351, WORLD ACCE,/
16,451,83460,Z,478980352,,ACH Debit Received, Ref Num: 478980352, WORLD ACCE,/
49,1498035,23/
98,1498035,1,16/
99,1498035,1,18/"""

    lines = [line.strip() for line in bai2_content.split('\n') if line.strip()]
    
    print("🔍 BAI2 File Analysis")
    print("=" * 60)
    
    # Count different record types
    record_counts = {
        '01': 0,  # File header
        '02': 0,  # Group header  
        '03': 0,  # Account identifier
        '16': 0,  # Transaction detail
        '88': 0,  # Account balance
        '49': 0,  # Account trailer
        '98': 0,  # Group trailer
        '99': 0   # File trailer
    }
    
    total_records = 0
    
    for i, line in enumerate(lines, 1):
        record_type = line.split(',')[0]
        if record_type in record_counts:
            record_counts[record_type] += 1
        total_records += 1
        print(f"Line {i:2d}: {record_type:2s} - {line}")
    
    print("\n📊 Record Type Summary:")
    print("-" * 30)
    for record_type, count in record_counts.items():
        print(f"Record {record_type}: {count:2d}")
    
    print(f"\nTotal Records: {total_records}")
    
    print("\n🔍 Account Section Analysis:")
    print("-" * 40)
    
    # Account section records (between 03 and 49)
    account_records = 0
    in_account_section = False
    
    for line in lines:
        record_type = line.split(',')[0]
        if record_type == '03':
            in_account_section = True
            account_records += 1  # Include the 03 record
        elif record_type == '49':
            in_account_section = False
            # Don't count the 49 record in account section
        elif in_account_section:
            account_records += 1
    
    print(f"Account section records (03 + 88s + 16s): {account_records}")
    
    # Group section records (between 02 and 98)
    group_records = 0
    in_group_section = False
    
    for line in lines:
        record_type = line.split(',')[0]
        if record_type == '02':
            in_group_section = True
            group_records += 1  # Include the 02 record
        elif record_type == '98':
            in_group_section = False
            # Don't count the 98 record in group section
        elif in_group_section:
            group_records += 1
    
    print(f"Group section records (02 + account section + 49): {group_records}")
    
    # File records (all except 99)
    file_records = total_records - 1  # All except the 99 record
    print(f"File records (all except 99): {file_records}")
    
    print("\n❌ Current Trailer Values:")
    print("-" * 30)
    print("Line 25 (49 record): 49,1498035,23/")
    print("Line 26 (98 record): 98,1498035,1,16/")  
    print("Line 27 (99 record): 99,1498035,1,18/")
    
    print("\n✅ Expected Values:")
    print("-" * 30)
    print(f"49 record should show: {account_records} records")
    print(f"98 record should show: {group_records} records") 
    print(f"99 record should show: {file_records} records")
    
    print("\n🚨 Error Analysis:")
    print("-" * 30)
    print(f"98 record shows 16, Workday expects 25 (difference: {25-16})")
    print(f"99 record shows 18, Workday expects 27 (difference: {27-18})")
    
    return account_records, group_records, file_records

if __name__ == "__main__":
    analyze_bai2_file()
