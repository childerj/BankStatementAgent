#!/usr/bin/env python3
"""
Test script to verify that the complete function uses extracted reference numbers in BAI2 output
"""
import json
import sys
import os

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
            
    except Exception as e:
        print(f"❌ Error loading local.settings.json: {e}")

# Load credentials before importing function_app
load_local_settings()

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

from function_app import send_to_openai_for_parsing, convert_to_bai2

def test_bai2_with_extracted_references():
    """Test that BAI2 file generation uses extracted reference numbers"""
    
    print("🧪 TESTING BAI2 GENERATION WITH EXTRACTED REFERENCE NUMBERS")
    print("=" * 70)
    
    # Sample OCR text with specific reference numbers
    sample_ocr_text = """
    BANK STATEMENT
    Account: 323809
    Statement Period: 08/12/2024 to 08/13/2024
    
    TRANSACTION HISTORY
    Date        Description                           Amount    Reference
    08/12/24    Deposit                              137.07    REF001
    08/12/24    Deposit                              325.10    REF002  
    08/12/24    Deposit                             1334.74    CHK123
    08/12/24    Deposit                             2135.48    TXN456
    08/12/24    ACH Debit WORLD ACCEPTANCE CONC     -150.00    ACH789
    08/13/24    Deposit Return Check 192             -50.00    RTN001
    08/13/24    ACH Debit WORLD ACCEPTANCE          -200.00    ACH999
    08/13/24    Deposit                              456.23    DEP777
    
    Opening Balance: $7,052.12
    Closing Balance: $8,126.60
    """
    
    # Mock data structure
    mock_data = {
        "ocr_text": sample_ocr_text,
        "ocr_text_lines": sample_ocr_text.split('\n')
    }
    
    try:
        print("🤖 Step 1: Extracting data with OpenAI...")
        
        # Call the extraction function
        extracted_data = send_to_openai_for_parsing(mock_data)
        
        if not extracted_data or not isinstance(extracted_data, dict):
            print("❌ OpenAI extraction failed")
            return False
            
        print("✅ OpenAI extraction successful")
        
        # Check extracted reference numbers
        transactions = extracted_data.get("transactions", [])
        print(f"📊 Found {len(transactions)} transactions")
        
        extracted_refs = []
        for i, txn in enumerate(transactions):
            ref_num = txn.get("reference_number", "")
            if ref_num and str(ref_num).strip() and str(ref_num).strip() != "null":
                extracted_refs.append(str(ref_num).strip())
                print(f"  Transaction {i+1}: Reference '{ref_num}'")
            else:
                print(f"  Transaction {i+1}: No reference extracted")
        
        print(f"🔍 Extracted references: {extracted_refs}")
        
        print("\n🏗️ Step 2: Generating BAI2 file...")
        
        # Generate BAI2 file
        bai2_content = convert_to_bai2(
            mock_data, 
            "test_statement.pdf", 
            extracted_data  # Pass extracted data as reconciliation_data
        )
        
        if not bai2_content:
            print("❌ BAI2 generation failed")
            return False
            
        print("✅ BAI2 file generated successfully")
        
        print("\n🔍 Step 3: Analyzing BAI2 content for reference numbers...")
        
        # Analyze BAI2 content for reference numbers
        bai2_lines = bai2_content.split('\n')
        transaction_lines = [line for line in bai2_lines if line.startswith('16,')]
        
        print(f"📊 Found {len(transaction_lines)} transaction records in BAI2")
        
        used_refs = []
        for i, line in enumerate(transaction_lines):
            # Parse BAI2 transaction line: 16,type,amount,funds_type,ref_num,bank_ref,text,/
            parts = line.split(',')
            if len(parts) >= 5:
                ref_num = parts[4]  # Reference number is 5th field
                used_refs.append(ref_num)
                print(f"  Transaction {i+1}: BAI2 uses reference '{ref_num}'")
        
        print(f"🎯 BAI2 references: {used_refs}")
        
        # Check if extracted references were used in BAI2
        matches = 0
        for extracted_ref in extracted_refs:
            if extracted_ref in used_refs:
                matches += 1
                print(f"✅ Extracted reference '{extracted_ref}' found in BAI2")
            else:
                print(f"❌ Extracted reference '{extracted_ref}' NOT found in BAI2")
        
        # Check for any synthetic references (our fallback format)
        synthetic_refs = [ref for ref in used_refs if ref.startswith('478980')]
        if synthetic_refs:
            print(f"⚠️ Found {len(synthetic_refs)} synthetic references: {synthetic_refs}")
            print("   This suggests fallback logic was used instead of extracted references")
        
        print(f"\n📈 RESULTS SUMMARY:")
        print(f"  Extracted references: {len(extracted_refs)}")
        print(f"  BAI2 references: {len(used_refs)}")
        print(f"  Matches: {matches}")
        print(f"  Synthetic references: {len(synthetic_refs)}")
        
        if matches > 0:
            print(f"✅ SUCCESS: {matches} extracted references used in BAI2!")
            return True
        elif len(synthetic_refs) == len(used_refs):
            print(f"⚠️ PARTIAL: All BAI2 references are synthetic (fallback logic)")
            return False
        else:
            print(f"❌ FAILURE: No extracted references used in BAI2")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_bai2_with_extracted_references()
