#!/usr/bin/env python3
import requests
import time
import json

def test_problematic_pdf():
    """Test the CBoKActivity (5).pdf that's showing 5594 instead of *5594"""
    
    print("🧪 TESTING PROBLEMATIC PDF")
    print("=" * 60)
    
    # Path to the problematic PDF
    pdf_path = r"C:\Users\jeff.childers\Downloads\CBoKActivity (5).pdf"
    
    try:
        # Check if file exists
        with open(pdf_path, 'rb') as f:
            file_content = f.read()
        
        print(f"📄 File: {pdf_path}")
        print(f"📊 Size: {len(file_content)} bytes")
        
        # Upload to Azure storage
        blob_url = "https://bankstatementagentc93d.blob.core.windows.net/incoming-bank-statements/CBoKActivity-5-test.pdf"
        
        # Upload with SAS token (you'll need to get this from Azure)
        print("📤 Uploading to Azure Blob Storage...")
        print("⚠️  Note: You'll need to manually upload this via Azure Portal or provide SAS token")
        print(f"   Target: {blob_url}")
        
        # Instead, let's check the Azure Function logs
        print("\n🔍 Checking Azure Function logs...")
        print("You should:")
        print("1. Upload the PDF manually to the incoming-bank-statements container")
        print("2. Check the Azure Function logs to see the enhanced logging output")
        print("3. Look for messages starting with '🔍' to trace account number extraction")
        
        print("\n📋 Expected Log Sequence:")
        print("  🔍 Extracting account number...")
        print("  🔍 Raw account from parsed data: '...' (or this step might be skipped)")
        print("  🔍 Searching OCR text for account number...")
        print("  🔍 Checking X raw fields for account number...")
        print("  🔍 Field 'field_name': 'content'")
        print("  🔍 After cleaning: '...'")
        print("  ❌ or ✅ Found account number...")
        
        print("\n🎯 What to Look For:")
        print("  - Does Document Intelligence extract '*5594' or '5594'?")
        print("  - Which field contains the account number?")
        print("  - Is the asterisk present in the raw field content?")
        print("  - At what point does the asterisk disappear?")
        
    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
        print("Please download the CBoKActivity (5).pdf file first")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_problematic_pdf()
