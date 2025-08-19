#!/usr/bin/env python3
"""
Test Enhanced BAI2 Reconciliation Comments
Tests the enhanced comment generation for different reconciliation scenarios
"""
import sys
import os

# Add the current directory to the path so we can import from function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2, create_error_bai2_file
from datetime import datetime

def test_successful_reconciliation():
    """Test BAI2 comments for successful reconciliation"""
    print("🧪 Testing successful reconciliation comments...")
    
    # Mock data with all balances available
    data = {
        "account_number": "123456789",
        "opening_balance": {"amount": 1000.00},
        "closing_balance": {"amount": 1050.00},
        "transactions": [
            {"date": "2025-08-12", "amount": 100.00, "description": "Deposit", "type": "deposit"},
            {"date": "2025-08-12", "amount": -50.00, "description": "Withdrawal", "type": "withdrawal"}
        ]
    }
    
    # Mock reconciliation data (successful)
    reconciliation_data = {
        "opening_balance": 1000.00,
        "opening_balance_known": True,
        "closing_balance": 1050.00,
        "closing_balance_known": True,
        "total_deposits": 100.00,
        "total_withdrawals": 50.00,
        "expected_closing": 1050.00,
        "difference": 0.00,
        "balanced": True,
        "transaction_count": 2,
        "reconciliation_status": "COMPLETE",
        "error_codes": [],
        "warnings": []
    }
    
    bai2_content = convert_to_bai2(data, "test_successful.pdf", reconciliation_data, "121000248")
    
    print("✅ BAI2 content with successful reconciliation:")
    print("=" * 60)
    # Print only the comment lines
    for line in bai2_content.split('\n'):
        if line.startswith('#'):
            print(line)
    print("=" * 60)
    
    return bai2_content

def test_missing_opening_balance():
    """Test BAI2 comments for missing opening balance"""
    print("\n🧪 Testing missing opening balance comments...")
    
    # Mock data with missing opening balance
    data = {
        "account_number": "987654321",
        "closing_balance": {"amount": 1200.00},
        "transactions": [
            {"date": "2025-08-12", "amount": 200.00, "description": "Deposit", "type": "deposit"},
            {"date": "2025-08-12", "amount": -100.00, "description": "Fee", "type": "fee"}
        ]
    }
    
    # Mock reconciliation data (partial - missing opening balance)
    reconciliation_data = {
        "opening_balance": 1100.00,  # Calculated value
        "opening_balance_known": False,
        "closing_balance": 1200.00,
        "closing_balance_known": True,
        "total_deposits": 200.00,
        "total_withdrawals": 100.00,
        "expected_closing": 1200.00,
        "difference": 0.00,
        "balanced": True,
        "transaction_count": 2,
        "reconciliation_status": "PARTIAL",
        "error_codes": ["OB_UNKNOWN"],
        "warnings": ["Opening balance not available - cannot perform full reconciliation"]
    }
    
    bai2_content = convert_to_bai2(data, "test_missing_opening.pdf", reconciliation_data, "026009593")
    
    print("✅ BAI2 content with missing opening balance:")
    print("=" * 60)
    # Print only the comment lines
    for line in bai2_content.split('\n'):
        if line.startswith('#'):
            print(line)
    print("=" * 60)
    
    return bai2_content

def test_missing_both_balances():
    """Test BAI2 comments for missing both balances"""
    print("\n🧪 Testing missing both balances comments...")
    
    # Mock data with no balance information
    data = {
        "account_number": "555666777",
        "transactions": [
            {"date": "2025-08-12", "amount": 150.00, "description": "Transfer In", "type": "deposit"},
            {"date": "2025-08-12", "amount": -75.00, "description": "Check", "type": "check"}
        ]
    }
    
    # Mock reconciliation data (failed - no balances)
    reconciliation_data = {
        "opening_balance": None,
        "opening_balance_known": False,
        "closing_balance": None,
        "closing_balance_known": False,
        "total_deposits": 150.00,
        "total_withdrawals": 75.00,
        "expected_closing": None,
        "difference": 0.00,
        "balanced": False,
        "transaction_count": 2,
        "reconciliation_status": "FAILED",
        "error_codes": ["OB_UNKNOWN", "CB_UNKNOWN"],
        "warnings": ["Cannot perform reconciliation - both opening and closing balances unknown"]
    }
    
    bai2_content = convert_to_bai2(data, "test_no_balances.pdf", reconciliation_data, "021000021")
    
    print("✅ BAI2 content with missing both balances:")
    print("=" * 60)
    # Print only the comment lines
    for line in bai2_content.split('\n'):
        if line.startswith('#'):
            print(line)
    print("=" * 60)
    
    return bai2_content

def test_balance_mismatch():
    """Test BAI2 comments for balance mismatch"""
    print("\n🧪 Testing balance mismatch comments...")
    
    # Mock data with balance mismatch
    data = {
        "account_number": "111222333",
        "opening_balance": {"amount": 800.00},
        "closing_balance": {"amount": 900.00},  # Should be 925.00 based on transactions
        "transactions": [
            {"date": "2025-08-12", "amount": 200.00, "description": "Salary", "type": "deposit"},
            {"date": "2025-08-12", "amount": -75.00, "description": "Utilities", "type": "withdrawal"}
        ]
    }
    
    # Mock reconciliation data (failed - balance mismatch)
    reconciliation_data = {
        "opening_balance": 800.00,
        "opening_balance_known": True,
        "closing_balance": 900.00,
        "closing_balance_known": True,
        "total_deposits": 200.00,
        "total_withdrawals": 75.00,
        "expected_closing": 925.00,
        "difference": -25.00,  # Actual is $25 less than expected
        "balanced": False,
        "transaction_count": 2,
        "reconciliation_status": "FAILED",
        "error_codes": ["BALANCE_MISMATCH"],
        "warnings": ["Balance reconciliation failed: difference of $-25.00"]
    }
    
    bai2_content = convert_to_bai2(data, "test_mismatch.pdf", reconciliation_data, "113122655")
    
    print("✅ BAI2 content with balance mismatch:")
    print("=" * 60)
    # Print only the comment lines
    for line in bai2_content.split('\n'):
        if line.startswith('#'):
            print(line)
    print("=" * 60)
    
    return bai2_content

def test_error_bai2_file():
    """Test enhanced error BAI2 file with detailed diagnostics"""
    print("\n🧪 Testing enhanced error BAI2 file...")
    
    now = datetime.now()
    file_date = now.strftime("%y%m%d")
    file_time = now.strftime("%H%M")
    
    error_bai2 = create_error_bai2_file("No account number found on statement", "error_test.pdf", file_date, file_time)
    
    print("✅ Error BAI2 content:")
    print("=" * 60)
    # Print only the comment lines
    for line in error_bai2.split('\n'):
        if line.startswith('#'):
            print(line)
    print("=" * 60)
    
    return error_bai2

def main():
    """Run all BAI2 comment enhancement tests"""
    print("🧪 BAI2 RECONCILIATION COMMENT ENHANCEMENT TESTS")
    print("=" * 70)
    
    # Test different reconciliation scenarios
    test_successful_reconciliation()
    test_missing_opening_balance()
    test_missing_both_balances()
    test_balance_mismatch()
    test_error_bai2_file()
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print("✅ All BAI2 comment enhancement tests completed")
    print("🎯 Enhanced comments now include:")
    print("   • Detailed reconciliation status and diagnostics")
    print("   • Specific balance information (found/missing/calculated)")
    print("   • Transaction summaries and calculations")
    print("   • Error codes with explanations")
    print("   • Specific failure reasons and recommendations")
    print("   • Step-by-step troubleshooting guidance")
    print("   • Processing timestamps and source file info")
    print("\n💡 These enhanced comments will help users understand:")
    print("   • Why reconciliation may have failed")
    print("   • What data was missing (opening/closing balance)")
    print("   • How to resolve processing issues")
    print("   • Whether the BAI2 file is safe to import into Workday")

if __name__ == "__main__":
    main()
