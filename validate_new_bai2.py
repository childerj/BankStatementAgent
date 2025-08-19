#!/usr/bin/env python3
"""
Script to validate the new BAI2 file record counts
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
        
        # Show all records with line numbers
        print(f"\n=== All Records ===")
        for i, record in enumerate(records):
            print(f"Line {i+1:2}: {record}")
        
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
                    
                    # Check what the BAI2toXML processor expects (based on error message)
                    expected_by_processor = 23  # From the error message
                    print(f"Expected by BAI2toXML processor: {expected_by_processor}")
                    
                    if reported_account_record_count == expected_by_processor:
                        print("✅ Account trailer count MATCHES BAI2toXML processor expectation")
                    else:
                        print(f"❌ Account trailer count MISMATCH! Difference: {reported_account_record_count - expected_by_processor}")
                        
                except ValueError:
                    print("❌ Invalid account record count in account trailer")
        
        # Validate group trailer (98 record)
        if group_trailer:
            parts = group_trailer.split(',')
            if len(parts) >= 4:
                try:
                    count_field = parts[3].rstrip('/')  # Group record count is 4th field
                    reported_group_record_count = int(count_field)
                    
                    # Calculate actual group records
                    actual_group_record_count = record_counts.get('02', 0) + record_counts.get('03', 0) + record_counts.get('88', 0) + record_counts.get('16', 0) + record_counts.get('49', 0)
                    print(f"Group Trailer (98): Reports {reported_group_record_count} group records")
                    print(f"Actual Group Records: {actual_group_record_count}")
                    
                    # Check what the BAI2toXML processor expects
                    expected_by_processor = 25  # From the error message
                    print(f"Expected by BAI2toXML processor: {expected_by_processor}")
                    
                    if reported_group_record_count == expected_by_processor:
                        print("✅ Group trailer count MATCHES BAI2toXML processor expectation")
                    else:
                        print(f"❌ Group trailer count MISMATCH! Difference: {reported_group_record_count - expected_by_processor}")
                        
                except ValueError:
                    print("❌ Invalid group record count in group trailer")
        
        # Validate file trailer (99 record)
        if file_trailer:
            parts = file_trailer.split(',')
            if len(parts) >= 4:
                try:
                    count_field = parts[3].rstrip('/')  # File record count is 4th field
                    reported_file_record_count = int(count_field)
                    
                    # File records = all records except file trailer itself
                    actual_file_record_count = len(records) - 1
                    print(f"File Trailer (99): Reports {reported_file_record_count} file records")
                    print(f"Actual File Records: {actual_file_record_count} (total {len(records)} - 1)")
                    
                    # Check what the BAI2toXML processor expects
                    expected_by_processor = 27  # From the error message
                    print(f"Expected by BAI2toXML processor: {expected_by_processor}")
                    
                    if reported_file_record_count == expected_by_processor:
                        print("✅ File trailer count MATCHES BAI2toXML processor expectation")
                    else:
                        print(f"❌ File trailer count MISMATCH! Difference: {reported_file_record_count - expected_by_processor}")
                        
                except ValueError:
                    print("❌ Invalid file record count in file trailer")
        
        return {
            'total_records': len(records),
            'record_counts': record_counts,
        }
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    # Check if file path is provided as argument
    if len(sys.argv) > 1:
        bai2_file = sys.argv[1]
    else:
        bai2_file = r"c:\Users\jeff.childers\Downloads\test-fixed-record-counting.bai"
    
    print("BAI2 File Record Count Validation - New File")
    print("=" * 60)
    
    result = analyze_bai2_file(bai2_file)
    
    if result:
        print(f"\n=== Summary ===")
        print(f"File analyzed successfully")
        print(f"Total records: {result['total_records']}")
    else:
        print("Failed to analyze file")
