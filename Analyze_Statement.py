"""
Enhanced Document Intelligence Analysis with Detailed Error Logging
Analyze any PDF document to identify ERROR_UNKNOWN causes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
import re
import traceback
from datetime import datetime

def enhanced_error_analysis(error_message, exception_obj=None):
    """Enhanced error analysis to identify specific ERROR_UNKNOWN causes"""
    print("\n🚨 ENHANCED ERROR ANALYSIS")
    print("=" * 50)
    
    error_lower = error_message.lower()
    exception_type = type(exception_obj).__name__ if exception_obj else "Unknown"
    
    print(f"🔍 Exception Type: {exception_type}")
    print(f"🔍 Error Message: {error_message}")
    print("")
    
    # Classify the error using the same logic as function_app.py
    if "document intelligence" in error_lower or "docintelligence" in error_lower:
        error_code = "ERROR_DOC_INTEL_FAILED"
        print("🎯 Classification: Document Intelligence Failure")
        print("💡 Likely causes:")
        print("   • Azure AI Document Intelligence service unavailable")
        print("   • API key incorrect or expired")
        print("   • PDF format not supported")
        print("   • Service rate limiting")
        
    elif "openai" in error_lower or "parsing" in error_lower:
        error_code = "ERROR_PARSING_FAILED" 
        print("🎯 Classification: OpenAI/Parsing Failure")
        print("💡 Likely causes:")
        print("   • OpenAI API unavailable or rate limited")
        print("   • Invalid API key")
        print("   • Model not available")
        
    elif "connection" in error_lower or "network" in error_lower:
        error_code = "ERROR_NETWORK_FAILED"
        print("🎯 Classification: Network/Connection Failure")
        print("💡 Likely causes:")
        print("   • Internet connectivity issues")
        print("   • Azure service endpoints unreachable")
        print("   • Firewall blocking requests")
        
    elif "timeout" in error_lower or exception_type in ["TimeoutError", "TimeoutException"]:
        error_code = "ERROR_TIMEOUT"
        print("🎯 Classification: Timeout Error")
        print("💡 Likely causes:")
        print("   • PDF too large or complex")
        print("   • Service overloaded")
        print("   • Network latency issues")
        
    elif exception_type in ["KeyError", "IndexError", "AttributeError"]:
        error_code = "ERROR_DATA_FORMAT"
        print("🎯 Classification: Data Format Error")
        print("💡 Likely causes:")
        print("   • Unexpected PDF structure")
        print("   • Missing expected data fields")
        print("   • API response format changed")
        
    elif exception_type in ["MemoryError"]:
        error_code = "ERROR_MEMORY_EXCEEDED"
        print("🎯 Classification: Memory Error")
        print("💡 Likely causes:")
        print("   • PDF file too large")
        print("   • Insufficient system memory")
        print("   • Memory leak in processing")
        
    elif "rate limit" in error_lower or "429" in error_lower:
        error_code = "ERROR_RATE_LIMITED"
        print("🎯 Classification: Rate Limiting")
        print("💡 Likely causes:")
        print("   • Too many API requests")
        print("   • Exceeded quota limits")
        print("   • Need to implement better throttling")
        
    elif "401" in error_lower or "403" in error_lower or "authentication" in error_lower:
        error_code = "ERROR_AUTH_FAILED"
        print("🎯 Classification: Authentication Error")
        print("💡 Likely causes:")
        print("   • Invalid API keys")
        print("   • Expired credentials")
        print("   • Insufficient permissions")
        
    else:
        error_code = "ERROR_UNKNOWN"
        print("🎯 Classification: Unknown Error")
        print("💡 This is the problematic case we're trying to solve!")
        print("💡 Possible causes:")
        print("   • Unexpected exception type")
        print("   • New error condition not handled")
        print("   • Python runtime error")
        print("   • Azure SDK changes")
    
    print(f"\n🏷️  ERROR CODE: {error_code}")
    
    if exception_obj:
        print(f"\n📋 FULL TRACEBACK:")
        print("-" * 30)
        tb_lines = traceback.format_exception(type(exception_obj), exception_obj, exception_obj.__traceback__)
        for line in tb_lines:
            print(line.rstrip())
    
    return error_code

def analyze_document_with_logging(pdf_filename=None):
    """Analyze PDF document with enhanced error logging"""
    
    # Get input filename from command line or use default
    if pdf_filename is None:
        if len(sys.argv) > 1:
            pdf_filename = sys.argv[1]
        else:
            pdf_filename = "410.pdf"  # Default to 410.pdf
    
    print(f"🔍 ENHANCED DOCUMENT ANALYSIS WITH ERROR LOGGING")
    print("=" * 60)
    print(f"📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📄 Target File: {pdf_filename}")
    print("")
    # Load environment variables
    try:
        from function_app import load_local_settings
        load_local_settings()
        print("✅ Environment variables loaded")
    except Exception as e:
        print(f"⚠️ Could not load environment variables: {e}")
        print("⚠️ Continuing with system environment variables...")
    
    # Get Document Intelligence credentials
    doc_intel_endpoint = os.environ.get("DOCINTELLIGENCE_ENDPOINT")
    doc_intel_key = os.environ.get("DOCINTELLIGENCE_KEY")
    
    if not doc_intel_endpoint or not doc_intel_key:
        error_msg = "Document Intelligence credentials not found in environment variables"
        print(f"❌ {error_msg}")
        enhanced_error_analysis(error_msg)
        return
    
    print("✅ Document Intelligence credentials loaded")
    print(f"📡 Endpoint: {doc_intel_endpoint[:50]}...")
    print("")
    
    # Look for PDF file in multiple locations
    possible_paths = [
        pdf_filename,  # Current directory
        f"Test Docs/{pdf_filename}",  # Test Docs folder
        f"New Test Docs/{pdf_filename}",  # New Test Docs folder
        f"c:/Users/jeff.childers/Documents/Bank Statement Reconciliation/Test Docs/{pdf_filename}",
        f"c:/Users/jeff.childers/Documents/Bank Statement Reconciliation/New Test Docs/{pdf_filename}",
    ]
    
    pdf_path = None
    for path in possible_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        error_msg = f"File not found: {pdf_filename}. Searched locations: {possible_paths}"
        print(f"❌ {error_msg}")
        enhanced_error_analysis(error_msg)
        return
    
    print(f"📄 Found file: {pdf_path}")
    
    try:
        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
        
        print(f"📊 File size: {len(file_bytes):,} bytes")
        
        if len(file_bytes) == 0:
            error_msg = f"File is empty: {pdf_path}"
            print(f"❌ {error_msg}")
            enhanced_error_analysis(error_msg)
            return
            
        print("✅ File loaded successfully")
        print("")
        
    except Exception as e:
        error_msg = f"Failed to read file {pdf_path}: {str(e)}"
        print(f"❌ {error_msg}")
        enhanced_error_analysis(error_msg, e)
        return
    
    # Initialize Document Intelligence client
    try:
        client = DocumentIntelligenceClient(
            endpoint=doc_intel_endpoint,
            credential=AzureKeyCredential(doc_intel_key)
        )
        print("✅ Document Intelligence client initialized")
        print("")
    except Exception as e:
        error_msg = f"Failed to initialize Document Intelligence client: {str(e)}"
        print(f"❌ {error_msg}")
        enhanced_error_analysis(error_msg, e)
        return
    
    try:
        # Analyze with bankStatement model
        print("🔍 ANALYZING WITH DOCUMENT INTELLIGENCE")
        print("=" * 50)
        print("📋 Model: prebuilt-bankStatement.us")
        print("⏳ Starting analysis...")
        
        poller = client.begin_analyze_document(
            "prebuilt-bankStatement.us",
            BytesIO(file_bytes),
            content_type="application/pdf"
        )
        
        print("⏳ Waiting for analysis to complete...")
        result = poller.result()
        
        if result:
            print("✅ Analysis completed successfully!")
            
            # Extract all fields with focus on account numbers
            print("\n📋 EXTRACTED FIELDS:")
            print("=" * 50)
            
            field_count = 0
            account_fields = []
            if result.documents:
                doc = result.documents[0]
                if hasattr(doc, 'fields') and doc.fields:
                    for field_name, field_data in doc.fields.items():
                        field_count += 1
                        if hasattr(field_data, 'content') and field_data.content:
                            confidence = getattr(field_data, 'confidence', 0.0)
                            print(f"Field: {field_name}")
                            print(f"Content: '{field_data.content}'")
                            print(f"Confidence: {confidence:.2%}")
                            
                            # Check if this looks like an account number
                            if 'account' in field_name.lower() or re.search(r'\b\d{4,}\b', field_data.content):
                                account_fields.append((field_name, field_data.content, confidence))
                            
                            print("-" * 30)
                        else:
                            print(f"Field: {field_name} (no content)")
                            print("-" * 30)
            
            print(f"📊 Total fields extracted: {field_count}")
            
            # Highlight potential account number fields
            if account_fields:
                print("\n🏦 POTENTIAL ACCOUNT NUMBER FIELDS:")
                print("=" * 50)
                for field_name, content, confidence in account_fields:
                    print(f"Field: {field_name}")
                    print(f"Content: '{content}'")
                    print(f"Confidence: {confidence:.2%}")
                    print("-" * 30)
            else:
                print("\n⚠️ NO ACCOUNT NUMBER FIELDS FOUND")
                print("This could explain why ERROR_UNKNOWN occurs!")
                print("")
            
            # Extract OCR text and search for account patterns
            print("\n📝 OCR TEXT ANALYSIS - SEARCHING FOR ACCOUNT NUMBERS:")
            print("=" * 50)
            
            if result.content:
                lines = result.content.split('\n')
                print(f"Total lines extracted: {len(lines)}")
                
                # Search for account-related content
                print("\n🔍 Searching for account number patterns...")
                account_patterns = [
                    r'account\s*(?:number|no\.?|#)?\s*:?\s*(\d+)',
                    r'acct\s*(?:number|no\.?|#)?\s*:?\s*(\d+)',
                    r'ending\s+(\d+)',
                    r'xxxx\s*(\d+)',
                    r'\*{4}\s*(\d+)',
                    r'\b\d{4,}\b',  # Any sequence of 4+ digits
                ]
                
                found_accounts = []
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    if any(keyword in line_lower for keyword in ['account', 'acct', 'ending']):
                        print(f"Line {i+1}: {line}")
                        
                        # Try to extract account numbers from this line
                        for pattern in account_patterns:
                            matches = re.finditer(pattern, line_lower)
                            for match in matches:
                                if match.groups():
                                    account_num = match.group(1)
                                else:
                                    account_num = match.group(0)
                                
                                if len(account_num) >= 4:  # Only consider 4+ digit numbers
                                    found_accounts.append((account_num, line, pattern))
                                    print(f"  → Found account pattern: '{account_num}' using pattern: {pattern}")
                
                print(f"\n📊 Found {len(found_accounts)} potential account numbers:")
                for account_num, source_line, pattern in found_accounts:
                    print(f"  • '{account_num}' from: '{source_line.strip()}'")
                
                if len(found_accounts) == 0:
                    print("⚠️ NO ACCOUNT NUMBERS FOUND IN OCR TEXT")
                    print("This is likely why the system generates ERROR_UNKNOWN!")
                    print("")
                
                # Also search for partial account patterns like "Ending 0327"
                print("\n🔍 Searching for partial account patterns...")
                partial_patterns = [
                    r'ending\s+(\d{4})',
                    r'last\s+four\s+(\d{4})',
                    r'xxxx\s*(\d{4})',
                    r'\*{4}\s*(\d{4})',
                ]
                
                found_partials = []
                for i, line in enumerate(lines):
                    line_lower = line.lower().strip()
                    for pattern in partial_patterns:
                        matches = re.finditer(pattern, line_lower)
                        for match in matches:
                            partial_num = match.group(1)
                            found_partials.append((partial_num, line, pattern))
                            print(f"Line {i+1}: {line}")
                            print(f"  → Found partial account: '{partial_num}' using pattern: {pattern}")
                
                print(f"\n📊 Found {len(found_partials)} potential partial account numbers:")
                for partial_num, source_line, pattern in found_partials:
                    print(f"  • '{partial_num}' from: '{source_line.strip()}'")
                
                # Show first 20 lines of OCR text for manual inspection
                print(f"\n📝 FIRST 20 LINES OF OCR TEXT:")
                print("=" * 50)
                for i, line in enumerate(lines[:20]):
                    print(f"{i+1:2d}: {line}")
                
                # Show lines containing numbers for pattern analysis
                print(f"\n🔢 LINES CONTAINING NUMBERS:")
                print("=" * 50)
                number_lines = []
                for i, line in enumerate(lines):
                    if re.search(r'\d', line):
                        number_lines.append((i+1, line))
                
                # Show first 30 lines with numbers
                for line_num, line in number_lines[:30]:
                    print(f"{line_num:2d}: {line}")
                    
                if len(number_lines) > 30:
                    print(f"... and {len(number_lines) - 30} more lines with numbers")
            else:
                print("❌ NO OCR CONTENT EXTRACTED")
                print("This could be why ERROR_UNKNOWN occurs!")
        
        else:
            error_msg = "No analysis result returned from Document Intelligence"
            print(f"❌ {error_msg}")
            enhanced_error_analysis(error_msg)
            
        print("\n✅ ANALYSIS COMPLETE")
        print("=" * 50)
    
    except Exception as e:
        error_msg = f"Error during Document Intelligence analysis: {str(e)}"
        print(f"❌ {error_msg}")
        enhanced_error_analysis(error_msg, e)

def main():
    """Main function to run document analysis"""
    print("🚨 BANK STATEMENT AGENT - ERROR UNKNOWN DIAGNOSTIC")
    print("=" * 60)
    
    # Get filename from command line or use default
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "410.pdf"
    
    print(f"📄 Analyzing: {filename}")
    print("")
    
    # Run the enhanced analysis
    analyze_document_with_logging(filename)

if __name__ == "__main__":
    main()
