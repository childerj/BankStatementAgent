#!/usr/bin/env python3
"""
Test Bank Routing Number Lookup Functionality
Tests the OpenAI-powered bank name to routing number lookup
"""
import os
import openai
import re

def is_valid_routing_number(routing_number):
    """Basic validation of routing number using checksum algorithm"""
    if not routing_number or len(routing_number) != 9 or not routing_number.isdigit():
        return False
    
    # ABA routing number checksum validation
    digits = [int(d) for d in routing_number]
    checksum = (3 * (digits[0] + digits[3] + digits[6]) +
                7 * (digits[1] + digits[4] + digits[7]) +
                1 * (digits[2] + digits[5] + digits[8]))
    
    return checksum % 10 == 0

def lookup_routing_number_by_bank_name(bank_name):
    """Use OpenAI to lookup routing number for a given bank name"""
    print(f"🤖 Looking up routing number for bank: {bank_name}")
    
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            print("❌ OpenAI API key not found in environment variables")
            return None
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=openai_api_key)
        
        prompt = f"""
        What is the primary ABA routing number for {bank_name}? 
        
        Please respond with ONLY the 9-digit routing number, no other text.
        If you're not certain or if the bank has multiple routing numbers, provide the most common one.
        If you cannot find a routing number for this bank, respond with "NOT_FOUND".
        
        Examples:
        - Wells Fargo Bank -> 121000248
        - Bank of America -> 026009593
        - Chase Bank -> 021000021
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a banking expert that provides accurate ABA routing numbers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )
        
        routing_number = response.choices[0].message.content.strip()
        
        # Validate the response
        if routing_number == "NOT_FOUND":
            print(f"❌ OpenAI could not find routing number for: {bank_name}")
            return None
        
        # Check if it's a valid 9-digit number
        if routing_number.isdigit() and len(routing_number) == 9:
            if is_valid_routing_number(routing_number):
                print(f"✅ OpenAI found routing number: {routing_number} for {bank_name}")
                return routing_number
            else:
                print(f"❌ OpenAI returned invalid routing number: {routing_number}")
                return None
        else:
            print(f"❌ OpenAI returned invalid format: {routing_number}")
            return None
            
    except Exception as e:
        print(f"❌ Error looking up routing number with OpenAI: {str(e)}")
        return None

def extract_bank_name_from_text(text):
    """Extract bank name from statement text"""
    print(f"🏦 Searching for bank name in text: '{text[:100]}...'")
    
    # Common bank name patterns
    bank_patterns = [
        r'([A-Z][a-z]+\s+Bank)',  # "First Bank"
        r'([A-Z][a-z]+\s+National\s+Bank)',  # "First National Bank"
        r'([A-Z][a-z]+\s+Trust)',  # "First Trust"
        r'([A-Z][a-z]+\s+Credit\s+Union)',  # "First Credit Union"
        r'(Bank\s+of\s+[A-Z][a-z]+)',  # "Bank of America"
        r'([A-Z][a-z]+\s+Financial)',  # "Wells Financial"
        r'([A-Z][a-z]+\s+Federal)',  # "Navy Federal"
    ]
    
    for pattern in bank_patterns:
        matches = re.findall(pattern, text)
        if matches:
            bank_name = matches[0].strip()
            print(f"🏦 Found potential bank name: {bank_name}")
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
                        print(f"🏦 Found potential bank name: {potential_name}")
                        return potential_name.strip()
    
    print("❌ No bank name found in statement text")
    return None

def test_routing_lookup():
    """Test the routing number lookup functionality"""
    print("🧪 TESTING BANK ROUTING NUMBER LOOKUP")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("⚠️  OPENAI_API_KEY environment variable not set")
        print("   This test requires an OpenAI API key to function")
        print("   Set the environment variable and try again")
        return
    
    print(f"✅ OpenAI API key found: {openai_api_key[:10]}...")
    print()
    
    # Test bank name extraction
    print("🧪 TESTING BANK NAME EXTRACTION")
    print("-" * 40)
    
    bank_text_samples = [
        "Wells Fargo Bank\nAccount Statement\nJohn Doe",
        "BANK OF AMERICA\nMonthly Statement",
        "Chase Bank Statement for Account 123456",
        "First National Bank\nCustomer: Jane Smith",
        "Navy Federal Credit Union Statement",
        "Unknown Financial Institution\nAccount Details",
        "Statement with no clear bank name\nAccount: 12345"
    ]
    
    extracted_banks = []
    
    for i, text in enumerate(bank_text_samples, 1):
        print(f"\nTest {i}: {text.replace(chr(10), ' ')[:50]}...")
        bank_name = extract_bank_name_from_text(text)
        if bank_name:
            extracted_banks.append(bank_name)
            print(f"✅ Extracted: {bank_name}")
        else:
            print("❌ No bank name extracted")
    
    print()
    print("🧪 TESTING ROUTING NUMBER LOOKUP")
    print("-" * 40)
    
    # Test known banks with known routing numbers
    test_banks = [
        ("Wells Fargo Bank", "121000248"),  # Known Wells Fargo routing
        ("Bank of America", "026009593"),   # Known BofA routing
        ("Chase Bank", "021000021"),        # Known Chase routing
        ("Fake Bank That Doesnt Exist", None),  # Should return None
    ]
    
    # Add extracted bank names to test list
    for bank in extracted_banks:
        test_banks.append((bank, None))  # We don't know the expected routing
    
    lookup_results = []
    
    for bank_name, expected_routing in test_banks:
        print(f"\n🏦 Testing: {bank_name}")
        result = lookup_routing_number_by_bank_name(bank_name)
        
        if result:
            print(f"✅ Got routing number: {result}")
            if expected_routing and result == expected_routing:
                print(f"✅ Matches expected: {expected_routing}")
            elif expected_routing and result != expected_routing:
                print(f"⚠️  Expected: {expected_routing}, Got: {result}")
            
            # Validate the routing number
            if is_valid_routing_number(result):
                print(f"✅ Routing number passes checksum validation")
            else:
                print(f"❌ Routing number fails checksum validation")
            
            lookup_results.append((bank_name, result))
        else:
            print(f"❌ No routing number found")
            if expected_routing:
                print(f"⚠️  Expected: {expected_routing}")
    
    print()
    print("📊 LOOKUP RESULTS SUMMARY")
    print("-" * 40)
    
    if lookup_results:
        print(f"✅ Successfully looked up {len(lookup_results)} routing numbers:")
        for bank, routing in lookup_results:
            print(f"   {bank}: {routing}")
    else:
        print("❌ No routing numbers were successfully looked up")
    
    print()
    print("🎯 TESTING COMPLETE")
    print("=" * 60)
    print("This test validates:")
    print("✅ Bank name extraction from text")
    print("✅ OpenAI API connectivity")  
    print("✅ Routing number format validation")
    print("✅ ABA checksum validation")
    print("✅ Error handling for unknown banks")

def test_integration_scenario():
    """Test a complete integration scenario"""
    print("\n🔄 INTEGRATION SCENARIO TEST")
    print("=" * 60)
    
    # Simulate a bank statement with no routing number but with bank name
    statement_text = """
    Wells Fargo Bank
    Monthly Account Statement
    
    Account Number: 1234567890
    Statement Period: July 1 - July 31, 2025
    
    Beginning Balance: $1,500.00
    Ending Balance: $1,250.00
    
    Transactions:
    07/05  Deposit               +$500.00
    07/10  ATM Withdrawal        -$100.00
    07/15  Check #1001           -$650.00
    """
    
    print("📄 Simulating bank statement processing...")
    print("   Statement contains bank name but no routing number")
    print()
    
    # Step 1: Try to extract bank name
    print("Step 1: Extract bank name from statement")
    bank_name = extract_bank_name_from_text(statement_text)
    
    if bank_name:
        print(f"✅ Bank name extracted: {bank_name}")
        
        # Step 2: Lookup routing number
        print("\nStep 2: Lookup routing number via OpenAI")
        routing_number = lookup_routing_number_by_bank_name(bank_name)
        
        if routing_number:
            print(f"✅ Routing number found: {routing_number}")
            print(f"✅ Complete integration successful!")
            print(f"   Bank: {bank_name}")
            print(f"   Routing: {routing_number}")
            return True
        else:
            print("❌ Routing number lookup failed")
            return False
    else:
        print("❌ Bank name extraction failed")
        return False

if __name__ == "__main__":
    test_routing_lookup()
    test_integration_scenario()
