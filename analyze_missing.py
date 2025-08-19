"""
Advanced pattern analysis to find the missing 24 transactions
"""
import os
import json
import re
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO

# Load environment variables
if os.path.exists('local.settings.json'):
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
        values = settings.get('Values', {})
        for key, value in values.items():
            os.environ[key] = value

def analyze_patterns_for_missing_transactions():
    """Analyze OCR text patterns to find missing transactions"""
    
    # Test file
    test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\822-847-896.pdf'
    
    print("🔍 PATTERN ANALYSIS FOR MISSING TRANSACTIONS")
    print("=" * 60)
    
    # Extract OCR data first
    endpoint = os.environ["DOCINTELLIGENCE_ENDPOINT"]
    key = os.environ["DOCINTELLIGENCE_KEY"]
    
    with open(test_file, 'rb') as f:
        file_bytes = f.read()
    
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )
    
    print("📊 Extracting OCR data...")
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=BytesIO(file_bytes),
        content_type="application/pdf"
    )
    result = poller.result()
    
    if result and result.content:
        ocr_text = result.content
    else:
        print("❌ Failed to extract OCR text")
        return
    
    print("🔍 Analyzing transaction patterns...")
    
    # Split into lines for better analysis
    lines = ocr_text.split('\n')
    
    # Pattern 1: Look for date + amount patterns
    date_amount_patterns = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Look for various date formats
        date_matches = re.findall(r'\b(\d{1,2}/\d{1,2}/?\d{0,4})\b', line)
        amount_matches = re.findall(r'\$?([\d,]+\.\d{2})', line)
        
        if date_matches and amount_matches:
            date_amount_patterns.append({
                'line': i+1,
                'text': line,
                'dates': date_matches,
                'amounts': amount_matches
            })
    
    print(f"📅 Found {len(date_amount_patterns)} lines with date+amount patterns:")
    for pattern in date_amount_patterns[:10]:  # Show first 10
        print(f"   Line {pattern['line']}: {pattern['text'][:80]}...")
    
    # Pattern 2: Look for transaction table sections
    print(f"\n📊 Looking for transaction table sections...")
    
    table_sections = []
    for i, line in enumerate(lines):
        if any(keyword in line.upper() for keyword in ['TRANSACTION', 'DEPOSIT', 'WITHDRAWAL', 'BALANCE']):
            # Show context around this line
            start = max(0, i-2)
            end = min(len(lines), i+3)
            context = '\n'.join(lines[start:end])
            table_sections.append({
                'line': i+1,
                'context': context
            })
    
    print(f"📊 Found {len(table_sections)} potential transaction table sections")
    
    # Pattern 3: Look for sequential amounts (might be balance columns)
    print(f"\n💰 Looking for amount sequences...")
    
    # Find lines with multiple amounts
    multi_amount_lines = []
    for i, line in enumerate(lines):
        amounts = re.findall(r'\$?([\d,]+\.\d{2})', line)
        if len(amounts) >= 2:
            multi_amount_lines.append({
                'line': i+1,
                'text': line,
                'amounts': amounts
            })
    
    print(f"💰 Found {len(multi_amount_lines)} lines with multiple amounts:")
    for pattern in multi_amount_lines[:10]:  # Show first 10
        print(f"   Line {pattern['line']}: {pattern['amounts']} -> {pattern['text'][:60]}...")
    
    # Pattern 4: Look for specific sections by page
    print(f"\n📄 Looking for page-specific patterns...")
    
    # Split by common page indicators
    page_splits = []
    current_page = 1
    page_content = []
    
    for line in lines:
        if 'PAGE' in line.upper() and any(x in line for x in ['OF', '1', '2', '3', '4', '5']):
            if page_content:
                page_splits.append({
                    'page': current_page,
                    'lines': len(page_content),
                    'content': '\n'.join(page_content)
                })
            page_content = []
            current_page += 1
        else:
            page_content.append(line)
    
    # Add the last page
    if page_content:
        page_splits.append({
            'page': current_page,
            'lines': len(page_content),
            'content': '\n'.join(page_content)
        })
    
    print(f"📄 Found {len(page_splits)} pages of content:")
    for page in page_splits:
        amounts_on_page = len(re.findall(r'\$?[\d,]+\.\d{2}', page['content']))
        dates_on_page = len(re.findall(r'\d{1,2}/\d{1,2}', page['content']))
        print(f"   Page {page['page']}: {page['lines']} lines, {dates_on_page} dates, {amounts_on_page} amounts")
        
        # Show a sample of this page
        print(f"   Sample: {page['content'][:100].replace(chr(10), ' ')}...")
    
    # Pattern 5: Look for check numbers or reference patterns
    print(f"\n🔢 Looking for check/reference patterns...")
    
    check_patterns = []
    for i, line in enumerate(lines):
        # Look for check numbers, reference numbers, etc.
        if re.search(r'\b(CHECK|CHK|REF|#)\s*\d+', line, re.IGNORECASE):
            check_patterns.append({
                'line': i+1,
                'text': line
            })
    
    print(f"🔢 Found {len(check_patterns)} lines with check/reference patterns")
    
    # Summary recommendations
    print(f"\n💡 ANALYSIS SUMMARY:")
    print(f"   📅 Date+Amount patterns: {len(date_amount_patterns)}")
    print(f"   📊 Table sections: {len(table_sections)}")
    print(f"   💰 Multi-amount lines: {len(multi_amount_lines)}")
    print(f"   📄 Pages found: {len(page_splits)}")
    print(f"   🔢 Check/ref patterns: {len(check_patterns)}")
    
    print(f"\n🎯 RECOMMENDATIONS TO FIND MISSING 24 TRANSACTIONS:")
    print(f"   1. Check multi-amount lines - these might contain running balances")
    print(f"   2. Look for transactions in different date formats")
    print(f"   3. Check for transactions spread across multiple pages")
    print(f"   4. Look for check transactions or other reference patterns")
    
    return {
        'date_amount_patterns': date_amount_patterns,
        'table_sections': table_sections,
        'multi_amount_lines': multi_amount_lines,
        'page_splits': page_splits,
        'check_patterns': check_patterns
    }

if __name__ == "__main__":
    results = analyze_patterns_for_missing_transactions()
