#!/usr/bin/env python3
"""
Test the corrected ERROR BAI2 file generation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import create_error_bai2_file

def test_error_bai2_generation():
    """Test the ERROR BAI2 file generation with correct record counts"""
    print("🧪 Testing Corrected ERROR BAI2 Generation")
    print("=" * 50)
    
    # Generate ERROR BAI2 file
    error_file = create_error_bai2_file(
        error_message="Test error - no routing number found",
        filename="test-file.pdf",
        file_date="250813",
        file_time="2030"
    )
    
    lines = [line.strip() for line in error_file.split('\n') if line.strip()]
    
    print(f"📄 Generated ERROR BAI2 ({len(lines)} lines):")
    print("-" * 40)
    
    for i, line in enumerate(lines, 1):
        record_type = line.split(',')[0]
        print(f"Line {i}: {record_type:2s} - {line}")
    
    # Analyze record counts
    print(f"\n🔍 Record Count Analysis:")
    print("-" * 30)
    
    # Account section: just the 03 record
    account_records = 1
    print(f"Account section (03 only): {account_records}")
    
    # Group section: 02 + account section + 49
    group_records = 1 + account_records + 1  # 02 + 03 + 49 = 3
    print(f"Group section (02 + account + 49): {group_records}")
    
    # File section: all except 99
    file_records = len(lines) - 1  # All except 99 = 5
    print(f"File section (all except 99): {file_records}")
    
    # Extract trailer counts
    trailer_49 = lines[3].split(',')[2].rstrip('/')
    trailer_98 = lines[4].split(',')[3].rstrip('/')
    trailer_99 = lines[5].split(',')[3].rstrip('/')
    
    print(f"\n📋 Trailer Record Counts:")
    print("-" * 30)
    print(f"49 record shows: {trailer_49} (expected: {account_records})")
    print(f"98 record shows: {trailer_98} (expected: {group_records})")
    print(f"99 record shows: {trailer_99} (expected: {file_records})")
    
    # Validation
    success = True
    
    if str(trailer_49) == str(account_records):
        print(f"✅ 49 record count correct")
    else:
        print(f"❌ 49 record count wrong")
        success = False
        
    if str(trailer_98) == str(group_records):
        print(f"✅ 98 record count correct")
    else:
        print(f"❌ 98 record count wrong")
        success = False
        
    if str(trailer_99) == str(file_records):
        print(f"✅ 99 record count correct")
    else:
        print(f"❌ 99 record count wrong")
        success = False
    
    if success:
        print(f"\n🎉 ERROR BAI2 record counts are now CORRECT!")
    else:
        print(f"\n❌ ERROR BAI2 still has issues!")
        
    return success, error_file

if __name__ == "__main__":
    test_error_bai2_generation()
