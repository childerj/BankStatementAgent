#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the enhanced bank name extraction logic for complex multi-word names
"""

def extract_complete_bank_name_from_line(line):
    """Extract complete bank name from a single line with advanced logic for complex names"""
    # Common bank name endings that indicate where to stop
    strong_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 'company', 'credit']
    # Common connecting words in bank names - these should NOT be endings
    connecting_words = ['of', 'and', '&', 'the', 'for', 'in', 'at', 'to']
    # Words that definitely indicate end of bank name
    stop_words = ['report', 'statement', 'date', 'page', 'account', 'balance', 'type', 'bai', 'test', 'customer', 'member', 'branch']
    
    words = line.split()
    if not words:
        return None
    
    # Strategy: Scan through words and find the LONGEST reasonable bank name
    # We'll look for natural completion points but prefer longer names
    
    candidate_names = []
    
    # Scan through possible ending points
    for i in range(1, min(len(words), 10)):  # Check up to 9 words
        word_lower = words[i].lower().rstrip('.,')
        
        # Immediate stop at obvious non-bank words
        if word_lower in stop_words:
            if i > 0:
                candidate_names.append(' '.join(words[:i]))
            break
        
        # If we hit a strong ending word, this could be an ending point
        if word_lower in strong_endings:
            # Check if there are connecting words after this that might extend the name
            has_extension = False
            if i + 1 < len(words):
                next_word = words[i + 1].lower().rstrip('.,')
                # If next word is a connector, keep going
                if next_word in connecting_words:
                    has_extension = True
                    # Look for the next logical ending after the connector
                    for j in range(i + 2, min(len(words), i + 6)):  # Look ahead up to 4 more words
                        future_word = words[j].lower().rstrip('.,')
                        if future_word in stop_words:
                            candidate_names.append(' '.join(words[:j]))
                            break
                        elif future_word in strong_endings:
                            candidate_names.append(' '.join(words[:j+1]))
                            break
                    else:
                        # No clear ending found, take a reasonable length
                        candidate_names.append(' '.join(words[:min(i + 5, len(words))]))
            
            # Always add the current ending as a candidate
            if not has_extension or not candidate_names:
                candidate_names.append(' '.join(words[:i+1]))
    
    # If no candidates found, try some fallback logic
    if not candidate_names:
        # Special case: If line starts with "Bank of [Something]", be more generous
        if len(words) >= 3 and words[0].lower() == 'bank' and words[1].lower() in connecting_words:
            # Take up to 8 words for "Bank of X Y Z..." patterns
            for i in range(3, min(len(words), 9)):
                word_lower = words[i].lower().rstrip('.,')
                if word_lower in stop_words:
                    candidate_names.append(' '.join(words[:i]))
                    break
            else:
                candidate_names.append(' '.join(words[:min(8, len(words))]))
        
        # Fallback: if reasonable length, take the whole line
        elif len(words) <= 8 and len(line) <= 80:
            candidate_names.append(line.strip())
    
    # Select the best candidate (prefer longer names that look complete)
    if candidate_names:
        # Remove duplicates and sort by length (prefer longer)
        unique_candidates = list(set(candidate_names))
        unique_candidates.sort(key=len, reverse=True)
        
        # Return the longest candidate that looks reasonable
        for candidate in unique_candidates:
            # Basic validation
            if (2 <= len(candidate) <= 80 and 
                any(c.isalpha() for c in candidate) and
                len(candidate.split()) >= 1):
                return candidate.strip()
    
    return None

# Test with challenging multi-word bank names
test_cases = [
    'Farmers and Merchants Bank of Central California',
    'Bank of the West',
    'Atlantic Union Bank',
    'Stock Yards Bank and Trust',
    'First National Bank of America',
    'Bank of New York Mellon Trust Company',
    'State Street Bank and Trust Company',
    'First United Bank and Trust Company',
    'Security National Bank and Trust',
    'Farmers and Merchants Bank',
    'Bank of America, N.A.',
    'JPMorgan Chase Bank, N.A.',
    'Wells Fargo Bank, National Association',
    'First Citizens Bank and Trust Company',
    'The Bank of New York Mellon Corporation',
    'VERABANK bai test Report Type:',
    'Farmers and Merchants Bank of Central California Statement',
    'Stock Yards Bank and Trust Account Summary'
]

print('ENHANCED BANK NAME EXTRACTION TEST:')
print('=' * 70)

successes = 0
for i, test_case in enumerate(test_cases, 1):
    result = extract_complete_bank_name_from_line(test_case)
    
    # Success criteria: Should capture multi-word names properly
    if 'Farmers and Merchants Bank of Central California' in test_case:
        expected_contains = 'Farmers and Merchants Bank of Central California'
        success = result and expected_contains in result
    elif 'Bank of the West' in test_case:
        success = result and 'Bank of the West' in result  
    elif 'Stock Yards Bank and Trust' in test_case:
        success = result and 'Stock Yards Bank and Trust' in result
    elif 'VERABANK' in test_case:
        success = result and result == 'VERABANK'
    else:
        # General success: got something meaningful and multi-word if expected
        success = result and len(result) > 2
    
    if success:
        successes += 1
    
    status = '✅' if success else '❌'
    print(f'{i:2d}. {test_case}')
    print(f'    -> {result} {status}')
    print()

print(f'SUCCESS RATE: {successes}/{len(test_cases)} = {(successes/len(test_cases)*100):.1f}%')

# Test the specific case mentioned
print()
print('SPECIFIC TEST: Farmers and Merchants Bank of Central California')
print('=' * 60)
specific_result = extract_complete_bank_name_from_line('Farmers and Merchants Bank of Central California')
print(f'Input:  "Farmers and Merchants Bank of Central California"')
print(f'Output: "{specific_result}"')
print(f'Match:  {specific_result == "Farmers and Merchants Bank of Central California"}')

# Additional debugging for the complex case
print()
print('DEBUGGING COMPLEX CASE:')
print('-' * 30)
line = 'Farmers and Merchants Bank of Central California'
words = line.split()
print(f'Words: {words}')
print(f'Word count: {len(words)}')

# Show step-by-step processing
strong_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 'company', 'credit']
connecting_words = ['of', 'and', '&', 'the', 'for', 'in', 'at', 'to']

print()
print('Step-by-step analysis:')
for i, word in enumerate(words):
    word_lower = word.lower().rstrip('.,')
    is_strong_ending = word_lower in strong_endings
    is_connecting = word_lower in connecting_words
    print(f'{i}: "{word}" -> strong_ending={is_strong_ending}, connecting={is_connecting}')
