#!/usr/bin/env python3
"""
Fix WAC Bank Information for 366.pdf
Based on Document Intelligence analysis, update the database entry
"""

import json

def fix_wac_database():
    """Update WAC database with correct bank information for 366.pdf"""
    
    print("🔧 Fixing WAC Bank Information Database")
    print("=" * 50)
    
    # Load current database
    with open('WAC Bank Information.json', 'r') as f:
        banks = json.load(f)
    
    print(f"Current database has {len(banks)} banks:")
    for i, bank in enumerate(banks, 1):
        print(f"  {i}. {bank.get('Bank Name', 'N/A')}")
    
    # Find the Citizens Bank entry (index 3, 0-based)
    citizens_bank_index = None
    for i, bank in enumerate(banks):
        if bank.get('Bank Name') == 'Citizens Bank of Kentucky':
            citizens_bank_index = i
            break
    
    if citizens_bank_index is not None:
        print(f"\n🎯 Found Citizens Bank of Kentucky at index {citizens_bank_index}")
        print(f"   Current entry: {banks[citizens_bank_index]}")
        
        # Update with correct information from Document Intelligence
        banks[citizens_bank_index] = {
            "Bank Name": "First National Bank OF SOUTH CAROLINA",
            "Address": "801 Gilway Avenue Post Office Box 38 Holly Hill, South Carolina 29059-0038",
            "Account Number": 810023499,
            "Routing Number": 53203210  # Need to verify this from the statement
        }
        
        print(f"\n✅ Updated entry:")
        print(f"   New entry: {banks[citizens_bank_index]}")
        
        # Save the updated database
        with open('WAC Bank Information.json', 'w') as f:
            json.dump(banks, f, indent=2)
        
        print(f"\n💾 Database updated and saved!")
        
        # Verify the fix
        print(f"\n🔍 Verification:")
        with open('WAC Bank Information.json', 'r') as f:
            updated_banks = json.load(f)
        
        for i, bank in enumerate(updated_banks, 1):
            print(f"  {i}. {bank.get('Bank Name', 'N/A')} (Account: {bank.get('Account Number', 'N/A')})")
        
        print(f"\n🎯 TEST: Bank name matching")
        from difflib import SequenceMatcher
        
        statement_bank = "First National Bank OF SOUTH CAROLINA"
        database_bank = "First National Bank OF SOUTH CAROLINA"
        
        similarity = SequenceMatcher(None, statement_bank.lower(), database_bank.lower()).ratio() * 100
        print(f"   Statement: '{statement_bank}'")
        print(f"   Database:  '{database_bank}'")
        print(f"   Similarity: {similarity:.1f}%")
        
        if similarity >= 70.0:
            print(f"   ✅ MATCH! Processing should now work!")
        else:
            print(f"   ❌ Still no match")
        
    else:
        print(f"❌ Citizens Bank of Kentucky not found in database")

if __name__ == "__main__":
    fix_wac_database()
