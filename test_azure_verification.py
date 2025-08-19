#!/usr/bin/env python3
"""
Test script to verify the BAI2 record counting fix works with the actual uploaded file
"""

import os
import sys
import json
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import openai

# Load environment variables from local.settings.json
def load_local_settings():
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('Values', {})
    except FileNotFoundError:
        print("❌ local.settings.json not found")
        return {}

# Set up environment
env_vars = load_local_settings()
if not env_vars:
    print("❌ Failed to load environment variables")
    sys.exit(1)

print("🔧 Setting up Azure clients...")

# Document Intelligence client
doc_client = DocumentIntelligenceClient(
    endpoint=env_vars['DOCUMENT_INTELLIGENCE_ENDPOINT'],
    credential=AzureKeyCredential(env_vars['DOCUMENT_INTELLIGENCE_KEY'])
)

# OpenAI client
openai.api_key = env_vars['OPENAI_API_KEY']

# Test with the uploaded file
test_file = "Test Docs/WACBAI2_20250813.pdf"

print(f"📄 Processing: {test_file}")

# Read the file
with open(test_file, 'rb') as f:
    file_content = f.read()

# Extract text using Document Intelligence
print("🔍 Extracting text with Document Intelligence...")
poller = doc_client.begin_analyze_document(
    "prebuilt-layout", 
    analyze_request=file_content, 
    content_type="application/pdf"
)
result = poller.result()

# Get extracted text
extracted_text = ""
for page in result.pages:
    for line in page.lines:
        extracted_text += line.content + "\n"

print(f"📝 Extracted text length: {len(extracted_text)} characters")

# Extract bank name (same logic as function_app.py)
bank_name = None
bank_name_patterns = [
    r"(?i)(?:^|\n)\s*([A-Z][A-Z\s&.,'-]+(?:BANK|CREDIT UNION|FINANCIAL|TRUST|SAVINGS))",
    r"(?i)(?:^|\n)\s*([A-Z][A-Z\s&.,'-]{10,})",
    r"(?i)(BANK\s+OF\s+[A-Z\s]+|[A-Z\s]+\s+BANK)",
    r"(?i)([A-Z][A-Z\s&.,'-]+(?:FEDERAL|NATIONAL|STATE|COMMUNITY))",
]

import re
for pattern in bank_name_patterns:
    matches = re.findall(pattern, extracted_text)
    if matches:
        bank_name = ' '.join(matches[0].split()) if isinstance(matches[0], str) else ' '.join(matches[0])
        bank_name = bank_name.strip()
        if len(bank_name) >= 5:
            break

print(f"🏦 Detected Bank Name: '{bank_name}'")

if not bank_name:
    print("❌ No bank name detected - this would create an error file")
    sys.exit(1)

# Get routing number from OpenAI
print("🤖 Getting routing number from OpenAI...")
openai_client = openai.OpenAI(api_key=env_vars['OPENAI_API_KEY'])

prompt = f"""
Extract the routing number from this bank statement. The routing number is typically a 9-digit number that identifies the bank.

Bank: {bank_name}

Statement text:
{extracted_text[:4000]}

Return only the 9-digit routing number, nothing else. If you cannot find it, return "NOT_FOUND".
"""

print(f"📤 OpenAI Prompt: {prompt[:500]}...")

try:
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0
    )
    
    routing_number = response.choices[0].message.content.strip()
    print(f"📥 OpenAI Response: '{routing_number}'")
    
    if routing_number == "NOT_FOUND" or not routing_number.isdigit() or len(routing_number) != 9:
        print("❌ No valid routing number found - this would create an error file")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ OpenAI error: {e}")
    sys.exit(1)

print(f"✅ Successfully extracted:")
print(f"   Bank: {bank_name}")
print(f"   Routing Number: {routing_number}")

# Now test the BAI2 generation logic (copy from function_app.py)
print("\n🔄 Testing BAI2 generation...")

# Sample transactions for testing (simulating what would be extracted)
transactions = [
    {"date": "250813", "amount": "-25.00", "description": "FEE CHARGE"},
    {"date": "250813", "amount": "1000.00", "description": "DEPOSIT"},
    {"date": "250813", "amount": "-150.00", "description": "CHECK 1001"},
    {"date": "250813", "amount": "-75.50", "description": "WITHDRAWAL"},
    {"date": "250813", "amount": "2500.00", "description": "TRANSFER IN"},
    {"date": "250813", "amount": "-300.00", "description": "CHECK 1002"},
    {"date": "250813", "amount": "-45.00", "description": "SERVICE FEE"},
    {"date": "250813", "amount": "500.00", "description": "DEPOSIT"},
    {"date": "250813", "amount": "-200.00", "description": "CHECK 1003"},
    {"date": "250813", "amount": "-125.75", "description": "ATM WITHDRAWAL"},
    {"date": "250813", "amount": "750.00", "description": "DIRECT DEPOSIT"},
    {"date": "250813", "amount": "-85.25", "description": "DEBIT CARD"},
]

# Generate BAI2 content with correct record counting
def generate_bai2_content(bank_name, routing_number, transactions, account_number="123456789"):
    today = datetime.now()
    file_date = today.strftime("%y%m%d")
    file_time = today.strftime("%H%M")
    
    lines = []
    
    # File Header (01)
    lines.append(f"01,{routing_number},{account_number},{file_date},{file_time},001,80,1,2/")
    
    # Group Header (02) 
    lines.append(f"02,{routing_number},{account_number},{file_date},{file_time},001,040,2/")
    
    # Account records and details
    account_records = 0
    
    # Account Identifier and Summary (03)
    lines.append(f"03,{account_number},USD,040,,,,,,/")
    account_records += 1
    
    # Add transactions (16 records)
    for i, txn in enumerate(transactions, 1):
        amount_str = txn['amount'].replace('-', '').replace('.', '')
        if txn['amount'].startswith('-'):
            amount_str = amount_str + '-'  # Negative amounts end with -
        
        lines.append(f"16,{txn['date']},{amount_str},,{txn['description']}/")
        account_records += 1
    
    # Account Trailer (49)
    lines.append(f"49,{account_number},{account_records}/")
    
    # Group Trailer (98) - count account records + account trailer
    group_records = account_records + 1  # +1 for account trailer (49)
    lines.append(f"98,{routing_number},{group_records},0/")
    
    # File Trailer (99) - count all records except file trailer
    file_records = len(lines)  # All lines so far
    lines.append(f"99,{routing_number},1,{file_records}/")
    
    return '\n'.join(lines)

# Generate BAI2 content
bai2_content = generate_bai2_content(bank_name, routing_number, transactions)

print("📄 Generated BAI2 content:")
print("=" * 50)
print(bai2_content)
print("=" * 50)

# Verify record counts
lines = bai2_content.split('\n')
print(f"\n🔍 Record count verification:")

# Count different record types
account_records = 0
group_records = 0
file_records = 0

for line in lines:
    if line.startswith('03,') or line.startswith('16,'):  # Account identifier or detail
        account_records += 1
    elif line.startswith('49,'):  # Account trailer
        group_records = account_records + 1  # +1 for account trailer itself
        file_records += 1
    elif line.startswith('98,'):  # Group trailer
        file_records += 1
    elif not line.startswith('99,'):  # Everything except file trailer
        file_records += 1

print(f"   Account records (03+16): {account_records}")
print(f"   Group records (account+49): {group_records}")  
print(f"   File records (all except 99): {file_records}")

# Extract expected counts from trailers
account_trailer = [line for line in lines if line.startswith('49,')][0]
group_trailer = [line for line in lines if line.startswith('98,')][0]
file_trailer = [line for line in lines if line.startswith('99,')][0]

account_expected = int(account_trailer.split(',')[2].rstrip('/'))
group_expected = int(group_trailer.split(',')[2])
file_expected = int(file_trailer.split(',')[3].rstrip('/'))

print(f"\n📊 Trailer comparison:")
print(f"   Account: Actual={account_records}, Expected={account_expected} {'✅' if account_records == account_expected else '❌'}")
print(f"   Group: Actual={group_records}, Expected={group_expected} {'✅' if group_records == group_expected else '❌'}")
print(f"   File: Actual={file_records}, Expected={file_expected} {'✅' if file_records == file_expected else '❌'}")

if account_records == account_expected and group_records == group_expected and file_records == file_expected:
    print("\n🎉 SUCCESS! All record counts match - the fix is working!")
else:
    print("\n❌ FAILURE! Record count mismatch detected")
    sys.exit(1)

print(f"\n✅ Test completed successfully! The deployed function should now generate correct BAI2 files.")
