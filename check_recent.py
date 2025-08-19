#!/usr/bin/env python3
"""
Check the most recent prosperity BAI file
"""

import json
from azure.storage.blob import BlobServiceClient

def check_recent_prosperity():
    """Check the most recent prosperity file"""
    
    print("🔍 Checking Most Recent Prosperity Processing")
    print("=" * 60)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        container_name = "bank-reconciliation"
        
        # Check the most recent prosperity file (the .bai file)
        blob_name = "bai2-outputs/test-prosperity-1755120036.bai"
        
        print(f"📄 Checking file: {blob_name}")
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        try:
            content = blob_client.download_blob().readall().decode('utf-8')
            print(f"✅ File downloaded, {len(content)} characters")
            
            lines = content.split('\n')
            print(f"📊 File contains {len(lines)} lines")
            
            if content.strip():
                print(f"\n📄 File Contents:")
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"   {i+1:2d}: {line}")
            else:
                print(f"❌ File is empty!")
                
                # This means it was an error case - check for error output
                print(f"\n🔍 Looking for error information...")
                
                # The file being empty likely means routing number extraction failed
                print(f"❌ This indicates routing number extraction failed")
                print(f"❌ Function created empty BAI file due to missing routing number")
                
        except Exception as e:
            print(f"❌ Could not read file: {e}")
        
        # Also check if there are any error logs we can find
        print(f"\n🔍 Checking for other recent files...")
        
        container_client = blob_service_client.get_container_client(container_name)
        blobs = list(container_client.list_blobs())
        
        # Look for any files with today's timestamp
        import datetime
        today = datetime.datetime.now().strftime('%Y%m%d')
        
        recent_files = [b for b in blobs if today in b.name or 'prosperity' in b.name.lower()]
        recent_files.sort(key=lambda x: x.last_modified, reverse=True)
        
        print(f"📁 Recent files (last 5):")
        for blob in recent_files[:5]:
            print(f"   📄 {blob.name} ({blob.last_modified})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_recent_prosperity()
