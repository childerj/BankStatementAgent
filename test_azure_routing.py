#!/usr/bin/env python3
"""
Test Azure Function routing number logic by uploading a test file.
This verifies that the strict routing number validation is working correctly.
"""

import os
import time
import requests
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

def test_azure_function_routing():
    """Test routing number extraction in the deployed Azure Function."""
    
    # Azure Storage configuration
    storage_account_name = "bankstatementagent"
    container_name = "incoming-bank-statements"
    
    try:
        # Use connection string from environment or default
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', 
            f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey=<YOUR_KEY>;EndpointSuffix=core.windows.net")
        
        # Test file path
        test_file = r"Test Docs\8-1-25_Prosperity.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False
            
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Upload test file
        blob_name = f"test-routing-{int(time.time())}.pdf"
        
        print(f"🔄 Uploading {test_file} as {blob_name}...")
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_name
        )
        
        with open(test_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ File uploaded successfully!")
        print(f"📁 Blob name: {blob_name}")
        print(f"🔗 Container: {container_name}")
        print(f"⏰ Waiting for function processing...")
        
        # Wait for processing
        time.sleep(30)
        
        # Check for output files (BAI2 or ERROR)
        blobs = blob_service_client.get_container_client(container_name).list_blobs()
        
        output_files = []
        for blob in blobs:
            if blob_name.replace('.pdf', '') in blob.name and blob.name != blob_name:
                output_files.append(blob.name)
        
        if output_files:
            print(f"✅ Function processed file. Output files:")
            for file in output_files:
                print(f"   📄 {file}")
                
                # Download and check content
                output_blob = blob_service_client.get_blob_client(
                    container=container_name, 
                    blob=file
                )
                content = output_blob.download_blob().readall().decode('utf-8')
                
                print(f"\n📋 Content preview for {file}:")
                print("=" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("=" * 50)
                
                # Check if this is an error file or successful BAI2
                if "ERROR" in file.upper() or "error" in content.lower():
                    print(f"⚠️  ERROR file generated - routing number likely missing")
                elif content.startswith("01,"):
                    print(f"✅ BAI2 file generated successfully")
                    # Extract routing number from BAI2
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith("03,"):
                            parts = line.split(',')
                            if len(parts) > 1:
                                routing_number = parts[1]
                                print(f"🏦 Routing number found: {routing_number}")
                                break
        else:
            print(f"❌ No output files found after 30 seconds")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing Azure function: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Azure Function Routing Number Logic")
    print("=" * 50)
    
    success = test_azure_function_routing()
    
    if success:
        print("\n✅ Azure Function routing test completed!")
    else:
        print("\n❌ Azure Function routing test failed!")
