#!/usr/bin/env python3
"""Analyze BAI files for Workday compatibility"""

def analyze_bai_workday_compatibility(file_path, file_name):
    """Analyze a BAI file for Workday upload compatibility"""
    
    print(f"\n🔍 Analyzing {file_name}:")
    print(f"   File: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
    except Exception as e:
        print(f"   ❌ Cannot read file: {e}")
        return False
    
    issues = []
    warnings = []
    
    # Check basic file structure
    if not lines:
        issues.append("File is empty")
        return False
    
    # Check for proper BAI format structure
    has_file_header = False
    has_group_header = False
    has_account_id = False
    has_transactions = False
    has_account_trailer = False
    has_group_trailer = False
    has_file_trailer = False
    
    transaction_count = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(',')
        if not parts:
            continue
            
        record_code = parts[0]
        
        # File Header (01)
        if record_code == '01':
            has_file_header = True
            if len(parts) < 9:
                issues.append(f"Line {i+1}: File header missing required fields")
            
        # Group Header (02)  
        elif record_code == '02':
            has_group_header = True
            if len(parts) < 6:
                issues.append(f"Line {i+1}: Group header missing required fields")
                
        # Account Identifier (03)
        elif record_code == '03':
            has_account_id = True
            if len(parts) < 6:
                issues.append(f"Line {i+1}: Account ID missing required fields")
            # Check account number format
            if len(parts) >= 2 and not parts[1]:
                warnings.append(f"Line {i+1}: Empty account number")
                
        # Transaction Detail (16)
        elif record_code == '16':
            has_transactions = True
            transaction_count += 1
            if len(parts) < 6:
                issues.append(f"Line {i+1}: Transaction missing required fields")
            # Check amount format
            if len(parts) >= 3:
                try:
                    amount = int(parts[2])
                    if amount < 0:
                        warnings.append(f"Line {i+1}: Negative amount found")
                except ValueError:
                    issues.append(f"Line {i+1}: Invalid amount format: {parts[2]}")
                    
        # Account Trailer (49)
        elif record_code == '49':
            has_account_trailer = True
            
        # Group Trailer (98)
        elif record_code == '98':
            has_group_trailer = True
            
        # File Trailer (99)
        elif record_code == '99':
            has_file_trailer = True
            
        # Check line length (BAI2 spec recommends max 80 chars)
        if len(line) > 80:
            warnings.append(f"Line {i+1}: Exceeds 80 character limit ({len(line)} chars)")
    
    # Check required structure
    if not has_file_header:
        issues.append("Missing File Header (01)")
    if not has_group_header:
        issues.append("Missing Group Header (02)")
    if not has_account_id:
        issues.append("Missing Account Identifier (03)")
    if not has_transactions:
        issues.append("No transactions found (16)")
    if not has_account_trailer:
        issues.append("Missing Account Trailer (49)")
    if not has_group_trailer:
        issues.append("Missing Group Trailer (98)")
    if not has_file_trailer:
        issues.append("Missing File Trailer (99)")
    
    # Check file encoding
    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        # Check for non-ASCII characters
        try:
            raw_content.decode('ascii')
        except UnicodeDecodeError:
            warnings.append("File contains non-ASCII characters (may cause issues)")
    except:
        pass
    
    # Check line endings
    if '\r\n' in content:
        line_ending = "CRLF (Windows)"
    elif '\n' in content:
        line_ending = "LF (Unix)"
    else:
        line_ending = "Unknown"
    
    # Print analysis results
    print(f"   📊 Structure Analysis:")
    print(f"      Total lines: {len(lines)}")
    print(f"      Transactions: {transaction_count}")
    print(f"      Line endings: {line_ending}")
    
    print(f"   ✅ Required Elements:")
    print(f"      File Header (01): {'✅' if has_file_header else '❌'}")
    print(f"      Group Header (02): {'✅' if has_group_header else '❌'}")
    print(f"      Account ID (03): {'✅' if has_account_id else '❌'}")
    print(f"      Transactions (16): {'✅' if has_transactions else '❌'}")
    print(f"      Account Trailer (49): {'✅' if has_account_trailer else '❌'}")
    print(f"      Group Trailer (98): {'✅' if has_group_trailer else '❌'}")
    print(f"      File Trailer (99): {'✅' if has_file_trailer else '❌'}")
    
    # Report issues
    if issues:
        print(f"   ❌ CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"      • {issue}")
    
    if warnings:
        print(f"   ⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"      • {warning}")
    
    # Workday compatibility assessment
    workday_compatible = len(issues) == 0
    
    if workday_compatible:
        if warnings:
            print(f"   🟡 WORKDAY COMPATIBLE (with warnings)")
        else:
            print(f"   ✅ WORKDAY COMPATIBLE")
    else:
        print(f"   ❌ NOT WORKDAY COMPATIBLE")
    
    return workday_compatible

def main():
    """Main analysis function"""
    
    print("🏢 BAI File Workday Compatibility Analysis")
    print("=" * 60)
    
    # File paths
    converted_file = r"C:\Users\jeff.childers\Downloads\Vera_baitest_20250728 converted.bai"
    original_file = r"C:\Users\jeff.childers\AppData\Local\Temp\Vera_baitest_20250728 (1) (2).bai"
    
    # Analyze both files
    converted_compatible = analyze_bai_workday_compatibility(converted_file, "CONVERTED FILE")
    original_compatible = analyze_bai_workday_compatibility(original_file, "ORIGINAL FILE")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📋 WORKDAY UPLOAD COMPATIBILITY SUMMARY:")
    print(f"   Converted File: {'✅ COMPATIBLE' if converted_compatible else '❌ NOT COMPATIBLE'}")
    print(f"   Original File:  {'✅ COMPATIBLE' if original_compatible else '❌ NOT COMPATIBLE'}")
    
    if converted_compatible and original_compatible:
        print(f"\n🎉 BOTH FILES CAN BE UPLOADED TO WORKDAY!")
        print(f"   • Both files follow proper BAI format")
        print(f"   • Both have required record types")
        print(f"   • Both should integrate successfully")
    elif converted_compatible:
        print(f"\n✅ CONVERTED FILE CAN BE UPLOADED TO WORKDAY")
        print(f"❌ ORIGINAL FILE HAS COMPATIBILITY ISSUES")
    elif original_compatible:
        print(f"\n✅ ORIGINAL FILE CAN BE UPLOADED TO WORKDAY")
        print(f"❌ CONVERTED FILE HAS COMPATIBILITY ISSUES")
    else:
        print(f"\n❌ NEITHER FILE IS COMPATIBLE WITH WORKDAY")
        print(f"   Both files need fixes before upload")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if converted_compatible:
        print(f"   • Use the CONVERTED file for Workday upload")
        print(f"   • It's cleaner and generated with proper formatting")
    print(f"   • Ensure your Workday BAI import job is configured correctly")
    print(f"   • Test with a small subset first")
    print(f"   • Verify account numbers match your Workday setup")

if __name__ == "__main__":
    main()
