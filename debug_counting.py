#!/usr/bin/env python3

# Debug the current counting logic issue
print('=== DEBUGGING CURRENT BAI2 COUNTING ISSUE ===')
print()

# What we have in the actual file:
print('Actual File Structure (27 lines total):')
lines = [
    '01,478980341,323809,250818,1403,202508181403,,,2/',  # File header
    '02,323809,478980341,1,250812,,USD,2/',               # Group header  
    '03,2375133,,010,,,Z/',                               # Account identifier
    '88,015,1498035,,Z/',                                 # Balance record 1
    '88,040,,,Z/',                                        # Balance record 2
    '88,045,1498035,,Z/',                                 # Balance record 3
    '88,072,311973,,Z/',                                  # Balance record 4
    '88,074,000,,Z/',                                     # Balance record 5
    '88,100,393239,4,Z/',                                 # Balance record 6
    '88,400,311973,8,Z/',                                 # Balance record 7
    '88,075,,,Z/',                                        # Balance record 8
    '88,079,,,Z/',                                        # Balance record 9
    # 12 transaction records (16)
    '16,301,13707,Z,478980340,0000025816,Commercial Deposit Serial Num: 1470 Ref Num: 478980340 Deposit,/',
    '16,301,32510,Z,478980341,0000025817,Commercial Deposit Serial Num: 1449 Ref Num: 478980341 Deposit,/',
    '16,301,133474,Z,478980342,0000025818,Commercial Deposit Serial Num: 1486 Ref Num: 478980342 Deposit,/',
    '16,301,213548,Z,478980343,0000025819,Commercial Deposit Serial Num: 1459 Ref Num: 478980343 Deposit,/',
    '16,555,18500,Z,478980344,,Deposited Item Returned Ref Num: 478980344 RETURNED DEPOSITED ITEM Check 192,/',
    '16,451,6900,Z,478980346,,ACH Debit Received Ref Num: 478980346 WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV,/',
    '16,451,9200,Z,478980347,,ACH Debit Received Ref Num: 478980347 WORLD ACCEPTANCE CONC DEBIT 1479 NICHOLASVI,/',
    '16,451,33360,Z,478980348,,ACH Debit Received Ref Num: 478980348 WORLD ACCEPTANCE CONC DEBIT 1486 GEORGETOWN,/',
    '16,451,34319,Z,478980349,,ACH Debit Received Ref Num: 478980349 WORLD ACCEPTANCE CONC DEBIT 1470 PARIS, KY,/',
    '16,451,55000,Z,478980350,,ACH Debit Received Ref Num: 478980350 WORLD ACCEPTANCE CONC DEBIT 1432 SHELBYVILL,/',
    '16,451,71234,Z,478980351,,ACH Debit Received Ref Num: 478980351 WORLD ACCEPTANCE CONC DEBIT 1459 CYNTHIANA,/',
    '16,451,83460,Z,478980352,,ACH Debit Received Ref Num: 478980352 WORLD ACCEPTANCE CONC DEBIT 1449 WINCHESTER,/',
    '49,1498035,22/',                                     # Account trailer
    '98,1498035,24/',                                     # Group trailer  
    '99,1498035,26/'                                      # File trailer
]

for i, line in enumerate(lines, 1):
    record_type = line[:2]
    print(f'Line {i:2d}: {record_type}')

print()
print('Current BAI2 File Shows:')
print('Account Trailer (49): 22')
print('Group Trailer (98): 24') 
print('File Trailer (99): 26')
print()

print('Processor Expects:')
print('Account Trailer (49): 23')
print('Group Trailer (98): 25')
print('File Trailer (99): 27')
print()

print('Analysis:')
# Account records: 03 + 9x88 + 12x16 = 22
account_records = 1 + 9 + 12
print(f'Account records (03 + 88s + 16s): {account_records}')
print(f'Account trailer currently shows: 22')
print(f'Account trailer should show: 23 (account records + trailer itself)')
print()

# Group records: 02 + account_records + 49 = 24  
group_records = 1 + account_records + 1  # group header + account records + account trailer
print(f'Group records (02 + account records + 49): {group_records}')
print(f'Group trailer currently shows: 24')
print(f'Group trailer should show: 25 (group records + trailer itself)')
print()

# File records: all except 01 and 99 = 25, but 99 should count itself = 26
file_records_excluding_headers_and_trailers = 1 + 1 + account_records + 1 + 1  # 02 + 03 + account_records + 49 + 98
print(f'File records (02 + 03 + account records + 49 + 98): {file_records_excluding_headers_and_trailers}')
print(f'File trailer currently shows: 26')  
print(f'File trailer should show: 27 (file records + trailer itself)')

print()
print('THE ISSUE:')
print('The code logic is correct in theory, but there might be a bug in the implementation.')
print('Let me check what account_record_count actually contains when the trailer is generated...')
