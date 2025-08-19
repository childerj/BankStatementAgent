"""
Test the complete BAI2 generation with improved JSON parsing
"""
import os
import json
from datetime import datetime

def create_test_bai2():
    """Create a BAI2 file from sample JSON data"""
    
    print("🧪 TESTING BAI2 GENERATION WITH SAMPLE JSON DATA")
    print("=" * 60)
    
    # Sample JSON data that matches what OpenAI should return
    sample_data = {
        "account_number": "8464",
        "statement_period": {
            "start_date": "2025-06-01",
            "end_date": "2025-06-30"
        },
        "opening_balance": {
            "amount": 5316.18,
            "date": "2025-06-01"
        },
        "closing_balance": {
            "amount": 3304.70,
            "date": "2025-06-30"
        },
        "transactions": [
            {"date": "2025-06-02", "amount": 2832.26, "description": "Deposit# 000000000000811", "type": "deposit"},
            {"date": "2025-06-02", "amount": -3429.93, "description": "WORLD ACCEPTANCE/CONC DEBIT", "type": "withdrawal"},
            {"date": "2025-06-03", "amount": 2536.10, "description": "Deposit# 000000000000811", "type": "deposit"},
            {"date": "2025-06-03", "amount": -2832.26, "description": "WORLD ACCEPTANCE/CONC DEBIT", "type": "withdrawal"},
            {"date": "2025-06-04", "amount": 2870.50, "description": "Deposit# 000000000000811", "type": "deposit"},
            {"date": "2025-06-04", "amount": -2556.10, "description": "WORLD ACCEPTANCE/CONC DEBIT", "type": "withdrawal"},
            {"date": "2025-06-30", "amount": -5.00, "description": "MAINT FEE", "type": "fee"}
        ],
        "summary": {
            "total_deposits": 8238.86,
            "total_withdrawals": 8823.29,
            "transaction_count": 7,
            "fee_count": 1
        }
    }
    
    print(f"📊 Sample data: {sample_data['summary']['transaction_count']} transactions")
    print(f"💰 Opening: ${sample_data['opening_balance']['amount']:,.2f}")
    print(f"💰 Closing: ${sample_data['closing_balance']['amount']:,.2f}")
    print("")
    
    # Generate BAI2 using our improved conversion logic
    filename = "test_sample.pdf"
    
    # Get current date and time for BAI2 header
    now = datetime.now()
    file_date = now.strftime("%y%m%d")
    file_time = now.strftime("%H%M")
    
    # Initialize values from JSON data
    vendor_name = "BANK"
    account_number = str(sample_data.get("account_number", "123456789")).replace("-", "").replace(" ", "")[:20]
    currency = "USD"
    opening_balance_amount = int(float(sample_data["opening_balance"]["amount"]) * 100)  # Convert to cents
    transactions = sample_data.get("transactions", [])
    
    print(f"🏦 Bank: {vendor_name}")
    print(f"📋 Account: {account_number}")
    print(f"💰 Opening balance: ${opening_balance_amount/100:,.2f}")
    print(f"📊 Processing {len(transactions)} transactions")
    print("")
    
    # Build BAI2 file structure
    lines = []
    record_count = 0
    
    # 01 - File Header
    lines.append(f"01,GSBI,{filename[:10]},{file_date},{file_time},1,,,2/")
    record_count += 1
    
    # 02 - Group Header  
    lines.append(f"02,{vendor_name[:10]},026015079,1,{file_date},{file_time},,/")
    record_count += 1
    
    # 03 - Account Identifier
    lines.append(f"03,{account_number},{currency},010,{opening_balance_amount},,,/")
    record_count += 1
    
    # 16 - Transaction Detail Records
    transaction_records = 0
    if transactions:
        print("📝 Processing transactions for BAI2:")
        for i, txn in enumerate(transactions, 1):
            amount = float(txn.get("amount", 0))
            original_description = str(txn.get("description", "Transaction"))
            txn_type_hint = str(txn.get("type", "")).lower()
            
            # Convert amount to cents for BAI2
            amount_cents = int(amount * 100)
            
            # Determine BAI2 transaction type code
            if amount < 0 or txn_type_hint in ["withdrawal", "debit", "fee", "check"]:
                txn_type = "475"  # Debit
                amount_abs = abs(amount_cents)
                direction = "DR"
            else:
                txn_type = "108"  # Credit/Deposit
                amount_abs = abs(amount_cents)
                direction = "CR"
            
            # Clean up description for BAI2 format
            description = original_description[:50]  # BAI2 limit
            description = description.replace(",", " ").replace("/", " ")  # Remove BAI2 delimiters
            
            bank_ref = f"TXN{transaction_records + 1:06d}"
            
            print(f"   {i}. {direction} ${abs(amount):,.2f} - {description}")
            
            if amount_abs > 0:
                lines.append(f"16,{txn_type},{amount_abs},,{bank_ref},,{description}/")
                record_count += 1
                transaction_records += 1
    
    # If no detailed transactions, add a summary transaction
    if transaction_records == 0:
        lines.append(f"16,010,{opening_balance_amount},,BAL001,,Opening Balance - {filename}/")
        record_count += 1
        transaction_records = 1
    
    # 49 - Account Trailer
    # Calculate the running balance for control total
    closing_balance_amount = opening_balance_amount
    if "closing_balance" in sample_data and sample_data["closing_balance"].get("amount") is not None:
        closing_balance_amount = int(float(sample_data["closing_balance"]["amount"]) * 100)
    
    account_control_total = closing_balance_amount  # Use closing balance as control total
    account_record_count = 1 + transaction_records  # Account identifier + transaction records
    lines.append(f"49,{account_control_total},{account_record_count}/")
    record_count += 1
    
    # 98 - Group Trailer  
    group_control_total = account_control_total
    number_of_accounts = 1
    group_record_count = account_record_count + 2  # Account records + group header + account trailer
    lines.append(f"98,{group_control_total},{number_of_accounts},{group_record_count}/")
    record_count += 1
    
    # 99 - File Trailer
    file_control_total = group_control_total
    number_of_groups = 1
    total_record_count = record_count + 1  # All records including this trailer
    lines.append(f"99,{file_control_total},{number_of_groups},{total_record_count}/")
    
    bai2_content = "\n".join(lines) + "\n"
    
    print(f"✅ BAI2 file created with {transaction_records} transactions")
    print(f"📏 BAI2 Size: {len(bai2_content.encode('utf-8')):,} bytes ({len(lines)} lines)")
    print("")
    print("🔍 BAI2 CONTENT PREVIEW:")
    print("=" * 40)
    for i, line in enumerate(lines[:10]):  # Show first 10 lines
        print(f"{i+1:2d}: {line}")
    if len(lines) > 10:
        print(f"... and {len(lines) - 10} more lines")
    
    print("")
    print("🔍 CONTROL TOTALS:")
    print(f"   Account control total: {account_control_total} (${account_control_total/100:,.2f})")
    print(f"   Group control total: {group_control_total} (${group_control_total/100:,.2f})")
    print(f"   File control total: {file_control_total} (${file_control_total/100:,.2f})")
    
    # Save to file for inspection
    with open("test_bai2_sample.bai2", "w") as f:
        f.write(bai2_content)
    
    print(f"💾 Saved to: test_bai2_sample.bai2")
    
    return bai2_content

if __name__ == "__main__":
    result = create_test_bai2()
    print("\\n🎉 BAI2 GENERATION TEST COMPLETED!")
