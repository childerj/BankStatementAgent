#!/usr/bin/env python
"""
Test script to upload a file to the incoming-bank-statements container to test the blob trigger.
"""
import os
import shutil
import json
from azure.storage.blob import BlobServiceClient
from pathlib import Path

def test_blob_trigger():
    """Upload a test file to trigger the blob function."""
    
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
    pdf_files = list(test_docs_path.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in Test Docs folder")
        return
    
    test_file = pdf_files[0]  # Use the first PDF file
    print(f"📄 Using test file: {test_file.name}")
    
    try:
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Upload the file
        blob_name = f"test-{test_file.name}"
        container_name = "bank-reconciliation"  # Updated to match our real container
        folder_name = "incoming-bank-statements"
        
        print(f"📤 Uploading {blob_name} to {container_name}/{folder_name}...")
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=f"{folder_name}/{blob_name}"
        )
        
        with open(test_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ Successfully uploaded {blob_name}")
        print(f"🔍 Watch the function logs for trigger activity...")
        
    except Exception as e:
        print(f"❌ Failed to upload file: {e}")

if __name__ == "__main__":
    test_blob_trigger()
