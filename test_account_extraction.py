#!/usr/bin/env python3
"""
Test Account Number Extraction and Error Handling
"""
import re

def extract_account_number_from_text(text):
    """Extract account number from bank statement text using regex patterns"""
    print(f"🔍 Searching for account number in text: '{text[:100]}...'")
    
    # Common account number patterns
    patterns = [
        r'account\s*#?\s*:?\s*(\d{6,20})',  # "Account #: 123456789"
        r'account\s*number\s*:?\s*(\d{6,20})',  # "Account number: 123456789"
        r'acct\s*#?\s*:?\s*(\d{6,20})',  # "Acct#: 123456789"
        r'a/c\s*#?\s*:?\s*(\d{6,20})',  # "A/C#: 123456789"
        r'account\s*(\d{6,20})',  # "Account 123456789"
        r'(\d{6,20})\s*account',  # "123456789 account"
        r'for\s*account\s*(\d{6,20})',  # "For account 123456789"
        r'ending\s*in\s*(\d{4,6})',  # "Ending in 1234" (partial account)
        r'account\s*#\s*(\d{6,20})',  # "Account # 123456789" (with space)
        r'a/c\s*#\s*(\d{6,20})',  # "A/C # 123456789" (with space)
        r'acct\s*#\s*(\d{6,20})',  # "Acct # 123456789" (with space)
        r'(\d{8,20})',  # Any 8-20 digit number (last resort, must be reasonable length)
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Basic validation for account number
            if is_valid_account_number(match):
                print(f"✅ Found potential account number: {match}")
                return match
    
    print("❌ No account number found in statement text")
    return None

def is_valid_account_number(account_number):
    """Basic validation of account number"""
    if not account_number or not account_number.isdigit():
        return False
    
    # Account numbers should be between 4 and 20 digits
    if len(account_number) < 4 or len(account_number) > 20:
        return False
    
    # Skip numbers that are obviously not account numbers
    if len(account_number) == 10 and account_number.startswith(('202', '214', '469', '713', '832', '903', '940', '956', '972', '979')):  # Texas area codes
        return False
    
    # Allow 9-digit numbers as they could be account numbers (even if they could also be routing numbers)
    # The context will help determine if it's actually an account number
    
    return True

def create_error_bai2_file(error_message, filename, file_date, file_time):
    """Create a minimal BAI2 file with error message for files that cannot be processed"""
    print(f"❌ Creating ERROR BAI2 file: {error_message}")
    
    lines = []
    
    # 01 - File Header (minimal structure)
    lines.append(f"01,ERROR,WORKDAY,{file_date},{file_time},1,,,2/")
    
    # 02 - Group Header
    lines.append(f"02,ERROR,000000000,1,{file_date},,USD,2/")
    
    # 03 - Account Identifier (use ERROR as account number)
    lines.append(f"03,ERROR,,010,0,,Z/")
    
    # 88 - Continuation Record with error message
    lines.append(f"88,{error_message}/")
    
    # 49 - Account Trailer
    lines.append(f"49,0,2/")
    
    # 98 - Group Trailer
    lines.append(f"98,0,1,5/")
    
    # 99 - File Trailer
    lines.append(f"99,0,1,7/")
    
    return "\n".join(lines) + "\n"

def test_account_extraction():
    """Test account number extraction with various text samples"""
    print("🧪 TESTING ACCOUNT NUMBER EXTRACTION")
    print("=" * 60)
    
    # Test cases with various account number formats
    test_cases = [
        # Valid account numbers
        ("Wells Fargo Bank Account Number: 1234567890", "1234567890"),
        ("Account #: 987654321", "987654321"),
        ("Acct# 5555666677778888", "5555666677778888"),
        ("For account 123456789012", "123456789012"),
        ("A/C#: 456789123", "456789123"),
        ("Account ending in 9876", "9876"),
        ("Statement for account 111222333444", "111222333444"),
        
        # Edge cases that should be filtered out
        ("Routing Number: 123456789", None),  # Should be filtered as routing number
        ("Call us at 214-555-1234", None),  # Should be filtered as phone number
        ("Date: 08/12/2025", None),  # Should be filtered as date
        ("Amount: $1,234.56", None),  # Should be filtered as amount
        
        # No account number present
        ("This is a bank statement with no account information", None),
        ("Transaction details: Deposit $500.00", None),
        
        # Mixed content
        ("Wells Fargo Bank\nAccount Number: 9988776655\nRouting: 121000248\nBalance: $1,500.00", "9988776655"),
    ]
    
    print("Testing account number extraction patterns:")
    print()
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"Test {i}: {text[:50]}...")
        result = extract_account_number_from_text(text)
        
        if result == expected:
            print(f"✅ PASS - Expected: {expected}, Got: {result}")
        else:
            print(f"❌ FAIL - Expected: {expected}, Got: {result}")
        print()
    
    # Test error BAI2 file creation
    print("\n🧪 TESTING ERROR BAI2 FILE CREATION")
    print("=" * 60)
    
    error_bai = create_error_bai2_file("No account number found on statement", "test.pdf", "250812", "1200")
    
    print("Generated ERROR BAI2 file:")
    print("-" * 40)
    print(error_bai)
    print("-" * 40)
    
    # Validate ERROR BAI2 structure
    lines = error_bai.strip().split('\n')
    expected_records = ['01', '02', '03', '88', '49', '98', '99']
    
    print(f"✅ ERROR BAI2 has {len(lines)} lines")
    for i, line in enumerate(lines):
        record_type = line.split(',')[0]
        expected_type = expected_records[i] if i < len(expected_records) else 'unknown'
        if record_type == expected_type:
            print(f"✅ Line {i+1}: {record_type} record correct")
        else:
            print(f"❌ Line {i+1}: Expected {expected_type}, got {record_type}")
    
    # Check if error message is present
    if "No account number found on statement" in error_bai:
        print("✅ Error message correctly included in BAI2 file")
    else:
        print("❌ Error message missing from BAI2 file")
    
    print("\n🎉 Account extraction testing complete!")

if __name__ == "__main__":
    test_account_extraction()
