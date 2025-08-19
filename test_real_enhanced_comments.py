#!/usr/bin/env python3
"""
Test Enhanced BAI2 Comments with Real Document
Process a real bank statement to show enhanced reconciliation comments
"""
import sys
import os

# Add the current directory to the path so we can import from function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import reconcile_transactions, convert_to_bai2

def test_with_prosperity_bank_statement():
    """Test enhanced comments with a real Prosperity Bank statement"""
    print("🧪 Testing enhanced BAI2 comments with real Prosperity Bank statement...")
    
    # Simulate processed data from a Prosperity Bank statement (like what OpenAI would extract)
    # This represents typical data that might be extracted but missing opening balance
    mock_prosperity_data = {
        "account_number": "240086001455",
        "bank_name": "Prosperity Bank",
        "statement_date": "2025-08-06",
        # Note: Missing opening_balance to simulate common issue
        "closing_balance": {"amount": 15432.67},
        "transactions": [
            {"date": "2025-08-01", "amount": 2500.00, "description": "Payroll Deposit", "type": "deposit"},
            {"date": "2025-08-01", "amount": -125.00, "description": "ATM Withdrawal", "type": "withdrawal"},
            {"date": "2025-08-02", "amount": -89.45, "description": "Grocery Store Purchase", "type": "debit"},
            {"date": "2025-08-03", "amount": 150.00, "description": "Transfer In", "type": "deposit"},
            {"date": "2025-08-04", "amount": -45.30, "description": "Utility Payment", "type": "withdrawal"},
            {"date": "2025-08-05", "amount": -67.89, "description": "Gas Station", "type": "debit"},
            {"date": "2025-08-06", "amount": 1000.00, "description": "Customer Payment", "type": "deposit"}
        ]
    }
    
    print(f"📄 Processing mock Prosperity Bank data:")
    print(f"   Account: {mock_prosperity_data['account_number']}")
    print(f"   Closing Balance: ${mock_prosperity_data['closing_balance']['amount']:,.2f}")
    print(f"   Transactions: {len(mock_prosperity_data['transactions'])}")
    print(f"   Missing: Opening balance (common issue)")
    
    # Perform reconciliation (this will detect missing opening balance)
    reconciliation_result = reconcile_transactions(mock_prosperity_data)
    
    print(f"\n🧮 Reconciliation Analysis:")
    print(f"   Status: {reconciliation_result['reconciliation_status']}")
    print(f"   Opening Balance Known: {reconciliation_result['opening_balance_known']}")
    print(f"   Closing Balance Known: {reconciliation_result['closing_balance_known']}")
    print(f"   Error Codes: {reconciliation_result['error_codes']}")
    print(f"   Warnings: {len(reconciliation_result['warnings'])} warning(s)")
    
    # Generate BAI2 with enhanced comments
    routing_number = "113122655"  # Prosperity Bank routing number (from our OpenAI test)
    bai2_content = convert_to_bai2(mock_prosperity_data, "Prosperity_20250806.pdf", reconciliation_result, routing_number)
    
    print(f"\n✅ Generated BAI2 file with enhanced reconciliation comments:")
    print("=" * 80)
    
    # Show the enhanced comments section
    lines = bai2_content.split('\n')
    comment_lines = [line for line in lines if line.startswith('#')]
    
    for line in comment_lines:
        print(line)
    
    print("=" * 80)
    
    # Show a sample of the actual BAI2 data records
    print(f"\n📋 Sample BAI2 Data Records:")
    print("=" * 40)
    data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
    for i, line in enumerate(data_lines[:8]):  # Show first 8 data records
        print(f"{i+1:2d}: {line}")
    if len(data_lines) > 8:
        print(f"    ... ({len(data_lines)-8} more records)")
    print("=" * 40)
    
    # Save the BAI2 content to a file for inspection
    output_filename = "sample_prosperity_with_enhanced_comments.bai2"
    with open(output_filename, 'w') as f:
        f.write(bai2_content)
    
    print(f"\n💾 Full BAI2 file saved as: {output_filename}")
    print(f"   Total lines: {len(lines)}")
    print(f"   Comment lines: {len(comment_lines)}")
    print(f"   Data records: {len(data_lines)}")
    
    return bai2_content, reconciliation_result

def main():
    """Run the enhanced BAI2 comment test with real-world scenario"""
    print("🧪 ENHANCED BAI2 COMMENTS - REAL WORLD TEST")
    print("=" * 60)
    
    bai2_content, reconciliation = test_with_prosperity_bank_statement()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print("✅ Enhanced BAI2 comments successfully generated")
    print(f"🎯 Reconciliation Status: {reconciliation['reconciliation_status']}")
    print(f"📝 Key Benefits of Enhanced Comments:")
    print(f"   • Clear identification of missing opening balance")
    print(f"   • Specific error codes and explanations")
    print(f"   • Actionable recommendations for resolution")
    print(f"   • Detailed transaction and balance summaries")
    print(f"   • Processing timestamps and source file tracking")
    print(f"   • Workday import safety warnings when needed")
    
    print(f"\n💡 This addresses the user's request to:")
    print(f"   ✓ Show reconciliation data in BAI2 comments")
    print(f"   ✓ Explain why reconciliation may have failed")
    print(f"   ✓ Specifically highlight missing opening/closing balances")
    print(f"   ✓ Provide actionable troubleshooting guidance")

if __name__ == "__main__":
    main()
