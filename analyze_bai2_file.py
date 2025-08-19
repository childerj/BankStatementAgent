#!/usr/bin/env python3
"""
Analyze BAI2 file for correctness
"""

def analyze_bai2_file(file_path):
    """Analyze a BAI2 file for format correctness"""
    print(f"🔍 Analyzing BAI2 file: {file_path}")
    print("=" * 60)
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Remove trailing newlines and split by commas
    records = []
    for line in lines:
        line = line.strip()
        if line:
            records.append(line.split(','))
    
    print(f"📊 Total lines/records: {len(records)}")
    
    # Analyze each record type
    record_counts = {}
    errors = []
    
    for i, record in enumerate(records, 1):
        if not record or len(record) < 2:
            errors.append(f"Line {i}: Invalid record format")
            continue
            
        record_type = record[0]
        record_counts[record_type] = record_counts.get(record_type, 0) + 1
        
        # Validate specific record types
        if record_type == '01':  # File Header
            if len(record) < 8:
                errors.append(f"Line {i}: File header missing required fields")
            print(f"📁 File Header: Sender ID={record[1]}, Receiver ID={record[2]}, File Date={record[3]}")
            
        elif record_type == '02':  # Group Header
            if len(record) < 7:
                errors.append(f"Line {i}: Group header missing required fields")
            print(f"🏦 Group Header: Bank={record[1]}, Account={record[2]}, Group Status={record[3]}")
            
        elif record_type == '03':  # Account Header
            if len(record) < 6:
                errors.append(f"Line {i}: Account header missing required fields")
            print(f"💳 Account Header: Customer Account={record[1]}, Currency={record[2]}")
            
        elif record_type == '16':  # Transaction Detail
            if len(record) < 6:
                errors.append(f"Line {i}: Transaction detail missing required fields")
            # Don't print all transactions, just count them
            
        elif record_type == '88':  # Account Summary
            if len(record) < 4:
                errors.append(f"Line {i}: Account summary missing required fields")
            # Print summary info
            if len(record) >= 4:
                summary_type = record[1]
                amount = record[2] if len(record) > 2 else "N/A"
                print(f"📋 Account Summary: Type={summary_type}, Amount={amount}")
                
        elif record_type == '49':  # Account Trailer
            if len(record) < 3:
                errors.append(f"Line {i}: Account trailer missing required fields")
            print(f"✅ Account Trailer: Control Total={record[1]}, Record Count={record[2]}")
            
        elif record_type == '98':  # Group Trailer
            if len(record) < 4:
                errors.append(f"Line {i}: Group trailer missing required fields")
            print(f"✅ Group Trailer: Control Total={record[1]}, Account Count={record[2]}, Record Count={record[3]}")
            
        elif record_type == '99':  # File Trailer
            if len(record) < 4:
                errors.append(f"Line {i}: File trailer missing required fields")
            print(f"✅ File Trailer: Control Total={record[1]}, Group Count={record[2]}, Record Count={record[3]}")
    
    print("\n📊 Record Type Summary:")
    print("-" * 30)
    for record_type, count in sorted(record_counts.items()):
        type_names = {
            '01': 'File Header',
            '02': 'Group Header', 
            '03': 'Account Header',
            '16': 'Transaction Detail',
            '88': 'Account Summary',
            '49': 'Account Trailer',
            '98': 'Group Trailer',
            '99': 'File Trailer'
        }
        name = type_names.get(record_type, f'Unknown ({record_type})')
        print(f"  {record_type}: {count:3d} - {name}")
    
    # Validate record structure
    print(f"\n🔍 Structure Validation:")
    print("-" * 30)
    
    # Check for required records
    required_records = ['01', '02', '03', '49', '98', '99']
    for req_type in required_records:
        if req_type not in record_counts:
            errors.append(f"Missing required record type: {req_type}")
        elif record_counts[req_type] != 1:
            errors.append(f"Expected exactly 1 {req_type} record, found {record_counts[req_type]}")
    
    # Validate transaction counts
    transaction_count = record_counts.get('16', 0)
    summary_count = record_counts.get('88', 0)
    
    print(f"  Transactions (16): {transaction_count}")
    print(f"  Summaries (88): {summary_count}")
    
    # Check trailer record counts
    if '49' in record_counts and len(records) > 0:
        for record in records:
            if record[0] == '49' and len(record) >= 3:
                reported_count = record[2]
                print(f"  Account Trailer reports: {reported_count} records")
                
    if '98' in record_counts and len(records) > 0:
        for record in records:
            if record[0] == '98' and len(record) >= 4:
                reported_count = record[3]
                print(f"  Group Trailer reports: {reported_count} records")
                
    if '99' in record_counts and len(records) > 0:
        for record in records:
            if record[0] == '99' and len(record) >= 4:
                reported_count = record[3]
                print(f"  File Trailer reports: {reported_count} records")
                print(f"  Actual total records: {len(records)}")
    
    # Report errors
    if errors:
        print(f"\n❌ Errors Found ({len(errors)}):")
        print("-" * 30)
        for error in errors:
            print(f"  • {error}")
    else:
        print(f"\n✅ No structural errors found!")
    
    print(f"\n{'='*60}")
    return len(errors) == 0

if __name__ == "__main__":
    # Analyze the downloaded BAI2 file
    file_path = r"c:\Users\jeff.childers\Downloads\prosperity-monitor-1755176613.bai"
    is_valid = analyze_bai2_file(file_path)
    
    if is_valid:
        print("🎉 BAI2 file appears to be structurally correct!")
    else:
        print("⚠️  BAI2 file has structural issues that need attention.")
