#!/usr/bin/env python3
"""Test the deployed Azure Function with a bank statement"""

import os
from azure.storage.blob import BlobServiceClient
import time

def test_azure_function():
    """Upload a test file to Azure storage to trigger the function"""
    
    print("🚀 TESTING DEPLOYED AZURE FUNCTION")
    print("=" * 50)
    
    # Use Azure storage connection string
    connection_string = "DefaultEndpointsProtocol=https;AccountName=bankstatementagent;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net"
    
    try:
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = "incoming-bank-statements"
        
        # Use one of our test files
        test_file_path = "Test Docs/8-1-25_Prosperity.pdf"
        blob_name = f"test_deploy_{int(time.time())}.pdf"
        
        print(f"📤 Uploading {test_file_path} as {blob_name}")
        
        # Upload the file
        with open(test_file_path, "rb") as data:
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            blob_client.upload_blob(data, overwrite=True)
            
        print("✅ File uploaded successfully!")
        print(f"🔔 Azure Function should process this file automatically")
        print(f"📁 Check the 'processed' container for the BAI2 output")
        print(f"🔍 Check Azure Function logs for processing details")
        
    except Exception as e:
        print(f"❌ Error testing Azure Function: {e}")
        print("💡 Make sure to update the connection string with your actual Azure Storage key")

if __name__ == "__main__":
    test_azure_function()
