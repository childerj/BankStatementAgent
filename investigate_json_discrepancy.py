#!/usr/bin/env python3
"""
Investigate why WAC Bank Information.json doesn't match the spreadsheet
"""

import json
import os

def investigate_json_vs_spreadsheet():
    """Check for discrepancies between JSON and spreadsheet data"""
    
    print("🔍 Investigating JSON vs Spreadsheet Discrepancy")
    print("=" * 60)
    
    # Check current JSON file
    with open('WAC Bank Information.json', 'r') as f:
        json_data = json.load(f)
    
    print(f"📄 Current JSON file contents:")
    for i, bank in enumerate(json_data, 1):
        bank_name = bank.get('Bank Name', 'N/A')
        account = bank.get('Account Number', 'N/A')
        routing = bank.get('Routing Number', 'N/A')
        print(f"   {i}. {bank_name}")
        print(f"      Account: {account}, Routing: {routing}")
    
    # What the spreadsheet says should be there
    print(f"\n📊 What spreadsheet says:")
    spreadsheet_data = {
        "Bank Name": "FIRST NATIONAL BANK OF SC",
        "Address": "P.O. BOX 38, HOLLY HILL, TN 29059, United States of America",
        "Account Number": 810023499,
        "Routing Number": 53203210
    }
    
    print(f"   Bank: {spreadsheet_data['Bank Name']}")
    print(f"   Account: {spreadsheet_data['Account Number']}")
    print(f"   Routing: {spreadsheet_data['Routing Number']}")
    
    # What Document Intelligence found in 366.pdf
    print(f"\n📋 What Document Intelligence found in 366.pdf:")
    doc_intel_data = {
        "Bank Name": "First National Bank OF SOUTH CAROLINA", 
        "Account Number": 810023499,
        "Routing Number": "053203210 (from analysis)"
    }
    
    print(f"   Bank: {doc_intel_data['Bank Name']}")
    print(f"   Account: {doc_intel_data['Account Number']}")
    print(f"   Routing: {doc_intel_data['Routing Number']}")
    
    # Check for matches
    print(f"\n🔍 Matching Analysis:")
    
    # Account number matching
    spreadsheet_account = spreadsheet_data['Account Number']
    doc_account = doc_intel_data['Account Number']
    
    print(f"   Account Numbers:")
    print(f"      Spreadsheet: {spreadsheet_account}")
    print(f"      Document:    {doc_account}")
    print(f"      Match: {'✅' if spreadsheet_account == doc_account else '❌'}")
    
    # Check if this account exists in current JSON
    json_accounts = [bank.get('Account Number') for bank in json_data]
    account_in_json = spreadsheet_account in json_accounts
    print(f"      In JSON: {'✅' if account_in_json else '❌'}")
    
    # Bank name similarity
    from difflib import SequenceMatcher
    
    spreadsheet_bank = spreadsheet_data['Bank Name'].lower()
    doc_bank = doc_intel_data['Bank Name'].lower()
    
    similarity = SequenceMatcher(None, spreadsheet_bank, doc_bank).ratio() * 100
    print(f"\n   Bank Names:")
    print(f"      Spreadsheet: '{spreadsheet_data['Bank Name']}'")
    print(f"      Document:    '{doc_intel_data['Bank Name']}'")
    print(f"      Similarity:  {similarity:.1f}%")
    
    # Check all JSON bank names against the expected one
    print(f"\n   JSON Bank Names vs Expected:")
    for bank in json_data:
        json_bank = bank.get('Bank Name', '').lower()
        similarity = SequenceMatcher(None, spreadsheet_bank, json_bank).ratio() * 100
        print(f"      '{bank.get('Bank Name', 'N/A')}' -> {similarity:.1f}%")
    
    # Possible reasons for discrepancy
    print(f"\n🤔 POSSIBLE REASONS FOR DISCREPANCY:")
    print(f"   " + "="*50)
    
    print(f"   1. 📝 MANUAL ENTRY ERROR:")
    print(f"      - Someone manually created the JSON file")
    print(f"      - Copied wrong information from spreadsheet")
    print(f"      - Typos or misreading during conversion")
    
    print(f"\n   2. 📊 SPREADSHEET UPDATE:")
    print(f"      - JSON was created from an old version of spreadsheet")
    print(f"      - Spreadsheet was updated after JSON creation")
    print(f"      - Multiple versions of the data source")
    
    print(f"\n   3. 🔄 CONVERSION PROCESS:")
    print(f"      - Automated conversion script had bugs")
    print(f"      - Field mapping was incorrect")
    print(f"      - Data transformation errors")
    
    print(f"\n   4. 🗂️ DATA SOURCE CONFUSION:")
    print(f"      - JSON created from different source than current spreadsheet")
    print(f"      - Multiple spreadsheets with different data")
    print(f"      - Test data mixed with production data")
    
    print(f"\n   5. 📅 TIMING ISSUES:")
    print(f"      - JSON created before account was properly set up")
    print(f"      - Bank information changed after JSON creation")
    print(f"      - Outdated cached data")
    
    # Check file timestamps
    print(f"\n📅 FILE TIMESTAMPS:")
    json_stat = os.stat('WAC Bank Information.json')
    json_mtime = json_stat.st_mtime
    
    import datetime
    json_modified = datetime.datetime.fromtimestamp(json_mtime)
    print(f"   JSON file last modified: {json_modified}")
    
    # Check if there's an Excel file
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'WAC' in f.upper()]
    print(f"\n📊 Excel files found: {len(excel_files)}")
    for excel_file in excel_files:
        excel_stat = os.stat(excel_file)
        excel_modified = datetime.datetime.fromtimestamp(excel_stat.st_mtime)
        print(f"   {excel_file}: {excel_modified}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   " + "="*40)
    print(f"   1. ✅ IMMEDIATE: Update JSON with correct spreadsheet data")
    print(f"   2. 🔧 PROCESS: Create automated sync between spreadsheet and JSON")
    print(f"   3. ✔️ VERIFY: Always validate JSON against source spreadsheet")
    print(f"   4. 📝 DOCUMENT: Track when and how JSON gets updated")
    print(f"   5. 🧪 TEST: Run this analysis after any data updates")

if __name__ == "__main__":
    investigate_json_vs_spreadsheet()
