#!/usr/bin/env python3

def analyze_bai2_file(filename):
    """Analyze the BAI2 file structure for Workday compatibility"""
    
    print("🔍 ANALYZING BAI2 FILE STRUCTURE")
    print("=" * 60)
    
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        print(f"📄 File: {filename}")
        print(f"📊 Total lines: {len(lines)}")
        print()
        
        # Parse key components
        file_header = None
        group_headers = []
        account_headers = []
        transactions = []
        group_trailers = []
        account_trailers = []
        file_trailer = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            # Parse record type (first 2 characters)
            record_type = line[:2]
            
            if record_type == "01":
                file_header = {"line": line_num, "content": line}
            elif record_type == "02":
                group_headers.append({"line": line_num, "content": line})
            elif record_type == "03":
                account_headers.append({"line": line_num, "content": line})
            elif record_type == "16":
                transactions.append({"line": line_num, "content": line})
            elif record_type == "88":
                # Transaction detail/continuation
                pass
            elif record_type == "49":
                account_trailers.append({"line": line_num, "content": line})
            elif record_type == "98":
                group_trailers.append({"line": line_num, "content": line})
            elif record_type == "99":
                file_trailer = {"line": line_num, "content": line}
        
        # Analysis
        print("📋 STRUCTURE ANALYSIS:")
        print("-" * 40)
        
        # File Header Analysis
        if file_header:
            parts = file_header["content"].split(",")
            sender_id = parts[1] if len(parts) > 1 else "MISSING"
            receiver_id = parts[2] if len(parts) > 2 else "MISSING"
            file_date = parts[3] if len(parts) > 3 else "MISSING"
            file_time = parts[4] if len(parts) > 4 else "MISSING"
            
            print(f"✅ File Header (01): Found")
            print(f"   Sender ID: {sender_id}")
            print(f"   Receiver ID: {receiver_id}")
            print(f"   File Date: {file_date}")
            print(f"   File Time: {file_time}")
        else:
            print("❌ File Header (01): MISSING")
        
        print()
        
        # Group Headers Analysis
        print(f"✅ Group Headers (02): {len(group_headers)} found")
        for i, gh in enumerate(group_headers):
            parts = gh["content"].split(",")
            originator_id = parts[1] if len(parts) > 1 else "MISSING"
            receiver_id = parts[2] if len(parts) > 2 else "MISSING"
            as_of_date = parts[4] if len(parts) > 4 else "MISSING"
            print(f"   Group {i+1}: Originator={originator_id}, AsOfDate={as_of_date}")
        
        print()
        
        # Account Headers Analysis
        print(f"✅ Account Headers (03): {len(account_headers)} found")
        for i, ah in enumerate(account_headers):
            parts = ah["content"].split(",")
            account_number = parts[1] if len(parts) > 1 else "MISSING"
            opening_balance = parts[3] if len(parts) > 3 else "MISSING"
            print(f"   Account {i+1}: Number={account_number}, Opening={opening_balance}")
        
        print()
        
        # Transaction Analysis
        print(f"✅ Transactions (16): {len(transactions)} found")
        deposit_count = 0
        debit_count = 0
        
        for tx in transactions:
            parts = tx["content"].split(",")
            type_code = parts[1] if len(parts) > 1 else ""
            if type_code == "174":  # Deposits
                deposit_count += 1
            elif type_code == "455":  # Debits
                debit_count += 1
        
        print(f"   Deposits (174): {deposit_count}")
        print(f"   Debits (455): {debit_count}")
        
        print()
        
        # Trailer Analysis
        print(f"✅ Account Trailers (49): {len(account_trailers)} found")
        print(f"✅ Group Trailers (98): {len(group_trailers)} found")
        if file_trailer:
            print(f"✅ File Trailer (99): Found")
        else:
            print("❌ File Trailer (99): MISSING")
        
        print()
        print("🎯 WORKDAY COMPATIBILITY CHECK:")
        print("-" * 40)
        
        issues = []
        
        # Check required components
        if not file_header:
            issues.append("Missing file header (01)")
        if len(group_headers) == 0:
            issues.append("Missing group headers (02)")
        if len(account_headers) == 0:
            issues.append("Missing account headers (03)")
        if not file_trailer:
            issues.append("Missing file trailer (99)")
        
        # Check balance
        if len(account_headers) != len(account_trailers):
            issues.append(f"Unbalanced accounts: {len(account_headers)} headers vs {len(account_trailers)} trailers")
        
        if len(group_headers) != len(group_trailers):
            issues.append(f"Unbalanced groups: {len(group_headers)} headers vs {len(group_trailers)} trailers")
        
        # Check account numbers
        for i, ah in enumerate(account_headers):
            parts = ah["content"].split(",")
            account_number = parts[1] if len(parts) > 1 else ""
            if not account_number or account_number in ["", "MISSING"]:
                issues.append(f"Account {i+1} has missing account number")
        
        if len(issues) == 0:
            print("✅ STRUCTURE LOOKS GOOD!")
            print("   All required components are present")
            print("   Headers and trailers are balanced")
            print("   Should upload successfully to Workday")
        else:
            print("⚠️  POTENTIAL ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")
        
        print()
        print("📈 SUMMARY:")
        print(f"   • {len(group_headers)} business days covered")
        print(f"   • {len(account_headers)} accounts")
        print(f"   • {len(transactions)} total transactions")
        print(f"   • {deposit_count} deposits, {debit_count} debits")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Error analyzing file: {str(e)}")
        return False

if __name__ == "__main__":
    # Analyze the uploaded BAI2 file
    filename = r"c:\Users\jeff.childers\Downloads\WACBAI2_20250812 (2).bai"
    is_valid = analyze_bai2_file(filename)
    
    if is_valid:
        print("\n🎉 RECOMMENDATION: File should upload successfully to Workday!")
    else:
        print("\n⚠️  RECOMMENDATION: Review and fix issues before uploading to Workday.")
