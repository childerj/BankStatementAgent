#!/usr/bin/env python3
"""
Test script to verify balance summary fix for missing opening balances
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

def test_balance_summary_fix():
    """Test that balance summary properly handles missing opening balance"""
    
    print("🧪 TESTING BALANCE SUMMARY FIX")
    print("=" * 50)
    
    # Sample OCR text WITHOUT opening balance
    sample_ocr_text = """
    BANK STATEMENT
    Account: 323809
    Statement Period: 08/12/2024 to 08/13/2024
    
    TRANSACTION HISTORY
    Date        Description                           Amount    Reference
    08/12/24    Deposit                              137.07    478980340
    08/12/24    Deposit                              325.10    478980341  
    08/12/24    Deposit                             1334.74    478980342
    08/12/24    ACH Debit WORLD ACCEPTANCE CONC     -150.00    478980343
    
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
        
        # Check what was extracted
        opening_balance = extracted_data.get("opening_balance", {})
        closing_balance = extracted_data.get("closing_balance", {})
        transactions = extracted_data.get("transactions", [])
        
        print(f"📊 Extracted data:")
        print(f"  Opening balance: {opening_balance}")
        print(f"  Closing balance: {closing_balance}")
        print(f"  Transactions: {len(transactions)}")
        
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
        
        print("\n🔍 Step 3: Analyzing balance summary records (88 records)...")
        
        # Analyze BAI2 content for balance summary
        bai2_lines = bai2_content.split('\n')
        balance_lines = [line for line in bai2_lines if line.startswith('88,')]
        
        print(f"📊 Found {len(balance_lines)} balance summary records:")
        
        balance_analysis = {}
        for line in balance_lines:
            parts = line.split(',')
            if len(parts) >= 3:
                code = parts[1]  # BAI code
                value = parts[2]  # Balance value
                balance_analysis[code] = value
                
                # Decode the balance codes
                code_names = {
                    '015': 'Opening Balance',
                    '040': 'Current Ledger',
                    '045': 'Available Balance',
                    '072': 'One Day Float',
                    '074': 'Two Day Float',
                    '100': 'Total Credits',
                    '400': 'Total Debits',
                    '075': 'Adjustments',
                    '079': 'Avg Available MTD'
                }
                
                code_name = code_names.get(code, f'Code {code}')
                if value:
                    if code in ['100', '400']:
                        # These include counts, so parse differently
                        print(f"  {code_name} ({code}): {value}")
                    else:
                        try:
                            amount = float(value) / 100 if value.isdigit() else value
                            print(f"  {code_name} ({code}): ${amount:,.2f}" if isinstance(amount, float) else f"  {code_name} ({code}): {value}")
                        except:
                            print(f"  {code_name} ({code}): {value}")
                else:
                    print(f"  {code_name} ({code}): EMPTY")
        
        # Check specific expectations
        print(f"\n🎯 VALIDATION:")
        
        # Opening balance should be empty when not available
        opening_bal_value = balance_analysis.get('015', '')
        if not opening_bal_value:
            print("✅ Opening balance (015) is correctly EMPTY")
        else:
            print(f"❌ Opening balance (015) should be empty but has value: {opening_bal_value}")
        
        # Current ledger and available should have same closing balance
        current_ledger = balance_analysis.get('040', '')
        available_balance = balance_analysis.get('045', '')
        
        if current_ledger and available_balance and current_ledger == available_balance:
            print(f"✅ Current ledger (040) and available balance (045) match: ${float(current_ledger)/100:,.2f}")
        else:
            print(f"❌ Current ledger (040): {current_ledger}, Available (045): {available_balance} - should match")
        
        # Float should be 0
        float_value = balance_analysis.get('072', '')
        if float_value == '000':
            print("✅ Float (072) is correctly 0")
        else:
            print(f"⚠️ Float (072) is {float_value}, expected 000")
        
        return True
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_balance_summary_fix()
