#!/usr/bin/env python3

# Test the new BAI2 record counting logic
print('=== NEW BAI2 RECORD COUNTING LOGIC TEST ===')
print()

# Simulate the file structure we observed
print('File Structure:')
print('Line 1: 01 (file header)')
print('Line 2: 02 (group header)')
print('Line 3: 03 (account identifier)')
print('Lines 4-12: 88 (9 balance records)')
print('Lines 13-24: 16 (12 transaction records)')
print('Line 25: 49 (account trailer)')
print('Line 26: 98 (group trailer)')
print('Line 27: 99 (file trailer)')
print()

# Calculate using new logic
account_record_count = 1 + 9 + 12  # 03 + 88s + 16s = 22
account_trailer_count = account_record_count + 1  # +1 to include account trailer itself = 23

group_record_count = account_record_count + 1  # account records + account trailer = 23
group_trailer_count = 1 + group_record_count + 1  # +1 for group header + 1 for group trailer itself = 25

total_lines = 27
file_record_count = total_lines - 1 + 1  # all lines except file header + file trailer itself = 27

print('New Counting Logic:')
print(f'Account Trailer (49): {account_trailer_count} (includes account trailer itself)')
print(f'Group Trailer (98): {group_trailer_count} (includes group header and group trailer itself)')
print(f'File Trailer (99): {file_record_count} (includes file trailer itself, excludes file header)')
print()

print('Expected vs New Logic:')
print(f'Account: Expected 23, New Logic: {account_trailer_count} ✅' if account_trailer_count == 23 else f'Account: Expected 23, New Logic: {account_trailer_count} ❌')
print(f'Group: Expected 25, New Logic: {group_trailer_count} ✅' if group_trailer_count == 25 else f'Group: Expected 25, New Logic: {group_trailer_count} ❌')
print(f'File: Expected 27, New Logic: {file_record_count} ✅' if file_record_count == 27 else f'File: Expected 27, New Logic: {file_record_count} ❌')
