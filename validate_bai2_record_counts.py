#!/usr/bin/env python3
"""
Script to validate BAI2 file record counts and structure
"""

def analyze_bai2_file(file_path):
    """Analyze BAI2 file and validate record counts"""
    print(f"\n=== Analyzing BAI2 File: {file_path} ===")
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Strip whitespace and filter non-empty lines
        records = [line.strip() for line in lines if line.strip()]
        
        print(f"Total lines in file: {len(records)}")
        
        # Count different record types
        record_counts = {}
        detail_records = []
        
        for i, record in enumerate(records):
            if not record:
                continue
                
            # Get record type code (first two digits)
            if len(record) >= 2 and record[:2].isdigit():
                record_type = record[:2]
                record_counts[record_type] = record_counts.get(record_type, 0) + 1
                
                # Track detail records (16)
                if record_type == '16':
                    detail_records.append((i + 1, record))
            else:
                print(f"Warning: Invalid record format at line {i + 1}: {record}")
        
        print(f"\nRecord Type Counts:")
        for record_type, count in sorted(record_counts.items()):
            record_name = {
                '01': 'File Header',
                '02': 'Group Header', 
                '03': 'Account Identifier',
                '16': 'Transaction Detail',
                '49': 'Account Trailer',
                '88': 'Account Status',
                '98': 'Group Trailer',
                '99': 'File Trailer'
            }.get(record_type, f'Unknown ({record_type})')
            print(f"  {record_type} ({record_name}): {count}")
        
        # Validate key records
        print(f"\n=== Record Count Validation ===")
        
        # Find trailer records that contain counts
        group_trailer = None
        file_trailer = None
        account_trailer = None
        
        for record in records:
            if record.startswith('49,'):
                account_trailer = record
            elif record.startswith('98,'):
                group_trailer = record
            elif record.startswith('99,'):
                file_trailer = record
        
        # Validate account trailer (49 record)
        if account_trailer:
            parts = account_trailer.split(',')
            if len(parts) >= 3:
                try:
                    # Remove trailing '/' character if present
                    count_field = parts[2].rstrip('/')
                    reported_account_record_count = int(count_field)
                    # Account records = Account Identifier (03) + Status records (88) + Transaction Detail records (16)
                    actual_account_record_count = record_counts.get('03', 0) + record_counts.get('88', 0) + record_counts.get('16', 0)
                    print(f"Account Trailer (49): Reports {reported_account_record_count} account records")
                    print(f"Actual Account Records: {actual_account_record_count} (03: {record_counts.get('03', 0)}, 88: {record_counts.get('88', 0)}, 16: {record_counts.get('16', 0)})")
                    if reported_account_record_count == actual_account_record_count:
                        print("✅ Account trailer count MATCHES actual account records")
                    else:
                        print("❌ Account trailer count MISMATCH!")
                except ValueError:
                    print("❌ Invalid account record count in account trailer")
        
        # Validate group trailer (98 record)
        if group_trailer:
            parts = group_trailer.split(',')
            if len(parts) >= 3:
                try:
                    count_field = parts[2].rstrip('/')
                    reported_account_count = int(count_field)
                    actual_account_count = record_counts.get('03', 0)
                    print(f"Group Trailer (98): Reports {reported_account_count} accounts")
                    print(f"Actual Account Records (03): {actual_account_count}")
                    if reported_account_count == actual_account_count:
                        print("✅ Group trailer count MATCHES actual account records")
                    else:
                        print("❌ Group trailer count MISMATCH!")
                except ValueError:
                    print("❌ Invalid account count in group trailer")
        
        # Validate file trailer (99 record)
        if file_trailer:
            parts = file_trailer.split(',')
            if len(parts) >= 3:
                try:
                    count_field = parts[2].rstrip('/')
                    reported_group_count = int(count_field)
                    actual_group_count = record_counts.get('02', 0)
                    print(f"File Trailer (99): Reports {reported_group_count} groups")
                    print(f"Actual Group Records (02): {actual_group_count}")
                    if reported_group_count == actual_group_count:
                        print("✅ File trailer count MATCHES actual group records")
                    else:
                        print("❌ File trailer count MISMATCH!")
                except ValueError:
                    print("❌ Invalid group count in file trailer")
        
        # Show detail records for verification
        print(f"\n=== Detail Records (16) ===")
        for line_num, record in detail_records:
            print(f"Line {line_num}: {record}")
        
        # Check for truncation in descriptions
        print(f"\n=== Description Analysis ===")
        truncated_descriptions = []
        for line_num, record in detail_records:
            parts = record.split(',')
            if len(parts) >= 6:
                description = parts[5] if len(parts) > 5 else ""
                if description and len(description) >= 35:  # Check if close to truncation limit
                    truncated_descriptions.append((line_num, description))
        
        if truncated_descriptions:
            print("Potentially truncated descriptions found:")
            for line_num, desc in truncated_descriptions:
                print(f"  Line {line_num}: {desc}")
        else:
            print("✅ No obviously truncated descriptions detected")
        
        return {
            'total_records': len(records),
            'record_counts': record_counts,
            'detail_count': record_counts.get('16', 0),
            'validation_passed': True  # Will be set based on validation
        }
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return None

if __name__ == "__main__":
    # Analyze the attached BAI2 file
    bai2_file = r"c:\Users\jeff.childers\Downloads\WACBAI2_20250813_12.bai"
    
    print("BAI2 File Record Count Validation")
    print("=" * 50)
    
    result = analyze_bai2_file(bai2_file)
    
    if result:
        print(f"\n=== Summary ===")
        print(f"File analyzed successfully")
        print(f"Total records: {result['total_records']}")
        print(f"Detail records (16): {result['detail_count']}")
    else:
        print("Failed to analyze file")
