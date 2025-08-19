"""
Test the convert_to_bai2 function directly with sample data
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))
from function_app import convert_to_bai2

def test_convert_to_bai2_balance():
    """Test that convert_to_bai2 uses actual balances correctly"""
    
    print("🧪 Testing convert_to_bai2 balance logic")
    print("=" * 50)
    
    # Create sample reconciliation data similar to what would be extracted
    sample_reconciliation_data = {
        "opening_balance": {"amount": 13033.44, "date": "2024-08-12"},
        "closing_balance": {"amount": 14980.35, "date": "2024-08-13"},
        "transactions": [
            {
                "amount": 393.24,
                "type": "credit",
                "description": "Deposit",
                "date": "2024-08-13"
            },
            {
                "amount": 311.97,
                "type": "debit", 
                "description": "Withdrawal",
                "date": "2024-08-13"
            }
        ]
    }
    
    # Sample parsed data structure
    sample_data = {
        "routing_number": "083000564",
        "account_number": "323809"
    }
    
    try:
        print("📊 Testing with sample data:")
        print(f"   Opening Balance: ${sample_reconciliation_data['opening_balance']['amount']:,.2f}")
        print(f"   Closing Balance: ${sample_reconciliation_data['closing_balance']['amount']:,.2f}")
        print(f"   Transactions: {len(sample_reconciliation_data['transactions'])}")
        
        # Call convert_to_bai2 function
        bai2_content = convert_to_bai2(
            data=sample_data,
            filename="test_stockyards.pdf",
            reconciliation_data=sample_reconciliation_data,
            routing_number="083000564"
        )
        
        if bai2_content:
            print("\n✅ BAI2 generation successful!")
            
            # Parse the content and extract balance records
            lines = bai2_content.split('\n')
            balance_records = [line for line in lines if line.startswith('88,')]
            
            print("\n🏦 Generated Balance Records:")
            for record in balance_records:
                print(f"   {record}")
            
            # Check specific balance records
            closing_ledger_record = next((line for line in lines if line.startswith('88,015,')), None)
            closing_available_record = next((line for line in lines if line.startswith('88,045,')), None)
            
            if closing_ledger_record:
                parts = closing_ledger_record.split(',')
                if len(parts) >= 3 and parts[2]:
                    closing_balance_cents = int(parts[2])
                    closing_balance_dollars = closing_balance_cents / 100
                    print(f"\n💰 88,015 (Closing Ledger): ${closing_balance_dollars:,.2f}")
                    
                    # Should match the input closing balance
                    expected_balance = sample_reconciliation_data['closing_balance']['amount']
                    if abs(closing_balance_dollars - expected_balance) < 0.01:
                        print(f"✅ CORRECT! Matches expected ${expected_balance:,.2f}")
                    else:
                        print(f"❌ INCORRECT! Expected ${expected_balance:,.2f}")
            
            if closing_available_record:
                parts = closing_available_record.split(',')
                if len(parts) >= 3 and parts[2]:
                    available_balance_cents = int(parts[2])
                    available_balance_dollars = available_balance_cents / 100
                    print(f"💰 88,045 (Closing Available): ${available_balance_dollars:,.2f}")
                    
                    # Should match 88,015
                    if closing_ledger_record:
                        ledger_parts = closing_ledger_record.split(',')
                        if len(ledger_parts) >= 3 and ledger_parts[2] == parts[2]:
                            print("✅ 88,045 matches 88,015 (correct)")
                        else:
                            print("❌ 88,045 does not match 88,015")
            
            # Check for empty 88,040 (opening available)
            opening_available_record = next((line for line in lines if line.startswith('88,040,')), None)
            if opening_available_record:
                parts = opening_available_record.split(',')
                if len(parts) >= 3 and not parts[2]:
                    print("✅ 88,040 (Opening Available) is empty (correct)")
                else:
                    print(f"❌ 88,040 should be empty but has: {parts[2] if len(parts) >= 3 else 'N/A'}")
            
        else:
            print("❌ BAI2 generation failed - no content returned")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_convert_to_bai2_balance()
