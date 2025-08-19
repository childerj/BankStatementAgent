#!/usr/bin/env python3
import re

def test_comprehensive_account_extraction():
    """Test the full account extraction flow to find where *5594 becomes 5594"""
    
    print("🔍 COMPREHENSIVE ACCOUNT EXTRACTION TEST")
    print("=" * 60)
    
    # Test data that would come from Document Intelligence
    test_cases = [
        {"name": "Direct OCR", "text": "Account Number: *5594"},
        {"name": "Field Content", "text": "*5594"},
        {"name": "Cleaned Content", "text": "5594"},  # What happens after .replace() calls
        {"name": "Mixed Format", "text": "Account: *5594 Balance: $1000"},
    ]
    
    # Current regex patterns from function_app.py
    patterns = [
        r'account\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'account\s*number\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'acct\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'a/c\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'account\s+([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'(?:^|\s)([A-Za-z0-9\-\*]+)\s+account(?:\s|$)',
        r'for\s*account\s+([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'ending\s*in\s+([A-Za-z0-9\*]+)(?:\s|$)',
        r'account\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'a/c\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'acct\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',
        r'(?:^|\s)([A-Za-z0-9\-\*]{8,})(?:\s|$)',
    ]
    
    def is_valid_account_number(account_number):
        """Current validation logic from function_app.py"""
        if "**" in str(account_number) or "*" in str(account_number):
            return False
        account_str = str(account_number).strip().lower()
        if len(account_str) < 4:
            return False
        excluded_words = ['number', 'account', 'acct', 'balance', 'total', 'amount', 'date', 'time', 'bank', 'statement']
        if account_str in excluded_words:
            return False
        if not account_str.replace("-", "").replace(" ", "").isalnum():
            return False
        return True
    
    def extract_account_number_from_text(text):
        """Current extraction logic from function_app.py"""
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if is_valid_account_number(match):
                    return match
                else:
                    if "*" in match:
                        print(f"    ❌ Found masked account number: {match} - rejected")
                    else:
                        print(f"    ❌ Found invalid account number: {match} - rejected")
        return None
    
    def simulate_field_cleaning(content):
        """Simulate the field cleaning logic from line 525"""
        return content.replace("-", "").replace(" ", "")
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"   Input: '{test_case['text']}'")
        
        # Test direct extraction
        result = extract_account_number_from_text(test_case['text'])
        print(f"   Direct extraction result: {result}")
        
        # Test with field cleaning
        cleaned = simulate_field_cleaning(test_case['text'])
        print(f"   After field cleaning: '{cleaned}'")
        
        # Test if cleaned version would be valid
        if cleaned != test_case['text']:
            if is_valid_account_number(cleaned):
                print(f"   🚨 PROBLEM: Cleaned version '{cleaned}' would be accepted as valid!")
            else:
                print(f"   ✅ Cleaned version '{cleaned}' correctly rejected")
        
        print()
    
    print("🎯 ANALYSIS:")
    print("-" * 40)
    print("The issue is likely in the field cleaning logic (line 525):")
    print("  clean_content = content.replace('-', '').replace(' ', '')")
    print()
    print("This removes dashes and spaces but NOT asterisks.")
    print("However, Document Intelligence might be extracting '*5594' as a field,")
    print("and then the .replace() calls don't remove the asterisk.")
    print()
    print("But somewhere the asterisk is being lost...")
    print()
    print("RECOMMENDATION: Add logging to track exactly what's happening")

if __name__ == "__main__":
    test_comprehensive_account_extraction()
