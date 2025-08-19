#!/usr/bin/env python3
"""
Analyze the latest BAI2 file to verify the record counting fix
"""

# Read the latest BAI2 file content
bai2_content = """01,478980341,323809,250814,1930,202508141930,,,2/
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
49,1498035,21/
98,1498035,1,23/
99,1498035,1,24/"""

lines = bai2_content.strip().split('\n')

print("🔍 Analyzing the latest BAI2 file record counts...")
print(f"📄 Total lines: {len(lines)}")
print()

# Count different record types
record_types = {}
account_detail_records = 0  # 03 + 16 records
summary_records = 0  # 88 records

for i, line in enumerate(lines, 1):
    record_type = line.split(',')[0]
    record_types[record_type] = record_types.get(record_type, 0) + 1
    
    if record_type == '03':  # Account identifier
        account_detail_records += 1
    elif record_type == '88':  # Account summary
        summary_records += 1
    elif record_type == '16':  # Transaction detail
        account_detail_records += 1

print("📊 Record type breakdown:")
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
for record_type, count in sorted(record_types.items()):
    print(f"   {record_type} ({type_names.get(record_type, 'Unknown')}): {count}")

print()
print("🧮 Calculated counts:")
print(f"   Account records (03+16): {account_detail_records}")
print(f"   Summary records (88): {summary_records}")
total_account_records = account_detail_records + summary_records
print(f"   Total account records (03+16+88): {total_account_records}")

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

# Account trailer verification: should count all account records (03 + 16 + 88)
account_match = total_account_records == account_expected
print(f"   Account: Actual={total_account_records}, Expected={account_expected} {'✅' if account_match else '❌'}")

# Group trailer verification: should count group header + all account records + account trailer  
# Group records = 02 + (03+16+88) + 49 = 1 + total_account_records + 1
actual_group_records = 1 + total_account_records + 1
group_match = actual_group_records == group_expected
print(f"   Group: Actual={actual_group_records}, Expected={group_expected} {'✅' if group_match else '❌'}")

# File trailer verification: should count all records except file trailer
actual_file_records = len(lines) - 1  # All lines except file trailer (99)
file_match = actual_file_records == file_expected
print(f"   File: Actual={actual_file_records}, Expected={file_expected} {'✅' if file_match else '❌'}")

print()
if account_match and group_match and file_match:
    print("🎉 SUCCESS! All record counts are now CORRECT!")
    print("✅ The BAI2 record counting fix is working perfectly!")
    print("✅ The Azure Function is generating valid BAI2 files!")
    print("🚀 Ready for downstream BAI2toXML processing!")
else:
    print("❌ Some record counts are still incorrect")
    if not account_match:
        print(f"   ❌ Account count mismatch: Expected {account_expected}, got {total_account_records}")
    if not group_match:
        print(f"   ❌ Group count mismatch: Expected {group_expected}, got {actual_group_records}")  
    if not file_match:
        print(f"   ❌ File count mismatch: Expected {file_expected}, got {actual_file_records}")

print()
print("🔍 Detailed breakdown:")
print(f"   - Account identifier (03): {record_types.get('03', 0)}")
print(f"   - Transaction details (16): {record_types.get('16', 0)}")
print(f"   - Account summaries (88): {record_types.get('88', 0)}")
print(f"   - Total account records: {total_account_records}")
print(f"   - Group header (02): {record_types.get('02', 0)}")
print(f"   - Account trailer (49): {record_types.get('49', 0)}")
print(f"   - Total group records: {actual_group_records}")
print(f"   - All records except file trailer: {actual_file_records}")

# Show comparison with previous file
print()
print("📈 Improvement from previous file:")
print("   Previous file had:")
print("     - Account: 22 actual vs 21 expected ❌")
print("     - Group: 24 actual vs 23 expected ❌") 
print("     - File: 26 actual vs 25 expected ❌")
print("   Current file has:")
print(f"     - Account: {total_account_records} actual vs {account_expected} expected {'✅' if account_match else '❌'}")
print(f"     - Group: {actual_group_records} actual vs {group_expected} expected {'✅' if group_match else '❌'}")
print(f"     - File: {actual_file_records} actual vs {file_expected} expected {'✅' if file_match else '❌'}")
