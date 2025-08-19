#!/usr/bin/env python3
"""
Upload a test PDF to trigger Azure Function processing with interactive console output
"""

from azure.storage.blob import BlobServiceClient
import os

def upload_test_file():
    """Upload a test PDF to trigger the processing"""
    print("🚀 UPLOADING TEST FILE TO TRIGGER PROCESSING")
    print("=" * 50)
    
    # Connect to storage
    storage_connection = 'YOUR_STORAGE_CONNECTION_STRING_HERE'
    blob_service = BlobServiceClient.from_connection_string(storage_connection)
    
    test_file = '811.pdf'
    test_path = f'Test Docs/{test_file}'
    
    if os.path.exists(test_path):
        print(f"📄 Found test file: {test_file}")
        print(f"📊 File size: {os.path.getsize(test_path):,} bytes")
        
        with open(test_path, 'rb') as data:
            blob_client = blob_service.get_blob_client(
                container='bank-reconciliation', 
                blob=f'incoming-bank-statements/{test_file}'
            )
            blob_client.upload_blob(data, overwrite=True)
            print(f"✅ Successfully uploaded {test_file}")
            print("")
            print("🎯 Azure Function should now be processing the file!")
            print("👀 Watch the Azure Functions terminal for:")
            print("   • Step-by-step processing narrative")
            print("   • Detailed field extraction results")
            print("   • Interactive ENTER prompt to continue")
            print("   • Complete processing summary")
            print("")
            print("⌨️  The function will pause and wait for you to press ENTER")
            print("🔴 You can press Ctrl+C to cancel processing")
    else:
        print(f"❌ File not found: {test_path}")

if __name__ == "__main__":
    upload_test_file()
