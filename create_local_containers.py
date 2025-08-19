#!/usr/bin/env python3
"""
Create the required containers for local testing
"""

import json
from azure.storage.blob import BlobServiceClient

def create_containers():
    """Create required containers for local testing"""
    
    print("🏗️ Creating Local Containers for Testing")
    print("=" * 50)
    
    try:
        # Load Azure storage connection from local settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        print("📦 Setting up blob containers...")
        
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        
        containers_to_create = [
            "bank-reconciliation",
            "processed-statements"
        ]
        
        for container_name in containers_to_create:
            try:
                container_client = blob_service_client.get_container_client(container_name)
                
                if container_client.exists():
                    print(f"✅ Container '{container_name}' already exists")
                else:
                    container_client.create_container()
                    print(f"✅ Created container '{container_name}'")
                    
            except Exception as e:
                print(f"❌ Error with container '{container_name}': {e}")
        
        print("\n🎉 Container setup complete!")
        
    except Exception as e:
        print(f"❌ Error during container creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_containers()
