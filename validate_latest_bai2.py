#!/usr/bin/env python3

# Validate the latest BAI2 file record counts
with open('c:\\Users\\jeff.childers\\Downloads\\WACBAI2_20250813_15.bai', 'r') as f:
    lines = f.readlines()

print('=== BAI2 FILE ANALYSIS ===')
print(f'Total lines in file: {len(lines)}')
print()

print('All Records:')
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line:
        record_type = line[:2]
        print(f'Line {i:2d}: {record_type} - {line}')

print()
print('=== RECORD COUNTS ===')

# Count records for account trailer (49)
# Should count: 03, 88, 16 records
account_records = []
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line.startswith(('03', '88', '16')):
        account_records.append((i, line[:2]))

print(f'Account Records (03, 88, 16): {len(account_records)}')
for line_num, record_type in account_records:
    print(f'  Line {line_num}: {record_type}')

# Count records for group trailer (98) 
# Should count: 02, 03, 88, 16, 49 records
group_records = []
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line.startswith(('02', '03', '88', '16', '49')):
        group_records.append((i, line[:2]))

print(f'\nGroup Records (02, 03, 88, 16, 49): {len(group_records)}')
for line_num, record_type in group_records:
    print(f'  Line {line_num}: {record_type}')

# Count records for file trailer (99)
# Should count all records except 01 and 99
file_records = []
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line and not line.startswith(('01', '99')):
        file_records.append((i, line[:2]))

print(f'\nFile Records (all except 01, 99): {len(file_records)}')
for line_num, record_type in file_records:
    print(f'  Line {line_num}: {record_type}')

print()
print('=== TRAILER RECORDS ===')
for i, line in enumerate(lines, 1):
    line = line.strip()
    if line.startswith(('49', '98', '99')):
        parts = line.split(',')
        count = parts[2].rstrip('/') if len(parts) >= 3 else 'N/A'
        print(f'Line {i}: {line[:2]} - Count: {count}')

print()
print('=== EXPECTED vs ACTUAL ===')
print(f'Account Trailer (49): Expected 23, Actual {len(account_records)}')
print(f'Group Trailer (98): Expected 25, Actual {len(group_records)}') 
print(f'File Trailer (99): Expected 27, Actual {len(file_records)}')
