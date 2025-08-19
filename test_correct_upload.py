#!/usr/bin/env python3
"""
Test the deployed Azure Function by uploading to the correct container structure
"""

import json
import time
from azure.storage.blob import BlobServiceClient

def test_correct_upload():
    """Upload file to the correct container structure for EventGrid trigger"""
    
    print("🧪 Testing Correct Container Upload for EventGrid Trigger")
    print("=" * 70)
    
    try:
        # Load Azure storage connection from local settings
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
            storage_connection = settings['Values']['AzureWebJobsStorage']
        
        print("📤 Setting up blob upload to correct container structure...")
        
        # Create blob client
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection)
        
        # Correct container structure based on function code analysis:
        # - Container: "bank-reconciliation" 
        # - Subfolder: "incoming-bank-statements/"
        # - Full path: "bank-reconciliation/incoming-bank-statements/filename"
        
        container_name = "bank-reconciliation"
        blob_name = "incoming-bank-statements/test-openai-prosperity.pdf"  # Note the subfolder
        local_file = "Test Docs/8-1-25_Prosperity.pdf"
        
        # Check if file exists
        import os
        if not os.path.exists(local_file):
            print(f"❌ Test file not found: {local_file}")
            return
        
        print("📋 Upload Details:")
        print(f"   Container: {container_name}")
        print(f"   Blob path: {blob_name}")
        print(f"   Local file: {local_file}")
        print()
        
        # Check if container exists
        try:
            container_client = blob_service_client.get_container_client(container_name)
            container_exists = container_client.exists()
            if not container_exists:
                print(f"❌ Container '{container_name}' does not exist!")
                print("Run the Azure Function setup endpoint first to create containers")
                return
            else:
                print(f"✅ Container '{container_name}' exists")
        except Exception as e:
            print(f"❌ Error checking container: {e}")
            return
        
        # Upload the file to correct location
        print(f"📤 Uploading {local_file} to {container_name}/{blob_name}...")
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_name
        )
        
        with open(local_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print("✅ File uploaded successfully to correct location!")
        print("⏳ EventGrid should trigger the Azure Function...")
        print("⏳ Waiting for processing (30 seconds)...")
        
        # Wait for processing
        time.sleep(30)
        
        # Check for results in the same container
        print("\n=== Checking for Processing Results ===")
        
        # Look for output files in bai2-outputs and archive folders
        container_client = blob_service_client.get_container_client(container_name)
        
        bai2_files = []
        error_files = []
        archived_files = []
        
        print("📁 Scanning for output files...")
        blobs = container_client.list_blobs()
        for blob in blobs:
            print(f"   Found: {blob.name}")
            
            if blob.name.startswith('bai2-outputs/') and blob.name.endswith('.bai2'):
                bai2_files.append(blob.name)
            elif blob.name.startswith('bai2-outputs/') and 'error' in blob.name.lower():
                error_files.append(blob.name)
            elif blob.name.startswith('archive/'):
                archived_files.append(blob.name)
        
        print(f"\n📊 Results Summary:")
        print(f"   📄 BAI2 files: {len(bai2_files)}")
        print(f"   ⚠️ Error files: {len(error_files)}")
        print(f"   📁 Archived files: {len(archived_files)}")
        
        # Check the most recent output files
        recent_bai2 = [f for f in bai2_files if 'prosperity' in f.lower() or 'test' in f.lower()]
        recent_error = [f for f in error_files if 'prosperity' in f.lower() or 'test' in f.lower()]
        
        if recent_bai2:
            print(f"\n✅ SUCCESS! Found BAI2 file: {recent_bai2[0]}")
            
            # Download and examine the BAI2 file
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=recent_bai2[0]
            )
            
            bai2_content = blob_client.download_blob().readall().decode('utf-8')
            lines = bai2_content.split('\n')
            
            print(f"📊 BAI2 file contains {len(lines)} lines")
            
            # Look for routing number in the file header
            for line in lines:
                if line.startswith('01,'):  # File header record
                    parts = line.split(',')
                    if len(parts) > 4:
                        routing_number = parts[4]
                        print(f"✅ Found routing number in BAI2: {routing_number}")
                        
                        # Check if this looks like a valid routing number
                        if len(routing_number) == 9 and routing_number.isdigit():
                            print(f"✅ Routing number format is valid")
                            
                            # Check if it matches Prosperity Bank pattern (starts with 113)
                            if routing_number.startswith('113'):
                                print(f"✅ SUCCESS! OpenAI found correct Prosperity Bank routing number")
                            else:
                                print(f"⚠️ Routing number doesn't match expected Prosperity pattern")
                        else:
                            print(f"❌ Invalid routing number format")
                        break
            
            print(f"\n📄 BAI2 file preview (first 5 lines):")
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    print(f"   {i+1}: {line}")
                    
        elif recent_error:
            print(f"\n⚠️ Found error file: {recent_error[0]}")
            
            # Download and check the error file
            blob_client = blob_service_client.get_blob_client(
                container=container_name, 
                blob=recent_error[0]
            )
            
            error_content = blob_client.download_blob().readall().decode('utf-8')
            print(f"❌ Error content: {error_content[:500]}...")
            
        else:
            print("\n❌ No output files found!")
            print("This indicates EventGrid trigger did not fire or processing failed")
            print("\nDebugging tips:")
            print("• Check Azure Function logs in Application Insights")
            print("• Verify EventGrid subscription is configured correctly")
            print("• Ensure blob upload triggered the EventGrid event")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 OpenAI Integration Test Complete!")
    print(f"If a BAI2 file was created with a valid routing number,")
    print(f"the OpenAI integration is working correctly in production!")

if __name__ == "__main__":
    test_correct_upload()
