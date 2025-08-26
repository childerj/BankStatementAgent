"""
Bank Information Loader and Matcher
Loads WAC Bank Information and provides fuzzy matching for bank names
"""

import pandas as pd
import yaml
import json
import os
from difflib import SequenceMatcher
from azure.storage.blob import BlobServiceClient

def load_local_settings():
    """Load environment variables from local.settings.json when running locally"""
    try:
        if os.path.exists('local.settings.json'):
            with open('local.settings.json', 'r') as f:
                settings = json.load(f)
                values = settings.get('Values', {})
                
                # Apply local settings without overriding existing environment variables
                for key, value in values.items():
                    if not os.getenv(key):
                        os.environ[key] = value
                        
                print("✅ Loaded local.settings.json for local development")
                return True
    except Exception as e:
        print(f"⚠️ Could not load local.settings.json: {e}")
        return False
    return True

def load_bank_information_yaml():
    """Load bank information from Azure storage and return as YAML"""
    
    try:
        # Load local settings if available
        load_local_settings()
        
        # Load connection string from environment
        connection_string = (
            os.getenv('AzureWebJobsStorage') or 
            os.getenv('DEPLOYMENT_STORAGE_CONNECTION_STRING')
        )
        
        if not connection_string:
            print("❌ No Azure Storage connection string found")
            return None, None
        
        # Azure storage details
        container_name = "bank-reconciliation"
        blob_path = "Bank_Data/WAC Bank Information.xlsx"
        
        print(f"🔄 Loading bank information from Azure Storage...")
        
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Download the file
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_path
        )
        
        # Download blob content
        blob_data = blob_client.download_blob()
        file_content = blob_data.readall()
        
        # Read as Excel with specific dtypes to ensure routing/account numbers are read as strings
        df = pd.read_excel(
            pd.io.common.BytesIO(file_content),
            dtype={
                'Routing Number': str,
                'Account Number': str
            }
        )
        
        print(f"✅ Loaded {len(df)} bank records")
        
        # Convert to YAML format
        bank_data = {
            'wac_banks': []
        }
        
        for _, row in df.iterrows():
            # Convert routing number properly, removing any .0 suffix from floats
            routing_number = str(row['Routing Number']).strip()
            if routing_number.endswith('.0'):
                routing_number = routing_number[:-2]
            
            # Convert account number properly, removing any .0 suffix from floats  
            account_number = str(row['Account Number']).strip()
            if account_number.endswith('.0'):
                account_number = account_number[:-2]
            
            bank_info = {
                'bank_name': str(row['Bank Name']).strip(),
                'address': str(row['Address']).strip(),
                'account_number': account_number,
                'routing_number': routing_number
            }
            bank_data['wac_banks'].append(bank_info)
        
        # Convert to YAML string
        yaml_content = yaml.dump(bank_data, default_flow_style=False, sort_keys=False)
        
        print(f"📄 Bank information converted to YAML format")
        return yaml_content, bank_data
        
    except Exception as e:
        print(f"❌ Error loading bank information: {e}")
        return None, None

def calculate_similarity(name1, name2):
    """Calculate similarity between two bank names"""
    
    # Normalize names for comparison
    norm1 = normalize_bank_name(name1)
    norm2 = normalize_bank_name(name2)
    
    # Calculate similarity ratio
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    return similarity

def normalize_bank_name(bank_name):
    """Normalize bank name for comparison with improved matching"""
    
    if not bank_name:
        return ""
    
    # Convert to uppercase for consistency
    normalized = str(bank_name).upper().strip()
    
    # Standardize common punctuation and spacing
    import re
    normalized = re.sub(r'[,\.]+', '', normalized)  # Remove commas and periods
    normalized = re.sub(r'\s+', ' ', normalized)    # Normalize spaces
    
    # Handle specific bank name variations that are causing low similarity scores
    # These transformations make bank names more similar for matching
    
    # Handle "Stock Yards" vs "STOCKYARDS" spacing issue
    normalized = re.sub(r'\bSTOCK\s+YARDS\b', 'STOCKYARDS', normalized)
    normalized = re.sub(r'\bSTOCKYARDS\b', 'STOCK YARDS', normalized)  # Normalize to spaced version
    
    # Standardize ampersand and "AND" - make them equivalent by removing both
    # This helps "Community Bank" match "Community Bank & Trust"
    normalized = re.sub(r'\s*&\s*', ' ', normalized)
    normalized = re.sub(r'\s+AND\s+', ' ', normalized)
    
    # Remove common bank suffixes that add noise to matching
    # This helps core bank names match better
    remove_suffixes = [
        r'\s+TRUST\s*$',
        r'\s+TRUST\s+COMPANY\s*$', 
        r'\s+AND\s+TRUST\s*$',
        r'\s+COMPANY\s*$',
        r'\s+N\.?A\.?\s*$',
        r'\s+NA\s*$',
        r'\s+INC\.?\s*$',
        r'\s+CORPORATION\s*$',
        r'\s+CORP\.?\s*$'
    ]
    
    for suffix_pattern in remove_suffixes:
        normalized = re.sub(suffix_pattern, '', normalized)
    
    # Standardize other common terms
    replacements = {
        'FEDERAL CREDIT UNION': 'FCU',
        'CREDIT UNION': 'CU',
        'NATIONAL BANK': 'BANK',
        'STATE BANK': 'BANK',
        'COMMUNITY BANK': 'COMMUNITY',  # Remove redundant "BANK" 
    }
    
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    
    # Final cleanup - remove extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized.strip()

def extract_account_digits(account_string):
    """Extract unmasked digits from a masked account number"""
    if not account_string:
        return ""
    
    # Remove common masking characters and extract digits
    import re
    # Remove asterisks, X's, dashes, spaces
    cleaned = re.sub(r'[*Xx\-\s]', '', str(account_string))
    # Extract only digits
    digits = re.findall(r'\d+', cleaned)
    return ''.join(digits) if digits else ""

def validate_account_match(detected_account, wac_account):
    """Validate if detected account matches WAC account number"""
    if not detected_account or not wac_account:
        return False, 0.0
    
    detected_digits = extract_account_digits(detected_account)
    wac_digits = str(wac_account).strip()
    
    if not detected_digits:
        return False, 0.0
    
    # Check if detected digits match the end of WAC account
    if wac_digits.endswith(detected_digits):
        # If the unmasked digits match the end, it's a 100% account validation
        return True, 1.0
    
    return False, 0.0

def find_matching_bank_with_account(detected_bank_name, detected_account=None, bank_data=None, threshold=0.70):
    """Find matching bank from WAC bank data with bank name and optional account validation"""
    
    if not detected_bank_name or not bank_data:
        return None, 0.0, {}
    
    best_match = None
    best_similarity = 0.0
    best_details = {}
    
    # Search quietly through all banks, only report the result
    for bank_info in bank_data.get('wac_banks', []):
        wac_bank_name = bank_info['bank_name']
        wac_account = bank_info['account_number']
        
        # Calculate bank name similarity
        name_similarity = calculate_similarity(detected_bank_name, wac_bank_name)
        
        # Account validation
        account_valid = False
        account_match_ratio = 0.0
        
        if detected_account:
            account_valid, account_match_ratio = validate_account_match(detected_account, wac_account)
        
        # Combined score calculation
        if detected_account and account_valid:
            # If account validation is successful, heavily weight the account match
            # Weight: 25% name similarity + 75% account validation
            combined_similarity = (name_similarity * 0.25) + (account_match_ratio * 0.75)
            match_details = {
                'name_similarity': name_similarity,
                'account_valid': account_valid,
                'account_match_ratio': account_match_ratio,
                'combined_score': combined_similarity,
                'validation_type': 'name_and_account'
            }
        else:
            # No account provided or no account match, use name similarity only
            combined_similarity = name_similarity
            match_details = {
                'name_similarity': name_similarity,
                'account_valid': False,
                'account_match_ratio': 0.0,
                'combined_score': combined_similarity,
                'validation_type': 'name_only'
            }
        
        # Track best match (removed verbose logging for cleaner output)
        if combined_similarity > best_similarity:
            best_similarity = combined_similarity
            best_match = bank_info
            best_details = match_details
    
    if best_similarity >= threshold:
        validation_msg = ""
        if best_details.get('account_valid'):
            validation_msg = f" with account validation ({best_details['account_match_ratio'] * 100:.1f}%)"
        
        print(f"✅ Found match: '{best_match['bank_name']}' ({best_similarity * 100:.1f}%{validation_msg})")
        print(f"   Account Number: {best_match['account_number']}")
        print(f"   Routing Number: {best_match['routing_number']}")
        return best_match, best_similarity, best_details
    else:
        print(f"❌ No match found above {threshold * 100}% threshold (best: {best_similarity * 100:.1f}%)")
        return None, best_similarity, best_details

def find_matching_bank(detected_bank_name, bank_data, threshold=0.8):
    """Find matching bank from WAC bank data with similarity threshold (legacy function)"""
    match, similarity, _ = find_matching_bank_with_account(detected_bank_name, None, bank_data, threshold)
    return match, similarity

def get_bank_info_for_processing(detected_bank_name, detected_account=None):
    """Get bank information for BAI2 processing with fallback logic"""
    
    print(f"\n🏦 Bank Information Lookup")
    print(f"=" * 50)
    
    # Load bank information
    yaml_content, bank_data = load_bank_information_yaml()
    
    if not bank_data:
        print("⚠️ Could not load WAC bank information, using current methods")
        return None, None, "fallback"
    
    # YAML content loaded (removed detailed printing to reduce log noise)
    print(f"📄 WAC Bank Information loaded ({len(bank_data['wac_banks'])} banks available)")
    
    # Find matching bank with enhanced account validation
    match, similarity, details = find_matching_bank_with_account(
        detected_bank_name, 
        detected_account, 
        bank_data, 
        threshold=0.70  # Lowered to handle edge cases like "Community Bank" vs "Community Bank & Trust"
    )
    
    if match:
        validation_info = ""
        # Only treat as WAC match if account validation was successful
        if details.get('account_valid'):
            validation_info = f" (with account validation)"
            print(f"\n✅ Using WAC bank information for processing{validation_info}")
            return match['account_number'], match['routing_number'], "wac_match"
        else:
            print(f"\n⚠️ Bank name matched but account validation failed")
            print(f"   This appears to be a customer statement, not a WAC operational account")
            return None, None, "customer_statement_detected"
    else:
        print(f"\n⚠️ No sufficient match found, using current methods")
        return None, None, "fallback"

def get_routing_for_extracted_account(detected_bank_name, extracted_account_number):
    """Get routing number for an extracted account number (for customer statements)
    
    This function is specifically for customer statements where we want to:
    1. Use the account number extracted from the PDF 
    2. Get the routing number from the bank database based on bank name match
    
    Args:
        detected_bank_name: Bank name extracted from statement
        extracted_account_number: Account number extracted from statement
        
    Returns:
        tuple: (extracted_account_number, routing_number, match_type) or (None, None, "no_match")
    """
    
    print(f"\n🏦 Customer Statement Processing")
    print(f"=" * 50)
    print(f"📋 Extracted Account: {extracted_account_number}")
    print(f"🏛️ Bank Name: {detected_bank_name}")
    
    # Load bank information
    yaml_content, bank_data = load_bank_information_yaml()
    
    if not bank_data:
        print("⚠️ Could not load bank information")
        return None, None, "no_data"
    
    print(f"📄 Bank database loaded ({len(bank_data['wac_banks'])} banks available)")
    
    # Find bank by name only (not account validation since this is a customer statement)
    best_match = None
    best_similarity = 0.0
    
    for bank_info in bank_data.get('wac_banks', []):
        wac_bank_name = bank_info['bank_name']
        
        # Calculate bank name similarity
        name_similarity = calculate_similarity(detected_bank_name, wac_bank_name)
        
        if name_similarity > best_similarity and name_similarity >= 0.70:  # 70% threshold
            best_similarity = name_similarity
            best_match = bank_info
    
    if best_match:
        routing_number = best_match['routing_number']
        print(f"\n✅ Bank match found!")
        print(f"   Matched Bank: {best_match['bank_name']} ({best_similarity:.1%} similarity)")
        print(f"   Using extracted account: {extracted_account_number}")
        print(f"   Using database routing: {routing_number}")
        
        return extracted_account_number, routing_number, "customer_statement"
    else:
        print(f"\n❌ No bank match found (best similarity: {best_similarity:.1%})")
        return None, None, "no_match"

def get_routing_for_account_number(extracted_account_number, extracted_bank_name=None):
    """Get routing number by looking up the exact account number in the database
    
    This function looks up the extracted account number directly in the Excel database
    to find the corresponding routing number. This is the most accurate method.
    
    Args:
        extracted_account_number: Account number extracted from statement
        extracted_bank_name: Optional bank name for validation
        
    Returns:
        tuple: (account_number, routing_number, match_type) or (None, None, "no_match")
    """
    
    print(f"\n🏦 Account Number Database Lookup")
    print(f"=" * 50)
    print(f"📋 Looking up account: {extracted_account_number}")
    if extracted_bank_name:
        print(f"🏛️ Expected bank: {extracted_bank_name}")
    
    # Load bank information
    yaml_content, bank_data = load_bank_information_yaml()
    
    if not bank_data:
        print("⚠️ Could not load bank information")
        return None, None, "no_data"
    
    print(f"📄 Bank database loaded ({len(bank_data['wac_banks'])} banks available)")
    
    # Search for exact account number match first
    matching_records = []
    for bank_info in bank_data.get('wac_banks', []):
        if bank_info['account_number'] == extracted_account_number:
            matching_records.append(bank_info)
    
    if matching_records:
        # Found exact account match
        match = matching_records[0]  # Should only be one exact match
        
        print(f"\n✅ Exact account match found!")
        print(f"   Account: {match['account_number']}")
        print(f"   Bank: {match['bank_name']}")
        print(f"   Routing: {match['routing_number']}")
        print(f"   Address: {match['address']}")
        
        # Validate bank name if provided
        if extracted_bank_name:
            name_similarity = calculate_similarity(extracted_bank_name, match['bank_name'])
            print(f"   Bank name validation: {name_similarity:.1%} similarity")
            if name_similarity < 0.7:
                print(f"⚠️ Warning: Bank name mismatch detected!")
                print(f"   PDF shows: {extracted_bank_name}")
                print(f"   Database shows: {match['bank_name']}")
        
        return match['account_number'], match['routing_number'], "exact_account_match"
    
    # If no exact match, try partial/masked account matching
    print(f"\n🔍 No exact match found, trying partial/masked account matching...")
    extracted_digits = extract_account_digits(extracted_account_number)
    
    if extracted_digits and len(extracted_digits) >= 4:  # Need at least 4 digits for matching
        print(f"   Extracted digits: {extracted_digits}")
        
        partial_matches = []
        for bank_info in bank_data.get('wac_banks', []):
            account_valid, match_ratio = validate_account_match(extracted_account_number, bank_info['account_number'])
            if account_valid:
                partial_matches.append((bank_info, match_ratio))
        
        if partial_matches:
            # Sort by match ratio (highest first) and bank name similarity if provided
            if extracted_bank_name:
                def match_score(item):
                    bank_info, account_ratio = item
                    name_similarity = calculate_similarity(extracted_bank_name, bank_info['bank_name'])
                    # Combined score: 60% account match + 40% name match
                    return (account_ratio * 0.6) + (name_similarity * 0.4)
                partial_matches.sort(key=match_score, reverse=True)
            else:
                partial_matches.sort(key=lambda x: x[1], reverse=True)  # Sort by account ratio only
            
            best_match, best_ratio = partial_matches[0]
            
            print(f"\n✅ Partial account match found!")
            print(f"   Account: {best_match['account_number']}")
            print(f"   Bank: {best_match['bank_name']}")
            print(f"   Routing: {best_match['routing_number']}")
            print(f"   Match Quality: {best_ratio:.1%}")
            
            # Validate bank name if provided
            if extracted_bank_name:
                name_similarity = calculate_similarity(extracted_bank_name, best_match['bank_name'])
                print(f"   Bank name validation: {name_similarity:.1%} similarity")
                if name_similarity < 0.7:
                    print(f"⚠️ Warning: Bank name mismatch detected!")
            
            return best_match['account_number'], best_match['routing_number'], "partial_account_match"
        else:
            print(f"   No partial matches found")
    else:
        print(f"   Insufficient digits for partial matching (need at least 4)")
    
    print(f"\n❌ Account number {extracted_account_number} not found in database")
    
    # If exact account not found, fall back to bank name matching
    if extracted_bank_name:
        print(f"🔄 Falling back to bank name matching...")
        return get_routing_for_extracted_account(extracted_bank_name, extracted_account_number)
    else:
        return None, None, "no_match"

# Test function for local testing
def test_bank_matcher():
    """Test the bank matching functionality"""
    
    print("🧪 Testing Bank Matcher")
    print("=" * 50)
    
    # Test cases
    test_banks = [
        "Stock Yards Bank",
        "VeraBank", 
        "Community Bank",
        "Citizens Bank of Kentucky",
        "Prosperity Bank",
        "Wells Fargo",  # Should not match
        "Chase",        # Should not match
    ]
    
    for test_bank in test_banks:
        print(f"\n📋 Testing: '{test_bank}'")
        account, routing, method = get_bank_info_for_processing(test_bank)
        
        if method == "wac_match":
            print(f"   ✅ Match found - Account: {account}, Routing: {routing}")
        else:
            print(f"   ❌ No match - Will use fallback method")

def test_bank_matcher_with_accounts():
    """Test the bank matching functionality with account validation"""
    
    print("\n🧪 Testing Bank Matcher with Account Validation")
    print("=" * 60)
    
    # Test cases with masked account numbers
    test_cases = [
        # (bank_name, masked_account, expected_wac_account)
        ("Stock Yards Bank", "*5133", "2375133"),      # Last 4 digits match
        ("Stock Yards Bank", "***5133", "2375133"),    # Last 4 digits match
        ("Stock Yards Bank", "*1234", "2375133"),      # Last 4 don't match
        ("VeraBank", "*2999", "1035012999"),           # Last 4 digits match  
        ("VeraBank", "XXXX2999", "1035012999"),        # Last 4 digits match
        ("Community Bank", "*4211", "13024211"),       # Last 4 digits match
        ("Prosperity Bank", "*6452", "6800416452"),    # Last 4 digits match
        ("Citizens Bank", "*5594", "21065594"),        # Last 4 digits match
        ("Wells Fargo", "*1234", None),                # Bank doesn't exist, should fail
    ]
    
    for bank_name, masked_account, expected_account in test_cases:
        print(f"\n📋 Testing: '{bank_name}' with account '{masked_account}'")
        account, routing, method = get_bank_info_for_processing(bank_name, masked_account)
        
        if method == "wac_match":
            print(f"   ✅ Match found - Account: {account}, Routing: {routing}")
            if expected_account and account == expected_account:
                print(f"   ✅ Account validation successful!")
            elif expected_account:
                print(f"   ⚠️ Account mismatch - Expected: {expected_account}, Got: {account}")
        else:
            print(f"   ❌ No match - Will use fallback method")

if __name__ == "__main__":
    # Run both tests if executed directly
    test_bank_matcher()
    test_bank_matcher_with_accounts()
