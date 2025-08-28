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
        
        print(f"✅ Loaded {len(df)} bank records from Excel file")
        
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

def find_accounts_ending_with(last_digits, yaml_data):
    """Find all accounts in WAC database that end with the specified digits"""
    if not last_digits or not yaml_data:
        return []
    
    matching_accounts = []
    
    try:
        for bank_name, bank_data in yaml_data.items():
            if isinstance(bank_data, dict) and 'accounts' in bank_data:
                for account_info in bank_data['accounts']:
                    account_number = str(account_info.get('account_number', ''))
                    
                    # Check if account ends with the specified digits
                    if account_number.endswith(last_digits):
                        matching_accounts.append({
                            'bank_name': bank_name,
                            'full_account': account_number,
                            'routing_number': account_info.get('routing_number', ''),
                            'bank_data': bank_data
                        })
    
    except Exception as e:
        print(f"❌ Error searching for accounts ending with {last_digits}: {e}")
    
    return matching_accounts

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
    """Find matching bank from WAC bank data based ONLY on account number - no bank name matching"""
    
    if not detected_account or not bank_data:
        return None, 0.0, {}
    
    print(f"🔍 ACCOUNT-ONLY MATCHING: Looking for account '{detected_account}' in WAC database")
    
    # Extract digits from detected account for partial/masked matching
    detected_digits = extract_account_digits(detected_account)
    print(f"   Extracted digits from account: '{detected_digits}'")
    
    # Check if this is a partial account (XXXXXX0327 format) or masked account (***95 format)
    is_partial_account = detected_account.startswith('XXXXXX') and len(detected_account) == 10
    is_masked_account = detected_account.startswith('***') and len(detected_digits) >= 2
    
    if is_partial_account:
        last_four_digits = detected_account[-4:]
        print(f"🎯 PARTIAL ACCOUNT DETECTED: Looking for accounts ending in '{last_four_digits}'")
        
        # Find all accounts ending with these 4 digits
        matching_accounts = []
        for bank_info in bank_data.get('wac_banks', []):
            wac_account = str(bank_info['account_number']).strip()
            if wac_account.endswith(last_four_digits):
                matching_accounts.append(bank_info)
                print(f"   ✅ Found candidate: {wac_account} from {bank_info['bank_name']}")
        
        if len(matching_accounts) == 1:
            # Single match - use it
            match = matching_accounts[0]
            print(f"✅ SINGLE PARTIAL MATCH: {match['account_number']}")
            print(f"   Bank: {match['bank_name']}")
            print(f"   Routing: {match['routing_number']}")
            return match, 1.0, {'account_valid': True, 'match_type': 'partial_single'}
        elif len(matching_accounts) > 1:
            # Multiple matches - try to disambiguate with bank name if provided
            if detected_bank_name:
                print(f"🔄 Multiple matches found - using bank name '{detected_bank_name}' to disambiguate")
                print(f"📊 Found {len(matching_accounts)} accounts ending in '{last_four_digits}':")
                
                best_match = None
                best_similarity = 0.0
                all_similarities = []
                
                for candidate in matching_accounts:
                    similarity = calculate_similarity(detected_bank_name, candidate['bank_name'])
                    all_similarities.append((candidate, similarity))
                    print(f"   {candidate['account_number']} ({candidate['bank_name']}): {similarity:.1%} similarity")
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = candidate
                
                # Check if best match meets the 50% threshold
                if best_match and best_similarity >= 0.5:
                    print(f"✅ DISAMBIGUATED PARTIAL MATCH: {best_match['account_number']}")
                    print(f"   Bank: {best_match['bank_name']} ({best_similarity:.1%} similarity)")
                    print(f"   Routing: {best_match['routing_number']}")
                    return best_match, best_similarity, {'account_valid': True, 'match_type': 'partial_disambiguated'}
                else:
                    # Bank name similarity below 50% - return specific error details
                    print(f"❌ Could not disambiguate - bank name similarity too low (best: {best_similarity:.1%})")
                    print(f"🚨 MULTIPLE ACCOUNT MATCHES with insufficient bank name similarity:")
                    
                    candidate_details = []
                    for candidate, similarity in all_similarities:
                        candidate_details.append({
                            'account': candidate['account_number'],
                            'bank': candidate['bank_name'],
                            'routing': candidate['routing_number'],
                            'similarity': similarity
                        })
                    
                    return None, best_similarity, {
                        'account_valid': False, 
                        'match_type': 'multiple_accounts_low_similarity',
                        'ending_digits': last_four_digits,
                        'candidate_count': len(matching_accounts),
                        'best_similarity': best_similarity,
                        'candidates': candidate_details,
                        'detected_bank': detected_bank_name
                    }
            else:
                print(f"❌ Multiple accounts end with '{last_four_digits}' - need bank name to disambiguate")
                print(f"📊 Found {len(matching_accounts)} matching accounts:")
                
                candidate_details = []
                for candidate in matching_accounts:
                    print(f"   {candidate['account_number']} ({candidate['bank_name']})")
                    candidate_details.append({
                        'account': candidate['account_number'],
                        'bank': candidate['bank_name'],
                        'routing': candidate['routing_number'],
                        'similarity': 0.0
                    })
                
                return None, 0.0, {
                    'account_valid': False, 
                    'match_type': 'multiple_accounts_no_bank_name',
                    'ending_digits': last_four_digits,
                    'candidate_count': len(matching_accounts),
                    'candidates': candidate_details,
                    'detected_bank': detected_bank_name or 'Not provided'
                }
            
            print(f"❌ AMBIGUOUS PARTIAL MATCH: {len(matching_accounts)} accounts end with '{last_four_digits}'")
            return None, 0.0, {'account_valid': False, 'match_type': 'ambiguous'}
        else:
            print(f"❌ NO PARTIAL MATCH: No accounts end with '{last_four_digits}'")
            return None, 0.0, {'account_valid': False, 'match_type': 'none'}
    
    # Handle masked accounts (***95 format)
    elif is_masked_account:
        print(f"🎯 MASKED ACCOUNT DETECTED: Looking for accounts ending in '{detected_digits}'")
        
        # Find all accounts ending with these digits
        matching_accounts = []
        for bank_info in bank_data.get('wac_banks', []):
            wac_account = str(bank_info['account_number']).strip()
            if wac_account.endswith(detected_digits):
                matching_accounts.append(bank_info)
                print(f"   ✅ Found candidate: {wac_account} from {bank_info['bank_name']}")
        
        if len(matching_accounts) == 1:
            # Single match - use it
            match = matching_accounts[0]
            print(f"✅ SINGLE MASKED MATCH: {match['account_number']}")
            print(f"   Bank: {match['bank_name']}")
            print(f"   Routing: {match['routing_number']}")
            return match, 1.0, {'account_valid': True, 'match_type': 'masked_single'}
        elif len(matching_accounts) > 1:
            # Multiple matches - try to disambiguate with bank name if provided
            if detected_bank_name:
                print(f"🔄 Multiple masked accounts found - using bank name '{detected_bank_name}' to disambiguate")
                print(f"📊 Found {len(matching_accounts)} accounts ending in '{detected_digits}':")
                
                best_match = None
                best_similarity = 0.0
                all_similarities = []
                
                for candidate in matching_accounts:
                    similarity = calculate_similarity(detected_bank_name, candidate['bank_name'])
                    all_similarities.append((candidate, similarity))
                    print(f"   {candidate['account_number']} ({candidate['bank_name']}): {similarity:.1%} similarity")
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = candidate
                
                # Check if best match meets the 50% threshold
                if best_match and best_similarity >= 0.5:
                    print(f"✅ DISAMBIGUATED MASKED MATCH: {best_match['account_number']}")
                    print(f"   Bank: {best_match['bank_name']} ({best_similarity:.1%} similarity)")
                    print(f"   Routing: {best_match['routing_number']}")
                    return best_match, best_similarity, {'account_valid': True, 'match_type': 'masked_disambiguated'}
                else:
                    # Bank name similarity below 50% - return specific error details
                    print(f"❌ Could not disambiguate masked account - bank name similarity too low (best: {best_similarity:.1%})")
                    print(f"🚨 MULTIPLE MASKED ACCOUNT MATCHES with insufficient bank name similarity:")
                    
                    candidate_details = []
                    for candidate, similarity in all_similarities:
                        candidate_details.append({
                            'account': candidate['account_number'],
                            'bank': candidate['bank_name'],
                            'routing': candidate['routing_number'],
                            'similarity': similarity
                        })
                    
                    return None, best_similarity, {
                        'account_valid': False, 
                        'match_type': 'multiple_accounts_low_similarity',
                        'ending_digits': detected_digits,
                        'candidate_count': len(matching_accounts),
                        'best_similarity': best_similarity,
                        'candidates': candidate_details,
                        'detected_bank': detected_bank_name
                    }
            else:
                print(f"❌ Multiple masked accounts end with '{detected_digits}' - need bank name to disambiguate")
                print(f"📊 Found {len(matching_accounts)} matching accounts:")
                
                candidate_details = []
                for candidate in matching_accounts:
                    print(f"   {candidate['account_number']} ({candidate['bank_name']})")
                    candidate_details.append({
                        'account': candidate['account_number'],
                        'bank': candidate['bank_name'],
                        'routing': candidate['routing_number'],
                        'similarity': 0.0
                    })
                
                return None, 0.0, {
                    'account_valid': False, 
                    'match_type': 'multiple_accounts_no_bank_name',
                    'ending_digits': detected_digits,
                    'candidate_count': len(matching_accounts),
                    'candidates': candidate_details,
                    'detected_bank': detected_bank_name or 'Not provided'
                }
        else:
            print(f"❌ NO MASKED MATCH: No accounts end with '{detected_digits}'")
            return None, 0.0, {'account_valid': False, 'match_type': 'no_account_match'}
    
    # Search through all banks for exact account match ONLY
    for bank_info in bank_data.get('wac_banks', []):
        wac_account = str(bank_info['account_number']).strip()
        
        # Normalize account numbers by removing leading zeros for comparison
        detected_normalized = detected_account.lstrip('0') if detected_account else ''
        wac_normalized = wac_account.lstrip('0') if wac_account else ''
        
        # Try exact match first (after normalization)
        if detected_account == wac_account:
            print(f"✅ EXACT ACCOUNT MATCH: {detected_account} = {wac_account}")
            print(f"   Bank: {bank_info['bank_name']}")
            print(f"   Routing: {bank_info['routing_number']}")
            return bank_info, 1.0, {'account_valid': True, 'match_type': 'exact'}
        
        # Try normalized match (removes leading zeros)
        elif detected_normalized and wac_normalized and detected_normalized == wac_normalized:
            print(f"✅ NORMALIZED ACCOUNT MATCH: {detected_account} (normalized: {detected_normalized}) = {wac_account} (normalized: {wac_normalized})")
            print(f"   Bank: {bank_info['bank_name']}")
            print(f"   Routing: {bank_info['routing_number']}")
            return bank_info, 1.0, {'account_valid': True, 'match_type': 'normalized'}
        
        # Try partial match for other masked formats (legacy support)
        if detected_digits and len(detected_digits) >= 3:  # At least 3 digits for meaningful match (supports XXXXX518 format)
            if wac_account.endswith(detected_digits):
                print(f"✅ LEGACY PARTIAL MATCH: {detected_digits} matches end of {wac_account}")
                print(f"   Bank: {bank_info['bank_name']}")
                print(f"   Routing: {bank_info['routing_number']}")
                return bank_info, 1.0, {'account_valid': True, 'match_type': 'legacy_partial'}
    
    print(f"❌ NO ACCOUNT MATCH: '{detected_account}' (digits: '{detected_digits}') not found in WAC database")
    return None, 0.0, {'account_valid': False, 'match_type': 'none'}

def find_matching_bank(detected_bank_name, bank_data, threshold=0.8):
    """Find matching bank from WAC bank data with similarity threshold (legacy function)"""
    match, similarity, _ = find_matching_bank_with_account(detected_bank_name, None, bank_data, threshold)
    return match, similarity

def get_bank_info_for_processing(detected_bank_name, detected_account=None):
    """Get bank information for BAI2 processing using ONLY account number matching"""
    
    print(f"\n🏦 Bank Information Lookup")
    print(f"=" * 50)
    
    # Load bank information
    yaml_content, bank_data = load_bank_information_yaml()
    
    if not bank_data:
        print("⚠️ Could not load WAC bank information")
        return None, None, "error", {}
    
    print(f"📄 WAC Bank Information loaded ({len(bank_data['wac_banks'])} banks available)")
    
    # ACCOUNT-ONLY matching - no bank name matching
    if not detected_account:
        print("❌ No account number provided - cannot match WAC operational account")
        return None, None, "error", {}
    
    # Find matching bank based ONLY on account number
    match, similarity, details = find_matching_bank_with_account(
        detected_bank_name,  # Still pass but not used for matching
        detected_account, 
        bank_data
    )
    
    if match and details.get('account_valid'):
        print(f"✅ WAC OPERATIONAL ACCOUNT FOUND")
        print(f"   Account: {match['account_number']}")
        print(f"   Routing: {match['routing_number']}")
        print(f"   Bank: {match['bank_name']}")
        return match['account_number'], match['routing_number'], "wac_account", details
    else:
        # Handle specific error cases for better error reporting
        match_type = details.get('match_type', 'unknown')
        
        if match_type == 'multiple_accounts_low_similarity':
            print(f"❌ MULTIPLE ACCOUNT MATCHES with low bank name similarity")
            print(f"   Ending digits: {details['ending_digits']}")
            print(f"   Candidates: {details['candidate_count']}")
            print(f"   Best similarity: {details['best_similarity']:.1%} (below 70% threshold)")
            return None, None, "multiple_accounts_low_similarity", details
            
        elif match_type == 'multiple_accounts_no_bank_name':
            print(f"❌ MULTIPLE ACCOUNT MATCHES without bank name for disambiguation")
            print(f"   Ending digits: {details['ending_digits']}")
            print(f"   Candidates: {details['candidate_count']}")
            return None, None, "multiple_accounts_no_bank_name", details
            
        elif match_type == 'none':
            print(f"❌ NOT A WAC OPERATIONAL ACCOUNT")
            print(f"   Account '{detected_account}' not found in WAC database")
            print(f"   This appears to be a customer account, not operational")
            return None, None, "no_account_match", details
            
        else:
            print(f"❌ NOT A WAC OPERATIONAL ACCOUNT")
            print(f"   Account '{detected_account}' not found in WAC database")
            print(f"   Match type: {match_type}")
            return None, None, "error", details

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
