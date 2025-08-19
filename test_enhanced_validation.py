#!/usr/bin/env python3

def test_enhanced_validation():
    """Test the enhanced validation logic"""
    
    print("🧪 TESTING ENHANCED VALIDATION")
    print("=" * 60)
    
    # Mock the print_and_log function for testing
    def print_and_log(message):
        print(message)
    
    # Copy the validation function from our updated code
    def is_valid_account_number(account_number):
        """Validate account number - reject any with asterisks (masked) or other invalid characteristics"""
        if not account_number:
            return False
        
        account_str = str(account_number).strip()
        
        # Critical: Reject account numbers containing asterisks (masked/redacted numbers)
        # This catches cases like "*5594", "5594*", "55*94", "****5594", etc.
        if "*" in account_str:
            print_and_log(f"❌ Account number validation failed: contains asterisk(s): '{account_str}'")
            return False
        
        # Also reject other masking characters sometimes used
        if any(char in account_str for char in ['x', 'X', '#']) and len(account_str) <= 8:
            # Allow X/x/# in longer account numbers, but not in short ones (likely masked)
            print_and_log(f"❌ Account number validation failed: likely masked with X/#: '{account_str}'")
            return False
        
        # Account numbers should be reasonable length (at least 4 characters after cleaning)
        clean_account = account_str.replace("-", "").replace(" ", "").replace("_", "")
        if len(clean_account) < 4:
            print_and_log(f"❌ Account number validation failed: too short after cleaning: '{clean_account}'")
            return False
        
        # Exclude common words that aren't account numbers
        excluded_words = ['number', 'account', 'acct', 'balance', 'total', 'amount', 'date', 'time', 'bank', 'statement', 'page', 'none', 'null', 'unknown']
        if clean_account.lower() in excluded_words:
            print_and_log(f"❌ Account number validation failed: excluded word: '{clean_account}'")
            return False
        
        # Must contain at least some alphanumeric characters
        if not clean_account.replace("-", "").replace(" ", "").replace("_", "").isalnum():
            print_and_log(f"❌ Account number validation failed: not alphanumeric: '{clean_account}'")
            return False
        
        # Additional validation: check for patterns that suggest partial/masked numbers
        # Reject if it's all the same character (like "0000", "1111", "xxxx")
        unique_chars = set(clean_account.replace("-", "").replace(" ", "").replace("_", ""))
        if len(unique_chars) == 1:
            print_and_log(f"❌ Account number validation failed: all same character: '{clean_account}'")
            return False
        
        # Special case: reject common partial account numbers that are often the result of masking
        # These are typically the last 4 digits of a masked account number like "*5594"
        if len(clean_account) == 4 and clean_account.isdigit():
            print_and_log(f"❌ Account number validation failed: likely partial/masked 4-digit number: '{clean_account}'")
            return False
        
        # If we get here, the account number passed all checks
        print_and_log(f"✅ Account number validation passed: '{account_str}' -> '{clean_account}'")
        return True
    
    # Test cases
    test_cases = [
        # Should be REJECTED
        ("*5594", False, "Asterisk at beginning"),
        ("5594*", False, "Asterisk at end"), 
        ("55*94", False, "Asterisk in middle"),
        ("5594", False, "4-digit number (likely partial)"),
        ("1234", False, "4-digit number (likely partial)"),
        ("0000", False, "All same digits"),
        ("xxxx", False, "Masked with x"),
        ("####", False, "Masked with #"),
        ("acc", False, "Too short"),
        ("account", False, "Excluded word"),
        
        # Should be ACCEPTED
        ("12345", True, "5-digit number"),
        ("ABC123456789", True, "Long alphanumeric"),
        ("1234567890", True, "10-digit number"),
        ("ACC-123-456", True, "With dashes"),
        ("123 456 789", True, "With spaces"),
        ("A1B2C3D4E5", True, "Mixed alphanumeric"),
        ("XXXXXXXXX123456", True, "Long with X at beginning"),
    ]
    
    print("Testing validation logic:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for account, expected, description in test_cases:
        result = is_valid_account_number(account)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        expectation = "ACCEPT" if expected else "REJECT"
        
        print(f"{status} '{account}' -> {result} (expected {expectation}) - {description}")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The validation should now correctly reject 5594.")
    else:
        print("⚠️  Some tests failed. Review the logic.")

if __name__ == "__main__":
    test_enhanced_validation()
