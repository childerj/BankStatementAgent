#!/usr/bin/env python3
"""
Check what FIRST NATIONAL BANK entries exist in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bank_info_loader import load_bank_information_yaml

def find_first_national_banks():
    """Find all First National Bank entries"""
    
    print("🔍 Finding all First National Bank entries")
    print("=" * 60)
    
    # Load bank data  
    yaml_content, bank_data = load_bank_information_yaml()
    
    if not bank_data:
        print("❌ Could not load bank data")
        return
    
    print(f"✅ Loaded {len(bank_data)} bank records")
    
    # Find all banks with "FIRST NATIONAL" in the name
    first_national_banks = []
    
    for bank in bank_data:
        bank_name = bank['bank_name'].upper()
        if 'FIRST NATIONAL' in bank_name:
            first_national_banks.append(bank)
    
    print(f"\n📋 Found {len(first_national_banks)} 'First National' banks:")
    print("-" * 60)
    
    for i, bank in enumerate(first_national_banks, 1):
        print(f"{i:3d}. {bank['bank_name']}")
        print(f"     Account: {bank['account_number']}, Routing: {bank['routing_number']}")
    
    # Specifically look for South Carolina variants
    print(f"\n🔍 Looking for South Carolina variants:")
    print("-" * 60)
    
    sc_variants = []
    for bank in bank_data:
        bank_name = bank['bank_name'].upper()
        if any(term in bank_name for term in ['SOUTH CAROLINA', ' SC', 'SC ']):
            sc_variants.append(bank)
    
    for bank in sc_variants:
        print(f"   {bank['bank_name']}")
        print(f"     Account: {bank['account_number']}, Routing: {bank['routing_number']}")
    
    # Check for the specific account 810023499 we expect
    print(f"\n🎯 Looking for account 810023499:")
    print("-" * 60)
    
    for bank in bank_data:
        if str(bank['account_number']) == '810023499':
            print(f"   ✅ FOUND: {bank['bank_name']}")
            print(f"     Account: {bank['account_number']}, Routing: {bank['routing_number']}")
            break
    else:
        print("   ❌ Account 810023499 not found in database")

if __name__ == "__main__":
    find_first_national_banks()
