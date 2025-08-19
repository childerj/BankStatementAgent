#!/usr/bin/env python3

import os
from azure.storage.blob import BlobServiceClient

def main():
    # Read connection string from local.settings.json
    import json
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            connection_string = settings['Values']['AzureWebJobsStorage']
    except Exception as e:
        print(f"Error reading local.settings.json: {e}")
        return

    # Create blob service client
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    
    # Upload test file
    test_file = "Test Docs/test-upload.pdf"
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    container_name = "bank-reconciliation"
    blob_name = "incoming-bank-statements/test-upload.pdf"
    
    try:
        # Get container client
        container_client = blob_service.get_container_client(container_name)
        
        # Upload file
        with open(test_file, "rb") as data:
            blob_client = container_client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True
            )
        
        print(f"✅ Successfully uploaded {test_file} to {container_name}/{blob_name}")
        print("🔄 Function should trigger automatically...")
        
    except Exception as e:
        print(f"❌ Error uploading file: {e}")

if __name__ == "__main__":
    main()
