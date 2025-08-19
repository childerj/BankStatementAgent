#!/usr/bin/env python3
"""
Test script to verify reference number extraction from bank statements
"""
import json
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Load OpenAI credentials from local.settings.json
def load_local_settings():
    """Load credentials from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            
            # Set environment variables
            os.environ['AZURE_OPENAI_ENDPOINT'] = values.get('AZURE_OPENAI_ENDPOINT', '')
            os.environ['AZURE_OPENAI_KEY'] = values.get('AZURE_OPENAI_KEY', '')
            os.environ['AZURE_OPENAI_DEPLOYMENT'] = values.get('AZURE_OPENAI_DEPLOYMENT', '')
            
            print(f"✅ Loaded OpenAI credentials:")
            print(f"  Endpoint: {os.environ['AZURE_OPENAI_ENDPOINT']}")
            print(f"  Deployment: {os.environ['AZURE_OPENAI_DEPLOYMENT']}")
            print(f"  Key: {'*' * 20}...{os.environ['AZURE_OPENAI_KEY'][-10:] if os.environ['AZURE_OPENAI_KEY'] else 'Not set'}")
            
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")

# Load credentials before importing function_app
load_local_settings()

from function_app import send_to_openai_for_parsing

def test_reference_number_extraction():
    """Test that reference numbers are correctly extracted from bank statements"""
    
    print("🧪 TESTING REFERENCE NUMBER EXTRACTION")
    print("=" * 60)
    
    # Sample OCR text with various reference number patterns
    sample_ocr_text = """
    BANK STATEMENT
    Account: 323809
    Statement Period: 08/12/2024 to 08/13/2024
    
    TRANSACTION HISTORY
    Date        Description                           Amount    Reference
    08/12/24    Deposit                              137.07    478980340
    08/12/24    Deposit                              325.10    478980341  
    08/12/24    Deposit                             1334.74    478980342
    08/12/24    Deposit                             2135.48    478980343
    08/12/24    ACH Debit WORLD ACCEPTANCE CONC     -150.00    478980344
    08/13/24    Deposit Return Check 192             -50.00    478980345
    08/13/24    ACH Debit WORLD ACCEPTANCE          -200.00    478980346
    08/13/24    Deposit                              456.23    478980347
    
    Opening Balance: $7,052.12
    Closing Balance: $8,126.60
    """
    
    # Mock data structure
    mock_data = {
        "ocr_text": sample_ocr_text,
        "ocr_text_lines": sample_ocr_text.split('\n')
    }
    
    try:
        print("🤖 Calling OpenAI extraction...")
        
        # Call the extraction function
        result = send_to_openai_for_parsing(mock_data)
        
        if result and isinstance(result, dict):
            print("✅ OpenAI extraction successful")
            
            # Check if transactions were extracted
            transactions = result.get("transactions", [])
            print(f"📊 Found {len(transactions)} transactions")
            
            # Analyze reference number extraction
            print("\n🔍 REFERENCE NUMBER ANALYSIS:")
            print("-" * 40)
            
            ref_numbers_found = []
            ref_numbers_missing = []
            
            for i, txn in enumerate(transactions):
                amount = txn.get("amount", 0)
                description = txn.get("description", "")
                ref_num = txn.get("reference_number", "")
                
                print(f"Transaction {i+1}:")
                print(f"  Amount: ${amount}")
                print(f"  Description: {description[:50]}...")
                print(f"  Reference: '{ref_num}'")
                
                if ref_num and str(ref_num).strip() and str(ref_num).strip() != "null":
                    ref_numbers_found.append(str(ref_num).strip())
                    print(f"  ✅ Reference number extracted: {ref_num}")
                else:
                    ref_numbers_missing.append(i+1)
                    print(f"  ❌ No reference number found")
                print()
            
            # Summary
            print("📈 EXTRACTION SUMMARY:")
            print(f"  Total transactions: {len(transactions)}")
            print(f"  Reference numbers found: {len(ref_numbers_found)}")
            print(f"  Reference numbers missing: {len(ref_numbers_missing)}")
            
            if ref_numbers_found:
                print(f"  Found references: {ref_numbers_found}")
            
            if ref_numbers_missing:
                print(f"  Missing references on transactions: {ref_numbers_missing}")
            
            # Check if we captured the expected sequence
            expected_refs = ["478980340", "478980341", "478980342", "478980343", "478980344", "478980345", "478980346", "478980347"]
            matches = [ref for ref in ref_numbers_found if ref in expected_refs]
            
            print(f"\n🎯 ACCURACY CHECK:")
            print(f"  Expected refs: {expected_refs}")
            print(f"  Matching refs: {matches}")
            print(f"  Accuracy: {len(matches)}/{len(expected_refs)} ({100*len(matches)/len(expected_refs):.1f}%)")
            
            if len(matches) >= 6:  # At least 75% accuracy
                print("✅ Reference number extraction working well!")
                return True
            else:
                print("⚠️ Reference number extraction needs improvement")
                return False
                
        else:
            print("❌ OpenAI extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_reference_number_extraction()
