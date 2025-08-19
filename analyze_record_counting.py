#!/usr/bin/env python3

def analyze_bai2_record_counting():
    """Analyze the BAI2 file to understand the record counting issue"""
    
    print("🔍 ANALYZING BAI2 RECORD COUNTING ISSUE")
    print("=" * 60)
    
    filename = r"c:\Users\jeff.childers\Downloads\WACBAI2_20250812.bai"
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        print("📊 BAI2 Structure Analysis:")
        print("-" * 40)
        
        current_group = 0
        current_account = 0
        record_count_in_account = 0
        record_count_in_group = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            record_type = line[:2]
            parts = line.split(',')
            
            if record_type == "01":
                print(f"Line {line_num:3d}: File Header (01)")
                
            elif record_type == "02":
                current_group += 1
                record_count_in_group = 1  # Start counting from this record
                print(f"Line {line_num:3d}: Group Header (02) - Group {current_group}")
                
            elif record_type == "03":
                current_account += 1
                record_count_in_account = 1  # Start counting from this record
                print(f"Line {line_num:3d}: Account Header (03) - Account {current_account}")
                
            elif record_type == "16":
                record_count_in_account += 1
                record_count_in_group += 1
                print(f"Line {line_num:3d}: Transaction (16)")
                
            elif record_type == "88":
                record_count_in_account += 1
                record_count_in_group += 1
                print(f"Line {line_num:3d}: Transaction Detail (88)")
                
            elif record_type == "49":
                record_count_in_account += 1  # Include the trailer itself
                record_count_in_group += 1
                reported_count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                expected_count = record_count_in_account
                status = "✅" if reported_count == expected_count else "❌"
                
                print(f"Line {line_num:3d}: Account Trailer (49) {status}")
                print(f"         Reported: {reported_count} records, Expected: {expected_count}")
                if reported_count != expected_count:
                    print(f"         ⚠️  MISMATCH: Difference of {abs(reported_count - expected_count)}")
                
            elif record_type == "98":
                record_count_in_group += 1  # Include the trailer itself
                reported_count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                expected_count = record_count_in_group
                status = "✅" if reported_count == expected_count else "❌"
                
                print(f"Line {line_num:3d}: Group Trailer (98) {status}")
                print(f"         Reported: {reported_count} records, Expected: {expected_count}")
                if reported_count != expected_count:
                    print(f"         ⚠️  MISMATCH: Difference of {abs(reported_count - expected_count)}")
                print()
                
            elif record_type == "99":
                print(f"Line {line_num:3d}: File Trailer (99)")
        
        print("🎯 ANALYSIS SUMMARY:")
        print("-" * 40)
        print("The issue is in record counting logic:")
        print("1. Account record count should include:")
        print("   - Account header (03)")
        print("   - All transaction records (16)")
        print("   - All transaction detail records (88)")
        print("   - Account trailer (49) itself")
        print()
        print("2. Group record count should include:")
        print("   - Group header (02)")
        print("   - Account header (03)")
        print("   - All transaction records (16)")
        print("   - All transaction detail records (88)")
        print("   - Account trailer (49)")
        print("   - Group trailer (98) itself")
        print()
        print("🔧 SOLUTION: Fix the counting logic in the BAI2 generation code")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    analyze_bai2_record_counting()
