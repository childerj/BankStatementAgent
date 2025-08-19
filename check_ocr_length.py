"""
Check OCR text length for the 5-page PDF
"""
import os
import json
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

def check_ocr_length():
    """Check how much OCR text we get from the 5-page PDF"""
    
    # Test file
    test_file = r'c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\822-847-896.pdf'
    
    print("🔍 CHECKING OCR TEXT LENGTH")
    print("=" * 50)
    
    # Extract OCR data
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
        
        print(f"📊 Total OCR text length: {len(ocr_text):,} characters")
        print(f"📊 Total OCR text words: {len(ocr_text.split()):,} words")
        print(f"📊 OCR text lines: {len(ocr_text.split(chr(10))):,} lines")
        
        # Show first 500 characters
        print("\n📄 First 500 characters:")
        print("-" * 50)
        print(ocr_text[:500])
        
        # Show last 500 characters  
        print("\n📄 Last 500 characters:")
        print("-" * 50)
        print(ocr_text[-500:])
        
        # Look for transaction patterns
        import re
        
        # Look for date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
            r'\d{1,2}/\d{1,2}',          # MM/DD
        ]
        
        total_dates = 0
        for pattern in date_patterns:
            dates = re.findall(pattern, ocr_text)
            total_dates += len(dates)
            print(f"📅 Found {len(dates)} dates matching pattern: {pattern}")
        
        print(f"📅 Total date matches: {total_dates}")
        
        # Look for amount patterns
        amount_patterns = [
            r'\$[\d,]+\.\d{2}',          # $1,234.56
            r'[\d,]+\.\d{2}',            # 1,234.56
            r'-\$[\d,]+\.\d{2}',         # -$1,234.56
        ]
        
        total_amounts = 0
        for pattern in amount_patterns:
            amounts = re.findall(pattern, ocr_text)
            total_amounts += len(amounts)
            print(f"💰 Found {len(amounts)} amounts matching pattern: {pattern}")
        
        print(f"💰 Total amount matches: {total_amounts}")
        
        return True
    else:
        print("❌ Failed to extract OCR text")
        return False

if __name__ == "__main__":
    check_ocr_length()
