#!/usr/bin/env python
"""
Test script to upload a file using direct HTTP PUT request.
"""
import requests
from pathlib import Path

def test_blob_upload():
    """Upload a test file using direct HTTP request."""
    
    # Get the first PDF file from Test Docs
    test_docs_path = Path(r"C:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs")
    pdf_files = list(test_docs_path.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in Test Docs folder")
        return
    
    test_file = pdf_files[0]  # Use the first PDF file
    print(f"📄 Using test file: {test_file.name}")
    
    # Upload the file using simple PUT request
    blob_name = f"test{test_file.stem}.pdf"
    container_name = "incoming-bank-statements"
    url = f"http://127.0.0.1:10000/devstoreaccount1/{container_name}/{blob_name}"
    
    print(f"📤 Uploading {blob_name} to {container_name} container...")
    print(f"🔗 URL: {url}")
    
    headers = {
        'x-ms-blob-type': 'BlockBlob',
        'x-ms-version': '2020-10-02',
        'Content-Type': 'application/octet-stream'
    }
    
    try:
        with open(test_file, 'rb') as data:
            response = requests.put(url, data=data, headers=headers)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully uploaded {blob_name}")
            print(f"🔍 Watch the function logs for trigger activity...")
        else:
            print(f"❌ Failed to upload file. Status: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Failed to upload file: {e}")

if __name__ == "__main__":
    test_blob_upload()
