"""
Test with Stockyards PDF to verify balance matches working file
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))
from function_app import process_bank_statement
import json

def test_stockyards_balance():
    """Test that the Stockyards PDF generates correct closing balance"""
    
    # Test with the Stockyards file that should match the working BAI2
    test_file_path = "Test Docs/Stockyards_20250806.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return
    
    print(f"🧪 Testing Stockyards balance with: {test_file_path}")
    print("=" * 60)
    
    try:
        # Read the file
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        # Process the file directly
        print("📊 Processing Stockyards bank statement...")
        result = process_bank_statement(file_content, "Stockyards_20250806.pdf")
        
        if result and result.get('success'):
            print("✅ Processing successful!")
            
            # Check if BAI2 content is available
            bai2_content = result.get('bai2_content')
            if bai2_content:
                print("\n📋 Generated BAI2 Content (Balance Records):")
                print("-" * 50)
                
                # Look for balance records (88 records)
                lines = bai2_content.split('\n')
                balance_records = [line for line in lines if line.startswith('88,')]
                
                print("🏦 Balance Records Found:")
                for record in balance_records:
                    print(f"   {record}")
                
                # Extract the closing balance specifically
                closing_balance_record = next((line for line in lines if line.startswith('88,015,')), None)
                if closing_balance_record:
                    parts = closing_balance_record.split(',')
                    if len(parts) >= 3 and parts[2]:
                        closing_balance_cents = int(parts[2])
                        closing_balance_dollars = closing_balance_cents / 100
                        print(f"\n💰 Generated Closing Balance: ${closing_balance_dollars:,.2f}")
                        
                        # Compare to working file closing balance: $14,980.35
                        working_file_balance = 14980.35
                        difference = abs(closing_balance_dollars - working_file_balance)
                        
                        print(f"🎯 Working File Balance:     ${working_file_balance:,.2f}")
                        print(f"📊 Difference:               ${difference:,.2f}")
                        
                        if difference < 1.00:  # Allow small rounding differences
                            print("✅ BALANCE MATCHES! Generated file matches working file.")
                        else:
                            print(f"❌ BALANCE MISMATCH! Difference of ${difference:,.2f}")
                            
                        # Also check 88,045 (should match 88,015)
                        available_balance_record = next((line for line in lines if line.startswith('88,045,')), None)
                        if available_balance_record:
                            parts = available_balance_record.split(',')
                            if len(parts) >= 3 and parts[2]:
                                available_balance_cents = int(parts[2])
                                available_balance_dollars = available_balance_cents / 100
                                if abs(available_balance_dollars - closing_balance_dollars) < 0.01:
                                    print("✅ Available balance (88,045) matches closing balance (88,015)")
                                else:
                                    print(f"❌ Available balance mismatch: ${available_balance_dollars:,.2f}")
                    else:
                        print("❌ No closing balance amount found in record")
                else:
                    print("❌ No closing balance record (88,015) found")
                
            else:
                print("❌ No BAI2 content generated")
                
        else:
            print("❌ Processing failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stockyards_balance()
