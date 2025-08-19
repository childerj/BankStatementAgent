#!/usr/bin/env python3
"""
Analyze the ERROR BAI2 file structure to verify it's correctly formatted.
"""

def analyze_error_bai2():
    """Analyze the ERROR BAI2 file structure"""
    
    error_bai2 = """01,ERROR,WORKDAY,250813,2012,1,,,2/
02,ERROR,000000000,1,250813,,USD,2/
03,ERROR,,010,0,,Z/
49,0,1/
98,0,1,4/
99,0,1,6/"""

    lines = [line.strip() for line in error_bai2.split('\n') if line.strip()]
    
    print("🔍 ERROR BAI2 File Analysis")
    print("=" * 50)
    
    # Count records
    record_counts = {}
    total_records = len(lines)
    
    for i, line in enumerate(lines, 1):
        record_type = line.split(',')[0]
        if record_type not in record_counts:
            record_counts[record_type] = 0
        record_counts[record_type] += 1
        print(f"Line {i}: {record_type:2s} - {line}")
    
    print(f"\n📊 Record Type Summary:")
    print("-" * 30)
    for record_type, count in sorted(record_counts.items()):
        print(f"Record {record_type}: {count}")
    
    print(f"\nTotal Records: {total_records}")
    
    # Analyze record counting
    print(f"\n🔍 Record Count Analysis:")
    print("-" * 40)
    
    # Account section (only 03 record in error case)
    account_section = 1  # Just the 03 record
    print(f"Account section records (03 only): {account_section}")
    
    # Group section (02 + account section + 49)
    group_section = 1 + account_section + 1  # 02 + 03 + 49
    print(f"Group section records (02 + account + 49): {group_section}")
    
    # File section (all except 99)
    file_section = total_records - 1  # All except 99
    print(f"File section records (all except 99): {file_section}")
    
    # Extract actual counts from trailer records
    trailer_49 = lines[3].split(',')[2].rstrip('/')  # 49 record
    trailer_98 = lines[4].split(',')[3].rstrip('/')  # 98 record  
    trailer_99 = lines[5].split(',')[3].rstrip('/')  # 99 record
    
    print(f"\n📋 Actual Trailer Counts:")
    print("-" * 30)
    print(f"49 record shows: {trailer_49}")
    print(f"98 record shows: {trailer_98}")
    print(f"99 record shows: {trailer_99}")
    
    print(f"\n✅ Expected Counts:")
    print("-" * 30)
    print(f"49 should show: {account_section}")
    print(f"98 should show: {group_section}")
    print(f"99 should show: {file_section}")
    
    # Validation
    print(f"\n🎯 Validation:")
    print("-" * 20)
    
    success = True
    
    if str(trailer_49) == str(account_section):
        print(f"✅ 49 record count correct: {trailer_49}")
    else:
        print(f"❌ 49 record count wrong: {trailer_49} vs {account_section}")
        success = False
        
    if str(trailer_98) == str(group_section):
        print(f"✅ 98 record count correct: {trailer_98}")
    else:
        print(f"❌ 98 record count wrong: {trailer_98} vs {group_section}")
        success = False
        
    if str(trailer_99) == str(file_section):
        print(f"✅ 99 record count correct: {trailer_99}")
    else:
        print(f"❌ 99 record count wrong: {trailer_99} vs {file_section}")
        success = False
    
    print(f"\n📝 ERROR BAI2 Purpose:")
    print("-" * 40)
    print("✅ This is an ERROR file - indicates processing failed")
    print("✅ Contains minimal structure to meet BAI2 format requirements")
    print("✅ Uses 'ERROR' placeholders where data couldn't be extracted")
    print("✅ Prevents invalid BAI2 files from being generated")
    print("✅ Provides clear indication that manual review is needed")
    
    if success:
        print(f"\n🎉 ERROR BAI2 structure is CORRECT!")
        print("This file properly indicates a processing error while maintaining valid BAI2 format.")
    else:
        print(f"\n❌ ERROR BAI2 has structural issues!")
        
    return success

if __name__ == "__main__":
    analyze_error_bai2()
