#!/usr/bin/env python3
"""Test BAI generation with reconciliation status"""

import json
import sys
import os

# Add the parent directory to the path to import function_app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from function_app import reconcile_transactions, convert_to_bai2

def test_bai_with_reconciliation():
    """Test BAI generation with different reconciliation scenarios"""
    
    print("🧪 Testing BAI Generation with Reconciliation Status")
    print("=" * 60)
    
    # Test Case 1: Opening balance unknown
    print("\n1️⃣  Test Case: Opening balance UNKNOWN")
    test_data = {
        "account_number": "1234567890",
        "closing_balance": {"amount": 1200.00},
        "transactions": [
            {"date": "2025-07-28", "amount": 300.00, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-28", "amount": -100.00, "description": "Withdrawal", "type": "withdrawal"}
        ]
    }
    
    try:
        # Perform reconciliation
        reconciliation = reconcile_transactions(test_data)
        
        # Generate BAI with reconciliation data
        bai_content = convert_to_bai2(test_data, "test_unknown_opening.pdf", reconciliation)
        
        print("\n📄 Generated BAI Content (first 20 lines):")
        lines = bai_content.split('\n')
        for i, line in enumerate(lines[:20]):
            if line.strip():
                print(f"   {i+1:2d}: {line}")
        
        # Show reconciliation-related lines
        recon_lines = [line for line in lines if line.startswith('#')]
        if recon_lines:
            print(f"\n🔍 Reconciliation Status Lines:")
            for line in recon_lines:
                print(f"   {line}")
        else:
            print(f"\n⚠️  No reconciliation status lines found")
            
        print(f"\n📊 BAI Summary:")
        print(f"   Total lines: {len([l for l in lines if l.strip()])}")
        print(f"   Reconciliation status: {reconciliation['reconciliation_status']}")
        print(f"   Error codes: {reconciliation['error_codes']}")
        
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test Case 2: Both balances unknown
    print("\n" + "="*60)
    print("\n2️⃣  Test Case: Both balances UNKNOWN")
    test_data_2 = {
        "account_number": "1234567890", 
        "transactions": [
            {"date": "2025-07-28", "amount": 300.00, "description": "Deposit", "type": "deposit"},
            {"date": "2025-07-28", "amount": -100.00, "description": "Withdrawal", "type": "withdrawal"}
        ]
    }
    
    try:
        # Perform reconciliation (will not raise exception for missing balances)
        reconciliation = reconcile_transactions(test_data_2)
        
        # Generate BAI with reconciliation data
        bai_content = convert_to_bai2(test_data_2, "test_both_unknown.pdf", reconciliation)
        
        # Show reconciliation-related lines
        lines = bai_content.split('\n')
        recon_lines = [line for line in lines if line.startswith('#')]
        if recon_lines:
            print(f"\n🔍 Reconciliation Status Lines:")
            for line in recon_lines:
                print(f"   {line}")
        
        print(f"\n📊 Summary:")
        print(f"   Reconciliation status: {reconciliation['reconciliation_status']}")
        print(f"   Error codes: {reconciliation['error_codes']}")
        print(f"   Warnings: {len(reconciliation['warnings'])}")
        
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 60)
    print("✅ BAI reconciliation testing complete!")

if __name__ == "__main__":
    test_bai_with_reconciliation()
