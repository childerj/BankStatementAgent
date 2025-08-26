"""
Enhanced OCR account extraction - find any "Account" label and extract contiguous numbers to the right
"""

import re

def extract_account_from_ocr_enhanced(text):
    """
    Enhanced account extraction from OCR text
    - Find any label containing "Account"
    - Extract contiguous numbers to the right as the account number
    """
    
    print("🔍 Enhanced OCR Account Extraction")
    print("=" * 50)
    
    lines = text.split('\n')
    print(f"Processing {len(lines)} lines of OCR text...")
    
    found_accounts = []
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Look for any variation of "Account" in the line (case insensitive)
        if re.search(r'\baccount\b', line_stripped, re.IGNORECASE):
            print(f"\nLine {line_num}: {line_stripped}")
            
            # Find the position of "Account" in the line
            account_match = re.search(r'\baccount\b', line_stripped, re.IGNORECASE)
            if account_match:
                account_start = account_match.start()
                account_end = account_match.end()
                
                # Get everything after "Account"
                after_account = line_stripped[account_end:].strip()
                print(f"  After 'Account': '{after_account}'")
                
                # Look for patterns like "No.", "Number", "#", ":" etc. followed by numbers
                # Pattern 1: Account [No./Number/#/ID] [:.] [spaces] [numbers]
                label_pattern = r'^[^0-9]*?(\d+)'
                label_match = re.search(label_pattern, after_account)
                
                if label_match:
                    # Extract contiguous numbers
                    number_start = label_match.start(1)
                    potential_account = label_match.group(1)
                    
                    # Continue extracting contiguous digits
                    remaining_text = after_account[label_match.end(1):]
                    additional_digits = re.match(r'^(\d*)', remaining_text)
                    if additional_digits and additional_digits.group(1):
                        potential_account += additional_digits.group(1)
                    
                    print(f"  → Found contiguous numbers: '{potential_account}'")
                    
                    # Validate the account number (reasonable length)
                    if len(potential_account) >= 4 and len(potential_account) <= 20:
                        found_accounts.append({
                            'line_number': line_num,
                            'line_text': line_stripped,
                            'account_number': potential_account,
                            'context': f"Line {line_num}: {line_stripped}"
                        })
                        print(f"  ✅ Valid account number: '{potential_account}'")
                    else:
                        print(f"  ❌ Invalid length: '{potential_account}' ({len(potential_account)} digits)")
                else:
                    # Also check if there are numbers at the beginning of the next line
                    if line_num < len(lines):
                        next_line = lines[line_num].strip()
                        if next_line:
                            next_line_numbers = re.match(r'^(\d+)', next_line)
                            if next_line_numbers:
                                potential_account = next_line_numbers.group(1)
                                print(f"  Next line has numbers: '{potential_account}'")
                                
                                if len(potential_account) >= 4 and len(potential_account) <= 20:
                                    found_accounts.append({
                                        'line_number': f"{line_num}-{line_num+1}",
                                        'line_text': f"{line_stripped} | {next_line}",
                                        'account_number': potential_account,
                                        'context': f"Lines {line_num}-{line_num+1}: {line_stripped} → {next_line}"
                                    })
                                    print(f"  ✅ Valid account number from next line: '{potential_account}'")
    
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"Found {len(found_accounts)} potential account numbers:")
    
    for i, account_info in enumerate(found_accounts, 1):
        print(f"\n{i}. Account: '{account_info['account_number']}'")
        print(f"   Context: {account_info['context']}")
    
    # Return the first valid account number found, or None
    if found_accounts:
        best_account = found_accounts[0]['account_number']
        print(f"\n✅ SELECTED ACCOUNT: '{best_account}'")
        return best_account
    else:
        print(f"\n❌ NO ACCOUNT NUMBERS FOUND")
        return None

def test_enhanced_extraction():
    """Test the enhanced extraction with the 402_507_528.pdf OCR text"""
    
    # Sample OCR text from 402_507_528.pdf
    test_ocr = """SB
State Bank
P.O. Box 668 DeKalb, Texas 75559
402/507/528
WFC LIMITED PARTNERSHIP (DBA) WORLD FINANCE CORPORATION PO BOX 6429 GREENVILLE, SC 29606-6429
E
Member FDIC
LENDER
FINANCIAL SERVICES STATEMENT
Statement Date: 06/30/2025
Account No .:
37567 Page: 1
SMALL BUSINESS CHECKING SUMMARY
Type : REG Status : Active"""

    print("Testing enhanced OCR account extraction...")
    print("=" * 60)
    
    result = extract_account_from_ocr_enhanced(test_ocr)
    
    print(f"\n🎯 FINAL RESULT: {result}")
    
    return result

if __name__ == "__main__":
    test_enhanced_extraction()
