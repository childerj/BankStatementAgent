#!/usr/bin/env python3
"""
Test actual Prosperity Bank PDF routing number extraction
"""

import json
import os
import time
from azure.storage.blob import BlobServiceClient

def test_prosperity_pdf():
    """Test with actual Prosperity Bank PDF"""
    
    print("🏦 Testing Prosperity Bank PDF Routing Extraction")
    print("=" * 60)
    
    try:
        # Load settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        # Test file
        test_file = "Test Docs/8-1-25_Prosperity.pdf"
        
        if not os.path.exists(test_file):
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"📄 Testing with: {test_file}")
        
        # Create blob client and upload
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        container_name = "bank-reconciliation"
        blob_name = f"incoming-bank-statements/test-prosperity-{int(time.time())}.pdf"
        
        print(f"📤 Uploading to: {container_name}/{blob_name}")
        
        # Ensure container exists
        try:
            container_client = blob_service_client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"✅ Created container: {container_name}")
        except:
            pass
        
        # Upload file
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        
        with open(test_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print("✅ File uploaded successfully!")
        print("⏳ Waiting for Azure Function processing...")
        
        # Wait for processing
        time.sleep(45)  # Give it time to process
        
        # Check for results
        print("\n📊 Checking for Results")
        print("-" * 30)
        
        container_client = blob_service_client.get_container_client(container_name)
        blobs = list(container_client.list_blobs())
        
        bai2_files = []
        error_files = []
        
        for blob in blobs:
            if blob.name.startswith('bai2-outputs/') and blob.name.endswith('.bai2'):
                if 'prosperity' in blob.name.lower() or 'test' in blob.name.lower():
                    bai2_files.append(blob.name)
            elif blob.name.startswith('bai2-outputs/') and 'error' in blob.name.lower():
                if 'prosperity' in blob.name.lower() or 'test' in blob.name.lower():
                    error_files.append(blob.name)
        
        print(f"📄 Found {len(bai2_files)} BAI2 files")
        print(f"⚠️ Found {len(error_files)} error files")
        
        success = False
        
        if bai2_files:
            # Check the most recent BAI2 file
            latest_bai2 = sorted(bai2_files)[-1]
            print(f"\n✅ SUCCESS! Found BAI2 file: {latest_bai2}")
            
            # Download and examine
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=latest_bai2)
            bai2_content = blob_client.download_blob().readall().decode('utf-8')
            
            lines = bai2_content.split('\n')
            print(f"📊 BAI2 file contains {len(lines)} lines")
            
            # Look for routing number in file header (01 record)
            for line in lines:
                if line.startswith('01,'):
                    parts = line.split(',')
                    if len(parts) > 4:
                        routing_number = parts[4]
                        print(f"\n🔍 Analysis:")
                        print(f"   Routing number in BAI2: {routing_number}")
                        
                        if len(routing_number) == 9 and routing_number.isdigit():
                            print(f"   ✅ Valid format: 9 digits")
                            
                            if routing_number.startswith('113'):
                                print(f"   ✅ SUCCESS! Matches Prosperity Bank pattern (113xxxxxx)")
                                print(f"   ✅ OpenAI integration working correctly!")
                                success = True
                            else:
                                print(f"   ⚠️ Unexpected routing number (expected 113xxxxxx)")
                        else:
                            print(f"   ❌ Invalid routing number format")
                        break
            
            # Show BAI2 preview
            print(f"\n📄 BAI2 File Preview:")
            for i, line in enumerate(lines[:3]):
                if line.strip():
                    print(f"   {i+1}: {line}")
                    
        elif error_files:
            latest_error = sorted(error_files)[-1]
            print(f"\n⚠️ Found error file: {latest_error}")
            
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=latest_error)
            error_content = blob_client.download_blob().readall().decode('utf-8')
            
            print(f"❌ Error details:")
            print(error_content[:500])
            
        else:
            print("\n❌ No output files found!")
            print("   This indicates the function may not have processed the file")
        
        # Cleanup
        try:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.delete_blob()
            print(f"\n🧹 Cleaned up uploaded file")
        except:
            pass
        
        return success
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prosperity_pdf()
    
    print(f"\n🎉 Prosperity Bank Test {'PASSED' if success else 'FAILED'}!")
    print(f"✅ Routing number extraction {'working correctly' if success else 'needs investigation'}")
    print(f"✅ OpenAI integration {'validated' if success else 'requires review'}")
