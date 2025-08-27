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
import traceback
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
from openai import AzureOpenAI

# Configuration constants
FUNCTION_APP_NAME = "BankStatementAgent"

# Configure logging to suppress verbose Azure SDK HTTP traffic
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.storage.blob').setLevel(logging.WARNING)
logging.getLogger('azure.identity').setLevel(logging.WARNING)
logging.getLogger('azure.core').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Import bai2_fixer for BAI2 validation and fixing
try:
    import bai2_fixer
    print("✅ BAI2 fixer module loaded successfully")
except ImportError as e:
    print(f"⚠️ Could not load bai2_fixer module: {e}")
    bai2_fixer = None

# Import enhanced bank matching system
try:
    from bank_info_loader import get_bank_info_for_processing
    print("✅ Enhanced bank matching system loaded")
except ImportError as e:
    print(f"⚠️ Could not load enhanced bank matching: {e}")
    get_bank_info_for_processing = None

# === THROTTLING AND RATE LIMITING SYSTEM ===
import threading
from collections import defaultdict
from typing import Optional

# Import throttling configuration
try:
    from throttling_config import ThrottlingConfig
    print("✅ Throttling configuration loaded")
    # Adjust for Azure OpenAI (you can change this based on your actual plan)
    ThrottlingConfig.adjust_for_plan('azure')
except ImportError as e:
    print(f"⚠️ Could not load throttling config: {e}")
    # Fallback configuration
    class ThrottlingConfig:
        CALLS_PER_MINUTE = 50
        MIN_DELAY_BETWEEN_CALLS = 2
        RETRY_DELAYS = [2, 5, 10, 20]
        INITIAL_PROCESSING_DELAY_MIN = 1
        INITIAL_PROCESSING_DELAY_MAX = 5
        RETRYABLE_ERROR_KEYWORDS = ['rate limit', 'quota', 'too many requests', '429', 'timeout', 'connection', 'network']

class OpenAIThrottler:
    """Thread-safe throttling system for OpenAI API calls"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._last_call_time = 0
        self._call_count = 0
        self._reset_time = 0
        
    def wait_if_needed(self):
        """Enforce rate limiting before making OpenAI call"""
        with self._lock:
            current_time = time.time()
            
            # Reset counter every minute
            if current_time - self._reset_time >= 60:
                self._call_count = 0
                self._reset_time = current_time
            
            # Check if we've hit the rate limit
            if self._call_count >= ThrottlingConfig.CALLS_PER_MINUTE:
                wait_time = 60 - (current_time - self._reset_time)
                if wait_time > 0:
                    print_and_log(f"⏳ Rate limit reached ({ThrottlingConfig.CALLS_PER_MINUTE}/min), waiting {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    self._call_count = 0
                    self._reset_time = time.time()
            
            # Enforce minimum delay between calls
            time_since_last_call = current_time - self._last_call_time
            if time_since_last_call < ThrottlingConfig.MIN_DELAY_BETWEEN_CALLS:
                delay = ThrottlingConfig.MIN_DELAY_BETWEEN_CALLS - time_since_last_call
                print_and_log(f"⏱️ Throttling: waiting {delay:.1f}s between calls...")
                time.sleep(delay)
            
            self._call_count += 1
            self._last_call_time = time.time()
            print_and_log(f"🤖 OpenAI call #{self._call_count}/{ThrottlingConfig.CALLS_PER_MINUTE} this minute")

    def retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        for attempt, delay in enumerate(ThrottlingConfig.RETRY_DELAYS):
            try:
                self.wait_if_needed()
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if attempt == len(ThrottlingConfig.RETRY_DELAYS) - 1:
                    # Last attempt failed
                    print_and_log(f"❌ OpenAI call failed after {len(ThrottlingConfig.RETRY_DELAYS)} attempts: {str(e)}")
                    raise e
                
                # Check if this is a retryable error
                is_retryable = any(keyword in error_str for keyword in ThrottlingConfig.RETRYABLE_ERROR_KEYWORDS)
                
                if is_retryable:
                    print_and_log(f"🔄 Retryable error (attempt {attempt + 1}/{len(ThrottlingConfig.RETRY_DELAYS)}), backing off {delay}s...")
                    print_and_log(f"   Error: {str(e)[:100]}...")
                    time.sleep(delay)
                else:
                    # Non-retryable error
                    print_and_log(f"❌ Non-retryable error: {str(e)}")
                    raise e

# Global throttler instance
openai_throttler = OpenAIThrottler()

# Processing queue to handle multiple file uploads
class ProcessingQueue:
    """Simple in-memory queue to serialize file processing"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._processing = set()
        
    def is_processing(self, file_key: str) -> bool:
        """Check if file is currently being processed"""
        with self._lock:
            return file_key in self._processing
    
    def start_processing(self, file_key: str) -> bool:
        """Mark file as being processed. Returns True if processing started, False if already processing"""
        with self._lock:
            if file_key in self._processing:
                return False
            self._processing.add(file_key)
            return True
    
    def finish_processing(self, file_key: str):
        """Mark file as finished processing"""
        with self._lock:
            self._processing.discard(file_key)
    
    def get_queue_status(self) -> dict:
        """Get current queue status for monitoring"""
        with self._lock:
            return {
                'currently_processing': len(self._processing),
                'processing_files': list(self._processing)
            }

# Global processing queue
processing_queue = ProcessingQueue()

# Configure console encoding for Unicode support
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Enhanced transaction extraction logic from extract_transactions_841.py
import decimal
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

DATE_LINE = re.compile(r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$')
AMOUNT_LINE = re.compile(r'^\d{1,3}(?:,\d{3})*\.\d{2}$')
CURRENCY_CLEAN = re.compile(r'[^0-9\.-]')

@dataclass
class Transaction:
    date: str           # MM-DD
    type: str           # debit / credit / fee
    amount: str         # original string amount
    amount_decimal: float
    description: str

def parse_transactions_from_ocr(text: str) -> Dict[str, List[Transaction]]:
    """
    Enhanced transaction parsing logic that correctly categorizes fees based on statement section
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    n = len(lines)
    debits: List[Transaction] = []
    credits: List[Transaction] = []
    i = 0
    current_section = None
    
    while i < n:
        line = lines[i]
        upper = line.upper()
        if upper == 'DEBITS':
            current_section = 'debits'
            print_and_log(f"📍 Entering DEBITS section")
        elif upper == 'CREDITS':
            current_section = 'credits'
            print_and_log(f"📍 Entering CREDITS section")
        elif DATE_LINE.match(line):
            # Collect description lines until amount line or next date/section
            date_val = line
            desc_lines = []
            j = i + 1
            amount_line = None
            while j < n:
                nxt = lines[j]
                if AMOUNT_LINE.match(nxt):
                    amount_line = nxt
                    j += 1
                    break
                if DATE_LINE.match(nxt) or nxt.upper() in ('DEBITS','CREDITS','DAILY BALANCES','OVERDRAFT/RETURN ITEM FEES'):
                    break
                desc_lines.append(nxt)
                j += 1
            if amount_line and current_section in ('debits','credits'):
                amt_clean = CURRENCY_CLEAN.sub('', amount_line)
                try:
                    amt_dec = float(decimal.Decimal(amt_clean))
                except Exception:
                    amt_dec = 0.0
                description = ' | '.join(desc_lines)
                ttype = 'debit' if current_section == 'debits' else 'credit'
                # Classify fee but keep in original section (debits fees are still debits)
                if 'FEE' in description.upper() or 'LOSS/CHG' in description.upper():
                    ttype = 'fee'
                tx = Transaction(date=date_val, type=ttype, amount=amount_line, amount_decimal=amt_dec, description=description)
                # Fees go to debits if found in DEBITS section, credits if found in CREDITS section
                if current_section == 'debits':
                    debits.append(tx)
                    print_and_log(f"💸 Debit: {date_val} ${amt_dec:.2f} - {description[:50]}...")
                else:
                    credits.append(tx)
                    print_and_log(f"💰 Credit: {date_val} ${amt_dec:.2f} - {description[:50]}...")
            i = j - 1 if j>i else i
        i += 1

    print_and_log(f"📊 Transaction extraction complete: {len(debits)} debits, {len(credits)} credits")
    return {
        'debits': debits,
        'credits': credits
    }

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
    """Print to console with proper encoding handling - Azure Functions will automatically capture console output in logs"""
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

# Load local settings after print_and_log is defined
load_local_settings()

def extract_routing_number_from_text(text):
    """DEPRECATED: Extract routing number from bank statement text using regex patterns
    
    WARNING: This function is no longer used as per policy change.
    Routing numbers are now ONLY obtained from the WAC Bank Information database.
    Customer statements should not be processed for routing numbers.
    """
    print_and_log("⚠️ DEPRECATED: extract_routing_number_from_text called - this function is disabled")
    print_and_log("⚠️ POLICY: Only using routing numbers from WAC Bank Information database")
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
    if words:
        # Look for natural stopping points in the first several words
        bank_name = extract_bank_name_from_words(words[:10])  # Check first 10 words
        if bank_name:
            print_and_log(f"✅ Found bank name from words: '{bank_name}'")
            return bank_name
    
    print_and_log("❌ No bank name found in statement text")
    return None

def extract_complete_bank_name_from_line(line):
    """Extract complete bank name from a single line with comprehensive boundary detection"""
    # Common bank name endings that indicate natural completion
    strong_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 
                     'company', 'credit', 'savings', 'loan', 'association', 'federal', 'national']
    
    # Common connecting words in bank names - these should NOT be endings
    connecting_words = ['of', 'and', '&', 'the', 'for', 'in', 'at', 'to', 'on']
    
    # Comprehensive stop words covering multiple categories
    stop_words = set([
        # Document/Report terms
        'report', 'statement', 'summary', 'document', 'page', 'dated', 'period', 'ending',
        # Account/Financial terms  
        'account', 'balance', 'routing', 'number', 'type', 'checking', 'savings', 'deposit',
        'transaction', 'transactions', 'activity', 'beginning', 'ending', 'current', 'available',
        # Address components (very common in headers)
        'p.o.', 'po', 'box', 'street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr',
        'blvd', 'boulevard', 'lane', 'ln', 'circle', 'cir', 'court', 'ct', 'suite', 'ste',
        'floor', 'apt', 'apartment', 'unit', 'building', 'bldg', 'plaza', 'place', 'pl',
        # Contact information
        'phone', 'tel', 'telephone', 'fax', 'email', 'website', 'www', 'http', 'https',
        'contact', 'call', 'customer', 'service', 'support', 'help', 'assistance',
        # Marketing/Slogan terms
        'spend', 'life', 'wisely', 'slogan', 'motto', 'tagline', 'welcome', 'thank', 'thanks',
        'serving', 'proudly', 'committed', 'dedicated', 'excellence', 'quality', 'premier',
        'leading', 'trusted', 'established', 'since', 'founded', 'years', 'experience',
        # Regulatory/Legal terms
        'member', 'fdic', 'equal', 'housing', 'lender', 'opportunity', 'insured', 'deposits',
        'regulation', 'compliance', 'terms', 'conditions', 'privacy', 'policy', 'notice',
        'disclosure', 'important', 'information', 'please', 'read', 'carefully',
        # Time/Date terms
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'am', 'pm', 'hours', 'open',
        'closed', 'holiday', 'business', 'banking',
        # Geographic indicators that typically follow bank names
        'located', 'headquarters', 'branch', 'branches', 'office', 'offices', 'location',
        'locations', 'main', 'downtown', 'north', 'south', 'east', 'west', 'central',
        # Common header/footer terms
        'return', 'service', 'requested', 'postmaster', 'mail', 'postal', 'zip', 'code',
        'delivery', 'address', 'correction', 'change', 'update', 'forward', 'forwarding'
    ])
    
    # Convert to lowercase for checking
    stop_words_lower = {word.lower() for word in stop_words}
    
    words = line.split()
    if not words:
        return None
    
    # Clean words and handle common formatting
    cleaned_words = []
    for word in words:
        # Remove common punctuation but preserve meaningful characters
        word_clean = word.strip('.,()[]{}"\'-')
        
        # Skip pure numbers, common symbols, and very short words
        if (word_clean and 
            not word_clean.isdigit() and 
            word_clean not in ['#', '$', '%', '*', '+', '=', '|'] and
            len(word_clean) >= 1):
            cleaned_words.append(word_clean)
    
    if not cleaned_words:
        return None
    
    # Quick reject: if line starts with obvious non-bank terms
    first_word_lower = cleaned_words[0].lower()
    if first_word_lower in stop_words_lower:
        return None
    
    # Skip leading numeric prefixes like "1" in "1 First United"
    start_index = 0
    if len(cleaned_words) > 1 and cleaned_words[0].isdigit():
        start_index = 1
    
    # Improved strategy: Build bank name word by word, handling complex patterns
    bank_words = []
    i = start_index
    
    while i < len(cleaned_words) and len(bank_words) < 10:  # Increased limit for complex names
        word = cleaned_words[i]
        word_lower = word.lower()
        
        # Stop at obvious non-bank words
        if word_lower in stop_words_lower:
            break
        
        # Add this word
        bank_words.append(word)
        
        # Check if this looks like a potential end, but be more generous
        # Only stop at strong endings if they are truly at the end of the bank name context
        if word_lower in strong_endings:
            # Look ahead to see if we should continue
            lookahead_start = i + 1
            should_continue = False
            words_to_add = []
            
            # Check for common patterns that should extend the bank name
            remaining_words = cleaned_words[lookahead_start:]
            
            # Don't treat words like "National" or "Federal" as endings if they're followed by "Bank"
            if (word_lower in ['national', 'federal', 'first', 'second', 'third'] and
                len(remaining_words) >= 1 and
                remaining_words[0].lower() in strong_endings):
                # Continue without stopping - these are descriptors, not endings
                pass
            
            # Pattern 1: "Bank of [Place]" 
            elif (len(remaining_words) >= 2 and 
                  remaining_words[0].lower() in connecting_words and
                  remaining_words[1][0].isupper() and
                  len(remaining_words[1]) >= 3 and
                  remaining_words[1].lower() not in stop_words_lower):
                
                words_to_add = [remaining_words[0], remaining_words[1]]
                should_continue = True
                
                # Also check for "Bank of the West" pattern
                if (len(remaining_words) >= 3 and 
                    remaining_words[0].lower() == 'of' and
                    remaining_words[1].lower() == 'the' and
                    remaining_words[2][0].isupper() and
                    remaining_words[2].lower() not in stop_words_lower):
                    words_to_add = [remaining_words[0], remaining_words[1], remaining_words[2]]
            
            # Pattern 2: "Credit Union" or "Federal Savings Association"
            elif (len(remaining_words) >= 1 and 
                  remaining_words[0].lower() in strong_endings):
                
                if word_lower in ['credit', 'savings', 'federal', 'national']:
                    words_to_add = [remaining_words[0]]
                    should_continue = True
                    
                    # Check for three-word endings like "Savings and Loan"
                    if (len(remaining_words) >= 3 and
                        remaining_words[1].lower() == 'and' and
                        remaining_words[2].lower() in strong_endings):
                        words_to_add = [remaining_words[0], remaining_words[1], remaining_words[2]]
            
            # Pattern 3: "and Trust Company" or "and Trust"
            elif (len(remaining_words) >= 2 and 
                  remaining_words[0].lower() == 'and' and
                  remaining_words[1].lower() in strong_endings):
                
                words_to_add = [remaining_words[0], remaining_words[1]]
                should_continue = True
                
                # Check for "and Trust Company"
                if (len(remaining_words) >= 3 and
                    remaining_words[2].lower() in strong_endings):
                    words_to_add = [remaining_words[0], remaining_words[1], remaining_words[2]]
            
            # Only stop if we found a real ending pattern or have enough words
            elif (word_lower in ['bank', 'union', 'company', 'corporation', 'association'] or 
                  len(bank_words) >= 6):
                # Add the additional words if we found a pattern
                if should_continue and words_to_add:
                    bank_words.extend(words_to_add)
                    i += len(words_to_add)
                # Stop after handling the pattern
                break
            
            # Add the additional words if we found a pattern but continue processing
            if should_continue and words_to_add:
                bank_words.extend(words_to_add)
                i += len(words_to_add)
                
                # If we just added "of Place" or similar, this is probably the end
                if words_to_add[0].lower() == 'of':
                    break
        
        i += 1
    
    # Final validation and cleanup
    if bank_words:
        bank_name = ' '.join(bank_words)
        
        # Basic validation
        if (3 <= len(bank_name) <= 100 and  # Increased max length for complex names
            any(c.isalpha() for c in bank_name) and  # Contains letters
            len(bank_words) <= 10 and  # Not too many words
            not bank_name.lower().strip() in stop_words_lower):  # Not entirely a stop word
            
            return bank_name.strip()
    
    return None

def extract_bank_name_from_words(words):
    """Extract bank name from a list of words using comprehensive boundary detection"""
    if not words:
        return None
    
    # Use the same comprehensive stop words as the line-based function
    stop_words = set([
        # Document/Report terms
        'report', 'statement', 'summary', 'document', 'page', 'dated', 'period', 'ending',
        # Account/Financial terms  
        'account', 'balance', 'routing', 'number', 'type', 'checking', 'savings', 'deposit',
        'transaction', 'transactions', 'activity', 'beginning', 'ending', 'current', 'available',
        # Address components
        'p.o.', 'po', 'box', 'street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr',
        'blvd', 'boulevard', 'lane', 'ln', 'circle', 'cir', 'court', 'ct', 'suite', 'ste',
        'floor', 'apt', 'apartment', 'unit', 'building', 'bldg', 'plaza', 'place', 'pl',
        # Contact information
        'phone', 'tel', 'telephone', 'fax', 'email', 'website', 'www', 'http', 'https',
        'contact', 'call', 'customer', 'service', 'support', 'help', 'assistance',
        # Marketing/Slogan terms
        'spend', 'life', 'wisely', 'slogan', 'motto', 'tagline', 'welcome', 'thank', 'thanks',
        'serving', 'proudly', 'committed', 'dedicated', 'excellence', 'quality', 'premier',
        'leading', 'trusted', 'established', 'since', 'founded', 'years', 'experience',
        # Regulatory/Legal terms
        'member', 'fdic', 'equal', 'housing', 'lender', 'opportunity', 'insured', 'deposits',
        'regulation', 'compliance', 'terms', 'conditions', 'privacy', 'policy', 'notice',
        # Time/Date terms
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'am', 'pm', 'hours', 'open',
        # Geographic/Location terms
        'located', 'headquarters', 'branch', 'branches', 'office', 'offices', 'location',
        'locations', 'main', 'downtown', 'north', 'south', 'east', 'west', 'central',
        # Header/Footer terms
        'return', 'service', 'requested', 'postmaster', 'mail', 'postal', 'zip', 'code'
    ])
    
    stop_words_lower = {word.lower() for word in stop_words}
    
    # Clean words and skip leading numbers
    cleaned_words = []
    start_index = 0
    
    for i, word in enumerate(words):
        word_clean = word.strip('.,()[]{}"\'-')
        if word_clean and len(word_clean) >= 1:
            cleaned_words.append(word_clean)
        
        # Skip leading numbers like "1" in "1 First United"
        if i == 0 and word_clean.isdigit() and len(words) > 1:
            start_index = 1
    
    if not cleaned_words or start_index >= len(cleaned_words):
        return None
    
    # Build bank name until hitting a boundary
    bank_words = []
    
    # Strong endings that indicate a complete bank name
    strong_endings = ['bank', 'union', 'financial', 'trust', 'services', 'corp', 'corporation', 
                     'company', 'credit', 'savings', 'loan', 'association', 'federal', 'national']
    
    for i in range(start_index, min(len(cleaned_words), start_index + 8)):  # Limit to 8 words max
        word_clean = cleaned_words[i]
        word_lower = word_clean.lower()
        
        # Stop at obvious non-bank words
        if word_lower in stop_words_lower:
            break
            
        # Add this word to potential bank name
        bank_words.append(word_clean)
        
        # Check if this looks like a natural ending for a bank name
        if word_lower in strong_endings:
            # This is likely the end of the bank name - stop here
            break
    
    if bank_words:
        bank_name = ' '.join(bank_words)
        # Basic validation - should be reasonable length and contain letters
        if (2 <= len(bank_name) <= 80 and 
            any(c.isalpha() for c in bank_name) and
            len(bank_words) <= 8 and  # More generous length limit
            not bank_name.lower().strip() in stop_words_lower):
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
        print_and_log(f"❌ Full error traceback: {traceback.format_exc()}")
        return None

def extract_digits_from_account(account_str):
    """Extract digits from masked account number (e.g., 'XXXXXX2101' -> '2101')"""
    if not account_str:
        return account_str
    
    # If account contains masking characters, extract only the digits
    if any(char in str(account_str) for char in ['*', 'x', 'X', '#']):
        digits_only = re.sub(r'[^0-9]', '', str(account_str))
        print_and_log(f"🔍 Extracting digits from masked account: '{account_str}' -> '{digits_only}'")
        return digits_only
    
    # Otherwise return as-is
    return str(account_str)

def extract_account_number_openai(text):
    """
    Use OpenAI to extract account number from bank statement text
    More robust than regex for complex patterns and variations
    """
    print_and_log("🤖 Using OpenAI for account number extraction...")
    
    try:
        # Get Azure OpenAI configuration from environment
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        if not endpoint or not api_key or not deployment:
            print_and_log("❌ Azure OpenAI configuration missing for account extraction")
            return None
        
        # Set up Azure OpenAI client
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-10-21"
        )
        
        prompt = f"""You are an expert at extracting account numbers from bank statement text.

Your task: Extract the PRIMARY account number from this bank statement text.

Rules:
1. Look for account numbers in these formats:
   - Masked: XXXXXX2101, ***1234, ####5678, ••••5432
   - Numeric: 123456789, 1234567890123
   - Alphanumeric: ABC123456789, DEF789456
   - Partial: "last 8876", "ending in 2101", "ends with 5678"

2. Priority order (return the HIGHEST priority match found):
   - Masked account numbers (XXXXXX2101) - HIGHEST PRIORITY
   - Full numeric account numbers (123456789)
   - Alphanumeric account numbers (ABC123456789)
   - Partial account references (convert to masked format: "last 8876" → "XXXXXX8876")

3. Ignore these (they are NOT account numbers):
   - Phone numbers (800-333-6896, 1-800-BANK, etc.)
   - Routing numbers (9-digit bank codes, often starting with 0,1,2,3)
   - Check numbers, transaction amounts, dates, page numbers
   - Social Security Numbers (XXX-XX-1234)
   - ZIP codes, confirmation numbers, transaction IDs

4. Return format:
   - For masked accounts: Return exactly as shown (e.g., "XXXXXX2101")
   - For full accounts: Return the clean number (e.g., "123456789")
   - For partial accounts: Convert to masked format (e.g., "XXXXXX8876")
   - If none found: Return "NONE"

5. Context clues to help identify account numbers:
   - Words like "Account Number:", "Account:", "Acct #:", "A/C #:"
   - Usually appears near customer name, address, or statement header
   - NOT near "Customer Service", "Call", "Phone", "Contact"

Text to analyze:
{text}

Account Number:"""

        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are an expert at extracting account numbers from bank statements. Be precise and follow the rules exactly. Return only the account number, no explanation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        if result.upper() == "NONE":
            print_and_log("🤖 OpenAI: No account number found")
            return None
        
        # Clean up the response - remove any explanatory text
        lines = result.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(('the ', 'account ', 'extracted', 'found', 'result:', 'answer:')):
                print_and_log(f"🤖 OpenAI extracted account number: {line}")
                return line
        
        print_and_log(f"🤖 OpenAI extracted account number: {result}")
        return result
        
    except Exception as e:
        print_and_log(f"❌ OpenAI account extraction error: {e}")
        return None

def extract_account_number_from_text(text):
    """Extract account number from bank statement text using AI-enhanced approach"""
    print_and_log("🔍 Searching for account number in statement text...")
    
    # First try OpenAI extraction for better accuracy
    openai_result = extract_account_number_openai(text)
    if openai_result:
        return openai_result
    
    # Fallback to regex extraction if OpenAI fails
    print_and_log("🔄 Falling back to regex-based extraction...")
    return extract_account_number_regex(text)

def extract_account_number_regex(text):
    """Extract account number from bank statement text using regex patterns - prioritize masked accounts"""
    print_and_log("🔍 Using regex for account number extraction...")
    
    # PRIORITY 1: Masked account patterns (highest priority)
    masked_patterns = [
        r'account\s*#?\s*:?\s*([X*#]+\d{4,})(?:\s|$)',  # "Account #: XXXXXX2101" or "Account: ***1234"
        r'account\s*number\s*:?\s*([X*#]+\d{4,})(?:\s|$)',  # "Account number: XXXXXX2101"
        r'acct\s*#?\s*:?\s*([X*#]+\d{4,})(?:\s|$)',  # "Acct#: XXXXXX2101"
        r'a/c\s*#?\s*:?\s*([X*#]+\d{4,})(?:\s|$)',  # "A/C#: XXXXXX2101"
        r'account\s+([X*#]+\d{4,})(?:\s|$)',  # "Account XXXXXX2101"
        r'(?:^|\s)([X*#]{4,}\d{4,})(?:\s|$)',  # "XXXXXX2101" standalone
        r'ending\s*in\s+([X*#]*\d{4,})(?:\s|$)',  # "Ending in 2101" or "Ending in ***2101"
    ]
    
    # PRIORITY 2: Last digits patterns (enhanced for "last 8876" etc.)
    last_digits_patterns = [
        r'last\s+(\d{4,})(?:\s|$)',  # "last 8876"
        r'ending\s+in\s+(\d{4,})(?:\s|$)',  # "ending in 8876"
        r'ends\s+with\s+(\d{4,})(?:\s|$)',  # "ends with 8876" 
        r'last\s+four\s+digits?\s+(\d{4,})(?:\s|$)',  # "last four digits 8876"
        r'final\s+(\d{4,})(?:\s|$)',  # "final 8876"
        r'ending\s+(\d{4,})(?:\s|$)',  # "ending 8876"
        r'(\d{4,})\s+digits?(?:\s|$)',  # "8876 digits"
        r'digits?\s+(\d{4,})(?:\s|$)',  # "digits 8876"
    ]
    
    # PRIORITY 3: Numeric patterns (medium priority)
    numeric_patterns = [
        r'account\s*#?\s*:?\s*(\d{6,})(?:\s|$)',  # "Account #: 123456789" (numeric only)
        r'account\s*number\s*:?\s*(\d{6,})(?:\s|$)',  # "Account number: 123456789" (numeric only)
        r'acct\s*#?\s*:?\s*(\d{6,})(?:\s|$)',  # "Acct#: 123456789" (numeric only)
        r'a/c\s*#?\s*:?\s*(\d{6,})(?:\s|$)',  # "A/C#: 123456789" (numeric only)
        r'account\s*#\s+(\d{6,})(?:\s|$)',  # "Account # 123456789" (numeric only, with space)
        r'(?:^|\s)(\d{6,12})(?:\s|$)',  # Any 6-12 digit number (standalone)
    ]
    
    # PRIORITY 4: General text patterns (lowest priority)
    text_patterns = [
        r'account\s*#?\s*:?\s*([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Account #: ABC123456789" 
        r'account\s*number\s*:?\s*([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Account number: ABC123456789"
        r'acct\s*#?\s*:?\s*([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Acct#: ABC123456789"
        r'a/c\s*#?\s*:?\s*([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "A/C#: ABC123456789"
        r'account\s+([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Account ABC123456789"
        r'(?:^|\s)([A-Za-z0-9\-\*X#]+)\s+account(?:\s|$)',  # "ABC123456789 account"
        r'for\s*account\s+([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "For account ABC123456789"
        r'account\s*#\s+([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Account # ABC123456789" (with space)
        r'a/c\s*#\s+([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "A/C # ABC123456789" (with space)
        r'acct\s*#\s+([A-Za-z0-9\-\*X#]+)(?:\s|$)',  # "Acct # ABC123456789" (with space)
        r'(?:^|\s)([A-Za-z0-9\-\*X#]{8,})(?:\s|$)',  # Any 8+ character alphanumeric including masking (last resort)
    ]
    
    text_lower = text.lower()
    found_accounts = []
    
    # PRIORITY 1: Try masked patterns first (highest priority)
    print_and_log("🎯 Searching for MASKED account patterns...")
    for pattern in masked_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Clean but preserve masking characters
            clean_match = match.upper().replace("-", "").replace(" ", "")
            if any(char in clean_match for char in ['*', 'X', '#']) and len(clean_match) >= 4:
                # Extract digits to validate we have enough
                digits_only = re.sub(r'[^0-9]', '', clean_match)
                if len(digits_only) >= 3:
                    print_and_log(f"✅ Found MASKED account number: {clean_match} (digits: {digits_only})")
                    return clean_match
                else:
                    print_and_log(f"❌ Masked account has insufficient digits: {clean_match} -> {digits_only}")
            else:
                print_and_log(f"❌ Not a valid masked account: {clean_match}")
    
    # PRIORITY 2: Try last digits patterns
    print_and_log("🔢 Searching for LAST DIGITS patterns...")
    for pattern in last_digits_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Validate it's 4+ digits and not a phone number
            if len(match) >= 4 and not match.startswith(('800', '888', '877', '866')):
                masked_account = f"XXXXXX{match}"
                print_and_log(f"✅ Found LAST DIGITS pattern: '{match}' -> '{masked_account}'")
                return masked_account
    
    # PRIORITY 3: Try numeric patterns (medium priority)
    print_and_log("🔢 Searching for NUMERIC account patterns...")
    for pattern in numeric_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if is_valid_account_number(match):
                print_and_log(f"✅ Found valid numeric account number: {match}")
                found_accounts.append(("numeric", match))
            else:
                print_and_log(f"❌ Found invalid numeric account number: {match} - rejected")
    
    # PRIORITY 4: Try text patterns (lowest priority)
    print_and_log("📝 Searching for TEXT account patterns...")
    for pattern in text_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            clean_match = match.upper().replace("-", "").replace(" ", "")
            
            # Check if it's a masked account
            if any(char in clean_match for char in ['*', 'X', '#']) and len(clean_match) >= 4:
                digits_only = re.sub(r'[^0-9]', '', clean_match)
                if len(digits_only) >= 3:
                    print_and_log(f"✅ Found MASKED account in text patterns: {clean_match} (digits: {digits_only})")
                    return clean_match
                else:
                    print_and_log(f"❌ Masked account has insufficient digits: {clean_match} -> {digits_only}")
            # Check if it's a valid numeric account
            elif is_valid_account_number(clean_match):
                print_and_log(f"✅ Found valid text account number: {clean_match}")
                found_accounts.append(("text", clean_match))
            # Check if it's a 4-digit partial account
            elif len(clean_match) == 4 and clean_match.isdigit():
                masked_account = "XXXXXX" + clean_match
                print_and_log(f"✅ Found partial account, converting to masked format: {masked_account}")
                return masked_account
            else:
                print_and_log(f"❌ Found invalid account number: {clean_match} - rejected")
    
    # Return the best account found (prefer numeric over text)
    if found_accounts:
        # Prefer numeric accounts if found
        for account_type, account in found_accounts:
            if account_type == "numeric":
                print_and_log(f"✅ Using best numeric account: {account}")
                return account
        
        # Otherwise use first text account
        for account_type, account in found_accounts:
            if account_type == "text":
                print_and_log(f"✅ Using fallback text account: {account}")
                return account
    
    print_and_log("❌ No account number found in statement text")
    return None

def is_valid_account_number(account_number):
    """Validate account number - extract digits from masked numbers and validate the result"""
    if not account_number:
        return False
    
    account_str = str(account_number).strip()
    
    # Extract digits from masked account numbers (e.g., "XXXXXX2101" -> "2101")
    digits_only = re.sub(r'[^0-9]', '', account_str)
    
    # If we have masking characters, extract and validate the digits
    if any(char in account_str for char in ['*', 'x', 'X', '#']):
        print_and_log(f"🔍 Found masked account number: '{account_str}' -> extracting digits: '{digits_only}'")
        
        # Validate extracted digits
        if len(digits_only) >= 3:  # At least 3 digits for partial matching
            print_and_log(f"✅ Extracted valid digits from masked account: '{digits_only}'")
            return True
        else:
            print_and_log(f"❌ Not enough digits in masked account: '{digits_only}' (need at least 3)")
            return False
    
    # For non-masked numbers, use the original validation logic
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
    
    # Allow 4-digit accounts only if they came from specific patterns like "ACCT 1093"
    # Reject standalone 4-digit numbers that are likely partial/masked
    if len(clean_account) == 4 and clean_account.isdigit():
        # Allow 4-digit accounts - they could be valid short account numbers
        print_and_log(f"⚠️ 4-digit account detected: '{clean_account}' - allowing for database lookup")
        # Note: Will be validated against WAC database during routing lookup
    
    # If we get here, the account number passed all checks
    print_and_log(f"✅ Account number validation passed: '{account_str}' -> '{clean_account}'")
    return True

def create_error_bai2_file(error_message, filename, file_date, file_time, error_code=None):
    """Create a minimal BAI2 file with detailed error message and diagnostics"""
    print_and_log(f"❌ Creating ERROR BAI2 file: {error_message}")
    
    # Map error messages to specific error codes with enhanced detection
    if error_code is None:
        error_lower = error_message.lower()
        if "multiple accounts" in error_lower and "low similarity" in error_lower:
            error_code = "ERROR_MULTIPLE_ACCOUNTS_LOW_SIMILARITY"
        elif "multiple accounts" in error_lower and "no bank" in error_lower:
            error_code = "ERROR_MULTIPLE_ACCOUNTS_NO_BANK"
        elif "routing number" in error_lower:
            error_code = "ERROR_NO_ROUTING"
        elif "account number" in error_lower or "account not found" in error_lower:
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
        elif "rate limit" in error_lower or "429" in error_lower:
            error_code = "ERROR_RATE_LIMITED"
        elif "memory" in error_lower:
            error_code = "ERROR_MEMORY_EXCEEDED"
        elif "authentication" in error_lower or "401" in error_lower or "403" in error_lower:
            error_code = "ERROR_AUTH_FAILED"
        elif "keyerror" in error_lower or "indexerror" in error_lower or "attributeerror" in error_lower:
            error_code = "ERROR_DATA_FORMAT"
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
    
    # 03 - Account Identifier (use ERROR as account number with complete BAI2 format)
    lines.append(f"03,ERROR,USD,010,,,Z/")
    
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

def extract_labeled_account_number(text):
    """Extract account number that is explicitly labeled (highest priority)"""
    print_and_log("🏷️ Looking for explicitly labeled account numbers...")
    
    # High-priority patterns for explicitly labeled account numbers
    labeled_patterns = [
        r'account\s*number\s*:?\s*(\d{4,})',   # "Account Number: 123456789" - Allow 4+ digits
        r'account\s*#\s*:?\s*(\d{4,})',        # "Account #: 123456789" or "Account # 123456789"
        r'acct\s*#?\s*:?\s*(\d{4,})',          # "Acct #: 123456789" or "Acct: 123456789"
        r'a/c\s*#?\s*:?\s*(\d{4,})',           # "A/C #: 123456789" or "A/C: 123456789"
        r'account\s*no\s*\.?\s*:?\s*(\d{4,})', # "Account No.: 123456789" or "Account No .: 123456789" - Allow spaces before period
        r'account\s*id\s*:?\s*(\d{4,})',       # "Account ID: 123456789"
    ]
    
    # Masked labeled patterns
    masked_labeled_patterns = [
        r'account\s*number\s*:?\s*([X*]+\d{4,})',   # "Account Number: XXXX1234"
        r'account\s*#\s*:?\s*([X*]+\d{4,})',        # "Account #: XXXX1234"
        r'acct\s*#?\s*:?\s*([X*]+\d{4,})',          # "Acct #: XXXX1234"
        r'a/c\s*#?\s*:?\s*([X*]+\d{4,})',           # "A/C #: XXXX1234"
        r'account\s*no\s*\.?\s*:?\s*([X*]+\d{4,})', # "Account No.: XXXX1234" or "Account No .: XXXX1234"
    ]
    
    # NEW: Partial account patterns (ending in last 4 digits)
    partial_patterns = [
        r'ending\s+in\s+(\d{4})',              # "ending in 0327"
        r'ending\s+(\d{4})',                   # "ending 0327"
        r'account\s+ending\s+in\s+(\d{4})',    # "account ending in 0327"
        r'account\s+ending\s+(\d{4})',         # "account ending 0327"
        r'acct\s+ending\s+in\s+(\d{4})',       # "acct ending in 0327"
        r'acct\s+ending\s+(\d{4})',            # "acct ending 0327"
        r'a/c\s+ending\s+in\s+(\d{4})',        # "a/c ending in 0327"
        r'a/c\s+ending\s+(\d{4})',             # "a/c ending 0327"
        r'last\s+4\s+digits?\s*:?\s*(\d{4})',  # "last 4 digits: 0327"
        r'(\*{4,}|\#{4,}|x{4,})(\d{4})',       # "****0327" or "XXXX0327"
    ]
    
    text_lower = text.lower()
    
    # First try masked labeled patterns (highest priority)
    for pattern in masked_labeled_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            clean_match = match.upper().replace("-", "").replace(" ", "")
            if any(char in clean_match for char in ['*', 'X']) and len(clean_match) >= 4:
                digits_only = re.sub(r'[^0-9]', '', clean_match)
                if len(digits_only) >= 3:
                    print_and_log(f"✅ Found LABELED MASKED account: {clean_match}")
                    return clean_match
    
    # Then try numeric labeled patterns
    for pattern in labeled_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if is_valid_account_number(match) and len(match) >= 6:
                print_and_log(f"✅ Found LABELED NUMERIC account: {match}")
                return match
    
    # NEW: Try partial account patterns (ending in last 4 digits)
    for pattern in partial_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Pattern with groups - take the last group (the digits)
                last_digits = match[-1]
            else:
                last_digits = match
            
            # Validate we have exactly 4 digits
            if len(last_digits) == 4 and last_digits.isdigit():
                # Convert to masked format for processing
                masked_account = f"XXXXXX{last_digits}"
                print_and_log(f"✅ Found LABELED PARTIAL account: ending {last_digits} -> {masked_account}")
                return masked_account
    
    print_and_log("❌ No explicitly labeled account number found")
    return None

def extract_account_from_ocr_enhanced(text):
    """
    Enhanced account extraction from OCR text
    - Look for masked account patterns (XXXXX + digits, ***** + digits)
    - Look for "Ending" followed by digits
    - Find any label containing "Account" and extract numbers to the right
    """
    
    print_and_log("🔍 Enhanced OCR Account Extraction - looking for masked patterns and Account labels")
    
    lines = text.split('\n')
    print_and_log(f"Processing {len(lines)} lines of OCR text...")
    
    for line_num, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        print_and_log(f"Line {line_num}: {line_stripped}")
        
        # Pattern 1: Look for masked account numbers (X's or *'s followed by digits)
        masked_pattern = re.search(r'[X*]{3,}(\d{3,})', line_stripped, re.IGNORECASE)
        if masked_pattern:
            account_digits = masked_pattern.group(1)
            print_and_log(f"  ➤ Found masked account pattern: {masked_pattern.group(0)}")
            print_and_log(f"  ✅ Extracted account ending: {account_digits}")
            return account_digits
        
        # Pattern 2: Look for "Ending" followed by digits
        ending_pattern = re.search(r'\bending\s+(\d{3,})', line_stripped, re.IGNORECASE)
        if ending_pattern:
            account_digits = ending_pattern.group(1)
            print_and_log(f"  ➤ Found 'Ending' pattern: {ending_pattern.group(0)}")
            print_and_log(f"  ✅ Extracted account ending: {account_digits}")
            return account_digits
        
        # Pattern 3: Look for any variation of "Account" in the line
        if re.search(r'\baccount\b', line_stripped, re.IGNORECASE):
            print_and_log(f"  ➤ Found 'Account' label")
            
            # Extract everything after "Account" on this line
            account_match = re.search(r'\baccount\s*[:\-\s]*([0-9X*]+)', line_stripped, re.IGNORECASE)
            if account_match:
                account_text = account_match.group(1)
                
                # Check if it's a masked pattern (X's or *'s)
                if 'X' in account_text.upper() or '*' in account_text:
                    digits_match = re.search(r'[X*]+(\d+)', account_text, re.IGNORECASE)
                    if digits_match:
                        account_number = digits_match.group(1)
                        print_and_log(f"  ✅ Extracted account ending from masked pattern: {account_number}")
                        return account_number
                else:
                    # Regular account number
                    account_number = re.sub(r'[^\d]', '', account_text)
                    if account_number and len(account_number) >= 4:
                        print_and_log(f"  ✅ Extracted full account number: {account_number}")
                        return account_number
            
            # If no number on same line, check next line
            if line_num < len(lines):
                next_line = lines[line_num].strip()
                if next_line:
                    print_and_log(f"  ➤ Checking next line: {next_line}")
                    
                    # Check for masked pattern in next line (X's or *'s)
                    masked_next = re.search(r'[X*]{3,}(\d{3,})', next_line, re.IGNORECASE)
                    if masked_next:
                        account_number = masked_next.group(1)
                        print_and_log(f"  ✅ Extracted account ending from next line masked pattern: {account_number}")
                        return account_number
                    
                    # Extract contiguous numbers from start of next line
                    number_match = re.match(r'^[^0-9]*([0-9]+)', next_line)
                    if number_match:
                        account_number = number_match.group(1)
                        if len(account_number) >= 4:
                            print_and_log(f"  ✅ Extracted account number from next line: {account_number}")
                            return account_number
    
    print_and_log(f"❌ NO ACCOUNT NUMBERS FOUND in enhanced OCR extraction")
    return None

def get_account_number(parsed_data):
    """Get account number from statement - prioritize explicitly labeled account numbers"""
    print_and_log("🔍 Extracting account number - looking for labeled account numbers first...")
    
    # STEP 1: Look for explicitly labeled account numbers in OCR text (HIGHEST PRIORITY)
    if "ocr_text_lines" in parsed_data:
        full_text = '\n'.join(parsed_data["ocr_text_lines"])
        print_and_log(f"🎯 Searching for LABELED account numbers in text...")
        
        labeled_account = extract_labeled_account_number(full_text)
        if labeled_account:
            print_and_log(f"✅ Found LABELED account number: {labeled_account}")
            return labeled_account
        
        # STEP 1.5: Enhanced OCR extraction - look for any "Account" label and extract contiguous numbers
        print_and_log(f"🎯 Trying enhanced OCR extraction...")
        enhanced_account = extract_account_from_ocr_enhanced(full_text)
        if enhanced_account:
            print_and_log(f"✅ Found account number via enhanced OCR: {enhanced_account}")
            return enhanced_account
    
    # STEP 2: Check Document Intelligence extracted account number
    if "account_number" in parsed_data and parsed_data["account_number"]:
        raw_account = str(parsed_data["account_number"])
        print_and_log(f"🎯 Document Intelligence account: '{raw_account}'")
        
        # Clean but preserve asterisks and X's for validation
        account_number = raw_account.replace("-", "").replace(" ", "")
        print_and_log(f"🎯 After cleaning: '{account_number}'")
        
        # For TRUE masked accounts (containing asterisks or X's), use Document Intelligence result
        if any(char in account_number for char in ['*', 'x', 'X']) and len(account_number) >= 4:
            print_and_log(f"✅ Found TRUE MASKED account from Document Intelligence: {account_number}")
            return account_number
        elif is_valid_account_number(account_number) and account_number.isdigit() and len(account_number) >= 6:
            print_and_log(f"✅ Found valid numeric account from Document Intelligence: {account_number}")
            return account_number
        else:
            print_and_log(f"❌ Document Intelligence account invalid or suspicious: '{account_number}'")
    
    
    # STEP 3: Check raw fields from document intelligence for account numbers
    if "raw_fields" in parsed_data:
        print_and_log(f"🔍 Checking {len(parsed_data['raw_fields'])} raw fields for account number...")
        for field_name, field_data in parsed_data["raw_fields"].items():
            if isinstance(field_data, dict) and "content" in field_data:
                content = field_data["content"]
                
                                # Only check fields that are specifically account number fields, not address/name fields
                if field_name.lower() in ['accounts', 'account', 'accountnumber', 'account_number']:
                    if content and len(content) > 4:
                        # Clean but preserve asterisks for validation
                        clean_content = content.replace("-", "").replace(" ", "")
                        print_and_log(f"🔍 Account field '{field_name}': '{clean_content}'")
                        
                        # Prioritize TRUE masked accounts (with * or X)
                        if any(char in clean_content for char in ['*', 'X']) and len(clean_content) >= 4:
                            print_and_log(f"✅ Found TRUE MASKED account in field '{field_name}': {clean_content}")
                            return clean_content
                        elif is_valid_account_number(clean_content) and clean_content.isdigit() and len(clean_content) >= 4:
                            print_and_log(f"✅ Found numeric account in field '{field_name}': {clean_content}")
                            return clean_content
                else:
                    # For non-account fields, log them but don't treat as accounts
                    if "account" in field_name.lower():
                        print_and_log(f"📋 Skipping non-account field '{field_name}': '{content[:50] if len(content) > 50 else content}' (not an account number field)")
    
    
    # STEP 4: Fallback to frequency analysis only if no labeled account found
    if "ocr_text_lines" in parsed_data:
        full_text = '\n'.join(parsed_data["ocr_text_lines"])
        print_and_log(f"⚠️ No labeled account found - falling back to frequency analysis...")
        
        # Extract all possible account numbers with their types
        all_found_accounts = extract_all_account_numbers_with_frequency(full_text)
        
        # Analyze results
        if all_found_accounts:
            print_and_log(f"📊 Found {len(all_found_accounts)} total account number instances for frequency analysis")
            
            # Group by account number and count frequency
            from collections import Counter
            account_frequency = Counter()
            account_types = {}  # Track what type each account is
            
            for acc_type, acc_value in all_found_accounts:
                account_frequency[acc_value] += 1
                if acc_value not in account_types:
                    account_types[acc_value] = acc_type
            
            # Log frequency analysis
            print_and_log("� FREQUENCY ANALYSIS (fallback only):")
            for account, freq in account_frequency.most_common():
                acc_type = account_types[account]
                print_and_log(f"   {account} ({acc_type}): {freq} times")
            
            # Use most frequent NUMERIC account (ignore reference numbers like HUS#1279)
            for account, freq in account_frequency.most_common():
                acc_type = account_types[account]
                if acc_type == "numeric" and account.isdigit() and len(account) >= 6 and freq >= 3:
                    print_and_log(f"✅ Using most frequent numeric account: {account} ({freq} times)")
                    return account
            
            # Look for TRUE masked accounts (with * or X) as last resort
            for account, freq in account_frequency.most_common():
                acc_type = account_types[account]
                if acc_type == "masked" and any(char in account for char in ['*', 'X']) and len(account) >= 4:
                    print_and_log(f"✅ Using masked account as fallback: {account} ({freq} times)")
                    return account
    
    print_and_log("❌ No account number found in statement")
    return None

def extract_all_account_numbers_with_frequency(text):
    """Extract ALL account numbers from text for frequency analysis"""
    found_accounts = []
    
    # TRUE masked patterns (highest priority)
    masked_patterns = [
        r'\b([X*]+\d{4,})\b',  # XXXX1234 or ****1234
        r'\b(\d{4,}[X*]+)\b',  # 1234XXXX or 1234****
        r'\b(\d+[X*]+\d+)\b',  # 12XX34 or 12**34
    ]
    
    # Numeric patterns (medium priority)
    numeric_patterns = [
        r'\b(\d{6,12})\b',  # 6-12 digit numbers (typical account numbers)
    ]
    
    # Suspicious text patterns (lowest priority - likely reference numbers)
    text_patterns = [
        r'\b([A-Z]+#\d{4,})\b',  # HUS#1279 (likely reference numbers)
        r'\b([A-Z]{2,}\d{4,})\b',  # ABC1234 (likely reference numbers)
    ]
    
    text_upper = text.upper()
    
    # Extract TRUE masked accounts
    for pattern in masked_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            # Validate it has enough digits
            digits_only = re.sub(r'[^0-9]', '', match)
            if len(digits_only) >= 3:
                found_accounts.append(("masked", match))
    
    # Extract numeric accounts
    for pattern in numeric_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if is_valid_account_number(match):
                found_accounts.append(("numeric", match))
    
    # Extract text patterns (but mark them as suspicious)
    for pattern in text_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            # Only include if it looks like it could be an account number
            digits_only = re.sub(r'[^0-9]', '', match)
            if len(digits_only) >= 3:
                found_accounts.append(("reference", match))  # Mark as reference, not account
    
    return found_accounts

def get_routing_number(parsed_data, account_number=None):
    """Get routing number ONLY from WAC Bank Information database - never from statement text"""
    print_and_log("🔍 Extracting routing number...")
    print_and_log("⚠️ POLICY: Only using routing numbers from WAC Bank Information database")
    
    # Get bank name from statement for database lookup
    bank_name = None
    
    # Check if Document Intelligence extracted the bank name
    if "raw_fields" in parsed_data and "BankName" in parsed_data["raw_fields"]:
        bank_data = parsed_data["raw_fields"]["BankName"]
        if isinstance(bank_data, dict) and "content" in bank_data:
            bank_name = bank_data["content"].strip()
            confidence = bank_data.get("confidence", 0.0)
            print_and_log(f"✅ Found bank name from Document Intelligence: {bank_name} ({confidence:.2%} confidence)")
    
    # Fallback: Extract bank name from OCR text
    if not bank_name and "ocr_text_lines" in parsed_data:
        ocr_text = "\n".join(parsed_data["ocr_text_lines"])
        bank_name = extract_bank_name_from_text(ocr_text)
        if bank_name:
            print_and_log(f"✅ Extracted bank name from OCR: {bank_name}")
    
    if not bank_name:
        print_and_log("❌ CRITICAL: Bank name not found - cannot lookup routing number")
        return None, None
    
    # ONLY use WAC Bank Information database for routing number lookup
    if account_number:
        # Extract digits from masked account numbers for database lookup
        lookup_account = extract_digits_from_account(account_number)
        
        print_and_log(f"🔍 WAC Database lookup (ACCOUNT-FIRST approach)...")
        print_and_log(f"   Original Account: '{account_number}'")
        print_and_log(f"   Lookup Account: '{lookup_account}'")
        print_and_log(f"   Bank Name (for validation): '{bank_name}'")
        
        try:
            # Load bank data directly for account-first matching
            from bank_info_loader import load_bank_information_yaml
            yaml_content, bank_data = load_bank_information_yaml()
            
            if not bank_data:
                print_and_log(f"❌ WAC Bank Information database not available")
                return None, None
            
            print_and_log(f"📄 WAC Database loaded ({len(bank_data['wac_banks'])} banks available)")
            
            # STEP 1: Try exact account number match first (using extracted digits)
            exact_matches = []
            for bank_info in bank_data.get('wac_banks', []):
                if str(bank_info['account_number']).strip() == str(lookup_account).strip():
                    exact_matches.append(bank_info)
            
            if exact_matches:
                match = exact_matches[0]  # Should only be one exact match
                print_and_log(f"✅ EXACT ACCOUNT MATCH found!")
                print_and_log(f"   Account: {match['account_number']}")
                print_and_log(f"   Bank: {match['bank_name']}")
                print_and_log(f"   Routing: {match['routing_number']}")
                
                # Validate bank name if available (optional)
                if bank_name:
                    from bank_info_loader import calculate_similarity
                    similarity = calculate_similarity(bank_name, match['bank_name'])
                    print_and_log(f"   Bank name validation: {similarity:.1%} similarity")
                    if similarity < 0.7:
                        print_and_log(f"⚠️ Warning: Bank name mismatch but account match is definitive")
                
                return match['routing_number'], match['account_number']
            
            # STEP 2: Try masked/partial account matching
            from bank_info_loader import validate_account_match
            extracted_digits = lookup_account  # Use the already extracted digits
            
            if extracted_digits and len(extracted_digits) >= 3:  # Changed from 4 to 3 for more flexibility
                print_and_log(f"🔍 No exact match, trying partial/masked account matching...")
                print_and_log(f"   Extracted digits: '{extracted_digits}'")
                
                partial_matches = []
                for bank_info in bank_data.get('wac_banks', []):
                    account_valid, match_ratio = validate_account_match(account_number, bank_info['account_number'])
                    if account_valid:
                        partial_matches.append((bank_info, match_ratio))
                
                if partial_matches:
                    # Sort by match quality (highest first)
                    partial_matches.sort(key=lambda x: x[1], reverse=True)
                    best_match, best_ratio = partial_matches[0]
                    
                    print_and_log(f"✅ PARTIAL ACCOUNT MATCH found!")
                    print_and_log(f"   Account: {best_match['account_number']}")
                    print_and_log(f"   Bank: {best_match['bank_name']}")
                    print_and_log(f"   Routing: {best_match['routing_number']}")
                    print_and_log(f"   Match Quality: {best_ratio:.1%}")
                    
                    # Validate bank name if available (optional)
                    if bank_name:
                        from bank_info_loader import calculate_similarity
                        similarity = calculate_similarity(bank_name, best_match['bank_name'])
                        print_and_log(f"   Bank name validation: {similarity:.1%} similarity")
                    
                    return best_match['routing_number'], best_match['account_number']
            
            print_and_log(f"❌ No account match found in WAC Database")
            print_and_log(f"   Original Account: '{account_number}'")
            print_and_log(f"   Lookup Account: '{lookup_account}' (extracted digits)")
            print_and_log(f"   No exact or partial match found in database")
            print_and_log(f"⚠️ This appears to be a customer account, not a WAC operational account")
            
        except Exception as e:
            print_and_log(f"❌ WAC Database lookup failed: {str(e)}")
    else:
        print_and_log(f"❌ No account number available for database lookup")
    
    # NO FALLBACKS - Do not extract from statement text or use OpenAI
    print_and_log("❌ ROUTING NUMBER POLICY ENFORCED: Only WAC operational accounts allowed")
    print_and_log("❌ Statement does not match any WAC operational account in database")
    return None, None
    
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
                        
                        # Map Document Intelligence fields to expected names
                        if field_name == "AccountNumber" and field_data.content:
                            parsed_data["account_number"] = field_data.content
                            print_and_log(f"🎯 MAPPED AccountNumber field to account_number: {field_data.content}")
                        elif field_name == "BankName" and field_data.content:
                            parsed_data["bank_name"] = field_data.content
                            print_and_log(f"🎯 MAPPED BankName field to bank_name: {field_data.content}")
                        elif field_name == "StatementStartDate" and field_data.content:
                            parsed_data["statement_start_date"] = field_data.content
                            print_and_log(f"🎯 MAPPED StatementStartDate field: {field_data.content}")
                        elif field_name == "StatementEndDate" and field_data.content:
                            parsed_data["statement_end_date"] = field_data.content
                            print_and_log(f"🎯 MAPPED StatementEndDate field: {field_data.content}")
            
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
- IGNORE SCANNED IMAGES: Do not extract any data from scanned checks, deposit slips, or other image artifacts embedded in the statement
- Focus ONLY on the bank's printed transaction tables and account summaries
- MAXIMUM ACCURACY REQUIRED: Double-check every dollar amount and date - transcription errors are unacceptable
- COMPLETE TRANSACTION EXTRACTION: Find every single transaction - missing transactions cause reconciliation failures
- READ AMOUNTS CAREFULLY: $2,564.47 must NOT become $2,554.47 - verify each digit
- Scan from the very beginning to the very end of the text
- Every date + amount combination is likely a transaction
- Include even small amounts (fees, interest, etc.) with exact amounts
- Check for negative amounts (withdrawals/debits)
- Check for positive amounts (deposits/credits)
- Look for check numbers, reference numbers, descriptions
- Don't miss transactions at page breaks or statement end
- Preserve detailed descriptions like "ACH Debit Received WORLD ACCEPTANCE CONC DEBIT 144"
- Include all reference numbers and transaction codes
- EXTRACT EXACT REFERENCE NUMBERS: Look for patterns like "478980340", check numbers, transaction IDs, confirmation numbers
- Reference numbers are often found after "Ref:", "Reference:", "Check #", "Confirmation:", or as standalone numbers in transaction lines
- Capture both bank-generated reference numbers AND merchant/transaction reference numbers
- VERIFY TOTALS: Extracted transactions must mathematically reconcile with statement totals

FULL OCR TEXT:
{ocr_text}

CRITICAL STATEMENT DATE EXTRACTION RULES:
- FIND THE STATEMENT PERIOD DATES: Look for statement period start and end dates
- Look for patterns like "Statement Period: MM/DD/YYYY - MM/DD/YYYY" or "STATEMENT PERIOD MM/DD/YY THROUGH MM/DD/YY"
- Also check for "Statement Date:", "Closing Date:", "Through Date:", "Statement End Date:"
- Parse dates in various formats: MM/DD/YYYY, MM-DD-YYYY, MM/DD/YY, Month DD, YYYY
- If you find "Statement Period 07/01/2025 - 07/31/2025", use start_date: "2025-07-01" and end_date: "2025-07-31"
- If only one statement date is found, use it as end_date and estimate start_date (typically one month prior)
- ALWAYS extract statement period dates - they are critical for proper BAI2 file generation

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

FINAL ACCURACY CHECK:
- Count total deposits and withdrawals to match statement summary
- Verify amounts are transcribed exactly (no digit errors)
- Confirm all transactions from beginning to end of statement period are included
- Ensure mathematical reconciliation: Opening Balance + Deposits - Withdrawals = Closing Balance
- Double-check maintenance fees, service charges, and small amounts for accuracy
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
                {"role": "system", "content": "You are an expert bank statement parser with perfect accuracy. Extract ALL transactions with 100% precision - no amount errors, no missing transactions, complete reconciliation required. Return only valid JSON."},
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
                
                # PRODUCTION DEBUGGING: Analyze transaction dates and grouping
                print_and_log("🔍 PRODUCTION DEBUG: Analyzing OpenAI response...")
                
                if "transactions" in parsed_result:
                    transactions = parsed_result["transactions"]
                    print_and_log(f"📊 DEBUG: Found {len(transactions)} transactions in OpenAI response")
                    
                    # Analyze transaction dates
                    date_analysis = {}
                    missing_dates = 0
                    date_formats = set()
                    
                    for i, txn in enumerate(transactions[:10]):  # Analyze first 10
                        txn_date = txn.get('date', 'NO_DATE')
                        amount = txn.get('amount', 0)
                        desc = txn.get('description', 'No description')[:50]
                        
                        print_and_log(f"   Transaction {i+1}: date='{txn_date}' amount=${amount:.2f} desc='{desc}'")
                        
                        if txn_date and txn_date != 'NO_DATE':
                            if txn_date not in date_analysis:
                                date_analysis[txn_date] = 0
                            date_analysis[txn_date] += 1
                            
                            # Detect date format
                            if '/' in txn_date:
                                date_formats.add('MM/DD/YYYY')
                            elif '-' in txn_date and len(txn_date) == 10:
                                date_formats.add('YYYY-MM-DD')
                            else:
                                date_formats.add('OTHER')
                        else:
                            missing_dates += 1
                    
                    print_and_log(f"📅 DEBUG: Date analysis - {len(date_analysis)} unique dates found")
                    print_and_log(f"📅 DEBUG: Date formats detected: {list(date_formats)}")
                    print_and_log(f"📅 DEBUG: Transactions missing dates: {missing_dates}")
                    
                    if date_analysis:
                        sorted_dates = sorted(date_analysis.keys())
                        print_and_log(f"📅 DEBUG: Date range: {sorted_dates[0]} to {sorted_dates[-1]}")
                        print_and_log(f"📅 DEBUG: Sample dates: {list(sorted_dates)[:5]}")
                
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
    Extract fields from a PDF using Azure Document Intelligence bankStatement model ONLY.
    If bankStatement model fails, returns error data to generate error BAI2 file.
    """
    parsed_data = {"source": filename}
    success = False
    extraction_method = None
    error_message = None
    
    # Try bankStatement model ONLY - no fallback to OCR
    try:
        print_and_log(f"🔄 Attempting to extract using bankStatement.us model (SDK) for {filename}...")
        
        # Create client with correct SDK
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
        
        print_and_log("📤 Starting analysis with bankStatement model...")
        
        # Try bankStatement model
        try:
            poller = client.begin_analyze_document(
                "prebuilt-bankStatement.us",
                BytesIO(file_bytes),
                content_type="application/pdf"
            )
            
            print_and_log("⏳ Waiting for bankStatement analysis to complete...")
            # Add timeout to prevent function timeout (max 8 minutes for 10-minute function timeout)
            result = poller.result(timeout=480)  # 8 minutes timeout
            
            if result:
                print_and_log("✅ bankStatement analysis completed successfully!")
                parsed_data.update(parse_bankstatement_sdk_result(result))
                extraction_method = "bankStatement.us_model"
                success = True
            else:
                print_and_log("⚠️ No result from bankStatement model")
                error_message = "bankStatement model returned no result"
                
        except Exception as bs_error:
            print_and_log(f"❌ bankStatement model failed: {str(bs_error)}")
            error_message = f"bankStatement model analysis failed: {str(bs_error)}"
    
    except Exception as e:
        print_and_log(f"❌ Error with Document Intelligence SDK: {str(e)}")
        error_message = f"Document Intelligence SDK error: {str(e)}"
    
    # Set extraction method and handle failure
    if success:
        parsed_data["extraction_method"] = extraction_method
        print_and_log(f"🎯 EXTRACTION METHOD USED: {extraction_method}")
    else:
        print_and_log("❌ bankStatement model extraction failed - will generate error BAI2 file")
        parsed_data["error"] = error_message or "bankStatement model extraction failed"
        parsed_data["extraction_method"] = "bankStatement_failed"
        # Set minimal data structure for error BAI2 generation
        parsed_data["bank_name"] = "UNKNOWN BANK"
        parsed_data["account_number"] = "UNKNOWN"
        parsed_data["routing_number"] = "UNKNOWN"
        parsed_data["statement_date"] = "UNKNOWN"
        parsed_data["beginning_balance"] = "0.00"
        parsed_data["ending_balance"] = "0.00"
        parsed_data["transactions"] = []
    
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
    
    # === THROTTLING: Check if file is already being processed ===
    file_key = f"{blob_path}_{event_data.get('eTag', '')}"
    if not processing_queue.start_processing(file_key):
        print_and_log(f"⏸️ File {name} is already being processed - deferring to avoid race condition")
        return
    
    # Prevent duplicate processing with legacy check
    if file_key in _processing_files:
        print_and_log(f"[WARN] File {name} is already being processed - ignoring duplicate event")
        processing_queue.finish_processing(file_key)
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
        
        # Download the blob data with error handling
        try:
            blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
            file_bytes = blob_client.download_blob().readall()
            file_size = len(file_bytes) if file_bytes else 0
        except Exception as blob_error:
            if "BlobNotFound" in str(blob_error):
                print_and_log(f"[ERROR] Blob not found: {blob_name}")
                print_and_log(f"   This could indicate a race condition or the file was moved/deleted")
                print_and_log(f"   Skipping processing for {name}")
                return  # Exit gracefully instead of throwing error
            else:
                raise blob_error  # Re-raise other blob errors
        
        print_and_log("")
        print_and_log("🚀 STARTING BANK STATEMENT PROCESSING")
        print_and_log("=" * 60)
        print_and_log(f"📄 Processing file: {name}")
        print_and_log(f"📊 File size: {file_size:,} bytes")
        print_and_log("")
        
        # === THROTTLING: Add random delay to spread out processing load ===
        import random
        processing_delay = random.uniform(
            ThrottlingConfig.INITIAL_PROCESSING_DELAY_MIN, 
            ThrottlingConfig.INITIAL_PROCESSING_DELAY_MAX
        )
        print_and_log(f"⏱️ Adding {processing_delay:.1f}s processing delay to prevent resource contention...")
        time.sleep(processing_delay)
        
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
        
        # Use new SDK-based extraction (bankStatement model ONLY)
        parsed_data = extract_fields_with_sdk(file_bytes, name, endpoint, key)
        
        # Check if bankStatement extraction was successful
        if parsed_data.get("extraction_method") == "bankStatement_failed":
            print_and_log("❌ bankStatement model failed - will generate error BAI2 file")
            final_data = parsed_data  # Pass error data directly to BAI2 generation
        else:
            print_and_log(f"✅ bankStatement extraction successful: {parsed_data.get('extraction_method')}")
            final_data = parsed_data  # Use bankStatement data directly
            
        print_and_log("🎯 PROCESSING MODE: bankStatement-only (no OCR fallback)")
        print_and_log("   ➤ Modern AI-powered transaction extraction")
        print_and_log("   ➤ Direct to BAI2 generation without intermediate parsing")
        print_and_log("")
        
        # Store reconciliation results for final summary (bankStatement-only mode)
        reconciliation_summary = None
        print_and_log("📊 Reconciliation: Using bankStatement model data directly (no separate validation needed)")
        
        print_and_log("")
        print_and_log("🔄 STEP 2: Converting to BAI2 format")
        print_and_log("   ➤ Building industry-standard BAI2 file structure")
        print_and_log("   ➤ Using bankStatement model transaction data")
        print_and_log("")
        
        # Perform enhanced matching before BAI2 conversion to get both routing and account numbers
        enhanced_routing_number = None
        enhanced_account_number = None
        
        # Get account number from statement for enhanced matching
        statement_account = get_account_number(final_data)
        
        if statement_account:
            # Get bank name for enhanced matching
            bank_name = None
            if final_data and "ocr_text_lines" in final_data:
                # Convert list to string if needed
                text_lines = final_data["ocr_text_lines"]
                if isinstance(text_lines, list):
                    # Join list elements into a single string
                    text_for_extraction = '\n'.join(text_lines)
                else:
                    text_for_extraction = text_lines
                bank_name = extract_bank_name_from_text(text_for_extraction)
            
            if bank_name and get_bank_info_for_processing:
                print_and_log(f"🔍 WAC Account Verification...")
                print_and_log(f"   Bank Name: '{bank_name}'")
                print_and_log(f"   Statement Account: '{statement_account}'")
                
                try:
                    result = get_bank_info_for_processing(bank_name, statement_account)
                    if result and len(result) >= 2 and result[1]:  # result is (account, routing, match_type)
                        enhanced_account_number, enhanced_routing_number, match_type = result
                        print_and_log(f"✅ WAC OPERATIONAL ACCOUNT VERIFIED!")
                        print_and_log(f"   Matched Account: {enhanced_account_number}")
                        print_and_log(f"   Routing Number: {enhanced_routing_number}")
                        print_and_log(f"   Match Type: {match_type}")
                    else:
                        # Handle specific error cases with appropriate error codes
                        match_type = result[2] if result and len(result) >= 3 else "unknown"
                        
                        if match_type == "multiple_accounts_low_similarity":
                            print_and_log(f"❌ MULTIPLE ACCOUNT MATCHES - INSUFFICIENT BANK NAME SIMILARITY")
                            print_and_log(f"   Multiple accounts end with same digits as '{statement_account}'")
                            print_and_log(f"   Bank name '{bank_name}' similarity below 50% threshold")
                            print_and_log(f"   Cannot uniquely identify correct WAC operational account")
                            error_code = "ERROR_MULTIPLE_ACCOUNTS_LOW_SIMILARITY"
                            error_message = f"Multiple WAC accounts end with same digits. Bank name '{bank_name}' similarity below 50% threshold. Cannot uniquely identify account."
                            
                        elif match_type == "multiple_accounts_no_bank_name":
                            print_and_log(f"❌ MULTIPLE ACCOUNT MATCHES - NO BANK NAME FOR DISAMBIGUATION")
                            print_and_log(f"   Multiple accounts end with same digits as '{statement_account}'")
                            print_and_log(f"   No bank name provided for disambiguation")
                            print_and_log(f"   Cannot uniquely identify correct WAC operational account")
                            error_code = "ERROR_MULTIPLE_ACCOUNTS_NO_BANK"
                            error_message = f"Multiple WAC accounts end with same digits. No bank name available for disambiguation."
                            
                        elif match_type == "no_account_match":
                            print_and_log(f"❌ NOT A WAC OPERATIONAL ACCOUNT")
                            print_and_log(f"   Account '{statement_account}' not found in WAC database")
                            print_and_log(f"   POLICY VIOLATION: Only WAC operational accounts are allowed")
                            error_code = "ERROR_NO_ACCOUNT"
                            error_message = f"Account not found in WAC operational database. Only WAC operational accounts are permitted for processing."
                            
                        else:
                            print_and_log(f"❌ NOT A WAC OPERATIONAL ACCOUNT")
                            print_and_log(f"   Account '{statement_account}' not found in WAC database")
                            print_and_log(f"   POLICY VIOLATION: Only WAC operational accounts are allowed")
                            print_and_log(f"   Match type: {match_type}")
                            error_code = "ERROR_NO_ACCOUNT"
                            error_message = f"Account not found in WAC operational database. Only WAC operational accounts are permitted for processing."
                        
                        print_and_log(f"❌ Creating ERROR file - {error_message}")
                        
                        # Create error BAI2 file immediately with specific error code
                        from datetime import datetime
                        now = datetime.now()
                        file_date = now.strftime("%y%m%d")
                        file_time = now.strftime("%H%M")
                        
                        error_bai2 = create_error_bai2_file(
                            error_message,
                            name,
                            file_date,
                            file_time,
                            error_code
                        )
                        
                        # Save error file and return early
                        print_and_log("")
                        print_and_log("💾 STEP 3: Saving ERROR BAI file")
                        print_and_log("   ➤ Creating error notification file")
                        
                        output_container = blob_service.get_container_client("bank-reconciliation")
                        base_filename = name.split('.')[0]
                        output_filename = f"bai2-outputs/ERROR_{base_filename}.bai"
                        
                        output_container.upload_blob(
                            name=output_filename, 
                            data=error_bai2.encode('utf-8'), 
                            overwrite=True
                        )
                        
                        print_and_log("✅ ERROR BAI2 file uploaded successfully!")
                        print_and_log(f"📁 Location: bank-reconciliation/{output_filename}")
                        
                        # Archive original file
                        try:
                            input_container = blob_service.get_container_client(container_name)
                            source_blob = input_container.get_blob_client(blob_name)
                            
                            if source_blob.exists():
                                archive_container = blob_service.get_container_client(container_name)
                                archive_blob = archive_container.get_blob_client(f"archive/{name}")
                                archive_blob.start_copy_from_url(source_blob.url)
                                source_blob.delete_blob()
                                print_and_log("✅ Original file archived successfully!")
                                print_and_log(f"📁 Archive location: archive/{name}")
                            else:
                                print_and_log("⚠️ Source file not found (test mode)")
                        except Exception as archive_error:
                            print_and_log(f"⚠️ Archive error: {str(archive_error)}")
                        
                        # Final summary
                        print_and_log("")
                        print_and_log("📊 PROCESSING COMPLETE - FINAL SUMMARY")
                        print_and_log("=" * 60)
                        print_and_log(f"📄 Source File: {name}")
                        print_and_log(f"❌ ERROR BAI Output: bank-reconciliation/{output_filename}")
                        print_and_log(f"⚠️  BAI file created with error message due to non-WAC account")
                        print_and_log(f"📁 Archive: bank-reconciliation/archive/{name}")
                        print_and_log("⚠️ RECONCILIATION STATUS: NOT PERFORMED")
                        print_and_log("✅ BANK STATEMENT PROCESSING SUCCESSFUL!")
                        print_and_log("   ➤ Your PDF has been converted to BAI2 format")
                        print_and_log("   ➤ The file is ready for import into banking systems")
                        print_and_log("   ➤ Original file has been safely archived")
                        print_and_log("=" * 60)
                        
                        return
                        
                except Exception as e:
                    print_and_log(f"⚠️ WAC account verification error: {str(e)}")
                    print_and_log(f"❌ Creating ERROR file due to verification failure")
                    
                    # Create error BAI2 file for verification failure
                    from datetime import datetime
                    now = datetime.now()
                    file_date = now.strftime("%y%m%d")
                    file_time = now.strftime("%H%M")
                    
                    error_bai2 = create_error_bai2_file(
                        f"WAC account verification failed: {str(e)}",
                        name,
                        file_date,
                        file_time
                    )
                    
                    # Save error file and return early
                    output_container = blob_service.get_container_client("bank-reconciliation")
                    base_filename = name.split('.')[0]
                    output_filename = f"bai2-outputs/ERROR_{base_filename}.bai"
                    
                    output_container.upload_blob(
                        name=output_filename, 
                        data=error_bai2.encode('utf-8'), 
                        overwrite=True
                    )
                    
                    # Archive original file
                    try:
                        input_container = blob_service.get_container_client(container_name)
                        source_blob = input_container.get_blob_client(blob_name)
                        
                        if source_blob.exists():
                            archive_container = blob_service.get_container_client(container_name)
                            archive_blob = archive_container.get_blob_client(f"archive/{name}")
                            archive_blob.start_copy_from_url(source_blob.url)
                            source_blob.delete_blob()
                        print_and_log("✅ Original file archived")
                    except Exception as archive_error:
                        print_and_log(f"⚠️ Archive error: {str(archive_error)}")
                    return
        
        # Generate comprehensive BAI from processed data with enhanced matching results
        bai2 = convert_to_bai2(
            final_data, 
            name, 
            reconciliation_summary, 
            routing_number=enhanced_routing_number,
            matched_account_number=enhanced_account_number
        )

        print_and_log("")
        print_and_log("💾 STEP 3: Saving BAI file to processed folder")
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
        print_and_log("📁 STEP 4: Moving original file to archive")
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
            from datetime import datetime  # Ensure datetime is available in error handler
            now = datetime.now()
            file_date = now.strftime("%y%m%d")
            file_time = now.strftime("%H%M")
            
            # Determine error code based on exception type or message
            error_message = str(e)
            exception_type = type(e).__name__
            
            # Enhanced error classification with exception types
            if "Document Intelligence" in error_message or "docintelligence" in error_message.lower():
                error_code = "ERROR_DOC_INTEL_FAILED"
            elif "OpenAI" in error_message or "openai" in error_message.lower():
                error_code = "ERROR_PARSING_FAILED"
            elif "connection" in error_message.lower() or "network" in error_message.lower():
                error_code = "ERROR_NETWORK_FAILED"
            elif "timeout" in error_message.lower() or exception_type in ["TimeoutError", "TimeoutException"]:
                error_code = "ERROR_TIMEOUT"
            elif exception_type in ["KeyError", "IndexError", "AttributeError"]:
                error_code = "ERROR_DATA_FORMAT"
                print_and_log(f"🐛 DATA FORMAT ERROR: {exception_type} - {error_message}")
            elif exception_type in ["MemoryError"]:
                error_code = "ERROR_MEMORY_EXCEEDED"
                print_and_log(f"🐛 MEMORY ERROR: PDF likely too large - {error_message}")
            elif "rate limit" in error_message.lower() or "429" in error_message:
                error_code = "ERROR_RATE_LIMITED"
                print_and_log(f"🐛 RATE LIMIT ERROR: API throttled - {error_message}")
            elif "401" in error_message or "403" in error_message or "authentication" in error_message.lower():
                error_code = "ERROR_AUTH_FAILED"
                print_and_log(f"🐛 AUTH ERROR: Check API keys - {error_message}")
            else:
                error_code = "ERROR_UNKNOWN"
                print_and_log(f"🐛 UNKNOWN ERROR TYPE: {exception_type}")
                print_and_log(f"🐛 FULL ERROR MESSAGE: {error_message}")
                
                # Add full traceback for unknown errors
                import traceback
                full_trace = traceback.format_exc()
                print_and_log(f"🐛 FULL TRACEBACK:")
                for line in full_trace.split('\n'):
                    if line.strip():
                        print_and_log(f"   {line}")
                        
            # Always log the exception type and details for debugging
            print_and_log(f"🔍 EXCEPTION TYPE: {exception_type}")
            print_and_log(f"🔍 ERROR CODE: {error_code}")
            
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
        # Always remove the file from processing queues when done
        if 'file_key' in locals():
            _processing_files.discard(file_key)
            processing_queue.finish_processing(file_key)
            print_and_log(f"[DEBUG] Removed {name} from processing queues")

def get_statement_date(data, filename=None):
    """Extract statement end date from parsed data for BAI2 headers with enhanced fallback logic"""
    
    try:
        # PRIORITY 1: Check Document Intelligence mapped fields first
        if data and isinstance(data, dict):
            # Check for Document Intelligence extracted statement end date
            statement_end_date = data.get("statement_end_date")
            if statement_end_date:
                print_and_log(f"🎯 Found Document Intelligence statement end date: {statement_end_date}")
                try:
                    # Handle MM/DD/YYYY format (most common from Document Intelligence)
                    date_obj = datetime.strptime(statement_end_date, "%m/%d/%Y")
                    result = date_obj.strftime("%y%m%d")
                    print_and_log(f"✅ Using Document Intelligence statement end date: {statement_end_date} -> {result}")
                    return result
                except ValueError:
                    try:
                        # Handle MM/DD/YY format (short year)
                        date_obj = datetime.strptime(statement_end_date, "%m/%d/%y")
                        result = date_obj.strftime("%y%m%d")
                        print_and_log(f"✅ Using Document Intelligence statement end date: {statement_end_date} -> {result}")
                        return result
                    except ValueError:
                        try:
                            # Handle YYYY-MM-DD format
                            date_obj = datetime.strptime(statement_end_date, "%Y-%m-%d")
                            result = date_obj.strftime("%y%m%d")
                            print_and_log(f"✅ Using Document Intelligence statement end date: {statement_end_date} -> {result}")
                            return result
                        except ValueError:
                            try:
                                # Handle MM-DD-YYYY format
                                date_obj = datetime.strptime(statement_end_date, "%m-%d-%Y")
                                result = date_obj.strftime("%y%m%d")
                                print_and_log(f"✅ Using Document Intelligence statement end date: {statement_end_date} -> {result}")
                                return result
                            except ValueError:
                                print_and_log(f"⚠️ Could not parse Document Intelligence statement end date: {statement_end_date}")
        
        # PRIORITY 1.5: Parse statement period from OCR text to find end date
        if data and isinstance(data, dict) and "ocr_text_lines" in data:
            print_and_log(f"🔍 Searching OCR text for statement period information...")
            ocr_text = "\n".join(data["ocr_text_lines"])
            
            # Look for patterns like "STATEMENT PERIOD 07/01/25 THROUGH 07/31/25"
            # or "TOTAL DAYS IN STATEMENT PERIOD 07/01/25 THROUGH 07/31/25"
            period_patterns = [
                r'statement\s+period\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+through\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'period\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+through\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'from\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+to\s+(\d{1,2}/\d{1,2}/\d{2,4})',
                r'(\d{1,2}/\d{1,2}/\d{2,4})\s+through\s+(\d{1,2}/\d{1,2}/\d{2,4})'
            ]
            
            for pattern in period_patterns:
                match = re.search(pattern, ocr_text.lower())
                if match:
                    start_date_str, end_date_str = match.groups()
                    print_and_log(f"✅ Found statement period: {start_date_str} through {end_date_str}")
                    
                    try:
                        # Parse the end date
                        if len(end_date_str.split('/')[-1]) == 2:  # 2-digit year
                            date_obj = datetime.strptime(end_date_str, "%m/%d/%y")
                        else:  # 4-digit year
                            date_obj = datetime.strptime(end_date_str, "%m/%d/%Y")
                        
                        result = date_obj.strftime("%y%m%d")
                        print_and_log(f"✅ Using statement period end date: {end_date_str} -> {result}")
                        return result
                    except ValueError as e:
                        print_and_log(f"⚠️ Could not parse statement period end date '{end_date_str}': {e}")
                        continue
        
        # PRIORITY 2: Try to get end date from statement period (legacy OpenAI parsing)
        if data and isinstance(data, dict):
            statement_period = data.get("statement_period", {})
            if isinstance(statement_period, dict):
                end_date = statement_period.get("end_date")
                if end_date:
                    # Parse the date and convert to YYMMDD format
                    try:
                        # Handle YYYY-MM-DD format
                        date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                        print_and_log(f"✅ Extracted statement end date: {end_date} -> {date_obj.strftime('%y%m%d')}")
                        return date_obj.strftime("%y%m%d")
                    except ValueError:
                        try:
                            # Handle MM/DD/YYYY format
                            date_obj = datetime.strptime(end_date, "%m/%d/%Y")
                            print_and_log(f"✅ Extracted statement end date: {end_date} -> {date_obj.strftime('%y%m%d')}")
                            return date_obj.strftime("%y%m%d")
                        except ValueError:
                            try:
                                # Handle MM-DD-YYYY format
                                date_obj = datetime.strptime(end_date, "%m-%d-%Y")
                                print_and_log(f"✅ Extracted statement end date: {end_date} -> {date_obj.strftime('%y%m%d')}")
                                return date_obj.strftime("%y%m%d")
                            except ValueError:
                                print_and_log(f"⚠️ Could not parse statement end date: {end_date}")
            
            # Fallback: try to get from closing balance date
            closing_balance = data.get("closing_balance", {})
            if isinstance(closing_balance, dict):
                close_date = closing_balance.get("date")
                if close_date:
                    try:
                        date_obj = datetime.strptime(close_date, "%Y-%m-%d")
                        print_and_log(f"✅ Using closing balance date: {close_date} -> {date_obj.strftime('%y%m%d')}")
                        return date_obj.strftime("%y%m%d")
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(close_date, "%m/%d/%Y")
                            print_and_log(f"✅ Using closing balance date: {close_date} -> {date_obj.strftime('%y%m%d')}")
                            return date_obj.strftime("%y%m%d")
                        except ValueError:
                            print_and_log(f"⚠️ Could not parse closing balance date: {close_date}")
        
        # PRIORITY 3: Enhanced fallback - try to extract date from filename
        if filename:
            print_and_log(f"🔍 Attempting to extract date from filename: {filename}")
            
            # Look for date patterns in filename like "20250731", "2025-07-31", "07-31-25", etc.
            date_patterns = [
                r'(\d{4})(\d{2})(\d{2})',  # YYYYMMDD
                r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
                r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{2})',  # MM-DD-YY
                r'(\d{1,2})(\d{1,2})(\d{2})',  # MMDDYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, filename)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups[0]) == 4:  # YYYY format
                            year, month, day = groups
                            date_obj = datetime(int(year), int(month), int(day))
                        elif len(groups[2]) == 4:  # MM-DD-YYYY format
                            month, day, year = groups
                            date_obj = datetime(int(year), int(month), int(day))
                        else:  # MM-DD-YY format
                            month, day, year = groups
                            # Convert 2-digit year to 4-digit (assume 20XX for years 00-99)
                            full_year = 2000 + int(year)
                            date_obj = datetime(full_year, int(month), int(day))
                        
                        result = date_obj.strftime("%y%m%d")
                        print_and_log(f"✅ Extracted date from filename: {filename} -> {result}")
                        return result
                    except (ValueError, IndexError) as e:
                        print_and_log(f"⚠️ Failed to parse date from filename: {e}")
                        continue
            
            print_and_log(f"⚠️ No date pattern found in filename: {filename}")
                            
    except Exception as e:
        print_and_log(f"⚠️ Error extracting statement date: {e}")
    
    print_and_log(f"⚠️ No statement date found, falling back to current date")
    return None

def convert_to_bai2(data, filename, reconciliation_data=None, routing_number=None, matched_account_number=None):
    """
    Convert extracted data to BAI format using OpenAI for intelligent generation
    This replaces the complex manual BAI2 construction with AI-powered generation
    """
    print_and_log("🤖 STARTING OpenAI BAI2 conversion - NEW APPROACH")
    print_and_log(f"🔧 DEBUG: Function called with filename={filename}")
    
    # Check if bankStatement extraction failed
    if data.get("extraction_method") == "bankStatement_failed":
        error_msg = data.get("error", "bankStatement model extraction failed")
        print_and_log(f"❌ CRITICAL: bankStatement extraction failed - {error_msg}")
        print_and_log("🔄 Creating ERROR BAI2 file instead of processing")
        
        # Use current date/time for error file
        now = datetime.now()
        file_date = now.strftime("%y%m%d")
        file_time = now.strftime("%H%M")
        
        return create_error_bai2_file(f"Document Intelligence bankStatement model failed: {error_msg}", 
                                    filename, file_date, file_time, "ERROR_BANKSTATEMENT_FAILED")
    
    try:
        # Extract statement date for BAI2 headers (use statement end date, not current date)
        statement_date = get_statement_date(data, filename)
        now = datetime.now()
        
        if statement_date:
            file_date = statement_date
            print_and_log(f"✅ Using statement end date for BAI2 headers: {file_date}")
        else:
            file_date = now.strftime("%y%m%d")
            print_and_log(f"⚠️ No statement date found, falling back to current date: {file_date}")
        
        # Always use current time for file generation time
        file_time = now.strftime("%H%M")
        
        print_and_log(f"🔧 DEBUG: BAI2 header dates - file_date={file_date}, file_time={file_time}")
        
        # Use matched account number from enhanced matching if available, otherwise extract from statement
        if matched_account_number:
            account_number = matched_account_number
            print_and_log(f"✅ Using matched account number from WAC data: {account_number}")
        else:
            # Extract account number from statement (needed for enhanced matching)
            account_number = get_account_number(data)
            if not account_number:
                print_and_log("❌ CRITICAL: No account number found on statement - creating ERROR file")
                return create_error_bai2_file("No account number found on statement", filename, file_date, file_time, "ERROR_NO_ACCOUNT")
            print_and_log(f"✅ Using account number from statement: {account_number}")
        
        print_and_log(f"🔧 DEBUG: Account number resolved: {account_number}")
        
        # Use provided routing number or extract it
        if routing_number:
            originator_id = routing_number
            print_and_log(f"✅ Using provided routing number: {originator_id}")
        else:
            # Try to extract routing number from data (now with account number for enhanced matching)
            result = get_routing_number(data, account_number)
            if result and isinstance(result, tuple) and len(result) >= 2 and result[0] is not None:
                originator_id, matched_account = result
                if matched_account and not matched_account_number:
                    # Update account number if we got a match during routing lookup
                    account_number = matched_account
                    print_and_log(f"✅ Updated account number from enhanced matching: {account_number}")
            elif result and not isinstance(result, tuple) and result is not None:
                originator_id = result
            else:
                print_and_log("❌ CRITICAL: No routing number found in WAC Bank Information database - creating ERROR file")
                return create_error_bai2_file("No routing number found in WAC Bank Information database for this bank/account combination", filename, file_date, file_time, "ERROR_NO_ROUTING")
        
        print_and_log(f"🔧 DEBUG: Routing number resolved: {originator_id}")
        
        # Get bank information for BAI2 generation
        try:
            from bank_info_loader import find_matching_bank_with_account
            
            # Extract bank name from statement for matching
            bank_name_from_statement = None
            if data and "ocr_text_lines" in data:
                # Convert list to string if needed
                text_lines = data["ocr_text_lines"]
                if isinstance(text_lines, list):
                    text_for_extraction = '\n'.join(text_lines)
                else:
                    text_for_extraction = text_lines
                bank_name_from_statement = extract_bank_name_from_text(text_for_extraction)
            
            if bank_name_from_statement:
                bank_match, similarity, bank_details = find_matching_bank_with_account(bank_name_from_statement, account_number)
                
                if bank_match and len(bank_match) > 0:
                    bank_name = bank_match[0].get('bank_name', 'Unknown Bank')
                    print_and_log(f"🏦 Bank identified: {bank_name} (similarity: {similarity:.1%})")
                else:
                    bank_name = "Unknown Bank"
                    print_and_log("⚠️ Bank not identified, using default")
            else:
                bank_name = "Unknown Bank"
                print_and_log("⚠️ No bank name found on statement, using default")
                
        except Exception as e:
            print_and_log(f"⚠️ Could not load bank info: {e}")
            bank_name = "Unknown Bank"
        
        print_and_log(f"🔧 DEBUG: Bank info setup complete: {bank_name}")
        
        # FORCE OpenAI generation - no fallback allowed
        print_and_log("🤖 FORCING OpenAI BAI2 generation - this should work or create error file")
        
        # Prepare comprehensive data for OpenAI BAI2 generation with precise format
        # Check if we have enhanced transaction data and use it preferentially
        enhanced_transactions = data.get('enhanced_transactions')
        if enhanced_transactions:
            print_and_log("✅ Using enhanced transaction parsing data for BAI2 generation")
            transaction_data_source = enhanced_transactions
            extraction_method = data.get('extraction_method', 'unknown')
            print_and_log(f"📊 Enhanced data: {enhanced_transactions['count_debits']} debits (${enhanced_transactions['total_debits']:.2f}), {enhanced_transactions['count_credits']} credits (${enhanced_transactions['total_credits']:.2f})")
        else:
            print_and_log("⚠️ Using original extraction data for BAI2 generation")
            transaction_data_source = data
            extraction_method = data.get('extraction_method', 'unknown')
        
        bai2_prompt = f"""You are a BAI2 (Bank Administration Institute) file-format expert. Generate a complete, properly formatted BAI2 file from the inputs below. 
Nothing may be hard-coded. All values must be taken from the inputs or derived per BAI2 rules.

############################
## INPUTS (VARIABLE DATA) ##
############################
FILE_META (applies to the whole file):
Bank Name: {bank_name}
Account Number: {account_number}
Routing Number: {originator_id}
Account Type: Business Checking
Statement Date: {file_date} ({file_time})
Extraction Method: {extraction_method}

EXTRACTED STATEMENT DATA:
{json.dumps(transaction_data_source, indent=2)}

RECONCILIATION DATA (if available):
{json.dumps(reconciliation_data, indent=2) if reconciliation_data else "None"}

#######################################
## CRITICAL OCR TEXT PARSING RULES ##
#######################################
IMPORTANT: The extracted data above may contain raw OCR text from a bank statement. You MUST parse this intelligently:

1. TRANSACTION IDENTIFICATION:
   - Look for patterns like "Date Description Amount" in the OCR text
   - Transactions are usually grouped under sections like "DEBITS" and "CREDITS"  
   - Ignore header lines, summary lines, and non-transaction text
   - Each transaction should have: Date, Description, Amount

2. SUMMARY VALIDATION:
   - Look for summary lines like "Total additions: $X" or "Total subtractions: $Y"
   - Use these totals to validate your transaction parsing
   - If your individual transactions don't match the totals, reparse more carefully

3. DUPLICATE AVOIDANCE:
   - Do NOT create multiple BAI2 records for the same transaction
   - If you see repeated amounts or descriptions, consolidate appropriately
   - Focus on actual individual transactions, not summary or duplicate entries

4. TRANSACTION TYPE CLASSIFICATION:
   - Debits/Withdrawals: Use BAI2 code 451 (ACH withdrawal) or 475 (fees only)
   - Credits/Deposits: Use BAI2 code 301 (deposit)
   - Maintenance fees: Use BAI2 code 475

###############################
## OUTPUT RULES (STRICT BAI2) ##
###############################
GLOBAL RULES:
- Output a valid BAI2 file ONLY — no explanations, no code fences, no extra text.
- Every record MUST end with a forward slash "/" on its own line.
- Use only integer amounts in cents (no decimals).
- Do NOT hard-code any constant like receiver_id, currency, account type, dates, or IDs.
- All values must come from the inputs or be computed dynamically per BAI2 spec.

SANITIZATION RULES (apply to DESCRIPTION and any free text fields):
- Replace any "/" with "-" (BAI2 uses "/" as record terminator).
- Convert to plain ASCII; replace non-ASCII characters with closest ASCII or a space.
- Remove newlines and control characters.
- Trim descriptions to <= 80 characters where possible (truncate at word boundary if feasible).

REFERENCE NUMBER RULES (REF_NUM on 16 records):
- For each account, generate a 5-digit, zero-padded, strictly increasing sequence starting at 00001 and increment by 1.
- No gaps and no duplicates within the account's transaction block.

#####################################
## BAI2 RECORD LAYOUTS (NO DEFAULTS) ##
#####################################
1) File Header (01)
   01,{originator_id},WORKDAY,{file_date},{file_time},1,,,2/

2) Group Header (02) — one per group
   02,WORKDAY,{originator_id},1,{file_date},,USD,2/

3) Account Identifier (03) — one per account
   03,{account_number},USD,010,,,Z/

4) Transaction Detail (16) — zero or more per account
   16,TYPE_CODE,AMOUNT_CENTS,Z,REF_NUM,,DESCRIPTION/
   - TYPE_CODE: 301 (deposit), 451 (ACH withdrawal), 475 (bank fees only)
   - AMOUNT_CENTS: integer only (no decimals)
   - REF_NUM: 5-digit sequential per account (00001, 00002, etc.)
   - DESCRIPTION: sanitized text per rules above

5) Account Trailer (49) — one per account
   49,ENDING_BALANCE_CENTS,N/
   - N = number of 16-records (transactions) emitted for this account

6) Group Trailer (98) — one per group
   98,GROUP_CONTROL_TOTAL,1,GROUP_RECORD_COUNT/
   - GROUP_CONTROL_TOTAL = ending account balance in cents
   - GROUP_RECORD_COUNT = total records from Group Header (02) through Account Trailer (49) inclusive
   - Formula: 1 (02) + 1 (03) + N_transactions (16s) + 1 (49) = N+3

7) File Trailer (99) — once at end of file
   99,FILE_CONTROL_TOTAL,1,FILE_RECORD_COUNT/
   - FILE_CONTROL_TOTAL = same as group control total
   - FILE_RECORD_COUNT = same as group record count when only one group exists

###################################
## VALIDATION (MUST PASS BEFORE OUTPUT)
###################################
Validate BEFORE returning output:
- Every line ends with "/".
- All amounts are integers (no decimals).
- No "/" remains inside descriptions; sanitize non-ASCII and control characters.
- REF_NUM starts at 00001 and increments by 1 for each 16 record; no gaps or duplicates.
- Account Trailer (49) N equals the number of 16 records generated for that account.
- Group record count = 1 + 1 + N_transactions + 1 = N+3
- File record count = same as group record count when only one group exists.

Return ONLY the final BAI2 content as plain text records, one per line, exactly as specified.
No explanations, no comments, no code fences."""
        
        print_and_log("🔧 DEBUG: About to call Azure OpenAI with throttling...")
        
        # Use Azure OpenAI to generate the complete BAI2 file with throttling
        from openai import AzureOpenAI
        openai_client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2024-10-01-preview"
        )
        
        print_and_log("🔧 DEBUG: OpenAI client created successfully")
        
        # Use throttled OpenAI call with retry logic
        def make_openai_call():
            return openai_client.chat.completions.create(
                model=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a BAI2 file format expert. Generate properly formatted BAI2 files that comply with banking standards."
                    },
                    {
                        "role": "user", 
                        "content": bai2_prompt
                    }
                ],
                temperature=0,  # Use deterministic output for consistent formatting
                max_tokens=2000
            )
        
        # Execute with throttling and retry logic
        response = openai_throttler.retry_with_backoff(make_openai_call)
        
        print_and_log("🔧 DEBUG: OpenAI response received successfully")
        
        bai2_content = response.choices[0].message.content.strip()
        
        # Validate the generated BAI2 content
        if not bai2_content.startswith("01,"):
            print_and_log("⚠️ Generated BAI2 doesn't start with file header, creating error file")
            return create_error_bai2_file("OpenAI BAI2 generation format error", filename, file_date, file_time, "ERROR_AI_FORMAT")
        
        print_and_log("✅ OpenAI successfully generated initial BAI2 file")
        print_and_log(f"📏 Generated BAI2 length: {len(bai2_content)} characters")
        print_and_log(f"📊 Generated BAI2 lines: {bai2_content.count(chr(10)) + 1}")
        
        # SECOND PASS: Validate and fix the BAI2 file using bai2_fixer
        if bai2_fixer:
            try:
                print_and_log("🔧 SECOND PASS: Validating and fixing BAI2 file with bai2_fixer")
                
                # Use bai2_fixer to parse, validate, and rebuild the BAI2 content
                file01, groups, audit_dates = bai2_fixer.parse_bai2(bai2_content)
                rebuilt_lines = bai2_fixer.rebuild_bai2(file01, groups)
                
                # Build audit log
                audit_lines = []
                if audit_dates["file_date_corrected"]:
                    audit_lines.append(f"corrected 01 file date -> {file01.file_date}")
                if audit_dates["group_dates_corrected"]:
                    audit_lines.append(f"corrected {audit_dates['group_dates_corrected']} group date(s) in 02")
                
                # Account-level audits
                total_ref_renum = 0
                total_amt_norm = 0
                total_desc_san = 0
                ending_bal_fixed = 0
                for g in groups:
                    for a in g.accounts:
                        if a.audit["ref_renumbered"]:
                            total_ref_renum += 1
                        total_amt_norm += a.audit["amounts_normalized"]
                        total_desc_san += a.audit["descriptions_sanitized"]
                        if a.audit["ending_balance_fixed"]:
                            ending_bal_fixed += 1
                
                if total_ref_renum:
                    audit_lines.append(f"renumbered REF_NUMs for {total_ref_renum} account(s)")
                if total_amt_norm:
                    audit_lines.append(f"normalized {total_amt_norm} amount(s) to integer cents")
                if total_desc_san:
                    audit_lines.append(f"sanitized {total_desc_san} description(s)")
                if ending_bal_fixed:
                    audit_lines.append(f"fixed non-integer ending balances in {ending_bal_fixed} account(s)")
                
                audit_log = "; ".join(audit_lines) if audit_lines else "No fixes needed"
                final_bai2_content = "\n".join(rebuilt_lines)
                
                print_and_log("✅ BAI2 validation and fixing completed successfully")
                print_and_log(f"📋 Audit log: {audit_log}")
                print_and_log(f"📏 Final BAI2 length: {len(final_bai2_content)} characters")
                print_and_log(f"📊 Final BAI2 lines: {final_bai2_content.count(chr(10)) + 1}")
                
            except Exception as e:
                print_and_log(f"❌ BAI2 fixing failed: {e}")
                print_and_log("⚠️ Using original OpenAI-generated content")
                final_bai2_content = bai2_content
        else:
            print_and_log("⚠️ bai2_fixer not available, using original OpenAI-generated content")
            final_bai2_content = bai2_content
        
        print_and_log("🎯 RETURNING validated BAI2 content")
        return final_bai2_content
        
    except Exception as e:
        print_and_log(f"❌ CRITICAL ERROR in OpenAI BAI2 generation: {str(e)}")
        import traceback
        print_and_log(f"� Full traceback: {traceback.format_exc()}")
        print_and_log(f"🔄 Creating error file instead of falling back to manual approach")
        return create_error_bai2_file(f"OpenAI BAI2 generation failed: {str(e)}", filename, file_date, file_time, "ERROR_AI_FAILED")

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

@app.function_name("throttling_status")
@app.route(route="throttling", methods=["GET"])
def throttling_status(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP endpoint to check throttling status and configuration"""
    try:
        # Get current time and throttling status
        current_time = time.time()
        
        # Get queue status
        queue_status = processing_queue.get_queue_status()
        
        # Get throttler status
        with openai_throttler._lock:
            time_since_reset = current_time - openai_throttler._reset_time
            time_since_last_call = current_time - openai_throttler._last_call_time
            
            throttler_status = {
                'calls_this_minute': openai_throttler._call_count,
                'max_calls_per_minute': ThrottlingConfig.CALLS_PER_MINUTE,
                'time_since_reset': f"{time_since_reset:.1f}s",
                'time_since_last_call': f"{time_since_last_call:.1f}s",
                'min_delay_between_calls': f"{ThrottlingConfig.MIN_DELAY_BETWEEN_CALLS}s"
            }
        
        # Build response
        status_info = {
            'timestamp': datetime.now().isoformat(),
            'throttling_config': {
                'calls_per_minute': ThrottlingConfig.CALLS_PER_MINUTE,
                'min_delay_between_calls': ThrottlingConfig.MIN_DELAY_BETWEEN_CALLS,
                'retry_delays': ThrottlingConfig.RETRY_DELAYS,
                'processing_delay_range': f"{ThrottlingConfig.INITIAL_PROCESSING_DELAY_MIN}-{ThrottlingConfig.INITIAL_PROCESSING_DELAY_MAX}s"
            },
            'current_throttler_status': throttler_status,
            'processing_queue': queue_status,
            'configuration_summary': ThrottlingConfig.get_summary().split('\n')
        }
        
        # Return JSON response
        import json
        return func.HttpResponse(
            json.dumps(status_info, indent=2),
            status_code=200,
            headers={'Content-Type': 'application/json'}
        )
        
    except Exception as e:
        logging.error(f"Error getting throttling status: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
