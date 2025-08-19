#!/usr/bin/env python3
"""Test script to upload a file and verify the AI extraction fix"""

import os
import requests
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

def test_azure_upload():
    """Upload a test file to Azure and verify processing"""
    
    # Get configuration
    storage_account = os.getenv('STORAGE_ACCOUNT_NAME')
    
    if not storage_account:
        print("❌ Missing STORAGE_ACCOUNT_NAME environment variable")
        return
    
    # Create blob service client
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account}.blob.core.windows.net",
        credential=DefaultAzureCredential()
    )
    
    # Test file path
    test_file = r"c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\test-upload.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    # Upload file
    container_name = "bank-reconciliation"
    blob_name = f"incoming-bank-statements/test-ai-fix-{os.path.basename(test_file)}"
    
    print(f"🔼 Uploading {test_file} to {container_name}/{blob_name}")
    
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        with open(test_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ Upload successful!")
        print(f"📁 File location: {container_name}/{blob_name}")
        print("⏳ Function should trigger within 1-3 minutes...")
        print("📊 Check Application Insights for logs")
        
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")

if __name__ == "__main__":
    test_azure_upload()
