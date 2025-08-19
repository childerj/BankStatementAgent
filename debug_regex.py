#!/usr/bin/env python3
"""
Debug Account Number Regex Patterns
"""
import re

def debug_regex_patterns():
    """Debug specific failing patterns"""
    
    # Failing test cases
    failing_cases = [
        "Account #: 987654321",
        "A/C#: 456789123", 
        "Account ending in 9876"
    ]
    
    # All patterns to test
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
    
    print("🔍 DEBUGGING REGEX PATTERNS")
    print("=" * 50)
    
    for text in failing_cases:
        print(f"\nTesting: '{text}'")
        text_lower = text.lower()
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                print(f"  Pattern {i+1}: {pattern}")
                print(f"  Matches: {matches}")
            else:
                # Try without case sensitivity
                matches_case = re.findall(pattern, text)
                if matches_case:
                    print(f"  Pattern {i+1} (case sensitive): {pattern}")
                    print(f"  Matches: {matches_case}")
        
        # Manual pattern testing
        print(f"  Raw text: '{text}'")
        print(f"  Lower text: '{text_lower}'")
        
        # Test individual parts
        if "#:" in text:
            print("  Contains '#:'")
        if "# :" in text:
            print("  Contains '# :'")

if __name__ == "__main__":
    debug_regex_patterns()
