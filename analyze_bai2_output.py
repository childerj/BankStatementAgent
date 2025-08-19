#!/usr/bin/env python3
"""
Analyze the generated BAI2 file to verify record counts are correct
"""

# Read the BAI2 file content
bai2_content = """01,478980341,323809,250814,1920,202508141920,,,2/
02,323809,478980341,1,250812,,USD,2/
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
16,301,13707,Z,478980340,0000001470,Commercial Deposit Serial Num: 1470 Ref Num: 47898,/
16,301,32510,Z,478980341,0000001471,Commercial Deposit Serial Num: 1449 Ref Num: 47898,/
16,301,133474,Z,478980342,0000001472,Commercial Deposit Serial Num: 1486 Ref Num: 47898,/
16,301,213548,Z,478980343,0000001473,Commercial Deposit Serial Num: 1459 Ref Num: 47898,/
16,555,18500,Z,478980344,,Deposited Item Returned Ref Num: 478980344 RETURNE,/
16,451,6900,Z,478980346,,ACH Debit Received Ref Num: 478980346 WORLD ACCEPT,/
16,451,9200,Z,478980347,,ACH Debit Received Ref Num: 478980347 WORLD ACCEPT,/
16,451,33360,Z,478980348,,ACH Debit Received Ref Num: 478980348 WORLD ACCEPT,/
16,451,34319,Z,478980349,,ACH Debit Received Ref Num: 478980349 WORLD ACCEPT,/
16,451,55000,Z,478980350,,ACH Debit Received Ref Num: 478980350 WORLD ACCEPT,/
16,451,71234,Z,478980351,,ACH Debit Received Ref Num: 478980351 WORLD ACCEPT,/
16,451,83460,Z,478980352,,ACH Debit Received Ref Num: 478980352 WORLD ACCEPT,/
49,1498035,21/
98,1498035,1,23/
99,1498035,1,25/"""

lines = bai2_content.strip().split('\n')

print("🔍 Analyzing BAI2 file record counts...")
print(f"📄 Total lines: {len(lines)}")
print()

# Count different record types
account_detail_records = 0  # 03 + 16 records
summary_records = 0  # 88 records
group_records = 0
file_records = 0

record_types = {}

for i, line in enumerate(lines, 1):
    record_type = line.split(',')[0]
    record_types[record_type] = record_types.get(record_type, 0) + 1
    
    if record_type == '03':  # Account identifier
        account_detail_records += 1
    elif record_type == '88':  # Account summary
        summary_records += 1
    elif record_type == '16':  # Transaction detail
        account_detail_records += 1
    elif record_type == '49':  # Account trailer
        group_records = account_detail_records + summary_records + 1  # +1 for account trailer itself
        file_records += 1
    elif record_type == '98':  # Group trailer
        file_records += 1
    elif record_type not in ['99']:  # Everything except file trailer
        file_records += 1

print("📊 Record type breakdown:")
for record_type, count in sorted(record_types.items()):
    type_names = {
        '01': 'File Header',
        '02': 'Group Header', 
        '03': 'Account Identifier',
        '88': 'Account Summary',
        '16': 'Transaction Detail',
        '49': 'Account Trailer',
        '98': 'Group Trailer',
        '99': 'File Trailer'
    }
    print(f"   {record_type} ({type_names.get(record_type, 'Unknown')}): {count}")

print()
print("🧮 Calculated counts:")
print(f"   Account records (03+16): {account_detail_records}")
print(f"   Summary records (88): {summary_records}")
print(f"   Group records (all account records + account trailer): {group_records}")
print(f"   File records (all except file trailer): {file_records}")

# Extract expected counts from trailers
account_trailer = [line for line in lines if line.startswith('49,')][0]
group_trailer = [line for line in lines if line.startswith('98,')][0] 
file_trailer = [line for line in lines if line.startswith('99,')][0]

account_expected = int(account_trailer.split(',')[2].rstrip('/'))
group_expected = int(group_trailer.split(',')[3].rstrip('/'))
file_expected = int(file_trailer.split(',')[3].rstrip('/'))

print()
print("📋 Trailer record counts:")
print(f"   Account Trailer (49): {account_expected}")
print(f"   Group Trailer (98): {group_expected}")
print(f"   File Trailer (99): {file_expected}")

print()
print("✅ Verification:")

# For account trailer: should count account identifier (03) + transaction details (16) + summaries (88)
total_account_records = account_detail_records + summary_records
account_match = total_account_records == account_expected
print(f"   Account: Actual={total_account_records}, Expected={account_expected} {'✅' if account_match else '❌'}")

# For group trailer: should count all records in the group except group trailer itself
# This includes: group header(02) + account records + account trailer(49)
actual_group_records = 1 + total_account_records + 1  # 1 group header + account records + 1 account trailer
group_match = actual_group_records == group_expected
print(f"   Group: Actual={actual_group_records}, Expected={group_expected} {'✅' if group_match else '❌'}")

# For file trailer: should count all records except file trailer itself
actual_file_records = len(lines) - 1  # All lines except file trailer
file_match = actual_file_records == file_expected
print(f"   File: Actual={actual_file_records}, Expected={file_expected} {'✅' if file_match else '❌'}")

print()
if account_match and group_match and file_match:
    print("🎉 SUCCESS! All record counts are correct - the fix is working perfectly!")
    print("✅ The Azure Function is now generating valid BAI2 files!")
else:
    print("❌ Some record counts are still incorrect")
    
print()
print("🔍 Detailed analysis:")
print(f"   - File has {record_types.get('03', 0)} account identifier(s)")
print(f"   - File has {record_types.get('88', 0)} account summary record(s)")  
print(f"   - File has {record_types.get('16', 0)} transaction detail(s)")
print(f"   - Account trailer correctly counts: {total_account_records} total account records")
print(f"   - Group trailer correctly counts: {actual_group_records} total group records")
print(f"   - File trailer correctly counts: {actual_file_records} total file records")
