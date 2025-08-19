#!/usr/bin/env python3
"""
Upload a test file with unique timestamp to trigger processing and debug bank name extraction
"""

from azure.storage.blob import BlobServiceClient
import os
from datetime import datetime
import time

def upload_debug_test():
    """Upload test file with unique name for debugging"""
    print("🔍 Uploading test file for bank name debugging...")
    
    try:
        # Azure Storage connection
        connection_string = "DefaultEndpointsProtocol=https;AccountName=waazuse1aistorage;AccountKey=FvdaW3gMjF2s9uTu4KGp+wD39Wq4T8g19NTvJ8QsKbJHXp1BSGLrLZFfFTpELCDZC5U4v7LRjNxH+AStZqjBAA==;EndpointSuffix=core.windows.net"
        
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"debug-bank-name-{timestamp}.pdf"
        
        # Upload the test file
        source_file = "Test Docs/8-1-25_Prosperity.pdf"
        blob_path = f"incoming-bank-statements/{unique_filename}"
        
        print(f"📤 Uploading {source_file} as {blob_path}...")
        
        with open(source_file, 'rb') as data:
            blob_client = blob_service.get_blob_client(
                container="bank-reconciliation", 
                blob=blob_path
            )
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ File uploaded successfully!")
        print(f"🔍 Waiting 30 seconds for processing...")
        
        time.sleep(30)
        
        # Check for output
        print("\n📁 Checking for processing results...")
        container_client = blob_service.get_container_client("bank-reconciliation")
        
        bai_found = False
        for blob in container_client.list_blobs(name_starts_with="bai2-outputs/"):
            if unique_filename.replace('.pdf', '') in blob.name:
                print(f"✅ Found BAI2 output: {blob.name}")
                bai_found = True
                break
        
        if not bai_found:
            print("❌ No BAI2 output found - check Azure Function logs")
        
        print(f"\n🎯 Test file uploaded: {unique_filename}")
        print("Check Azure Function logs for detailed bank name extraction debugging")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    upload_debug_test()
