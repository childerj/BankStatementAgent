#!/usr/bin/env python3
"""
Simple analysis of 366.pdf processing issues
"""

import json

def analyze_366_simple():
    """Simple analysis of the 366.pdf issues"""
    
    print("🔍 Analysis of 366.pdf Processing Failure")
    print("=" * 60)
    
    # Load the WAC Bank Information directly
    print("\n1. 🏦 Checking WAC Bank Information Database...")
    
    try:
        with open('WAC Bank Information.json', 'r') as f:
            bank_data = json.load(f)
        
        print(f"   ✅ Loaded {len(bank_data)} bank records")
        
        # Search for Citizens Bank entries
        citizens_banks = []
        for bank in bank_data:
            bank_name = bank.get('BankName', '').lower()
            if 'citizen' in bank_name:
                citizens_banks.append(bank)
        
        print(f"\n   📋 Citizens Bank entries found: {len(citizens_banks)}")
        for bank in citizens_banks:
            print(f"      - {bank.get('BankName', 'N/A')} (ABA: {bank.get('ABA_Number', 'N/A')})")
            accounts = bank.get('AccountNumbers', [])
            if accounts:
                print(f"        Accounts: {accounts}")
        
    except Exception as e:
        print(f"   ❌ Error loading bank info: {e}")
        return
    
    # Test bank name matching manually
    print(f"\n2. 🔍 Manual Bank Name Matching Test...")
    
    statement_bank_name = "The Citizens Bank"
    print(f"   Statement Bank Name: '{statement_bank_name}'")
    
    # Manual similarity calculation
    from difflib import SequenceMatcher
    
    best_match = None
    best_score = 0
    
    for bank in bank_data:
        bank_name = bank.get('BankName', '')
        if 'citizen' in bank_name.lower():
            similarity = SequenceMatcher(None, statement_bank_name.lower(), bank_name.lower()).ratio() * 100
            print(f"      '{bank_name}' -> {similarity:.1f}%")
            
            if similarity > best_score:
                best_score = similarity
                best_match = bank
    
    print(f"\n   Best Match: {best_match.get('BankName', 'None') if best_match else 'None'}")
    print(f"   Best Score: {best_score:.1f}%")
    print(f"   Threshold: 70.0%")
    
    if best_score < 70.0:
        print(f"   ❌ FAILED - Score {best_score:.1f}% below 70% threshold")
    else:
        print(f"   ✅ PASSED - Score above threshold")
    
    # Analyze account numbers from logs
    print(f"\n3. 📋 Account Numbers from Logs Analysis...")
    
    # These were extracted from the failure logs
    extracted_accounts = [
        '810023499',  # Found multiple times - likely false positive
        '6232024',    # Shorter number
        '131441',     # Short number  
        '543283',     # Short number
        '8335286',    # This appears to be the real account (8 digits)
        '296066429',  # 9 digits - could be routing or phone
        '4965011',    # 7 digits
        '8003336896', # 10 digits - phone number format
        '8008472911', # 10 digits - phone number format
        '08530002860303000'  # 17 digits - from masked account
    ]
    
    print(f"   Found {len(extracted_accounts)} potential account numbers:")
    for acc in extracted_accounts:
        length = len(acc)
        if length == 10 and acc.startswith('8'):
            category = "📞 Phone Number"
        elif length < 6:
            category = "❌ Too Short"
        elif length > 15:
            category = "🎭 Masked/Long"
        elif 6 <= length <= 12:
            category = "✅ Possible Account"
        else:
            category = "❓ Unknown"
        
        print(f"      {acc} ({length} digits) - {category}")
    
    # Check if any match the bank accounts (if we found a bank)
    if best_match and best_score >= 70.0:
        print(f"\n4. 🔍 Account Matching with Bank Database...")
        bank_accounts = best_match.get('AccountNumbers', [])
        print(f"   Bank has {len(bank_accounts)} accounts in database")
        
        found_matches = []
        for acc in extracted_accounts:
            if acc in [str(x) for x in bank_accounts]:
                found_matches.append(acc)
                print(f"      ✅ {acc} matches bank account")
        
        if not found_matches:
            print(f"      ❌ No extracted accounts match bank database")
    else:
        print(f"\n4. ❌ Cannot check account matching - no bank match found")
    
    # Analyze the masked account specifically
    print(f"\n5. 🎭 Masked Account Analysis...")
    masked_account = "08530002860303000*"
    print(f"   Original: {masked_account}")
    
    # Extract just the digits
    import re
    digits = re.sub(r'[^0-9]', '', masked_account)
    print(f"   Digits Only: {digits} ({len(digits)} digits)")
    
    # This is very long - might be a concatenated number or routing+account
    if len(digits) == 17:
        print(f"   Possible interpretations:")
        print(f"      - Full concatenated number: {digits}")
        print(f"      - First 9 digits (routing?): {digits[:9]}")
        print(f"      - Last 8 digits (account?): {digits[9:]}")
        print(f"      - Last 10 digits: {digits[7:]}")
    
    # Summary
    print(f"\n6. 📝 SUMMARY OF ISSUES:")
    print(f"   " + "="*50)
    
    print(f"   ❌ PRIMARY ISSUE: Bank Name Matching")
    print(f"      - Statement shows: 'The Citizens Bank'")
    if best_score < 70.0:
        print(f"      - Best match: '{best_match.get('BankName', 'None') if best_match else 'None'}' ({best_score:.1f}%)")
        print(f"      - Falls short of 70% threshold")
    
    print(f"\n   ⚠️ SECONDARY ISSUES:")
    print(f"      - Too many false positive account extractions")
    print(f"      - Phone numbers extracted as accounts (800-333-6896, 800-847-2911)")
    print(f"      - Repetitive account number processing in logs")
    print(f"      - Need better filtering for valid account patterns")
    
    print(f"\n   💡 RECOMMENDATIONS:")
    if best_score < 70.0:
        print(f"      1. 🏦 Add 'The Citizens Bank' to WAC Bank Information database")
        print(f"         - Or update existing Citizens Bank entry with alias")
    print(f"      2. 🔢 Improve account number extraction:")
    print(f"         - Filter out phone numbers (10-digit numbers starting with 8)")
    print(f"         - Focus on 6-12 digit account numbers")
    print(f"         - Use the masked account: 08530002860303000* -> 0853002860303000")
    print(f"      3. 🧹 Reduce log verbosity for account extraction")
    print(f"      4. 🎯 Prioritize the main account number: 8335286")

if __name__ == "__main__":
    analyze_366_simple()
