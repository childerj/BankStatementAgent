# -*- coding: utf-8 -*-
import azure.functions as func
import logging
import os
import requests
import time
import sys
import json
import re
import openai
from datetime import datetime
from azure.storage.blob import BlobServiceClient

# Configure console encoding for Unicode support
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def load_local_settings():
    """Load environment variables from local.settings.json when running locally"""
    try:
        # Detect local execution environment
        if not os.getenv('FUNCTIONS_WORKER_RUNTIME') or os.path.exists('local.settings.json'):
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

def print_and_log(message):
    """Print to console and log simultaneously with proper encoding handling"""
    # Create emoji replacements dictionary
    emoji_replacements = {
        '🚀': '[START]',
        '📄': '[FILE]',
        '📊': '[SIZE]',
        '🤖': '[AI]',
        '🔍': '[SEARCH]',
        '⚠️': '[WARNING]',
        '✅': '[SUCCESS]',
        '⏳': '[WAIT]',
        '🧠': '[BRAIN]',
        '🏦': '[BANK]',
        '🔢': '[NUMBER]',
        '💱': '[CURRENCY]',
        '💰': '[MONEY]',
        '💸': '[WITHDRAW]',
        '📝': '[NOTES]',
        '📋': '[LIST]',
        '⏸️': '[PAUSE]',
        '🔄': '[CONVERT]',
        '💾': '[SAVE]',
        '📁': '[FOLDER]',
        '🎉': '[COMPLETE]',
        '❌': '[ERROR]',
        '🛠️': '[TOOLS]',
        '🟢': '[HIGH]',
        '🟡': '[MED]',
        '🔴': '[LOW]',
        '📌': '[PIN]',
        '🏷️': '[TAG]',
        '📂': '[DIR]',
        '🔸': '[ITEM]',
        '🧮': '[CALC]',
        '📈': '[UP]',
        '📉': '[DOWN]',
        '🎯': '[TARGET]',
        '👍': '[GOOD]',
        '⏱️': '[TIMER]',
        '📥': '[IN]',
        '🔧': '[FIX]',
        '📏': '[SIZE]',
        # Arrow and bullet characters
        '➤': '->',
        '→': '->',
        '↳': '->',
        '▶': '>',
        '►': '>',
        '•': '*',
        '‣': '*',
        '⁃': '*',
        '◦': '-',
        '▪': '*',
        '▫': '-',
        '◾': '*',
        '◽': '-',
        # Additional emojis that might be in the code
        '🔐': '[SECURE]',
        '🎵': '[AUDIO]',
        '🎶': '[MUSIC]',
        '🎼': '[SCORE]',
        '🎤': '[MIC]',
        '🎪': '[SHOW]',
        '🏪': '[STORE]',
        '🏫': '[SCHOOL]',
        '🏬': '[MALL]',
        '🏭': '[FACTORY]',
        '🏮': '[LANTERN]',
        '🏯': '[CASTLE]',
        '🏰': '[PALACE]',
        '🚁': '[HELI]',
        '🚂': '[TRAIN]',
        '🚃': '[CAR]',
        '🚄': '[SPEED]',
        '🚅': '[BULLET]',
        '🚆': '[METRO]',
        '🚇': '[SUBWAY]',
        '🚈': '[LIGHT]',
        '🚉': '[STATION]',
        '🚊': '[TRAM]',
        '🚋': '[TROLLEY]',
        '�': '[BUS]',
        '🚍': '[COMING]',
        '�': '[TROLLEY_BUS]',
        '🚏': '[BUS_STOP]',
        '�': '[MINIBUS]',
        '🚑': '[AMBULANCE]',
        '�': '[FIRE_ENGINE]',
        '🚓': '[POLICE]',
        '�': '[COMING_POLICE]',
        '🚕': '[TAXI]',
        '🚖': '[COMING_TAXI]',
        '🚗': '[CAR]',
        '�': '[COMING_CAR]',
        '🚙': '[SUV]',
        '🚚': '[TRUCK]',
        '�': '[SEMI]',
        '🚜': '[TRACTOR]',
        '�': '[MONORAIL]',
        '🚞': '[MOUNTAIN_RAILWAY]',
        '🚟': '[SUSPENSION_RAILWAY]',
        '🚠': '[CABLE]',
        '🚡': '[AERIAL]',
        '🚢': '[SHIP]',
        '�': '[ROWBOAT]',
        '🚤': '[SPEEDBOAT]',
        '🚥': '[TRAFFIC_LIGHT]',
        '�': '[VERTICAL_TRAFFIC_LIGHT]',
        '🚧': '[CONSTRUCTION]',
        '�': '[SIREN]',
        '🚩': '[FLAG]',
        '�': '[DOOR]',
        '🚫': '[NO_ENTRY]',
        '�': '[SMOKING]',
        '🚭': '[NO_SMOKING]',
        '🚮': '[LITTER]',
        '🚯': '[NO_LITTERING]',
        '�': '[POTABLE_WATER]',
        '🚱': '[NON_POTABLE_WATER]',
        '�': '[BICYCLE]',
        '🚳': '[NO_BICYCLES]',
        '🚴': '[BICYCLIST]',
        '🚵': '[MOUNTAIN_BICYCLIST]',
        '�': '[PEDESTRIAN]',
        '🚷': '[NO_PEDESTRIANS]',
        '�': '[CHILDREN_CROSSING]',
        '🚹': '[MENS]',
        '🚺': '[WOMENS]',
        '🚻': '[RESTROOM]',
        '�': '[BABY_SYMBOL]',
        '🚽': '[TOILET]',
        '🚾': '[WATER_CLOSET]',
        '🚿': '[SHOWER]',
        '�': '[BATH]',
        '🛁': '[BATHTUB]',
        '�': '[PASSPORT_CONTROL]',
        '🛃': '[CUSTOMS]',
        '🛄': '[BAGGAGE_CLAIM]',
        '🛅': '[LEFT_LUGGAGE]'
    }
    
    # Clean the message for console output
    clean_message = message
    for emoji, replacement in emoji_replacements.items():
        clean_message = clean_message.replace(emoji, replacement)
    
    try:
        print(clean_message, flush=True)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        safe_message = clean_message.encode('ascii', 'replace').decode('ascii')
        print(safe_message, flush=True)
    
    # For logging, create a clean ASCII version
    try:
        import re
        
        # Convert the message to ASCII, replacing all non-ASCII characters
        # This is more aggressive but ensures clean logs
        log_message = message.encode('ascii', 'replace').decode('ascii')
        
        # Clean up any question marks or replacement characters that result from encoding
        log_message = log_message.replace('?', ' ')
        
        # Apply emoji replacements on the original message before ASCII conversion
        # This preserves intended emoji meanings
        for emoji, replacement in emoji_replacements.items():
            if emoji in message:  # Check original message
                log_message = log_message.replace('?', replacement, 1)  # Replace one ? with the meaning
        
        # Clean up multiple spaces and ensure we have clean content
        log_message = ' '.join(log_message.split())
        
        if log_message.strip():  # Only log if there's content left
            logging.info(log_message)
    except Exception as e:
        # Ultimate fallback - log a basic message
        logging.info(f"Message logged ({len(message)} chars): {str(e)}")

# Load local settings after print_and_log is defined
load_local_settings()

def extract_routing_number_from_text(text):
    """Extract routing number from bank statement text using regex patterns"""
    print_and_log("🔍 Searching for routing number in statement text...")
    
    # Common routing number patterns
    patterns = [
        r'routing\s*#?\s*:?\s*(\d{9})',  # "Routing #: 123456789"
        r'routing\s*number\s*:?\s*(\d{9})',  # "Routing number: 123456789"
        r'rt\s*#?\s*:?\s*(\d{9})',  # "RT#: 123456789"
        r'aba\s*#?\s*:?\s*(\d{9})',  # "ABA#: 123456789"
        r'transit\s*#?\s*:?\s*(\d{9})',  # "Transit#: 123456789"
        r'routing\s*(\d{9})',  # "Routing 123456789"
        r'(\d{9})\s*routing',  # "123456789 routing"
        r'\b(\d{9})\b',  # Any 9-digit number (last resort)
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Validate routing number (basic checksum)
            if is_valid_routing_number(match):
                print_and_log(f"✅ Found valid routing number: {match}")
                return match
    
    print_and_log("❌ No routing number found in statement text")
    return None

def is_valid_routing_number(routing_number):
    """Basic validation of routing number using checksum algorithm"""
    if not routing_number or len(routing_number) != 9 or not routing_number.isdigit():
        return False
    
    # Check for obviously invalid numbers
    if routing_number in ['000000000', '999999999'] or len(set(routing_number)) == 1:
        return False
    
    # ABA routing number checksum validation
    digits = [int(d) for d in routing_number]
    checksum = (3 * (digits[0] + digits[3] + digits[6]) +
                7 * (digits[1] + digits[4] + digits[7]) +
                1 * (digits[2] + digits[5] + digits[8]))
    
    return checksum % 10 == 0

def extract_bank_name_from_text(text):
    """Extract bank name from statement text using intelligent word boundary detection"""
    print_and_log("🏦 Searching for bank name in statement text...")
    print_and_log(f"🏦 DEBUG: Input text length: {len(text)} characters")
    print_and_log(f"🏦 DEBUG: Input text sample: {text[:200]}...")
    
    # Smart approach: Look for the bank name at the beginning of the statement
    # Most bank statements start with the bank name as the first meaningful content
    lines = text.split('\n')
    words = text.split()
    
    # Try to find complete bank name by looking for natural stopping points
    print_and_log("🏦 SMART EXTRACTION: Looking for complete bank name at document start...")
    
    # Check first few lines for bank name
    for line_num, line in enumerate(lines[:5], 1):
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        print_and_log(f"🏦 DEBUG: Line {line_num}: '{line}'")
        
        # Skip obvious non-bank content
        if any(skip_word in line.lower() for skip_word in ['report', 'statement', 'date', 'page', 'account', 'balance']):
            continue
            
        # This line might contain the bank name - extract it intelligently
        bank_name = extract_complete_bank_name_from_line(line)
        if bank_name:
            print_and_log(f"✅ Found complete bank name: '{bank_name}'")
            return bank_name
    
    # Fallback: Try first few words approach
    print_and_log("🏦 FALLBACK: Using first meaningful words approach...")
    if len(words) >= 1:
        # Look for natural stopping points in the first several words
        bank_name = extract_bank_name_from_words(words[:10])  # Check first 10 words
        if bank_name:
            print_and_log(f"✅ Found bank name from words: '{bank_name}'")
            return bank_name
    
    print_and_log("❌ No bank name found in statement text")
    return None

def extract_complete_bank_name_from_line(line):
    """Extract complete bank name from a single line with advanced logic for complex names"""
    # Common bank name endings that indicate where to stop
    strong_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 'company', 'credit']
    # Common connecting words in bank names - these should NOT be endings
    connecting_words = ['of', 'and', '&', 'the', 'for', 'in', 'at', 'to']
    # Words that definitely indicate end of bank name
    stop_words = ['report', 'statement', 'date', 'page', 'account', 'balance', 'type', 'bai', 'test', 'customer', 'member', 'branch', 'routing', 'number']
    
    words = line.split()
    if not words:
        return None
    
    # Quick reject: if line starts with obvious non-bank terms
    first_word_lower = words[0].lower()
    if first_word_lower in ['account', 'statement', 'routing', 'balance', 'transaction', 'date', 'page']:
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

def extract_bank_name_from_words(words):
    """Extract bank name from a list of words looking for natural boundaries"""
    if not words:
        return None
    
    # Start with first word and keep adding until we hit a logical stop
    bank_words = []
    
    for i, word in enumerate(words):
        word_clean = word.strip('.,')
        word_lower = word_clean.lower()
        
        # Stop words that indicate end of bank name
        if word_lower in ['report', 'statement', 'date', 'page', 'account', 'balance', 'type', 'currency']:
            break
            
        # Add this word to potential bank name
        bank_words.append(word_clean)
        
        # Check if this looks like a natural ending for a bank name
        if word_lower in ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 'company', 'co']:
            # This is likely the end of the bank name
            break
            
        # Don't let bank names get too long
        if len(bank_words) >= 6:
            break
    
    if bank_words:
        bank_name = ' '.join(bank_words)
        # Basic validation - should be reasonable length and contain letters
        if 2 <= len(bank_name) <= 50 and any(c.isalpha() for c in bank_name):
            return bank_name
    
    return None

def lookup_routing_number_by_bank_name(bank_name):
    """Use Azure OpenAI to lookup routing number for a given bank name"""
    print_and_log(f"🤖 Looking up routing number for bank: {bank_name}")
    
    try:
        # Get Azure OpenAI configuration from environment
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        print_and_log(f"🔍 DEBUG: OpenAI Environment Variables:")
        print_and_log(f"🔍 DEBUG: AZURE_OPENAI_ENDPOINT: {endpoint}")
        print_and_log(f"🔍 DEBUG: AZURE_OPENAI_KEY: {'SET' if api_key else 'NOT SET'}")
        print_and_log(f"🔍 DEBUG: AZURE_OPENAI_DEPLOYMENT: {deployment}")
        
        if not endpoint or not api_key or not deployment:
            print_and_log("❌ Azure OpenAI configuration missing from environment variables")
            return None
        
        # Set up Azure OpenAI client
        from openai import AzureOpenAI
        print_and_log(f"🔍 DEBUG: Creating Azure OpenAI client...")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-10-21"
        )
        
        prompt = f"""
        What is the primary ABA routing number for {bank_name}? 
        
        Please respond with ONLY the 9-digit routing number, no other text.
        If you're not certain or if the bank has multiple routing numbers, provide the most common one.
        If you cannot find a routing number for this bank, respond with "NOT_FOUND".
        
        IMPORTANT: For RCB BANK (Regional Commerce Bank), the routing number is 103112594.
        
        Examples:
        - Wells Fargo Bank -> 121000248
        - Bank of America -> 026009593
        - Chase Bank -> 021000021
        - RCB BANK -> 103112594
        """
        
        print_and_log(f"🤖 DEBUG: OPENAI PROMPT BEING SENT:")
        print_and_log(f"=====================================")
        print_and_log(prompt)
        print_and_log(f"=====================================")
        
        print_and_log(f"🔍 DEBUG: Making OpenAI API call...")
        
        response = client.chat.completions.create(
            model=deployment,  # Use the deployment name from environment
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        print_and_log(f"🤖 DEBUG: OPENAI RESPONSE RECEIVED:")
        print_and_log(f"=====================================")
        print_and_log(f"Raw response: '{routing_number}'")
        print_and_log(f"Response length: {len(routing_number)} characters")
        print_and_log(f"Is digits only: {routing_number.isdigit()}")
        print_and_log(f"=====================================")
        
        # Validate the response
        if routing_number == "NOT_FOUND":
            print_and_log(f"❌ OpenAI could not find routing number for: {bank_name}")
            return None
        
        # Check if it's a valid 9-digit number
        if routing_number.isdigit() and len(routing_number) == 9:
            print_and_log(f"🔍 DEBUG: Validating routing number: {routing_number}")
            if is_valid_routing_number(routing_number):
                print_and_log(f"✅ OpenAI found routing number: {routing_number} for {bank_name}")
                return routing_number
            else:
                print_and_log(f"❌ OpenAI returned invalid routing number: {routing_number}")
                return None
        else:
            print_and_log(f"❌ OpenAI returned invalid format: {routing_number}")
            return None
            
    except Exception as e:
        print_and_log(f"❌ Error looking up routing number with OpenAI: {str(e)}")
        import traceback
        print_and_log(f"❌ Full error traceback: {traceback.format_exc()}")
        return None

def extract_account_number_from_text(text):
    """Extract account number from bank statement text using regex patterns"""
    print_and_log("🔍 Searching for account number in statement text...")
    
    # Common account number patterns - now includes asterisks to capture masked numbers for validation
    patterns = [
        r'account\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Account #: ABC123456789" or "Account #: *5594"
        r'account\s*number\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Account number: ABC123456789" or "Account number: *5594"
        r'acct\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Acct#: ABC123456789" or "Acct#: *5594"
        r'a/c\s*#?\s*:?\s*([A-Za-z0-9\-\*]+)(?:\s|$)',  # "A/C#: ABC123456789" or "A/C#: *5594"
        r'account\s+([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Account ABC123456789" or "Account *5594"
        r'(?:^|\s)([A-Za-z0-9\-\*]+)\s+account(?:\s|$)',  # "ABC123456789 account" or "*5594 account"
        r'for\s*account\s+([A-Za-z0-9\-\*]+)(?:\s|$)',  # "For account ABC123456789" or "For account *5594"
        r'ending\s*in\s+([A-Za-z0-9\*]+)(?:\s|$)',  # "Ending in AB1234" or "Ending in *1234" (partial account)
        r'account\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Account # ABC123456789" or "Account # *5594" (with space)
        r'a/c\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',  # "A/C # ABC123456789" or "A/C # *5594" (with space)
        r'acct\s*#\s+([A-Za-z0-9\-\*]+)(?:\s|$)',  # "Acct # ABC123456789" or "Acct # *5594" (with space)
        r'(?:^|\s)([A-Za-z0-9\-\*]{8,})(?:\s|$)',  # Any 8+ character alphanumeric including asterisks (last resort)
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Basic validation for account number (this will reject asterisks)
            if is_valid_account_number(match):
                print_and_log(f"✅ Found potential account number: {match}")
                return match
            else:
                # Log what we found but rejected
                if "*" in match:
                    print_and_log(f"❌ Found masked account number with asterisks: {match} - treating as missing")
                else:
                    print_and_log(f"❌ Found invalid account number: {match} - rejected")
    
    print_and_log("❌ No account number found in statement text")
    return None

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

def create_error_bai2_file(error_message, filename, file_date, file_time, error_code=None):
    """Create a minimal BAI2 file with detailed error message and diagnostics"""
    print_and_log(f"❌ Creating ERROR BAI2 file: {error_message}")
    
    # Map error messages to specific error codes
    if error_code is None:
        error_lower = error_message.lower()
        if "routing number" in error_lower:
            error_code = "ERROR_NO_ROUTING"
        elif "account number" in error_lower:
            error_code = "ERROR_NO_ACCOUNT"
        elif "bank name" in error_lower:
            error_code = "ERROR_NO_BANK_NAME"
        elif "openai" in error_lower or "parsing" in error_lower:
            error_code = "ERROR_PARSING_FAILED"
        elif "document intelligence" in error_lower or "docintelligence" in error_lower:
            error_code = "ERROR_DOC_INTEL_FAILED"
        elif "network" in error_lower or "connection" in error_lower:
            error_code = "ERROR_NETWORK_FAILED"
        elif "timeout" in error_lower:
            error_code = "ERROR_TIMEOUT"
        elif "processing failed" in error_lower:
            error_code = "ERROR_PROCESSING_FAILED"
        else:
            error_code = "ERROR_UNKNOWN"
    
    now = datetime.now()
    
    lines = []
    
    # 01 - File Header (minimal structure)
    lines.append(f"01,ERROR,WORKDAY,{file_date},{file_time},1,,,2/")
    
    # 02 - Group Header
    lines.append(f"02,ERROR,000000000,1,{file_date},,USD,2/")
    
    # 03 - Account Identifier (use ERROR as account number) - NO routing number
    lines.append(f"03,ERROR,,010,0,,Z/")
    
    # Add error diagnostic record for detection with specific error code
    lines.append(f"88,999,{error_code},,Z/")
    
    # Account section records so far: 03 + 88 = 2
    account_records_excl_49 = 2
    
    # 49 - Account Trailer - include itself in the count (03 + 88 + 49 = 3)
    lines.append(f"49,0,{account_records_excl_49 + 1}/")  # 03 + 88 + 49 = 3
    
    # Group counts: 02 + (03 + 88 + 49) + 98 = 1 + 3 + 1 = 5
    group_record_count_inclusive = 1 + (account_records_excl_49 + 1) + 1  # = 5
    
    # 98 - Group Trailer - MUST include number of accounts (4 fields)
    lines.append(f"98,0,1,{group_record_count_inclusive}/")
    
    # 99 - File Trailer - include itself and number of groups (4 fields)
    total_file_records = len(lines) + 1  # includes the 99 itself
    lines.append(f"99,0,1,{total_file_records}/")
    
    return "\n".join(lines) + "\n"

def get_account_number(parsed_data):
    """Get account number from statement"""
    print_and_log("🔍 Extracting account number...")
    
    # Attempt to extract account number from OpenAI parsed data
    if "account_number" in parsed_data and parsed_data["account_number"]:
        raw_account = str(parsed_data["account_number"])
        print_and_log(f"🔍 Raw account from parsed data: '{raw_account}'")
        
        # Clean but preserve asterisks for validation
        account_number = raw_account.replace("-", "").replace(" ", "")
        print_and_log(f"🔍 After cleaning: '{account_number}'")
        
        if is_valid_account_number(account_number):
            print_and_log(f"✅ Found account number from parsed data: {account_number}")
            return account_number
        else:
            if "*" in account_number:
                print_and_log(f"❌ Parsed data account number contains asterisks (masked): '{account_number}' - treating as missing")
            else:
                print_and_log(f"❌ Parsed data account number invalid: '{account_number}' - rejected")
    
    # Check OCR text lines
    if "ocr_text_lines" in parsed_data:
        full_text = '\n'.join(parsed_data["ocr_text_lines"])
        print_and_log(f"🔍 Searching OCR text for account number...")
        account_number = extract_account_number_from_text(full_text)
        if account_number:
            return account_number
    
    # Check raw fields from document intelligence
    if "raw_fields" in parsed_data:
        print_and_log(f"🔍 Checking {len(parsed_data['raw_fields'])} raw fields for account number...")
        for field_name, field_data in parsed_data["raw_fields"].items():
            if isinstance(field_data, dict) and "content" in field_data:
                content = field_data["content"]
                print_and_log(f"🔍 Field '{field_name}': '{content}'")
                
                if "account" in field_name.lower():
                    if content and len(content) > 4:
                        # Clean but preserve asterisks for validation
                        clean_content = content.replace("-", "").replace(" ", "")
                        print_and_log(f"🔍 Account field cleaned: '{clean_content}'")
                        
                        if is_valid_account_number(clean_content):
                            print_and_log(f"✅ Found account number in field '{field_name}': {clean_content}")
                            return clean_content
                        else:
                            if "*" in clean_content:
                                print_and_log(f"❌ Account field contains asterisks (masked): '{clean_content}' - skipping")
                            else:
                                print_and_log(f"❌ Account field invalid: '{clean_content}' - skipping")
                
                # Also try extracting from any field content
                print_and_log(f"🔍 Trying regex extraction on field '{field_name}' content...")
                account_number = extract_account_number_from_text(field_data["content"])
                if account_number:
                    return account_number
    
    print_and_log("❌ No account number found in statement")
    return None

def get_routing_number(parsed_data):
    """Get routing number from statement or lookup via OpenAI"""
    print_and_log("🔍 Extracting routing number...")
    print_and_log(f"🔍 DEBUG: parsed_data keys: {list(parsed_data.keys())}")
    
    # Extract routing number directly from statement text
    routing_number = None
    
    # Check OCR text lines
    if "ocr_text_lines" in parsed_data:
        full_text = '\n'.join(parsed_data["ocr_text_lines"])
        print_and_log(f"🔍 DEBUG: OCR text length: {len(full_text)} characters")
        print_and_log(f"🔍 DEBUG: OCR text preview: {full_text[:200]}...")
        routing_number = extract_routing_number_from_text(full_text)
        if routing_number:
            print_and_log(f"✅ DEBUG: Found routing number in OCR text: {routing_number}")
    
    # Check raw fields from document intelligence
    if not routing_number and "raw_fields" in parsed_data:
        print_and_log(f"🔍 DEBUG: Checking {len(parsed_data['raw_fields'])} raw fields")
        for field_name, field_data in parsed_data["raw_fields"].items():
            print_and_log(f"🔍 DEBUG: Field '{field_name}': {field_data}")
            if isinstance(field_data, dict) and "content" in field_data:
                routing_number = extract_routing_number_from_text(field_data["content"])
                if routing_number:
                    print_and_log(f"✅ DEBUG: Found routing number in field '{field_name}': {routing_number}")
                    break
    
    # If no routing number found, attempt lookup by bank name
    if not routing_number:
        print_and_log("🏦 No routing number found, attempting bank name lookup...")
        
        bank_name = None
        
        print_and_log(f"🏦 DEBUG: BANK NAME DETECTION PROCESS")
        print_and_log(f"=====================================")
        
        # Display parsed data structure for bank name extraction
        print_and_log(f"🔍 DEBUG: parsed_data keys: {list(parsed_data.keys())}")
        if "raw_fields" in parsed_data:
            print_and_log(f"🔍 DEBUG: raw_fields keys: {list(parsed_data['raw_fields'].keys())}")
            for field_name, field_data in parsed_data["raw_fields"].items():
                print_and_log(f"🔍 DEBUG: Field '{field_name}': {field_data}")
        
        # Check if Document Intelligence extracted the bank name directly
        if "raw_fields" in parsed_data and "BankName" in parsed_data["raw_fields"]:
            bank_data = parsed_data["raw_fields"]["BankName"]
            if isinstance(bank_data, dict) and "content" in bank_data:
                bank_name = bank_data["content"].strip()
                confidence = bank_data.get("confidence", 0.0)
                print_and_log(f"✅ DEBUG: Found bank name from Document Intelligence: {bank_name} ({confidence:.2%} confidence)")
            else:
                print_and_log(f"❌ DEBUG: BankName field exists but wrong format: {bank_data}")
        else:
            print_and_log(f"❌ DEBUG: No BankName field found in raw_fields")
        
        # FALLBACK: Try to extract bank name from OCR text if Document Intelligence failed
        if not bank_name:
            print_and_log("🔍 FALLBACK: Attempting manual bank name extraction from OCR text...")
            if "ocr_text_lines" in parsed_data and parsed_data["ocr_text_lines"]:
                ocr_text = "\n".join(parsed_data["ocr_text_lines"])
                bank_name = extract_bank_name_from_text(ocr_text)
                if bank_name:
                    print_and_log(f"✅ FALLBACK: Extracted bank name from OCR: {bank_name}")
                else:
                    print_and_log("❌ FALLBACK: No bank name found in OCR text")
            
            # Additional fallback: Check table data for bank names
            if not bank_name and "raw_fields" in parsed_data and "tables" in parsed_data["raw_fields"]:
                print_and_log("🔍 FALLBACK: Checking table data for bank name...")
                tables = parsed_data["raw_fields"]["tables"]
                for table in tables:
                    if "cells" in table:
                        for cell in table["cells"]:
                            cell_content = cell.get("content", "").strip()
                            if cell_content and any(keyword in cell_content.upper() for keyword in ['BANK', 'FCB', 'FEB']):
                                print_and_log(f"🔍 FALLBACK: Found potential bank name in table: {cell_content}")
                                bank_name = extract_bank_name_from_text(cell_content)
                                if bank_name:
                                    print_and_log(f"✅ FALLBACK: Extracted bank name from table: {bank_name}")
                                    break
                    if bank_name:
                        break
        
        # Final check - if still no bank name found
        if not bank_name:
            print_and_log("❌ CRITICAL: Bank name not found in Document Intelligence or fallback methods")
            return None
        
        # SUMMARY OF BANK NAME DETECTION
        print_and_log(f"🏦 BANK NAME DETECTION RESULT:")
        print_and_log(f"=====================================")
        print_and_log(f"✅ BANK NAME FOUND: '{bank_name}'")
        print_and_log(f"=====================================")
        
        # Lookup routing number by bank name
        print_and_log(f"🤖 DEBUG: Attempting OpenAI lookup for bank: {bank_name}")
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        if routing_number:
            print_and_log(f"✅ DEBUG: OpenAI returned routing number: {routing_number}")
        else:
            print_and_log(f"❌ DEBUG: OpenAI lookup failed for bank: {bank_name}")
    
    # No fallback - return None if routing number cannot be determined
    if not routing_number:
        print_and_log("❌ CRITICAL: No routing number found and unable to lookup by bank name")
        return None
    
    print_and_log(f"✅ Using routing number: {routing_number}")
    return routing_number

def parse_bankstatement_sdk_result(result):
    """Parse bankStatement.us model results using SDK format"""
    parsed_data = {
        "extraction_method": "bankStatement.us_sdk",
        "raw_fields": {},
        "ocr_text_lines": []
    }
    
    try:
        if result.documents:
            doc = result.documents[0]
            if hasattr(doc, 'fields') and doc.fields:
                for field_name, field_data in doc.fields.items():
                    if hasattr(field_data, 'content') and field_data.content:
                        parsed_data["raw_fields"][field_name] = {
                            "content": field_data.content,
                            "confidence": getattr(field_data, 'confidence', 0.0)
                        }
                        print_and_log(f"✅ Field '{field_name}': {field_data.content} ({getattr(field_data, 'confidence', 0.0):.2%})")
            
        # Also extract text content for fallback processing
        if result.content:
            parsed_data["ocr_text_lines"] = result.content.split('\n')
            print_and_log(f"📝 Extracted {len(parsed_data['ocr_text_lines'])} lines of text")
    
    except Exception as e:
        print_and_log(f"❌ Error parsing bankStatement SDK result: {str(e)}")
    
    return parsed_data

def parse_layout_sdk_result(result):
    """Parse layout model results using SDK format"""
    parsed_data = {
        "extraction_method": "layout_sdk", 
        "raw_fields": {},
        "ocr_text_lines": []
    }
    
    try:
        # Extract text content
        if result.content:
            parsed_data["ocr_text_lines"] = result.content.split('\n')
            print_and_log(f"📝 Extracted {len(parsed_data['ocr_text_lines'])} lines of OCR text")
        
        # Extract tables if present
        if result.tables:
            print_and_log(f"📊 Found {len(result.tables)} tables")
            parsed_data["raw_fields"]["tables"] = []
            
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                
                for cell in table.cells:
                    cell_data = {
                        "content": cell.content,
                        "row_index": cell.row_index,
                        "column_index": cell.column_index
                    }
                    table_data["cells"].append(cell_data)
                
                parsed_data["raw_fields"]["tables"].append(table_data)
    
    except Exception as e:
        print_and_log(f"❌ Error parsing layout SDK result: {str(e)}")
    
    return parsed_data

def send_to_openai_for_parsing(ocr_data):
    """Send OCR data to OpenAI for intelligent parsing with comprehensive optimization"""
    
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    openai_key = os.environ.get("AZURE_OPENAI_KEY")
    
    if not openai_endpoint or not openai_key:
        print_and_log("❌ OpenAI credentials not configured")
        return None
    
    # Build comprehensive data context
    ocr_text = ""
    if "ocr_text_lines" in ocr_data:
        ocr_text = '\n'.join(ocr_data["ocr_text_lines"])
    
    # Show OCR text statistics
    word_count = len(ocr_text.split())
    print_and_log(f"📊 Total OCR text: {len(ocr_text):,} characters ({word_count:,} words)")
    
    # For very large documents, implement smart truncation
    if len(ocr_text) > 12000:  # OpenAI context limit consideration
        print_and_log(f"⚠️  Large document detected - implementing smart processing...")
        
        # Focus on transaction-rich sections
        lines = ocr_text.split('\n')
        transaction_lines = []
        balance_lines = []
        
        for line in lines:
            line_lower = line.lower()
            # Look for lines that likely contain transactions
            if any(keyword in line_lower for keyword in [
                'deposit', 'withdrawal', 'debit', 'credit', 'check', 'transfer', 
                'fee', 'charge', 'payment', 'world acceptance', 'ach', 'atm'
            ]) or any(char.isdigit() and '$' in line for char in line):
                transaction_lines.append(line)
            # Also capture balance/summary lines
            elif any(keyword in line_lower for keyword in [
                'balance', 'total', 'beginning', 'ending', 'summary'
            ]):
                balance_lines.append(line)
        
        # Create focused text
        focused_text = '\n'.join(balance_lines[:10] + transaction_lines + balance_lines[-10:])
        
        if len(focused_text) < len(ocr_text) * 0.8:  # If we filtered significantly
            ocr_text = focused_text
            print_and_log(f"📊 Focused on transactions: {len(ocr_text):,} characters ({len(ocr_text.split()):,} words)")
        else:
            print_and_log(f"📊 Using full text (filtering didn't reduce significantly)")
    else:
        print_and_log(f"📊 Sending FULL TEXT to OpenAI")
    
    # Ultra-comprehensive prompt designed to find ALL transactions with detailed descriptions
    prompt = f"""
You are an expert bank statement parser. Extract ALL financial transactions from this bank statement with complete accuracy and detailed descriptions.

SCANNING STRATEGY:
1. Scan EVERY SINGLE LINE of the OCR text below
2. Look for transaction patterns throughout ALL pages
3. Find dates in MM/DD, MM/DD/YY, or MM-DD-YYYY formats
4. Find corresponding dollar amounts ($X.XX or X.XX)
5. Include ALL transaction types: deposits, withdrawals, checks, fees, transfers, interest, ATM transactions
6. Parse transaction tables row by row completely
7. Look for balance columns that might indicate transaction amounts
8. Extract COMPLETE transaction descriptions including reference numbers, merchant names, and transaction codes

CRITICAL PARSING RULES:
- Scan from the very beginning to the very end of the text
- Every date + amount combination is likely a transaction
- Include even small amounts (fees, interest, etc.)
- Check for negative amounts (withdrawals/debits)
- Check for positive amounts (deposits/credits)
- Look for check numbers, reference numbers, descriptions
- Don't miss transactions at page breaks
- Preserve detailed descriptions like "ACH Debit Received WORLD ACCEPTANCE CONC DEBIT 144"
- Include all reference numbers and transaction codes
- EXTRACT EXACT REFERENCE NUMBERS: Look for patterns like "478980340", check numbers, transaction IDs, confirmation numbers
- Reference numbers are often found after "Ref:", "Reference:", "Check #", "Confirmation:", or as standalone numbers in transaction lines
- Capture both bank-generated reference numbers AND merchant/transaction reference numbers

FULL OCR TEXT:
{ocr_text}

CRITICAL BALANCE EXTRACTION RULES:
- Opening balance is the STARTING account balance at the beginning of the statement period
- Look for terms like "Previous Balance", "Beginning Balance", "Opening Balance", "Balance Forward"
- Opening balance should NOT be confused with individual transaction amounts
- If no clear opening balance is stated, set opening_balance amount to null
- Closing balance is the ENDING account balance at the end of the statement period
- Look for terms like "Ending Balance", "Closing Balance", "Current Balance", "New Balance"
- DO NOT use individual transaction amounts as opening/closing balances
- Transaction amounts go in the transactions array, NOT in balance fields

Return ONLY valid JSON with this structure (NO markdown, NO explanations):
{{
    "account_number": "extracted account number",
    "statement_period": {{
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }},
    "opening_balance": {{
        "amount": number OR null (if no clear opening balance found),
        "date": "YYYY-MM-DD"
    }},
    "closing_balance": {{
        "amount": number OR null (if no clear closing balance found),
        "date": "YYYY-MM-DD"
    }},
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "amount": number (positive for deposits, negative for withdrawals),
            "description": "complete detailed transaction description including reference numbers",
            "type": "deposit|withdrawal|fee|interest|transfer|check|ach|other",
            "balance_after": number,
            "reference_number": "exact transaction reference, check number, confirmation number, or bank reference number from statement (e.g., 478980340, CHK123, REF456789)"
        }}
    ],
    "summary": {{
        "total_deposits": number,
        "total_withdrawals": number,
        "transaction_count": number,
        "deposit_count": number,
        "withdrawal_count": number
    }}
}}

EXTRACT ALL TRANSACTIONS WITH DETAILED DESCRIPTIONS - FIND EVERY ONE!
"""

    try:
        print_and_log("🤖 Sending comprehensive prompt to OpenAI...")
        
        deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
        url = f"{openai_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-10-21"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": openai_key
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are an expert bank statement parser. Extract ALL transactions with 100% accuracy. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 16000,  # Increased token limit
            "temperature": 0.0
        }
        
        # Implement retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print_and_log(f"🤖 Sending to OpenAI (attempt {attempt + 1}/{max_retries})...")
                
                # Set reasonable timeout - don't wait too long
                timeout = 60  # Reduced from 120-180 to prevent hanging
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
                
                break  # Success, exit retry loop
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8 seconds
                    print_and_log(f"⏱️  Request timed out. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print_and_log("❌ Final timeout after all retries")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff
                    print_and_log(f"⚠️  Request failed: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print_and_log(f"❌ Final error after all retries: {e}")
                    return None
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            print_and_log(f"📥 Response length: {len(content):,} characters")
            
            # Clean up the response
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                parsed_result = json.loads(content)
                print_and_log("✅ Successfully parsed JSON response!")
                
                # Detailed analysis
                if "transactions" in parsed_result:
                    transactions = parsed_result["transactions"]
                    
                    # Count by type
                    deposits = [t for t in transactions if t.get('amount', 0) > 0]
                    withdrawals = [t for t in transactions if t.get('amount', 0) < 0]
                    
                    print_and_log(f"🎯 EXTRACTION RESULTS:")
                    print_and_log(f"   📊 Total found: {len(transactions)} transactions")
                    print_and_log(f"   💰 Deposits: {len(deposits)}")
                    print_and_log(f"   💸 Withdrawals: {len(withdrawals)}")
                    
                    if len(transactions) >= 100:
                        print_and_log("   ✅ HIGH VOLUME STATEMENT!")
                    elif len(transactions) >= 50:
                        print_and_log("   👍 GOOD VOLUME STATEMENT!")
                    elif len(transactions) >= 20:
                        print_and_log("   📊 MODERATE VOLUME STATEMENT")
                    else:
                        print_and_log("   ⚠️  LOW VOLUME STATEMENT")
                
                if "summary" in parsed_result:
                    summary = parsed_result["summary"]
                    print_and_log(f"💰 FINANCIAL SUMMARY:")
                    print_and_log(f"   Deposits: ${summary.get('total_deposits', 0):,.2f}")
                    print_and_log(f"   Withdrawals: ${abs(summary.get('total_withdrawals', 0)):,.2f}")
                    print_and_log(f"   Net change: ${summary.get('total_deposits', 0) + summary.get('total_withdrawals', 0):,.2f}")
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                print_and_log(f"❌ JSON parsing error: {e}")
                print_and_log(f"📄 Response length: {len(content)} characters")
                print_and_log(f"📄 Response preview (first 500): {content[:500]}...")
                print_and_log(f"📄 Response preview (last 500): ...{content[-500:]}")
                
                # Extract partial JSON array for transactions if possible
                try:
                    print_and_log("🔧 Attempting to extract partial transaction data...")
                    
                    # Look for transaction array pattern
                    array_start = content.find('"transactions": [')
                    if array_start >= 0:
                        print_and_log("   Found transactions array start")
                        
                        # Find the content within the array
                        bracket_start = content.find('[', array_start) + 1
                        bracket_count = 0
                        array_end = -1
                        
                        for i, char in enumerate(content[bracket_start:], bracket_start):
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                if bracket_count == 0:
                                    array_end = i
                                    break
                                bracket_count -= 1
                        
                        if array_end > bracket_start:
                            # Extract the transaction array content
                            array_content = content[bracket_start:array_end]
                            partial_json = f'{{"transactions": [{array_content}]}}'
                            
                            try:
                                parsed_result = json.loads(partial_json)
                                print_and_log("   ✅ Successfully extracted partial transaction data!")
                                
                                transactions = parsed_result.get("transactions", [])
                                print_and_log(f"   📊 Recovered {len(transactions)} transactions")
                                
                                return {"transactions": transactions}
                                
                            except json.JSONDecodeError as parse_error:
                                print_and_log(f"   ❌ Partial parsing also failed: {parse_error}")
                        else:
                            print_and_log("   ❌ Could not find complete transaction array")
                    else:
                        print_and_log("   ❌ Could not find transactions array in response")
                        
                except Exception as fallback_e:
                    print_and_log(f"   ❌ Fallback extraction failed: {fallback_e}")
                
                return None
                
        else:
            print_and_log(f"❌ OpenAI API error: {response.status_code}")
            print_and_log(f"Error: {response.text[:500]}...")
            return None
    
    except Exception as e:
        print_and_log(f"❌ Error: {str(e)}")
        return None

def reconcile_transactions(parsed_data):
    """
    Reconcile opening/closing balances with transactions.
    Returns reconciliation results and throws error if balances don't match.
    """
    print_and_log("🧮 Starting balance reconciliation...")
    
    opening_balance = 0
    closing_balance = 0
    total_deposits = 0
    total_withdrawals = 0
    opening_balance_known = False
    closing_balance_known = False
    
    # Get opening balance
    if parsed_data.get("opening_balance") and parsed_data["opening_balance"].get("amount") is not None:
        opening_balance = float(parsed_data["opening_balance"]["amount"])
        opening_balance_known = True
        print_and_log(f"💰 Opening balance: ${opening_balance:,.2f}")
    else:
        print_and_log("⚠️  Opening balance: UNKNOWN")
    
    # Get closing balance
    if parsed_data.get("closing_balance") and parsed_data["closing_balance"].get("amount") is not None:
        closing_balance = float(parsed_data["closing_balance"]["amount"])
        closing_balance_known = True
        print_and_log(f"💰 Closing balance: ${closing_balance:,.2f}")
    else:
        print_and_log("⚠️  Closing balance: UNKNOWN")
    
    # Calculate transaction totals
    transactions = parsed_data.get("transactions", [])
    for txn in transactions:
        # Validate that txn is a dictionary
        if not isinstance(txn, dict):
            print_and_log(f"⚠️ Skipping invalid transaction in reconciliation: {type(txn)} - {txn}")
            continue
            
        amount = float(txn.get("amount", 0))
        if amount > 0:
            total_deposits += amount
        else:
            total_withdrawals += abs(amount)
    
    print_and_log(f"📈 Total deposits: ${total_deposits:,.2f}")
    print_and_log(f"📉 Total withdrawals: ${total_withdrawals:,.2f}")
    
    # Initialize warnings only (removing error codes)
    warnings = []
    reconciliation_status = "COMPLETE"
    balanced = False
    balance_difference = 0
    expected_closing = None
    
    # VALIDATION: Check if opening balance suspiciously equals total deposits
    # This often indicates OpenAI confused a large deposit for the opening balance
    if opening_balance_known and abs(opening_balance - total_deposits) < 0.01 and opening_balance > 1000:
        print_and_log(f"⚠️  SUSPICIOUS: Opening balance (${opening_balance:,.2f}) equals total deposits!")
        print_and_log(f"⚠️  This suggests OpenAI mistook a large deposit for opening balance")
        print_and_log(f"⚠️  Marking opening balance as SUSPICIOUS and treating as unknown")
        
        # Mark as suspicious but keep the original value for reference
        opening_balance_known = False
        warnings.append("Opening balance likely confused with large deposit")
        reconciliation_status = "INCOMPLETE"
    elif not opening_balance_known:
        # Truly missing balance - no need for warning, just mark as incomplete
        reconciliation_status = "INCOMPLETE"
        
    if not closing_balance_known:
        reconciliation_status = "INCOMPLETE"
    
    # Perform reconciliation only if we have both balances
    if opening_balance_known and closing_balance_known:
        expected_closing = opening_balance + total_deposits - total_withdrawals
        print_and_log(f"🧮 Expected closing balance: ${expected_closing:,.2f}")
        
        # Check if balances match (allow for small rounding differences)
        balance_difference = abs(closing_balance - expected_closing)
        tolerance = 0.01  # 1 cent tolerance
        balanced = balance_difference <= tolerance
        
        if not balanced:
            reconciliation_status = "FAILED"
            warnings.append(f"Balance reconciliation failed: difference of ${balance_difference:,.2f}")
            
    else:
        # Cannot perform reconciliation without both opening and closing balances
        reconciliation_status = "INCOMPLETE" 
        print_and_log("⚠️  Cannot calculate reconciliation - missing essential balance data")
    
    reconciliation_result = {
        "opening_balance": opening_balance,
        "opening_balance_known": opening_balance_known,
        "closing_balance": closing_balance,
        "closing_balance_known": closing_balance_known,
        "total_deposits": total_deposits,
        "total_withdrawals": total_withdrawals,
        "expected_closing": expected_closing,
        "difference": balance_difference,
        "balanced": balanced,
        "transaction_count": len(transactions),
        "reconciliation_status": reconciliation_status,
        "warnings": warnings
    }
    
    # Log reconciliation results
    if reconciliation_status == "COMPLETE" and balanced:
        print_and_log("✅ Balances reconciled successfully!")
        print_and_log(f"   Opening: ${opening_balance:,.2f}")
        print_and_log(f"   + Deposits: ${total_deposits:,.2f}")
        print_and_log(f"   - Withdrawals: ${total_withdrawals:,.2f}")
        print_and_log(f"   = Expected: ${expected_closing:,.2f}")
        print_and_log(f"   Actual closing: ${closing_balance:,.2f}")
        print_and_log(f"   Difference: ${balance_difference:,.2f}")
        
    elif reconciliation_status == "PARTIAL":
        print_and_log("⚠️  Partial reconciliation completed")
        for warning in warnings:
            print_and_log(f"   • {warning}")
            
    elif reconciliation_status == "INCOMPLETE":
        print_and_log("⚠️  Incomplete reconciliation - missing balance information")
        for warning in warnings:
            print_and_log(f"   • {warning}")
            
    elif reconciliation_status == "FAILED":
        error_msg = f"❌ RECONCILIATION FAILED!"
        error_msg += f"\n   Opening: ${opening_balance:,.2f}"
        error_msg += f"\n   + Deposits: ${total_deposits:,.2f}"
        error_msg += f"\n   - Withdrawals: ${total_withdrawals:,.2f}"
        error_msg += f"\n   = Expected: ${expected_closing:,.2f}"
        error_msg += f"\n   Actual closing: ${closing_balance:,.2f}"
        error_msg += f"\n   Difference: ${balance_difference:,.2f}"
        for warning in warnings:
            error_msg += f"\n   • {warning}"
        print_and_log(error_msg)
        
        # Only raise exception for balance mismatches, not missing balances
        raise Exception(f"Balance reconciliation failed: difference of ${balance_difference:,.2f}")
    
    return reconciliation_result

def extract_fields_with_sdk(file_bytes, filename, endpoint, key):
    """
    Extract fields from a PDF using Azure Document Intelligence SDK.
    Falls back to OCR/Read model if bankStatement model fails.
    """
    parsed_data = {"source": filename}
    success = False
    
    # Extract bank statement data using Document Intelligence bankStatement model
    try:
        print_and_log(f"🔄 Attempting to extract using bankStatement.us model (SDK) for {filename}...")
        
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        from io import BytesIO
        
        # Create client with correct SDK
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        print_and_log("📤 Starting analysis with layout model...")
        
        # Analyze document with layout model using proper SDK format
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            BytesIO(file_bytes),
            content_type="application/pdf"
        )
        
        print_and_log("⏳ Waiting for analysis to complete...")
        result = poller.result()
        
        if result:
            print_and_log("✅ Layout analysis completed successfully!")
            parsed_data.update(parse_layout_sdk_result(result))
            success = True
        else:
            print_and_log("⚠️ No result found")
    
    except Exception as e:
        print_and_log(f"❌ Error with bankStatement.us model (SDK): {str(e)}")
    
    # If bankStatement.us model failed, try layout model for OCR
    if not success:
        try:
            print_and_log(f"🔄 Falling back to layout model (OCR/Read) for {filename}...")
            
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            from io import BytesIO
            
            # Create client
            client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
            
            # Analyze document with layout model
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                document=BytesIO(file_bytes)
            )
            
            print_and_log("⏳ Waiting for OCR analysis to complete...")
            result = poller.result()
            
            if result:
                print_and_log("✅ OCR analysis completed successfully!")
                parsed_data.update(parse_layout_sdk_result(result))
                success = True
            else:
                print_and_log("⚠️ No result from OCR analysis")
        
        except Exception as e:
            print_and_log(f"❌ Error with OCR fallback: {str(e)}")
    
    if not success:
        print_and_log("❌ All extraction methods failed")
        parsed_data["error"] = "Failed to extract data using both bankStatement.us and OCR methods"
    
    return parsed_data

app = func.FunctionApp()

# Global variable to track processing files and prevent duplicate processing
_processing_files = set()

@app.event_grid_trigger(arg_name="event")
def process_new_file(event: func.EventGridEvent):
    # Extract blob information from EventGrid event
    event_data = event.get_json()
    
    # Log the incoming EventGrid event data
    print_and_log(f"[DEBUG] EventGrid event received: {event_data}")
    
    # Extract blob URL and subject from the event
    blob_url = event_data.get('url', '')
    subject = event_data.get('subject', '')
    
    print_and_log(f"[DEBUG] Blob URL: {blob_url}")
    print_and_log(f"[DEBUG] Subject: {subject}")
    
    # Subject format: /blobServices/default/containers/{container}/blobs/{path}/{filename}
    # Extract filename from subject or URL
    if subject:
        # Extract path from subject: /blobServices/default/containers/bank-reconciliation/blobs/incoming-bank-statements/filename
        subject_parts = subject.split('/')
        if len(subject_parts) >= 7 and 'incoming-bank-statements' in subject:
            name = subject_parts[-1]  # Get the filename
            blob_path = '/'.join(subject_parts[6:])  # Get path from blobs/ onwards
        else:
            print_and_log(f"[DEBUG] Subject format not recognized or not in monitored folder: {subject}")
            return
    else:
        # Fallback to URL parsing
        url_parts = blob_url.split('/')
        name = url_parts[-1]  # Get the filename
        blob_path = '/'.join(url_parts[4:])  # Get container/path/filename
    
    print_and_log(f"[DEBUG] Extracted filename: {name}")
    print_and_log(f"[DEBUG] Extracted blob path: {blob_path}")
    
    # Check if this is the container and folder we're monitoring
    if not blob_path.startswith('incoming-bank-statements/'):
        print_and_log(f"[INFO] Ignoring file {name} - not in monitored folder (path: {blob_path})")
        return
    
    # Prevent duplicate processing of the same file
    file_key = f"{blob_path}_{event_data.get('eTag', '')}"
    if file_key in _processing_files:
        print_and_log(f"[WARN] File {name} is already being processed - ignoring duplicate event")
        return
    
    # Add to processing set
    _processing_files.add(file_key)
    
    try:
        # Get storage connection and download the blob
        storage_connection = os.environ["AzureWebJobsStorage"]
        blob_service = BlobServiceClient.from_connection_string(storage_connection)
        
        # For EventGrid events, we know the container is bank-reconciliation
        container_name = "bank-reconciliation"
        blob_name = blob_path  # This should be 'incoming-bank-statements/filename'
        
        print_and_log(f"[DEBUG] Downloading blob: container={container_name}, blob={blob_name}")
        
        # Download the blob data
        blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
        file_bytes = blob_client.download_blob().readall()
        file_size = len(file_bytes) if file_bytes else 0
        
        print_and_log("")
        print_and_log("🚀 STARTING BANK STATEMENT PROCESSING")
        print_and_log("=" * 60)
        print_and_log(f"📄 Processing file: {name}")
        print_and_log(f"📊 File size: {file_size:,} bytes")
        print_and_log("")
        
        if file_size == 0:
            raise Exception(f"File {name} is empty or could not be read")

        endpoint = os.environ["DOCINTELLIGENCE_ENDPOINT"]
        key = os.environ["DOCINTELLIGENCE_KEY"]
        storage_connection = os.environ["AzureWebJobsStorage"]

        # Ensure required containers exist
        blob_service = BlobServiceClient.from_connection_string(storage_connection)
        
        # All folders (incoming-bank-statements, bai2-outputs, archive) 
        # are within the bank-reconciliation container

        # Submit to Document Intelligence - single method for all PDFs
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/pdf"
        }

        print_and_log("🤖 STEP 1: Using Document Intelligence AI extraction")
        print_and_log("   ➤ AI-powered analysis works for both digital and scanned PDFs")
        print_and_log("   ➤ Automatically detects document structure and extracts fields")
        print_and_log("   ➤ Handles complex layouts and various bank statement formats")
        print_and_log("")
        
        # Use new SDK-based extraction
        parsed_data = extract_fields_with_sdk(file_bytes, name, endpoint, key)
        
        # Send to OpenAI for intelligent parsing if we have OCR data
        openai_result = None
        if parsed_data.get("ocr_text_lines"):
            print_and_log("")
            print_and_log("🤖 STEP 2: OpenAI Intelligent Parsing")
            print_and_log("   ➤ Using AI to understand transaction patterns")
            print_and_log("   ➤ Extracting all deposits, withdrawals, and balances")
            print_and_log("")
            
            openai_result = send_to_openai_for_parsing(parsed_data)
            
            if openai_result:
                # Perform reconciliation check
                try:
                    reconciliation = reconcile_transactions(openai_result)
                    print_and_log("")
                    print_and_log("✅ All checks passed - ready for BAI2 conversion!")
                except Exception as reconcile_error:
                    print_and_log(f"❌ Reconciliation failed: {str(reconcile_error)}")
                    # Continue processing with reconciliation error noted
                    openai_result["reconciliation_error"] = str(reconcile_error)
        
        # Use OpenAI result for transaction data but preserve Document Intelligence structure
        if openai_result:
            # Merge OpenAI transaction data with Document Intelligence structure
            final_data = parsed_data.copy()  # Start with Document Intelligence data (has raw_fields, ocr_text_lines)
            final_data.update({
                'account_number': openai_result.get('account_number'),
                'statement_period': openai_result.get('statement_period'),
                'opening_balance': openai_result.get('opening_balance'),
                'closing_balance': openai_result.get('closing_balance'),
                'transactions': openai_result.get('transactions'),
                'summary': openai_result.get('summary')
            })
            print_and_log("✅ Merged OpenAI transaction data with Document Intelligence structure")
        else:
            # Use Document Intelligence data only
            final_data = parsed_data
            print_and_log("✅ Using Document Intelligence data only")
        
        # Store reconciliation results for final summary (if available)
        reconciliation_summary = None
        if 'reconciliation' in locals() and reconciliation:
            reconciliation_summary = reconciliation
        elif openai_result and "reconciliation_error" in openai_result:
            reconciliation_summary = {"error": openai_result["reconciliation_error"]}
        
        print_and_log("")
        print_and_log("🔄 STEP 3: Converting to BAI2 format")
        print_and_log("   ➤ Building industry-standard BAI2 file structure")
        print_and_log("   ➤ Including all extracted transactions and balances")
        print_and_log("")
        
        # Generate comprehensive BAI from processed data
        bai2 = convert_to_bai2(final_data, name, reconciliation_summary)

        print_and_log("")
        print_and_log("💾 STEP 4: Saving BAI file to processed folder")
        print_and_log("   ➤ Creating compliant banking format file")
        print_and_log("")
        
        # Check if this is an error BAI file (updated detection for new error format)
        is_error_file = "ERROR_NO_ACCOUNT" in bai2 or "03,ERROR," in bai2
        
        # Save BAI2 file with appropriate filename
        output_container = blob_service.get_container_client("bank-reconciliation")
        
        if is_error_file:
            # Generate error filename for files with missing account numbers
            base_filename = name.split('.')[0]
            output_filename = f"bai2-outputs/ERROR_{base_filename}.bai"
            print_and_log("❌ Creating ERROR BAI file due to missing account number")
        else:
            # Normal filename for successful processing
            output_filename = f"bai2-outputs/{name.split('.')[0]}.bai"
            print_and_log("✅ Creating normal BAI file")
        
        output_blob = output_container.get_blob_client(output_filename)
        output_blob.upload_blob(bai2.encode("utf-8"), overwrite=True)

        print_and_log(f"✅ BAI2 file uploaded successfully!")
        print_and_log(f"📁 Location: bank-reconciliation/{output_filename}")
        
        # Show some statistics about the BAI2 content
        bai2_lines = bai2.count('\n')
        bai2_size = len(bai2.encode('utf-8'))
        
        print_and_log("")
        print_and_log("📁 STEP 5: Moving original file to archive")
        print_and_log("   ➤ Preserving original PDF for record keeping")

        # Check if we're in a test mode (no actual incoming blob)
        try:
            # Move original to archive
            input_container = blob_service.get_container_client(container_name)
            source_blob = input_container.get_blob_client(blob_name)
            
            # Check if source blob exists
            if not source_blob.exists():
                print_and_log("⚠️ Source file not found in incoming folder (test mode)")
                print_and_log("✅ Archiving skipped for test")
            else:
                archive_container = blob_service.get_container_client(container_name)
                archive_blob = archive_container.get_blob_client(f"archive/{name}")

                print_and_log(f"🔍 Debug: Source blob path: {blob_name}")
                print_and_log(f"🔍 Debug: Archive blob path: archive/{name}")
                print_and_log(f"🔍 Debug: Source blob URL: {source_blob.url}")

                # Start copy operation and wait for completion
                copy_operation = archive_blob.start_copy_from_url(source_blob.url)
                
                # Wait for copy to complete before deleting source (with timeout)
                max_wait_time = 60  # Maximum 60 seconds for copy operation
                start_time = time.time()
                
                while True:
                    # Check timeout
                    if time.time() - start_time > max_wait_time:
                        print_and_log("⚠️ Copy operation timed out - proceeding without deleting source")
                        break
                        
                    copy_props = archive_blob.get_blob_properties()
                    if copy_props.copy.status == 'success':
                        # Now safe to delete the source blob
                        source_blob.delete_blob()
                        print_and_log(f"✅ Original file archived successfully!")
                        break
                    elif copy_props.copy.status == 'failed':
                        raise Exception(f"Failed to copy blob to archive: {copy_props.copy.status_description}")
                    print(".", end="", flush=True)  # Show progress
                    time.sleep(1)
                print_and_log(f"📁 Archive location: archive/{name}")
                
        except Exception as archive_error:
            print_and_log(f"⚠️ Archiving failed: {str(archive_error)}")
            print_and_log("✅ Processing continues despite archiving issue")
        
        print_and_log("")
        print_and_log("📊 PROCESSING COMPLETE - FINAL SUMMARY")
        print_and_log("=" * 60)
        print_and_log(f"📄 Source File: {name}")
        
        if is_error_file:
            print_and_log(f"❌ ERROR BAI Output: {container_name}/{output_filename}")
            print_and_log("⚠️  BAI file created with error message due to missing account number")
        else:
            print_and_log(f"✅ BAI Output: {container_name}/{output_filename}")
        
        print_and_log(f"📄 Archive: {container_name}/archive/{name}")
        print_and_log(f"📏 BAI2 Size: {bai2_size:,} bytes ({bai2_lines} lines)")
        print_and_log("")
        
        # Display reconciliation information
        if reconciliation_summary:
            if "error" in reconciliation_summary:
                print_and_log("⚠️ RECONCILIATION STATUS: FAILED")
                print_and_log(f"   Error: {reconciliation_summary['error']}")
            else:
                print_and_log("✅ RECONCILIATION STATUS: SUCCESSFUL")
                print_and_log(f"   Opening Balance: ${reconciliation_summary.get('opening_balance', 0):,.2f}")
                print_and_log(f"   Closing Balance: ${reconciliation_summary.get('closing_balance', 0):,.2f}")
                print_and_log(f"   Total Deposits: ${reconciliation_summary.get('total_deposits', 0):,.2f}")
                print_and_log(f"   Total Withdrawals: ${reconciliation_summary.get('total_withdrawals', 0):,.2f}")
                print_and_log(f"   Transactions: {reconciliation_summary.get('transaction_count', 0)}")
                if reconciliation_summary.get('difference', 0) > 0:
                    print_and_log(f"   Balance Difference: ${reconciliation_summary.get('difference', 0):,.2f}")
        else:
            print_and_log("⚠️ RECONCILIATION STATUS: NOT PERFORMED")
        print_and_log("")
        
        print_and_log("🎉 BANK STATEMENT PROCESSING SUCCESSFUL!")
        print_and_log("   ➤ Your PDF has been converted to BAI2 format")
        print_and_log("   ➤ The file is ready for import into banking systems")
        print_and_log("   ➤ Original file has been safely archived")
        print_and_log("=" * 60)

    except Exception as e:
        # Log error with detailed context
        print_and_log("")
        print_and_log("❌ PROCESSING FAILED")
        print_and_log("=" * 50)
        print_and_log(f"📄 File: {name}")
        print_and_log(f"🚨 Error: {str(e)}")
        print_and_log("")
        print_and_log("🛠️  TROUBLESHOOTING TIPS:")
        print_and_log("   • Check if the PDF is a scanned image (may need better OCR)")
        print_and_log("   • Verify the PDF contains bank statement data")
        print_and_log("   • Ensure the file is not password protected")
        print_and_log("   • Try with a different bank statement format")
        print_and_log("=" * 50)
        
        logging.error(f"Error processing {name}: {str(e)}")
        
        # Create error BAI2 file for general processing failures
        try:
            now = datetime.now()
            file_date = now.strftime("%y%m%d")
            file_time = now.strftime("%H%M")
            
            # Determine error code based on exception type or message
            error_message = str(e)
            if "Document Intelligence" in error_message or "docintelligence" in error_message.lower():
                error_code = "ERROR_DOC_INTEL_FAILED"
            elif "OpenAI" in error_message or "openai" in error_message.lower():
                error_code = "ERROR_PARSING_FAILED"
            elif "connection" in error_message.lower() or "network" in error_message.lower():
                error_code = "ERROR_NETWORK_FAILED"
            elif "timeout" in error_message.lower():
                error_code = "ERROR_TIMEOUT"
            else:
                error_code = "ERROR_PROCESSING_FAILED"
            
            error_bai2_content = create_error_bai2_file(
                f"Processing failed: {error_message}",
                name,
                file_date,
                file_time,
                error_code
            )
            
            # Upload error BAI2 file
            error_filename = f"ERROR_{name.replace('.pdf', '')}.bai"
            blob_service = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
            error_blob_client = blob_service.get_blob_client(
                container="bank-reconciliation",
                blob=f"bai2-outputs/{error_filename}"
            )
            error_blob_client.upload_blob(error_bai2_content, overwrite=True)
            print_and_log(f"✅ Error BAI2 file created: {error_filename}")
            
        except Exception as bai2_error:
            print_and_log(f"⚠️  Could not create error BAI2 file: {str(bai2_error)}")
        
        raise
    finally:
        # Always remove the file from processing set when done
        if 'file_key' in locals():
            _processing_files.discard(file_key)
            print_and_log(f"[DEBUG] Removed {name} from processing queue")

def convert_to_bai2(data, filename, reconciliation_data=None, routing_number=None):
    """
    Convert extracted data to comprehensive BAI format like Vera_baitest_20250728 (1) (1).bai
    Generates multi-day format with detailed transaction records and summary codes
    """
    print_and_log("🔄 Converting to comprehensive BAI format...")
    
    # Get current date and time for BAI header
    now = datetime.now()
    file_date = now.strftime("%y%m%d")
    file_time = now.strftime("%H%M")
    
    # Use provided routing number or extract it
    if routing_number:
        originator_id = routing_number
        print_and_log(f"✅ Using provided routing number: {originator_id}")
    else:
        # Try to extract routing number from data
        originator_id = get_routing_number(data)
        if not originator_id:
            print_and_log("❌ CRITICAL: No routing number found on statement and unable to lookup by bank name - creating ERROR file")
            return create_error_bai2_file("No routing number found on statement", filename, file_date, file_time, "ERROR_NO_ROUTING")
        print_and_log(f"✅ Extracted routing number: {originator_id}")
    
    # Initialize other defaults (these could also be made dynamic in the future)
    receiver_id = "323809"  # Workday-configured company identifier
    
    # Extract account number from statement
    account_number = get_account_number(data)
    if not account_number:
        print_and_log("❌ CRITICAL: No account number found on statement - creating ERROR file")
        return create_error_bai2_file("No account number found on statement", filename, file_date, file_time, "ERROR_NO_ACCOUNT")
    
    print_and_log(f"✅ Using account number: {account_number}")
    
    currency = "USD"
    opening_balance_amount = 0
    transactions = []
    reconciliation_status = "UNKNOWN"
    error_codes = []
    
    # Extract reconciliation status if available
    if reconciliation_data:
        if isinstance(reconciliation_data, dict):
            reconciliation_status = reconciliation_data.get("reconciliation_status", "UNKNOWN")
            if "error" in reconciliation_data:
                reconciliation_status = "ERROR"
        print_and_log(f"🔍 Reconciliation Status: {reconciliation_status}")
    
    # Handle OpenAI parsed data (prioritize reconciliation_data if available)
    if reconciliation_data and isinstance(reconciliation_data, dict) and "transactions" in reconciliation_data:
        print_and_log("✅ Using OpenAI parsed transaction data from reconciliation_data")
        
        # Extract opening balance - handle both dict format {"amount": value} and direct float value
        opening_balance_value = reconciliation_data.get("opening_balance")
        if opening_balance_value is not None:
            if isinstance(opening_balance_value, dict) and opening_balance_value.get("amount") is not None:
                # Dict format: {"amount": value}
                opening_balance_amount = int(float(opening_balance_value["amount"]) * 100)  # Convert to cents
                print_and_log(f"💰 Opening balance: ${opening_balance_amount/100:,.2f}")
            elif isinstance(opening_balance_value, (int, float)):
                # Direct number format
                opening_balance_amount = int(float(opening_balance_value) * 100)  # Convert to cents
                print_and_log(f"💰 Opening balance: ${opening_balance_amount/100:,.2f}")
            else:
                print_and_log(f"⚠️ Unrecognized opening balance format: {type(opening_balance_value)}")
        
        
        # Extract transactions
        transactions = reconciliation_data.get("transactions", [])
        print_and_log(f"📊 Processing {len(transactions)} transactions from reconciliation_data")
        
        # Validate and clean transactions array
        if transactions:
            valid_transactions = []
            for i, txn in enumerate(transactions):
                if isinstance(txn, dict):
                    valid_transactions.append(txn)
                else:
                    print_and_log(f"⚠️ Skipping invalid transaction at index {i}: {type(txn)} - {txn}")
            transactions = valid_transactions
            print_and_log(f"✅ Validated transactions: {len(transactions)} valid transactions")
        
    # Handle OpenAI parsed data in main data structure
    elif "transactions" in data:
        print_and_log("✅ Using OpenAI parsed transaction data from main data")
        
        # Extract opening balance - handle both dict format {"amount": value} and direct float value
        opening_balance_value = data.get("opening_balance")
        if opening_balance_value is not None:
            if isinstance(opening_balance_value, dict) and opening_balance_value.get("amount") is not None:
                # Dict format: {"amount": value}
                opening_balance_amount = int(float(opening_balance_value["amount"]) * 100)  # Convert to cents
                print_and_log(f"💰 Opening balance: ${opening_balance_amount/100:,.2f}")
            elif isinstance(opening_balance_value, (int, float)):
                # Direct number format
                opening_balance_amount = int(float(opening_balance_value) * 100)  # Convert to cents
                print_and_log(f"💰 Opening balance: ${opening_balance_amount/100:,.2f}")
            else:
                print_and_log(f"⚠️ Unrecognized opening balance format: {type(opening_balance_value)}")
        
        
        # Extract transactions
        transactions = data.get("transactions", [])
        print_and_log(f"📊 Processing {len(transactions)} transactions from main data")
    
    # Validate and clean transactions array - ensure all items are dictionaries
    if transactions:
        valid_transactions = []
        for i, txn in enumerate(transactions):
            if isinstance(txn, dict):
                valid_transactions.append(txn)
            else:
                print_and_log(f"⚠️ Skipping invalid transaction at index {i}: {type(txn)} - {txn}")
        transactions = valid_transactions
        print_and_log(f"✅ Validated transactions: {len(transactions)} valid transactions")
    
    # Handle raw extraction data - NO FALLBACK, return error
    else:
        print_and_log("❌ CRITICAL: OpenAI parsing failed and no reconciliation data available - creating ERROR file")
        return create_error_bai2_file("OpenAI parsing failed - no transaction data available", filename, file_date, file_time, "ERROR_PARSING_FAILED")
    
    # Build comprehensive BAI file structure
    lines = []
    record_count = 0  # Track records in the file (excluding file header)
    
    # Generate dynamic File ID (sequential based on timestamp)
    file_id = int(now.strftime('%Y%m%d%H%M'))  # YYYYMMDDHHMM format
    
    # 01 - File Header (comprehensive format)
    lines.append(f"01,{originator_id},{receiver_id},{file_date},{file_time},{file_id},,,2/")
    # Don't count the file header in record_count
    
    # Always calculate transaction totals and closing balance from source data
    # This ensures we show actual data even if reconciliation failed
    source_total_deposits = 0
    source_total_withdrawals = 0
    source_transaction_count = 0
    source_closing_balance = None
    source_opening_balance = None
    
    # Calculate from source data (transactions) - prioritize reconciliation_data
    transaction_data_source = reconciliation_data if reconciliation_data and "transactions" in reconciliation_data else data
    
    if "transactions" in transaction_data_source:
        transactions_for_calc = transaction_data_source.get("transactions", [])
        source_transaction_count = len(transactions_for_calc)
        for txn in transactions_for_calc:
            # Validate that txn is a dictionary
            if not isinstance(txn, dict):
                print_and_log(f"⚠️ Skipping invalid transaction in source calculation: {type(txn)} - {txn}")
                continue
                
            amount = float(txn.get("amount", 0))
            if amount > 0:
                source_total_deposits += amount
            else:
                source_total_withdrawals += abs(amount)
    
    # Get balances from source data - handle both dict and direct float formats
    closing_balance_value = data.get("closing_balance")
    if closing_balance_value is not None:
        if isinstance(closing_balance_value, dict) and closing_balance_value.get("amount") is not None:
            source_closing_balance = float(closing_balance_value["amount"])
        elif isinstance(closing_balance_value, (int, float)):
            source_closing_balance = float(closing_balance_value)
    
    opening_balance_value = data.get("opening_balance")
    if opening_balance_value is not None:
        if isinstance(opening_balance_value, dict) and opening_balance_value.get("amount") is not None:
            source_opening_balance = float(opening_balance_value["amount"])
        elif isinstance(opening_balance_value, (int, float)):
            source_opening_balance = float(opening_balance_value)
    
    # Perform detailed reconciliation calculations (logic preserved but comments removed from BAI2 file)
    if reconciliation_status != "UNKNOWN":
        logging.info(f"Reconciliation status: {reconciliation_status}")
        
        # Add detailed reconciliation data and explanations (all logic preserved)
        if reconciliation_data:
            # Balance information (prefer reconciliation data, fallback to source)
            opening_bal = reconciliation_data.get("opening_balance")
            closing_bal = reconciliation_data.get("closing_balance")
            opening_known = reconciliation_data.get("opening_balance_known", False)
            closing_known = reconciliation_data.get("closing_balance_known", False)
            
            # Check if opening balance is marked as suspicious due to warnings
            warnings = reconciliation_data.get("warnings", [])
            opening_is_suspicious = any("confused" in warning.lower() for warning in warnings)
            
            # Only use source opening balance if reconciliation doesn't have it and it's NOT suspicious
            if not opening_known and not opening_is_suspicious:
                opening_bal = source_opening_balance
                if opening_bal is not None:
                    opening_known = True
            
            # If opening balance is marked as unknown or suspicious, set to None regardless of source
            if not opening_known or opening_is_suspicious:
                opening_bal = None
                opening_known = False
            
            # Only use source closing balance if reconciliation doesn't have it 
            if not closing_known:
                closing_bal = source_closing_balance
                if closing_bal is not None:
                    closing_known = True
            
            # Log balance information
            if opening_known and opening_bal is not None:
                logging.info(f"Opening balance: ${opening_bal:,.2f} (from statement)")
            else:
                logging.info("Opening balance: UNKNOWN")
            
            if closing_known and closing_bal is not None:
                logging.info(f"Closing balance: ${closing_bal:,.2f} (from statement)")
            else:
                logging.info("Closing balance: UNKNOWN")
            
            # Transaction summary (prefer reconciliation data, fallback to source calculation)
            total_deposits = reconciliation_data.get("total_deposits", source_total_deposits)
            total_withdrawals = reconciliation_data.get("total_withdrawals", source_total_withdrawals)
            transaction_count = reconciliation_data.get("transaction_count", source_transaction_count)
            
            logging.info(f"Total deposits: ${total_deposits:,.2f} ({transaction_count} transactions)")
            logging.info(f"Total withdrawals: ${total_withdrawals:,.2f}")
            
            # Add reconciliation calculation breakdown only if we have sufficient data
            if opening_known and opening_bal is not None and closing_bal is not None:
                # We have both balances and opening is not suspicious - show full calculation
                logging.info("Reconciliation calculation:")
                logging.info(f"  Starting Balance:    ${opening_bal:,.2f}")
                logging.info(f"  + Total Deposits:    ${total_deposits:,.2f}")
                logging.info(f"  - Total Withdrawals: ${total_withdrawals:,.2f}")
                calculated_closing = opening_bal + total_deposits - total_withdrawals
                logging.info(f"  = Calculated Close:  ${calculated_closing:,.2f}")
                logging.info(f"  Actual Close:       ${closing_bal:,.2f}")
                
                actual_difference = closing_bal - calculated_closing
                if abs(actual_difference) > 0.01:
                    logging.info(f"  Difference:          ${actual_difference:,.2f}")
                    if actual_difference > 0:
                        logging.info(f"    (Actual is ${actual_difference:,.2f} higher)")
                    else:
                        logging.info(f"    (Actual is ${abs(actual_difference):,.2f} lower)")
                else:
                    logging.info("  ✓ BALANCED - No difference")
            else:
                # Missing essential balance data or opening balance is suspicious - cannot calculate
                logging.info("Reconciliation status:")
                if not opening_known:
                    logging.info("  Opening balance unreliable - cannot use for calculation")
                elif opening_bal is None:
                    logging.info("  Opening balance missing from statement")
                    logging.info("  Cannot calculate expected closing balance")
                
                if closing_bal is None:
                    logging.info("  Closing balance missing from statement")
                    logging.info("  Cannot verify balance accuracy")
                else:
                    logging.info(f"  Actual Close:       ${closing_bal:,.2f}")
                    
                logging.info(f"  Transaction totals: ${total_deposits:,.2f} deposits, ${total_withdrawals:,.2f} withdrawals")
            
            # Reconciliation calculations
            expected_closing = reconciliation_data.get("expected_closing")
            difference = reconciliation_data.get("difference", 0)
            
            if expected_closing is not None:
                logging.info(f"Expected closing: ${expected_closing:,.2f}")
            
            if abs(difference) > 0.01:  # More than 1 cent difference
                logging.info(f"Balance difference: ${difference:,.2f}")
        else:
            # No reconciliation data available - use source data
            if source_opening_balance is not None:
                logging.info(f"Opening balance: ${source_opening_balance:,.2f} (from statement)")
            else:
                logging.info("Opening balance: NOT_FOUND - Missing from bank statement")
            
            if source_closing_balance is not None:
                logging.info(f"Closing balance: ${source_closing_balance:,.2f} (from statement)")
            else:
                logging.info("Closing balance: NOT_FOUND - Missing from bank statement")
            
            logging.info(f"Total deposits: ${source_total_deposits:,.2f} ({source_transaction_count} transactions)")
            logging.info(f"Total withdrawals: ${source_total_withdrawals:,.2f}")
            
            # Add calculation breakdown even without reconciliation data
            logging.info("Balance calculation:")
            if source_opening_balance is not None:
                logging.info(f"  Starting Balance:    ${source_opening_balance:,.2f}")
                logging.info(f"  + Total Deposits:    ${source_total_deposits:,.2f}")
                logging.info(f"  - Total Withdrawals: ${source_total_withdrawals:,.2f}")
                calculated_closing = source_opening_balance + source_total_deposits - source_total_withdrawals
                logging.info(f"  = Calculated Close:  ${calculated_closing:,.2f}")
                
                if source_closing_balance is not None:
                    logging.info(f"  Actual Close:       ${source_closing_balance:,.2f}")
                    actual_difference = source_closing_balance - calculated_closing
                    if abs(actual_difference) > 0.01:
                        logging.info(f"  Difference:          ${actual_difference:,.2f}")
                        if actual_difference > 0:
                            logging.info(f"    (Actual is ${actual_difference:,.2f} higher)")
                        else:
                            logging.info(f"    (Actual is ${abs(actual_difference):,.2f} lower)")
                    else:
                        logging.info("  ✓ BALANCED - No difference")
                else:
                    logging.info("  Actual Close:       UNKNOWN")
                    logging.info("  Cannot verify balance accuracy")
            else:
                logging.info("  Starting Balance:    UNKNOWN")
                logging.info(f"  + Total Deposits:    ${source_total_deposits:,.2f}")
                logging.info(f"  - Total Withdrawals: ${source_total_withdrawals:,.2f}")
                if source_closing_balance is not None:
                    logging.info(f"  Actual Close:       ${source_closing_balance:,.2f}")
                    logging.info("  Cannot calculate expected close without starting balance")
                else:
                    logging.info("  Actual Close:       UNKNOWN")
                    logging.info("  Cannot perform calculation - missing balances")
        
        # Check for reconciliation failure and log balance difference info
        if reconciliation_data and abs(reconciliation_data.get("difference", 0)) > 0.01:
            difference = reconciliation_data.get("difference", 0)
            logging.info(f"Balance difference: ${difference:,.2f}")
            if reconciliation_status == "FAILED":
                logging.info("Reconciliation failed: Balance difference exceeds tolerance")
        
        # Note: Warnings section disabled - only process valid transactions
        
        # Log recommendations based on reconciliation status
        if reconciliation_status == "COMPLETE":
            logging.info("Recommendation: Reconciliation successful - BAI2 data is accurate")
        elif reconciliation_status == "PARTIAL":
            logging.info("Recommendation: Partial reconciliation - verify missing balance data manually")
        elif reconciliation_status == "INCOMPLETE":
            logging.info("Recommendation: Incomplete reconciliation - manual verification required")
        elif reconciliation_status == "FAILED":
            logging.info("Recommendation: Reconciliation failed - review statement and re-process")
            logging.info("Possible causes: OCR errors, statement format changes, missing data")
    else:
        logging.info("Reconciliation status: No reconciliation data available")
        
        # Still log balance and transaction information from source data
        if source_opening_balance is not None:
            logging.info(f"Opening balance: ${source_opening_balance:,.2f} (from statement)")
        else:
            logging.info("Opening balance: NOT_FOUND - Missing from bank statement")
        
        if source_closing_balance is not None:
            logging.info(f"Closing balance: ${source_closing_balance:,.2f} (from statement)")
        else:
            logging.info("Closing balance: NOT_FOUND - Missing from bank statement")
        
        logging.info(f"Total deposits: ${source_total_deposits:,.2f} ({source_transaction_count} transactions)")
        logging.info(f"Total withdrawals: ${source_total_withdrawals:,.2f}")
        logging.info("Recommendation: Process with full reconciliation analysis for accuracy")
    
    # Group transactions by date (simulate multi-day format)
    transaction_groups = {}
    for txn in transactions:
        # Validate that txn is a dictionary (not a float or other type)
        if not isinstance(txn, dict):
            print_and_log(f"⚠️ Skipping invalid transaction: {type(txn)} - {txn}")
            continue
            
        txn_date = txn.get("date", now.strftime("%Y-%m-%d"))
        # Convert date to YYMMDD format
        try:
            dt = datetime.strptime(txn_date, "%Y-%m-%d")
            group_date = dt.strftime("%y%m%d")
        except:
            group_date = file_date
        
        if group_date not in transaction_groups:
            transaction_groups[group_date] = []
        transaction_groups[group_date].append(txn)
    
    # If no transaction groups, create a default group
    if not transaction_groups:
        transaction_groups[file_date] = []
    
    total_control_total = 0
    total_groups = 0
    previous_ending_balance = opening_balance_amount  # Track balance continuity for Workday
    
    # Process each group (day)
    for group_date in sorted(transaction_groups.keys()):
        group_transactions = transaction_groups[group_date]
        
        # 02 - Group Header
        lines.append(f"02,{receiver_id},{originator_id},1,{group_date},,{currency},2/")
        group_record_count = 0  # Track records in this group (excluding the group header)
        
        # Calculate group totals
        credit_total = 0
        debit_total = 0
        credit_count = 0
        debit_count = 0
        
        for txn in group_transactions:
            # Validate that txn is a dictionary
            if not isinstance(txn, dict):
                print_and_log(f"⚠️ Skipping invalid transaction in group totals: {type(txn)} - {txn}")
                continue
                
            amount = float(txn.get("amount", 0))
            if amount >= 0:
                credit_total += int(amount * 100)
                credit_count += 1
            else:
                debit_total += int(abs(amount) * 100)
                debit_count += 1
        
        # Determine starting balance for this group to maintain continuity
        if total_groups == 0:
            # First group uses actual opening balance
            starting_balance = opening_balance_amount
        else:
            # Subsequent groups use previous group's ending balance to maintain continuity
            starting_balance = previous_ending_balance
        # Calculate ending balance properly based on extracted closing balance or calculation
        if reconciliation_data and isinstance(reconciliation_data, dict):
            # Try to get closing balance from reconciliation data - handle both dict and direct float formats
            closing_balance_data = reconciliation_data.get("closing_balance")
            if closing_balance_data is not None:
                if isinstance(closing_balance_data, dict) and closing_balance_data.get("amount") is not None:
                    # Dict format: {"amount": value}
                    ending_balance = int(float(closing_balance_data["amount"]) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted closing balance: ${ending_balance/100:,.2f}")
                elif isinstance(closing_balance_data, (int, float)):
                    # Direct number format
                    ending_balance = int(float(closing_balance_data) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted closing balance: ${ending_balance/100:,.2f}")
                else:
                    # Calculate from starting balance + transactions
                    ending_balance = starting_balance + credit_total - debit_total
                    print_and_log(f"💰 Calculated ending balance: ${ending_balance/100:,.2f}")
            else:
                # Calculate from starting balance + transactions
                ending_balance = starting_balance + credit_total - debit_total
                print_and_log(f"💰 Calculated ending balance: ${ending_balance/100:,.2f}")
        else:
            # Fallback calculation
            ending_balance = starting_balance + credit_total - debit_total
            print_and_log(f"💰 Calculated ending balance: ${ending_balance/100:,.2f}")
        
        # 03 - Account Identifier (account_number, currency, status_code) - NO routing number
        lines.append(f"03,{account_number},,010,,,Z/")
        group_record_count += 1
        account_record_count = 1  # Start with 1 to include the account identifier (03)
        
        # 88 - Summary Records (BAI summary codes) - Standard BAI2 continuation records
        # Extract actual opening and closing balances from reconciliation data or source data
        opening_balance_cents = ""
        closing_balance_cents = ""
        
        # Get opening balance from reconciliation data - handle both dict and direct float formats
        if reconciliation_data and isinstance(reconciliation_data, dict):
            opening_balance_data = reconciliation_data.get("opening_balance")
            if opening_balance_data is not None:
                if isinstance(opening_balance_data, dict) and opening_balance_data.get("amount") is not None:
                    # Dict format: {"amount": value}
                    opening_balance_cents = int(float(opening_balance_data["amount"]) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted opening balance: ${opening_balance_cents/100:,.2f}")
                elif isinstance(opening_balance_data, (int, float)):
                    # Direct number format
                    opening_balance_cents = int(float(opening_balance_data) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted opening balance: ${opening_balance_cents/100:,.2f}")
            
            # Get closing balance from reconciliation data - handle both dict and direct float formats
            closing_balance_data = reconciliation_data.get("closing_balance")
            if closing_balance_data is not None:
                if isinstance(closing_balance_data, dict) and closing_balance_data.get("amount") is not None:
                    # Dict format: {"amount": value}
                    closing_balance_cents = int(float(closing_balance_data["amount"]) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted closing balance: ${closing_balance_cents/100:,.2f}")
                elif isinstance(closing_balance_data, (int, float)):
                    # Direct number format
                    closing_balance_cents = int(float(closing_balance_data) * 100)  # Convert to cents
                    print_and_log(f"💰 Using extracted closing balance: ${closing_balance_cents/100:,.2f}")
        
        # Fallback to source data if not in reconciliation data
        if not opening_balance_cents and source_opening_balance is not None:
            opening_balance_cents = int(float(source_opening_balance) * 100)
            print_and_log(f"💰 Using source opening balance: ${opening_balance_cents/100:,.2f}")
        
        if not closing_balance_cents and source_closing_balance is not None:
            closing_balance_cents = int(float(source_closing_balance) * 100)
            print_and_log(f"💰 Using source closing balance: ${closing_balance_cents/100:,.2f}")
        
        # Generate balance summary records matching working file format
        # Based on working file analysis:
        # 88,015 = Closing ledger balance (this is the important end-of-day balance)
        # 88,040 = Opening available balance (empty in first section)
        # 88,045 = Closing available balance (matches closing ledger)
        # 88,072 = Transaction-based calculated amount 
        
        if closing_balance_cents:
            lines.append(f"88,015,{closing_balance_cents},,Z/")  # Closing ledger balance
        else:
            lines.append(f"88,015,,,Z/")  # Empty closing balance if not available
        
        lines.append(f"88,040,,,Z/")  # Opening available balance (empty like working file)
        
        # 045 = Closing available balance (should match closing ledger balance)
        if closing_balance_cents:
            lines.append(f"88,045,{closing_balance_cents},,Z/")  # Closing available balance (matches 015)
        else:
            lines.append(f"88,045,,,Z/")  # Empty closing available balance if not available
        
        lines.append(f"88,072,{debit_total},,Z/")  # Transaction-based calculated amount
        lines.append(f"88,074,000,,Z/")  # Total rejected credits
        lines.append(f"88,100,{credit_total},{credit_count},Z/")  # Credit summary
        lines.append(f"88,400,{debit_total},{debit_count},Z/")  # Debit summary
        lines.append(f"88,075,,,Z/")  # Total rejected debits
        lines.append(f"88,079,,,Z/")  # Total rejected transactions
        
        account_record_count += 9  # Add 9 summary records (88 records)
        group_record_count += 9   # Also add to group count
        
        # 16 - Transaction Detail Records (comprehensive format)
        transaction_id = 2147809075 + (total_groups * 100)  # Sequential transaction IDs
        
        if group_transactions:
            for i, txn in enumerate(group_transactions):
                # Validate that txn is a dictionary
                if not isinstance(txn, dict):
                    print_and_log(f"⚠️ Skipping invalid transaction in BAI generation: {type(txn)} - {txn}")
                    continue
                    
                amount = float(txn.get("amount", 0))
                original_description = str(txn.get("description", "Transaction"))
                txn_type_hint = str(txn.get("type", "")).lower()
                extracted_ref = txn.get("reference_number", "")  # Get extracted reference number
                
                # Convert amount to cents for BAI
                amount_cents = int(abs(amount) * 100)
                
                # Use extracted reference number if available, otherwise generate in working format
                if extracted_ref and str(extracted_ref).strip() and str(extracted_ref).strip() != "null":
                    ref_num = str(extracted_ref).strip()
                    print_and_log(f"✅ Using extracted reference number: {ref_num}")
                else:
                    ref_num = f"478980{340 + i:03d}"  # Fallback to working file format
                    print_and_log(f"⚠️ No reference number extracted, using generated: {ref_num}")
                
                # Determine BAI transaction type code
                if amount < 0 or txn_type_hint in ["withdrawal", "debit", "fee", "check"]:
                    # Check if it's a return or ACH debit
                    if "return" in original_description.lower() or "returned" in original_description.lower():
                        txn_type = "555"  # Returns
                    else:
                        txn_type = "451"  # ACH debits
                    bank_ref = ""  # Empty for debits in working file
                    text_desc = original_description if original_description else ""
                    lines.append(f"16,{txn_type},{amount_cents},Z,{ref_num},{bank_ref},{text_desc},/")
                    # REMOVED: 88 transaction detail records per user request to remove all comments
                    group_record_count += 1
                    account_record_count += 1
                else:
                    txn_type = "301"  # Deposits
                    # Use timestamp-based reference to ensure uniqueness across banks
                    import time
                    base_ref = int(time.time()) % 100000
                    bank_ref = f"0000{base_ref + i:06d}"
                    text_desc = original_description if original_description else "Deposit"  # Use actual description from statement
                    lines.append(f"16,{txn_type},{amount_cents},Z,{ref_num},{bank_ref},{text_desc},/")
                    group_record_count += 1
                    account_record_count += 1
                
                transaction_id += 1
        
        # 49 - Account Trailer
        account_control_total = ending_balance
        # Account trailer should count all account records (03 + 88s + 16s) INCLUDING itself (49)
        # Current account_record_count = 22, we need to add 1 for the trailer itself
        account_trailer_count = account_record_count + 1  # Add 1 for the account trailer itself
        print_and_log(f"📊 DEBUG: account_record_count={account_record_count}, account_trailer_count={account_trailer_count}")
        lines.append(f"49,{account_control_total},{account_trailer_count}/")
        group_record_count += 1  # Add account trailer to group count
        
        # 98 - Group Trailer  
        number_of_accounts = 1
        # Group trailer counts all group records (02 + account records + 49) INCLUDING itself (98)
        # group_record_count now includes: account records + account trailer = 23
        # We need to add the group header (02) and the group trailer itself (98)
        group_trailer_count = 1 + group_record_count + 1  # +1 for group header (02) + 1 for group trailer itself (98)
        print_and_log(f"📊 DEBUG: group_record_count={group_record_count}, group_trailer_count={group_trailer_count}")
        group_control_total = account_control_total  # Same as account control total for single account
        # Group trailer includes number_of_accounts field - BAI2 format requires 4 fields for record 98
        lines.append(f"98,{group_control_total},{number_of_accounts},{group_trailer_count}/")  # 4 fields for BAI2 compliance
        
        total_control_total += group_control_total
        total_groups += 1
        # Calculate file records including all created records
        
        # Update balance for next group continuity
        previous_ending_balance = ending_balance
    
    # 99 - File Trailer (control_total, number_of_groups, record_count) - BAI2 format requires 4 fields
    # File trailer counts all records except file header (01) INCLUDING the file trailer (99) itself
    # At this point, len(lines) = 26 (includes 01,02,03,88s,16s,49,98 but NOT 99 yet)
    # We need to count: 02,03,88s,16s,49,98,99 = len(lines) - 1 (remove 01) + 1 (add 99) = len(lines)
    total_file_records = len(lines) + 1  # Include the 99 record itself
    print_and_log(f"📊 DEBUG: len(lines) before 99={len(lines)}, total_groups={total_groups}, total_file_records={total_file_records}")
    # File trailer includes total_groups field - BAI2 format requires 4 fields for record 99  
    lines.append(f"99,{total_control_total},{total_groups},{total_file_records}/")
    
    print_and_log(f"✅ Comprehensive BAI file created with {len(transactions)} transactions across {total_groups} groups")
    print_and_log(f"📊 File structure: {len(lines)} total lines")
    print_and_log(f"📊 Final record counts - Account: {account_trailer_count}, Group: {group_trailer_count}, File: {total_file_records}")
    print_and_log(f"💰 Control total: ${total_control_total/100:,.2f}")
    
    return "\n".join(lines) + "\n"

@app.function_name("setup_containers")
@app.route(route="setup", methods=["GET"])
def setup_containers(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP endpoint to manually create required storage container and folder structure"""
    try:
        # Validate environment variables
        print_and_log("=== DEBUG: Environment Check ===")
        storage_connection = os.environ.get("AzureWebJobsStorage", "NOT_FOUND")
        print_and_log(f"Connection string found: {len(storage_connection) > 10}")
        print_and_log(f"Connection string starts with: {storage_connection[:50]}...")
        
        if storage_connection == "NOT_FOUND":
            return func.HttpResponse("AzureWebJobsStorage environment variable not found", status_code=500)
        
        # Test connection
        blob_service = BlobServiceClient.from_connection_string(storage_connection)
        print_and_log("✅ BlobServiceClient created successfully")
        
        # List existing containers
        containers = list(blob_service.list_containers())
        print_and_log(f"Found {len(containers)} existing containers")
        
        # Create main container
        container_name = "bank-reconciliation"
        try:
            blob_service.create_container(container_name)
            print_and_log(f"Created container: {container_name}")
            created_container = True
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                print_and_log(f"Container already exists: {container_name}")
                created_container = False
            else:
                raise e
        
        # Create folder structure by uploading placeholder files
        container_client = blob_service.get_container_client(container_name)
        folders = ["incoming-bank-statements", "bai2-outputs", "archive"]
        created_folders = []
        
        for folder in folders:
            placeholder_blob = f"{folder}/.placeholder"
            try:
                # Check if folder already has content
                blobs = list(container_client.list_blobs(name_starts_with=f"{folder}/"))
                if not blobs:
                    # Create placeholder to establish folder structure
                    container_client.upload_blob(
                        name=placeholder_blob,
                        data="This file creates the folder structure. You can delete it once you have other files in this folder.",
                        overwrite=True
                    )
                    created_folders.append(folder)
                    print_and_log(f"Created folder structure: {folder}")
                else:
                    print_and_log(f"Folder already has content: {folder}")
            except Exception as e:
                logging.error(f"Error creating folder {folder}: {str(e)}")
        
        message_parts = []
        if created_container:
            message_parts.append("Created container: bank-reconciliation")
        if created_folders:
            message_parts.append(f"Created folder structure: {', '.join(created_folders)}")
        if not created_container and not created_folders:
            message_parts.append("Container and folder structure already exist")
        
        message = ". ".join(message_parts) + "."
        return func.HttpResponse(message, status_code=200)
        
    except Exception as e:
        logging.error(f"Error setting up container structure: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
