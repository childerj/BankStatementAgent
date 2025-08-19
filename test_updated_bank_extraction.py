#!/usr/bin/env python3
"""
Test the updated bank name extraction function
"""

import re

def print_and_log(message):
    """Simple print function"""
    print(message)

def extract_bank_name_from_text(text):
    """Extract bank name from statement text"""
    print_and_log("🏦 Searching for bank name in statement text...")
    
    # Common bank name patterns - ordered by specificity (most specific first)
    bank_patterns = [
        r'(Stock\s+Yards\s+Bank(?:\s+&\s+Trust)?)',  # "Stock Yards Bank" or "Stock Yards Bank & Trust"
        r'(Wells\s+Fargo)',  # "Wells Fargo" - specific pattern first
        r'(Bank\s+of\s+[A-Z][a-z]+)',  # "Bank of America"
        r'(Chase)',  # "Chase"
        r'(Citibank)',  # "Citibank"
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+Bank(?:\s+&\s+Trust)?)',  # "First National Bank" or "Stock Yards Bank"
        r'([A-Z][a-z]+\s+National\s+Bank)',  # "First National Bank"
        r'([A-Z][a-z]+\s+Federal\s+Credit\s+Union)',  # "Navy Federal Credit Union"
        r'([A-Z][a-z]+\s+Credit\s+Union)',  # "First Credit Union"
        r'([A-Z][a-z]+\s+Trust)',  # "First Trust"
        r'([A-Z][a-z]+\s+Bank)',  # "First Bank" - more general pattern (last)
        r'([A-Z][a-z]+\s+Financial)',  # "Wells Financial"
        r'([A-Z][a-z]+\s+Federal)',  # "Navy Federal"
        r'([A-Z][a-z]+\s+Savings)',  # "First Savings"
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            bank_name = matches[0].strip()
            print_and_log(f"🏦 Found bank name: {bank_name}")
            return bank_name
    
    # Try to find bank name near common keywords
    lines = text.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        if any(keyword in line.lower() for keyword in ['bank', 'financial', 'credit union', 'trust']):
            # Extract bank name from this line
            words = line.split()
            for i, word in enumerate(words):
                if word.lower() in ['bank', 'financial', 'trust']:
                    if i > 0:
                        potential_name = ' '.join(words[max(0, i-2):i+1])
                        print_and_log(f"🏦 Found potential bank name: {potential_name}")
                        return potential_name.strip()
    
    print_and_log("❌ No bank name found in statement text")
    return None

def test_bank_name_extraction():
    """Test bank name extraction with different text samples"""
    
    test_cases = [
        {
            "name": "Stock Yards Bank & Trust",
            "text": "Stock Yards Bank & Trust SINCE 1904\nWACBAI2\nReport Type:",
            "expected": "Stock Yards Bank & Trust"
        },
        {
            "name": "Stock Yards Bank",
            "text": "Stock Yards Bank\nWACBAI2\nReport Type:",
            "expected": "Stock Yards Bank"
        },
        {
            "name": "Wells Fargo",
            "text": "Wells Fargo Bank\nStatement\nAccount Information:",
            "expected": "Wells Fargo"
        },
        {
            "name": "First National Bank",
            "text": "First National Bank\nMonthly Statement\nAccount:",
            "expected": "First National Bank"
        }
    ]
    
    print_and_log("🧪 TESTING BANK NAME EXTRACTION")
    print_and_log("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print_and_log(f"\nTest {i}: {test_case['name']}")
        print_and_log("-" * 30)
        print_and_log(f"Text: {test_case['text'][:50]}...")
        print_and_log(f"Expected: {test_case['expected']}")
        
        result = extract_bank_name_from_text(test_case['text'])
        
        if result == test_case['expected']:
            print_and_log(f"✅ PASS: Got '{result}'")
        else:
            print_and_log(f"❌ FAIL: Expected '{test_case['expected']}', got '{result}'")

if __name__ == "__main__":
    test_bank_name_extraction()
