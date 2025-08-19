#!/usr/bin/env python3
"""
Test script to check if Azure Storage container and folder structure exist.
"""
import os
from azure.storage.blob import BlobServiceClient

def main():
    try:
        # Get connection string from environment
        storage_connection = os.environ.get("AzureWebJobsStorage")
        if not storage_connection:
            print("❌ AzureWebJobsStorage environment variable not set")
            print("Please set it in your local.settings.json file")
            return
        
        # Connect to blob service
        blob_service = BlobServiceClient.from_connection_string(storage_connection)
        
        container_name = "bank-reconciliation"
        required_folders = ["incoming-bank-statements", "bai2-outputs", "archive"]
        
        print("🔍 Checking Azure Storage container and folder structure...")
        print(f"Storage Account: {blob_service.account_name}")
        
        # Check if main container exists
        try:
            containers = blob_service.list_containers()
            existing_containers = [c.name for c in containers]
            
            if container_name not in existing_containers:
                print(f"❌ Container '{container_name}' does not exist")
                return
            else:
                print(f"✅ Container '{container_name}' exists")
        except Exception as e:
            print(f"❌ Error listing containers: {e}")
            return
        
        # Check folder structure
        container_client = blob_service.get_container_client(container_name)
        
        for folder in required_folders:
            try:
                blobs = list(container_client.list_blobs(name_starts_with=f"{folder}/"))
                if blobs:
                    print(f"✅ Folder '{folder}' exists with {len(blobs)} items")
                else:
                    print(f"⚠️  Folder '{folder}' is empty (will be created when first file is uploaded)")
            except Exception as e:
                print(f"❌ Error checking folder '{folder}': {e}")
        
        print(f"\n📂 Current structure in '{container_name}':")
        try:
            all_blobs = container_client.list_blobs()
            for blob in all_blobs:
                print(f"   📄 {blob.name}")
        except Exception as e:
            print(f"❌ Error listing blobs: {e}")
        
        print("\n🎉 Setup verification complete!")
        print(f"You can now upload PDF files to '{container_name}/incoming-bank-statements/' folder")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
