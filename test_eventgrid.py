#!/usr/bin/env python
"""
Test script to upload a file with a unique name to test EventGrid.
"""
import os
import shutil
import json
import time
from azure.storage.blob import BlobServiceClient
from pathlib import Path

def test_eventgrid():
    """Upload a test file with timestamp to trigger EventGrid."""
    
    # Load configuration from local.settings.json
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            values = settings.get('Values', {})
            for key, value in values.items():
                os.environ[key] = value
    except FileNotFoundError:
        print("❌ local.settings.json not found")
        return
    
    # Use real Azure storage connection string 
    connection_string = os.environ.get('AzureWebJobsStorage')
    if not connection_string:
        print("❌ AzureWebJobsStorage environment variable not set")
        return
    
    # Get the first PDF file from Test Docs
    test_docs_path = Path(r"C:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs")
    
    if not test_docs_path.exists():
        print(f"❌ Test Docs directory not found: {test_docs_path}")
        return
    
    pdf_files = list(test_docs_path.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in Test Docs directory")
        return
    
    test_file = pdf_files[0]
    
    # Create a unique filename with timestamp
    timestamp = int(time.time())
    unique_filename = f"eventgrid-test-{timestamp}.pdf"
    
    try:
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        print(f"📄 Using test file: {test_file.name}")
        print(f"📤 Uploading {unique_filename} to bank-reconciliation/incoming-bank-statements...")
        
        # Upload to the incoming-bank-statements folder
        blob_client = blob_service_client.get_blob_client(
            container="bank-reconciliation",
            blob=f"incoming-bank-statements/{unique_filename}"
        )
        
        with open(test_file, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ Successfully uploaded {unique_filename}")
        print(f"🔍 Check EventGrid logs and function execution...")
        print(f"🕒 Timestamp: {timestamp}")
        
        # Also print the full path for verification
        print(f"📍 Full path: bank-reconciliation/incoming-bank-statements/{unique_filename}")
        
    except Exception as e:
        print(f"❌ Error uploading file: {str(e)}")

if __name__ == "__main__":
    test_eventgrid()
