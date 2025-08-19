#!/usr/bin/env python3
"""
Compare working BAI2 file with generated BAI2 file to identify differences
"""

def parse_bai2_file(content):
    """Parse BAI2 file into structured data for comparison"""
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    
    parsed = {
        'file_header': None,
        'groups': [],
        'file_trailer': None
    }
    
    current_group = None
    current_account = None
    
    for line in lines:
        if line.startswith('01,'):  # File header
            parsed['file_header'] = line
        elif line.startswith('02,'):  # Group header
            if current_group:
                parsed['groups'].append(current_group)
            current_group = {
                'header': line,
                'accounts': [],
                'trailer': None
            }
        elif line.startswith('03,'):  # Account identifier
            if current_account:
                current_group['accounts'].append(current_account)
            current_account = {
                'identifier': line,
                'summary_records': [],
                'transactions': [],
                'trailer': None
            }
        elif line.startswith('88,'):  # Account summary
            if current_account:
                current_account['summary_records'].append(line)
        elif line.startswith('16,'):  # Transaction detail
            if current_account:
                current_account['transactions'].append(line)
        elif line.startswith('49,'):  # Account trailer
            if current_account:
                current_account['trailer'] = line
                current_group['accounts'].append(current_account)
                current_account = None
        elif line.startswith('98,'):  # Group trailer
            if current_group:
                current_group['trailer'] = line
        elif line.startswith('99,'):  # File trailer
            parsed['file_trailer'] = line
    
    # Handle any remaining items
    if current_account:
        current_group['accounts'].append(current_account)
    if current_group:
        parsed['groups'].append(current_group)
    
    return parsed

def compare_bai2_structures(working_content, generated_content):
    """Compare two BAI2 files and identify differences"""
    
    print("🔍 DETAILED BAI2 FILE COMPARISON")
    print("=" * 80)
    
    # Parse both files
    working = parse_bai2_file(working_content)
    generated = parse_bai2_file(generated_content)
    
    print("\n📊 STRUCTURE OVERVIEW:")
    print(f"Working file - Groups: {len(working['groups'])}")
    print(f"Generated file - Groups: {len(generated['groups'])}")
    
    # Compare file headers
    print("\n📋 FILE HEADERS:")
    print(f"Working:   {working['file_header']}")
    print(f"Generated: {generated['file_header']}")
    
    if working['file_header'] != generated['file_header']:
        print("❌ FILE HEADERS DIFFER")
        # Parse header components
        w_parts = working['file_header'].split(',')
        g_parts = generated['file_header'].split(',')
        for i, (w, g) in enumerate(zip(w_parts, g_parts)):
            if w != g:
                labels = ['Record Type', 'Originator ID', 'Receiver ID', 'Date', 'Time', 'File ID', 'Physical Record Length', 'Block Size', 'Version']
                label = labels[i] if i < len(labels) else f'Field {i}'
                print(f"  - {label}: Working='{w}' vs Generated='{g}'")
    else:
        print("✅ FILE HEADERS MATCH")
    
    # Compare groups
    for i, (w_group, g_group) in enumerate(zip(working['groups'], generated['groups'])):
        print(f"\n📂 GROUP {i+1} COMPARISON:")
        
        # Group headers
        print(f"Working Header:   {w_group['header']}")
        print(f"Generated Header: {g_group['header']}")
        
        if w_group['header'] != g_group['header']:
            print("❌ GROUP HEADERS DIFFER")
        else:
            print("✅ GROUP HEADERS MATCH")
        
        # Group trailers
        print(f"Working Trailer:   {w_group['trailer']}")
        print(f"Generated Trailer: {g_group['trailer']}")
        
        if w_group['trailer'] != g_group['trailer']:
            print("❌ GROUP TRAILERS DIFFER")
        else:
            print("✅ GROUP TRAILERS MATCH")
        
        # Compare accounts
        print(f"  Accounts: Working={len(w_group['accounts'])}, Generated={len(g_group['accounts'])}")
        
        for j, (w_acc, g_acc) in enumerate(zip(w_group['accounts'], g_group['accounts'])):
            print(f"\n  🏦 ACCOUNT {j+1}:")
            
            # Account identifiers
            print(f"    Working ID:   {w_acc['identifier']}")
            print(f"    Generated ID: {g_acc['identifier']}")
            
            if w_acc['identifier'] != g_acc['identifier']:
                print("    ❌ ACCOUNT IDENTIFIERS DIFFER")
            else:
                print("    ✅ ACCOUNT IDENTIFIERS MATCH")
            
            # Summary records (88 records)
            print(f"    Summary Records: Working={len(w_acc['summary_records'])}, Generated={len(g_acc['summary_records'])}")
            
            if len(w_acc['summary_records']) != len(g_acc['summary_records']):
                print(f"    ❌ DIFFERENT NUMBER OF SUMMARY RECORDS")
                print(f"    Working has {len(w_acc['summary_records'])}, Generated has {len(g_acc['summary_records'])}")
            
            # Show all summary records for comparison
            max_summaries = max(len(w_acc['summary_records']), len(g_acc['summary_records']))
            for k in range(max_summaries):
                w_summary = w_acc['summary_records'][k] if k < len(w_acc['summary_records']) else "MISSING"
                g_summary = g_acc['summary_records'][k] if k < len(g_acc['summary_records']) else "MISSING"
                
                print(f"    Summary {k+1}:")
                print(f"      Working:   {w_summary}")
                print(f"      Generated: {g_summary}")
                
                if w_summary != g_summary:
                    print(f"      ❌ SUMMARY RECORD {k+1} DIFFERS")
                else:
                    print(f"      ✅ SUMMARY RECORD {k+1} MATCHES")
            
            # Transactions
            print(f"    Transactions: Working={len(w_acc['transactions'])}, Generated={len(g_acc['transactions'])}")
            
            if len(w_acc['transactions']) != len(g_acc['transactions']):
                print(f"    ❌ DIFFERENT NUMBER OF TRANSACTIONS")
                print(f"    Working has {len(w_acc['transactions'])}, Generated has {len(g_acc['transactions'])}")
            
            # Show first few transactions for comparison
            max_transactions = min(max(len(w_acc['transactions']), len(g_acc['transactions'])), 5)
            for k in range(max_transactions):
                w_txn = w_acc['transactions'][k] if k < len(w_acc['transactions']) else "MISSING"
                g_txn = g_acc['transactions'][k] if k < len(g_acc['transactions']) else "MISSING"
                
                print(f"    Transaction {k+1}:")
                print(f"      Working:   {w_txn}")
                print(f"      Generated: {g_txn}")
                
                if w_txn != g_txn:
                    print(f"      ❌ TRANSACTION {k+1} DIFFERS")
                else:
                    print(f"      ✅ TRANSACTION {k+1} MATCHES")
            
            if len(w_acc['transactions']) > 5 or len(g_acc['transactions']) > 5:
                print(f"    ... (showing first 5 of {max(len(w_acc['transactions']), len(g_acc['transactions']))} transactions)")
            
            # Account trailers
            print(f"    Working Trailer:   {w_acc['trailer']}")
            print(f"    Generated Trailer: {g_acc['trailer']}")
            
            if w_acc['trailer'] != g_acc['trailer']:
                print("    ❌ ACCOUNT TRAILERS DIFFER")
            else:
                print("    ✅ ACCOUNT TRAILERS MATCH")
    
    # File trailers
    print(f"\n📋 FILE TRAILERS:")
    print(f"Working:   {working['file_trailer']}")
    print(f"Generated: {generated['file_trailer']}")
    
    if working['file_trailer'] != generated['file_trailer']:
        print("❌ FILE TRAILERS DIFFER")
    else:
        print("✅ FILE TRAILERS MATCH")
    
    return working, generated

def analyze_balance_codes(working_content, generated_content):
    """Analyze balance code differences specifically"""
    print("\n\n🏦 BALANCE CODE ANALYSIS")
    print("=" * 80)
    
    # Extract all 88 records
    working_88s = [line for line in working_content.split('\n') if line.strip().startswith('88,')]
    generated_88s = [line for line in generated_content.split('\n') if line.strip().startswith('88,')]
    
    print(f"Working file has {len(working_88s)} balance records (88)")
    print(f"Generated file has {len(generated_88s)} balance records (88)")
    
    print("\nWorking file balance codes:")
    for i, record in enumerate(working_88s):
        parts = record.split(',')
        if len(parts) >= 3:
            balance_code = parts[1]
            amount = parts[2]
            print(f"  {i+1}. Code {balance_code}: {amount}")
    
    print("\nGenerated file balance codes:")
    for i, record in enumerate(generated_88s):
        parts = record.split(',')
        if len(parts) >= 3:
            balance_code = parts[1]
            amount = parts[2]
            print(f"  {i+1}. Code {balance_code}: {amount}")

if __name__ == "__main__":
    # Read the working BAI2 file
    working_bai2 = """01,083000564,323809,250813,0936,168262,,,2/
02,323809,083000564,1,250812,,USD,2/
03,2375133,,010,,,Z/
88,015,1498035,,Z/
88,040,,,Z/
88,045,1498035,,Z/
88,072,225962,,Z/
88,074,000,,Z/
88,100,393239,4,Z/
88,400,311973,8,Z/
88,075,,,Z/
88,079,,,Z/
16,301,13707,Z,478980340,0000001470,Deposit,/
16,301,32510,Z,478980341,0000001449,Deposit,/
16,301,133474,Z,478980342,0000001486,Deposit,/
16,301,213548,Z,478980343,0000001459,Deposit,/
16,555,18500,Z,478980344,,RETURNED DEPOSITED ITEM Check 192,/
16,451,6900,Z,478980346,,WORLD ACCEPTANCE CONC DEBIT 1455 SHEPHERDSV,/
16,451,9200,Z,478980347,,WORLD ACCEPTANCE CONC DEBIT 1479 NICHOLASVI,/
16,451,33360,Z,478980348,,WORLD ACCEPTANCE CONC DEBIT 1486 GEORGETOWN,/
16,451,34319,Z,478980349,,WORLD ACCEPTANCE CONC DEBIT 1470 PARIS,KY,/
16,451,55000,Z,478980350,,WORLD ACCEPTANCE CONC DEBIT 1432 SHELBYVILL,/
16,451,71234,Z,478980351,,WORLD ACCEPTANCE CONC DEBIT 1459 CYNTHIANA,,/
16,451,83460,Z,478980352,,WORLD ACCEPTANCE CONC DEBIT 1449 WINCHESTER,/
49,4632456,23/
98,4632456,1,25/
02,323809,083000564,1,250813,,USD,2/
03,2375133,,010,1498035,,Z/
88,015,,,Z/
88,040,1498035,,Z/
88,045,,,Z/
88,072,,,Z/
88,074,,,Z/
88,100,0,0,Z/
88,400,0,0,Z/
88,075,,,Z/
88,079,,,Z/
49,2996070,11/
98,2996070,1,13/
99,7628526,2,40/"""

    # Read the generated BAI2 file
    generated_bai2 = """01,083000564,323809,250813,1626,202508131626,,,2/
02,323809,083000564,1,250812,,USD,2/
03,2375133,,010,,,Z/
88,015,,,Z/
88,040,393239,,Z/
88,045,,,Z/
88,072,311973,,Z/
88,074,000,,Z/
88,100,393239,4,Z/
88,400,311973,8,Z/
88,075,,,Z/
88,079,,,Z/
16,301,13707,Z,478980340,0000001470,Commercial Deposit, Serial Num: 1470, Ref Num: 478,/
16,301,32510,Z,478980341,0000001471,Commercial Deposit, Serial Num: 1449, Ref Num: 478,/
16,301,133474,Z,478980342,0000001472,Commercial Deposit, Serial Num: 1486, Ref Num: 478,/
16,301,213548,Z,478980343,0000001473,Commercial Deposit, Serial Num: 1459, Ref Num: 478,/
16,555,18500,Z,478980344,,Deposited Item Returned, Ref Num: 478980344, RETUR,/
16,451,6900,Z,478980346,,ACH Debit Received, Ref Num: 478980346, WORLD ACCE,/
16,451,9200,Z,478980347,,ACH Debit Received, Ref Num: 478980347, WORLD ACCE,/
16,451,33360,Z,478980348,,ACH Debit Received, Ref Num: 478980348, WORLD ACCE,/
16,451,34319,Z,478980349,,ACH Debit Received, Ref Num: 478980349, WORLD ACCE,/
16,451,55000,Z,478980350,,ACH Debit Received, Ref Num: 478980350, WORLD ACCE,/
16,451,71234,Z,478980351,,ACH Debit Received, Ref Num: 478980351, WORLD ACCE,/
16,451,83460,Z,478980352,,ACH Debit Received, Ref Num: 478980352, WORLD ACCE,/
49,1498035,23/
98,1498035,1,16/
99,1498035,1,18/"""

    # Perform comparison
    working_parsed, generated_parsed = compare_bai2_structures(working_bai2, generated_bai2)
    analyze_balance_codes(working_bai2, generated_bai2)
    
    print("\n\n🔧 KEY DIFFERENCES IDENTIFIED:")
    print("=" * 80)
    print("1. ❌ File headers have different File IDs and timestamps")
    print("2. ❌ Group 1 balance codes differ:")
    print("   - Working: 88,015,1498035 vs Generated: 88,015,")
    print("   - Working: 88,040, vs Generated: 88,040,393239")
    print("   - Working: 88,045,1498035 vs Generated: 88,045,")
    print("   - Working: 88,072,225962 vs Generated: 88,072,311973")
    print("3. ❌ Transaction descriptions are more verbose in generated file")
    print("4. ❌ Group 2 appears to be missing or structured differently")
    print("5. ❌ Account trailers and file trailers have different control totals")
    
    print("\n💡 RECOMMENDED FIXES:")
    print("1. Fix balance code calculations - especially opening/closing balances")
    print("2. Ensure proper multi-day/group structure")
    print("3. Adjust transaction descriptions to match working format")
    print("4. Fix control total calculations")
