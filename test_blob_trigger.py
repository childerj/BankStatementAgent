#!/usr/bin/env python3
"""
Test script to upload a file to blob storage and trigger the function
"""
import os
import json
from azure.storage.blob import BlobServiceClient

def load_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('Values', {})
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}

def main():
    print("🔧 Loading local settings...")
    settings = load_settings()
    
    # Get connection string
    connection_string = settings.get('AzureWebJobsStorage')
    if not connection_string:
        print("❌ AzureWebJobsStorage not found in local.settings.json")
        return
    
    print("✅ Loaded settings from local.settings.json")
    
    try:
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Upload test file
        container_name = "bank-reconciliation"
        blob_name = "incoming-bank-statements/test-upload.pdf"
        
        # Use existing test file
        test_file_path = "test-trigger.pdf"
        if not os.path.exists(test_file_path):
            test_file_path = "Test Docs/8-1-25_Prosperity.pdf"
        
        if not os.path.exists(test_file_path):
            print(f"❌ Test file not found: {test_file_path}")
            return
        
        print(f"📁 Uploading {test_file_path} to {container_name}/{blob_name}")
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Upload file
        with open(test_file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ Successfully uploaded blob: {blob_name}")
        print(f"🎯 This should trigger the process_new_file function!")
        
    except Exception as e:
        print(f"❌ Error uploading blob: {e}")

if __name__ == "__main__":
    main()
