#!/usr/bin/env python3

def test_account_extraction_debug():
    """Debug the account number extraction to see what's happening"""
    
    # Simulate the text that would be extracted from CBoKActivity (5).pdf
    test_text = """
    Account Number: *5594
    Beginning Balance: $943.22
    Ending Balance: $19,646.90
    Account: *5594
    Acct: *5594
    """
    
    print("🔍 DEBUGGING ACCOUNT NUMBER EXTRACTION")
    print("=" * 60)
    print(f"Test text:\n{test_text}")
    print("-" * 40)
    
    # Test the regex patterns that should be in function_app.py
    import re
    
    # Pattern that should capture asterisks
    patterns = [
        r'(?:account\s*(?:number|#)?|acct\.?)\s*:?\s*([*\d\w\-]+)',
        r'account\s*:?\s*([*\d\w\-]+)',
        r'acct\.?\s*:?\s*([*\d\w\-]+)',
        r'account\s*number\s*:?\s*([*\d\w\-]+)'
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"Pattern {i}: {pattern}")
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        print(f"Matches: {matches}")
        
        for match in matches:
            print(f"  Found: '{match}'")
            if '*' in match:
                print(f"  ✅ Contains asterisk - should be INVALID")
            else:
                print(f"  ❌ No asterisk - would be treated as valid")
        print()
    
    # Test validation function
    def is_valid_account_number(account_num):
        if not account_num or len(account_num.strip()) < 4:
            return False
        if '*' in account_num:
            return False
        return True
    
    test_numbers = ['5594', '*5594', '**5594', '5594*', '*55*94']
    
    print("VALIDATION TESTS:")
    print("-" * 20)
    for test_num in test_numbers:
        result = is_valid_account_number(test_num)
        status = "✅ VALID" if result else "❌ INVALID"
        print(f"'{test_num}' -> {status}")

if __name__ == "__main__":
    test_account_extraction_debug()
