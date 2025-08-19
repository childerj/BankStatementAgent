#!/usr/bin/env python3

def analyze_bai_files():
    """Compare working BAI2 file with generated file to identify differences"""
    
    print("🔍 ANALYZING BAI2 FILE DIFFERENCES")
    print("=" * 60)
    
    # Working file content
    working_file = """01,083000564,323809,250813,0936,168262,,,2/
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

    # Generated file content
    generated_file = """01,083000564,323809,250813,1455,202508131455,,,2/
02,323809,083000564,1,250812,,USD,2/
03,2375133,,010,,,Z/
88,015,705212,,Z/
88,040,81266,,Z/
88,045,705212,,Z/
88,072,000,,Z/
88,074,000,,Z/
88,100,393239,4,Z/
88,400,311973,8,Z/
88,075,,,Z/
88,079,,,Z/
16,301,13707,,2147809075,,/
16,301,32510,,2147809077,,/
16,301,133474,,2147809079,,/
16,301,213548,,2147809081,,/
16,555,18500,,2147809083,,/
88,Deposited Item Returned Ref Num: 478980344 RETURNED DEPOSITE,/
16,451,6900,,2147809085,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0346 WORLD ACCEPTANCE CON 0346 WORLD ACCEPTANCE CON,/
16,451,9200,,2147809087,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0347 WORLD ACCEPTANCE CON 0347 WORLD ACCEPTANCE CON,/
16,451,33360,,2147809089,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0348 WORLD ACCEPTANCE CON 0348 WORLD ACCEPTANCE CON,/
16,451,34319,,2147809091,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0349 WORLD ACCEPTANCE CON 0349 WORLD ACCEPTANCE CON,/
16,451,55000,,2147809093,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0350 WORLD ACCEPTANCE CON 0350 WORLD ACCEPTANCE CON,/
16,451,71234,,2147809095,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0351 WORLD ACCEPTANCE CON 0351 WORLD ACCEPTANCE CON,/
16,451,83460,,2147809097,,/
88,WORLD ACCEPTANCE/CONC DEBIT 0352 WORLD ACCEPTANCE CON 0352 WORLD ACCEPTANCE CON,/
49,81266,31/
98,81266,1,33/
99,81266,1,35/"""

    working_lines = working_file.strip().split('\n')
    generated_lines = generated_file.strip().split('\n')
    
    print("📊 KEY DIFFERENCES ANALYSIS:")
    print()
    
    # Analyze header differences
    print("1️⃣ HEADER DIFFERENCES:")
    w_header = working_lines[0].split(',')
    g_header = generated_lines[0].split(',')
    
    print(f"   Working:   {working_lines[0]}")
    print(f"   Generated: {generated_lines[0]}")
    print(f"   📌 File ID: Working={w_header[5]} vs Generated={g_header[5]}")
    print()
    
    # Analyze transaction record format differences
    print("2️⃣ TRANSACTION RECORD FORMAT:")
    
    # Find first transaction line in each
    working_txn = None
    generated_txn = None
    
    for line in working_lines:
        if line.startswith('16,'):
            working_txn = line
            break
    
    for line in generated_lines:
        if line.startswith('16,'):
            generated_txn = line
            break
    
    if working_txn and generated_txn:
        w_parts = working_txn.split(',')
        g_parts = generated_txn.split(',')
        
        print(f"   Working:   {working_txn}")
        print(f"   Generated: {generated_txn}")
        print()
        print("   📌 Field Differences:")
        print(f"      Field 3 (Funds Type): Working='{w_parts[3]}' vs Generated='{g_parts[3]}'")
        print(f"      Field 4 (Reference): Working='{w_parts[4]}' vs Generated='{g_parts[4]}'")
        print(f"      Field 5 (Bank Ref): Working='{w_parts[5]}' vs Generated='{g_parts[5]}'")
        print(f"      Field 6 (Text): Working='{w_parts[6]}' vs Generated='{g_parts[6]}'")
    print()
    
    # Analyze detailed description differences
    print("3️⃣ DETAILED DESCRIPTION (88 Records):")
    
    working_88_lines = [line for line in working_lines if line.startswith('88,') and 'WORLD ACCEPTANCE' in line]
    generated_88_lines = [line for line in generated_lines if line.startswith('88,') and 'WORLD ACCEPTANCE' in line]
    
    if working_88_lines and generated_88_lines:
        print(f"   Working:   {working_88_lines[0]}")
        print(f"   Generated: {generated_88_lines[0]}")
    print()
    
    # Analyze balance summary differences
    print("4️⃣ BALANCE SUMMARY (88 Records):")
    for i, line in enumerate(working_lines[:15]):
        if line.startswith('88,'):
            if i < len(generated_lines):
                w_parts = line.split(',')
                g_parts = generated_lines[i].split(',')
                if w_parts[1] != g_parts[1] or w_parts[2] != g_parts[2]:
                    print(f"   Line {i+1}: Working={line} vs Generated={generated_lines[i]}")
    print()
    
    # Count differences
    print("5️⃣ STRUCTURE DIFFERENCES:")
    print(f"   Working file lines: {len(working_lines)}")
    print(f"   Generated file lines: {len(generated_lines)}")
    
    working_16_count = len([line for line in working_lines if line.startswith('16,')])
    generated_16_count = len([line for line in generated_lines if line.startswith('16,')])
    print(f"   Transaction records (16,): Working={working_16_count} vs Generated={generated_16_count}")
    
    working_88_count = len([line for line in working_lines if line.startswith('88,')])
    generated_88_count = len([line for line in generated_lines if line.startswith('88,')])
    print(f"   Detail records (88,): Working={working_88_count} vs Generated={generated_88_count}")
    print()
    
    print("🎯 CRITICAL FIXES NEEDED:")
    print("   1. Transaction records missing 'Z' in funds type field")
    print("   2. Reference numbers format different (478980340 vs 2147809075)")
    print("   3. Bank reference field format (0000001470 vs empty)")
    print("   4. Text field format (Deposit vs empty)")
    print("   5. 88 record descriptions too verbose/incorrect")
    print("   6. Balance summary values incorrect")

if __name__ == "__main__":
    analyze_bai_files()
