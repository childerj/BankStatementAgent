#!/usr/bin/env python3
"""
Quick check of remaining unfixed issues: bank references and descriptions
"""
import json
import sys
import os

# Load OpenAI credentials
def load_local_settings():
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            os.environ['AZURE_OPENAI_ENDPOINT'] = values.get('AZURE_OPENAI_ENDPOINT', '')
            os.environ['AZURE_OPENAI_KEY'] = values.get('AZURE_OPENAI_KEY', '')
            os.environ['AZURE_OPENAI_DEPLOYMENT'] = values.get('AZURE_OPENAI_DEPLOYMENT', '')
    except Exception as e:
        print(f"Error loading settings: {e}")

load_local_settings()
sys.path.insert(0, os.getcwd())

from function_app import send_to_openai_for_parsing, convert_to_bai2

def check_remaining_issues():
    """Check bank references and transaction descriptions"""
    
    print("CHECKING REMAINING UNFIXED ISSUES")
    print("=" * 50)
    
    # Sample with specific descriptions that should be short
    sample_ocr_text = """
    BANK STATEMENT - Account: 323809
    
    TRANSACTIONS:
    08/12/24    Deposit                           137.07    Ref: 478980340    Bank: 0000001470
    08/12/24    RETURNED DEPOSITED ITEM Check 192 -50.00    Ref: 478980344    Bank: 0000001485
    08/12/24    WORLD ACCEPTANCE CONC DEBIT 1455  -69.00    Ref: 478980346    Bank: 0000001499
    
    Closing Balance: $8,000.00
    """
    
    mock_data = {
        "ocr_text": sample_ocr_text,
        "ocr_text_lines": sample_ocr_text.split('\n')
    }
    
    try:
        # Extract and generate BAI2
        extracted_data = send_to_openai_for_parsing(mock_data)
        bai2_content = convert_to_bai2(mock_data, "test.pdf", extracted_data)
        
        if not bai2_content:
            print("BAI2 generation failed")
            return
            
        print("ANALYZING BAI2 TRANSACTION RECORDS:")
        print("-" * 40)
        
        bai2_lines = bai2_content.split('\n')
        transaction_lines = [line for line in bai2_lines if line.startswith('16,')]
        
        for i, line in enumerate(transaction_lines):
            parts = line.split(',')
            if len(parts) >= 7:
                txn_type = parts[1]
                amount = parts[2]
                ref_num = parts[4]
                bank_ref = parts[5]
                text_desc = parts[6].replace('/', '')
                
                print(f"Transaction {i+1}:")
                print(f"  Type: {txn_type}")
                print(f"  Amount: {amount}")
                print(f"  Ref Number: {ref_num}")
                print(f"  Bank Ref: '{bank_ref}'")
                print(f"  Description: '{text_desc}'")
                print()
        
        print("ISSUE ANALYSIS:")
        print("-" * 20)
        
        # Check bank references
        bank_refs = [line.split(',')[5] for line in transaction_lines if len(line.split(',')) >= 6]
        print(f"Bank References: {bank_refs}")
        
        # Check if they're sequential vs actual
        sequential_pattern = all(bank_refs[i] == f"0000{1470 + i:06d}" for i in range(len(bank_refs)) if bank_refs[i])
        if sequential_pattern:
            print("❌ ISSUE: Bank references are sequential (generated) instead of actual")
        else:
            print("✅ Bank references appear to be extracted from statement")
        
        # Check descriptions
        descriptions = [line.split(',')[6].replace('/', '') for line in transaction_lines if len(line.split(',')) >= 7]
        print(f"Descriptions: {descriptions}")
        
        long_descriptions = [desc for desc in descriptions if len(desc) > 30]
        if long_descriptions:
            print(f"❌ ISSUE: {len(long_descriptions)} descriptions are too long/verbose")
            for desc in long_descriptions:
                print(f"  '{desc}' ({len(desc)} chars)")
        else:
            print("✅ Descriptions are appropriately concise")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_remaining_issues()
