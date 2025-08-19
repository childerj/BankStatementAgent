#!/usr/bin/env python3
"""
Check what files are in the blob container
"""

import json
from azure.storage.blob import BlobServiceClient

def check_container_contents():
    """Check what's in the blob container"""
    
    print("📁 Checking Blob Container Contents")
    print("=" * 50)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        container_name = "bank-reconciliation"
        
        container_client = blob_service_client.get_container_client(container_name)
        
        if not container_client.exists():
            print(f"❌ Container '{container_name}' does not exist")
            return
        
        print(f"📦 Container: {container_name}")
        print()
        
        blobs = list(container_client.list_blobs())
        
        if not blobs:
            print("📁 Container is empty")
            return
        
        # Group by folder
        folders = {}
        for blob in blobs:
            folder = blob.name.split('/')[0] if '/' in blob.name else 'root'
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(blob)
        
        for folder, blob_list in folders.items():
            print(f"📁 {folder}/")
            for blob in sorted(blob_list, key=lambda x: x.last_modified, reverse=True):
                size_kb = blob.size / 1024 if blob.size else 0
                print(f"   📄 {blob.name} ({size_kb:.1f} KB, {blob.last_modified})")
            print()
        
        # Find recent files
        recent_bai2 = [b for b in blobs if b.name.endswith('.bai2') and 'prosperity' in b.name.lower()]
        recent_errors = [b for b in blobs if 'error' in b.name.lower() and 'prosperity' in b.name.lower()]
        
        print(f"🔍 Recent Prosperity files:")
        print(f"   BAI2: {len(recent_bai2)} files")
        print(f"   Errors: {len(recent_errors)} files")
        
        if recent_bai2:
            latest = sorted(recent_bai2, key=lambda x: x.last_modified, reverse=True)[0]
            print(f"   Most recent BAI2: {latest.name}")
            
            # Download and check
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=latest.name)
            content = blob_client.download_blob().readall().decode('utf-8')
            
            lines = content.split('\n')
            print(f"   Content: {len(lines)} lines")
            
            # Show file header
            for line in lines[:3]:
                if line.strip():
                    print(f"   {line}")
        
        if recent_errors:
            latest_error = sorted(recent_errors, key=lambda x: x.last_modified, reverse=True)[0]
            print(f"   Most recent error: {latest_error.name}")
            
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=latest_error.name)
            error_content = blob_client.download_blob().readall().decode('utf-8')
            print(f"   Error: {error_content[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_container_contents()
