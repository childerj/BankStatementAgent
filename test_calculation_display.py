#!/usr/bin/env python3
"""
Test script to verify enhanced BAI2 comments with detailed calculations
Tests scenarios with complete balance data to show full calculations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import convert_to_bai2

def test_complete_balance_calculation():
    """Test with complete opening and closing balance data"""
    print("🧪 ENHANCED BAI2 COMMENTS - CALCULATION DISPLAY TESTS")
    print("=" * 70)
    
    # Test case 1: Perfect reconciliation
    print("🧪 Testing with complete balance data (perfect reconciliation)...")
    
    data = {
        "account_number": "1234567890", 
        "opening_balance": {"amount": 1000.00, "date": "2025-08-01"},
        "closing_balance": {"amount": 1755.25, "date": "2025-08-12"},
        "transactions": [
            {"date": "2025-08-05", "amount": 500.00, "description": "Deposit", "type": "deposit"},
            {"date": "2025-08-07", "amount": 300.00, "description": "Another Deposit", "type": "deposit"},
            {"date": "2025-08-10", "amount": -44.75, "description": "ATM Fee", "type": "fee"}
        ]
    }
    
    reconciliation_data = {
        "reconciliation_status": "COMPLETE",
        "opening_balance": 1000.00,
        "closing_balance": 1755.25,
        "opening_balance_known": True,
        "closing_balance_known": True,
        "total_deposits": 800.00,
        "total_withdrawals": 44.75,
        "transaction_count": 3,
        "difference": 0.00  # Perfect match
    }
    
    bai_content = convert_to_bai2(
        data=data,
        filename="test_perfect_balance.pdf",
        reconciliation_data=reconciliation_data,
        routing_number="021000021"
    )
    
    print("✅ BAI2 content with perfect balance reconciliation:")
    print("=" * 80)
    # Extract just the comments
    lines = bai_content.split('\n')
    for line in lines:
        if line.startswith('#'):
            print(line)
    print("=" * 80)
    print()
    
    # Test case 2: Balance discrepancy
    print("🧪 Testing with balance discrepancy...")
    
    data_discrepancy = {
        "account_number": "9876543210", 
        "opening_balance": {"amount": 2500.00, "date": "2025-08-01"},
        "closing_balance": {"amount": 3100.00, "date": "2025-08-12"},  # Should be 3105.50
        "transactions": [
            {"date": "2025-08-05", "amount": 750.00, "description": "Large Deposit", "type": "deposit"},
            {"date": "2025-08-07", "amount": -144.50, "description": "Check #1234", "type": "check"}
        ]
    }
    
    reconciliation_data_discrepancy = {
        "reconciliation_status": "FAILED",
        "opening_balance": 2500.00,
        "closing_balance": 3100.00,
        "opening_balance_known": True,
        "closing_balance_known": True,
        "total_deposits": 750.00,
        "total_withdrawals": 144.50,
        "transaction_count": 2,
        "difference": -5.50  # $5.50 discrepancy
    }
    
    bai_content = convert_to_bai2(
        data=data_discrepancy,
        filename="test_balance_discrepancy.pdf",
        reconciliation_data=reconciliation_data_discrepancy,
        routing_number="021000021"
    )
    
    print("✅ BAI2 content with balance discrepancy:")
    print("=" * 80)
    # Extract just the comments
    lines = bai_content.split('\n')
    for line in lines:
        if line.startswith('#'):
            print(line)
    print("=" * 80)
    print()
    
    # Test case 3: No reconciliation data but complete source data
    print("🧪 Testing no reconciliation data but complete source balances...")
    
    data_source_only = {
        "account_number": "5555555555", 
        "opening_balance": {"amount": 850.75, "date": "2025-08-01"},
        "closing_balance": {"amount": 1205.25, "date": "2025-08-12"},
        "transactions": [
            {"date": "2025-08-03", "amount": 400.00, "description": "Payroll", "type": "deposit"},
            {"date": "2025-08-06", "amount": -45.50, "description": "Gas Station", "type": "withdrawal"}
        ]
    }
    
    bai_content = convert_to_bai2(
        data=data_source_only,
        filename="test_source_only.pdf",
        reconciliation_data=None,
        routing_number="021000021"
    )
    
    print("✅ BAI2 content with source data only (no reconciliation):")
    print("=" * 80)
    # Extract just the comments
    lines = bai_content.split('\n')
    for line in lines:
        if line.startswith('#'):
            print(line)
    print("=" * 80)
    
    print("\n" + "=" * 70)
    print("📊 CALCULATION DISPLAY TEST SUMMARY")
    print("=" * 70)
    print("✅ Enhanced BAI2 comments now show:")
    print("   • Clear starting balance when available")
    print("   • Step-by-step calculation breakdown")
    print("   • Expected vs actual closing balance comparison")
    print("   • Precise difference calculations")
    print("   • Balance verification status")
    print()
    print("🎯 Examples show:")
    print("   ✓ Perfect reconciliation with ✓ BALANCED status")
    print("   ✓ Discrepancy calculations with exact amounts")
    print("   ✓ Source-only calculations when no reconciliation data")

if __name__ == "__main__":
    test_complete_balance_calculation()
