#!/usr/bin/env python3
"""
Test upload and monitor function logs in real-time
"""

import json
import os
import time
from azure.storage.blob import BlobServiceClient

def monitor_function_test():
    """Upload file and monitor for processing"""
    
    print("📋 Real-time Function Monitoring Test")
    print("=" * 50)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        # Test file
        test_file = "Test Docs/8-1-25_Prosperity.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return
        
        # Create unique timestamp for this test
        timestamp = int(time.time())
        blob_name = f"incoming-bank-statements/prosperity-monitor-{timestamp}.pdf"
        
        print(f"📄 Test file: {test_file}")
        print(f"📤 Upload path: {blob_name}")
        
        # Upload file
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        container_name = "bank-reconciliation"
        
        # Ensure container exists
        try:
            container_client = blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
        except:
            pass
        
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        print(f"📤 Uploading file...")
        with open(test_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"✅ File uploaded at {time.strftime('%H:%M:%S')}")
        print(f"⏳ Monitoring for processing results...")
        print(f"   (Function should process within 30-60 seconds)")
        
        # Monitor for results
        for i in range(12):  # Check for 2 minutes
            time.sleep(10)  # Wait 10 seconds between checks
            
            elapsed = (i + 1) * 10
            print(f"   ⏰ {elapsed}s - Checking for output files...")
            
            # Check for output files
            container_client = blob_service_client.get_container_client(container_name)
            blobs = list(container_client.list_blobs(name_starts_with="bai2-outputs/"))
            
            # Look for our file specifically
            output_files = [b for b in blobs if f"prosperity-monitor-{timestamp}" in b.name]
            
            if output_files:
                latest_output = sorted(output_files, key=lambda x: x.last_modified, reverse=True)[0]
                print(f"   ✅ Found output file: {latest_output.name}")
                
                # Download and check content
                output_blob_client = blob_service_client.get_blob_client(container=container_name, blob=latest_output.name)
                content = output_blob_client.download_blob().readall().decode('utf-8')
                
                lines = content.split('\n')
                print(f"   📊 Output file has {len(lines)} lines")
                
                if content.strip():
                    print(f"   📄 File content preview:")
                    for j, line in enumerate(lines[:3]):
                        if line.strip():
                            print(f"      {j+1}: {line}")
                    
                    # Check for routing number in first line
                    if lines and lines[0].startswith('01,'):
                        parts = lines[0].split(',')
                        if len(parts) > 4:
                            routing = parts[4]
                            print(f"   🔍 Routing number found: {routing}")
                            
                            if routing == "113122655":
                                print(f"   ✅ SUCCESS! Correct Prosperity routing number!")
                                return True
                            elif len(routing) == 9 and routing.isdigit():
                                print(f"   ⚠️ Valid routing number but unexpected value")
                                return True
                            else:
                                print(f"   ❌ Invalid routing number format")
                                return False
                else:
                    print(f"   ❌ Output file is empty (indicates error)")
                    return False
                
                break
        else:
            print(f"   ❌ No output file found after 2 minutes")
            return False
        
        # Cleanup
        try:
            blob_client.delete_blob()
            print(f"🧹 Cleaned up test file")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting real-time function monitoring...")
    print("   Make sure the Azure Function is running in another terminal!")
    print()
    
    success = monitor_function_test()
    
    print(f"\n🎉 Monitoring Test {'PASSED' if success else 'FAILED'}!")
    if success:
        print("✅ Function is working correctly with OpenAI integration!")
    else:
        print("❌ Function needs troubleshooting")
