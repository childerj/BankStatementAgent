#!/usr/bin/env python3
"""
Download and examine the most recent BAI2 file to check routing number
"""

from azure.storage.blob import BlobServiceClient
import os
from datetime import datetime

def check_recent_bai2():
    """Download and examine the most recent BAI2 file"""
    print("🔍 Checking most recent BAI2 file for routing number...")
    
    try:
        # Azure Storage connection
        connection_string = "DefaultEndpointsProtocol=https;AccountName=waazuse1aistorage;AccountKey=FvdaW3gMjF2s9uTu4KGp+wD39Wq4T8g19NTvJ8QsKbJHXp1BSGLrLZFfFTpELCDZC5U4v7LRjNxH+AStZqjBAA==;EndpointSuffix=core.windows.net"
        
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service.get_container_client("bank-reconciliation")
        
        # List BAI2 files, get the most recent
        print("📁 Listing BAI2 files...")
        bai2_blobs = []
        for blob in container_client.list_blobs(name_starts_with="bai2-outputs/"):
            if blob.name.endswith(('.bai', '.bai2')):
                bai2_blobs.append((blob.name, blob.last_modified))
        
        if not bai2_blobs:
            print("❌ No BAI2 files found")
            return
        
        # Sort by last modified, get most recent
        bai2_blobs.sort(key=lambda x: x[1], reverse=True)
        most_recent = bai2_blobs[0]
        
        print(f"📄 Most recent BAI2 file: {most_recent[0]}")
        print(f"⏰ Last modified: {most_recent[1]}")
        
        # Download and examine the file
        blob_client = container_client.get_blob_client(most_recent[0])
        content = blob_client.download_blob().readall().decode('utf-8')
        
        print(f"\n📊 BAI2 File Content ({len(content)} bytes):")
        print("=" * 60)
        
        lines = content.split('\n')
        for i, line in enumerate(lines[:10], 1):  # Show first 10 lines
            print(f"{i:2}: {line}")
        
        if len(lines) > 10:
            print(f"... ({len(lines) - 10} more lines)")
        
        print("=" * 60)
        
        # Extract routing number from header line
        if lines and lines[0].startswith('01,'):
            parts = lines[0].split(',')
            if len(parts) > 4:
                routing_number = parts[4]
                print(f"\n🏦 Routing Number Found: {routing_number}")
                
                # Validate routing number format
                if len(routing_number) == 9 and routing_number.isdigit():
                    print("✅ Valid 9-digit routing number format")
                else:
                    print(f"❌ Invalid routing number format (length: {len(routing_number)})")
                    print("   Expected: 9 digits")
        
        # Check for account information in account identifier line
        for line in lines:
            if line.startswith('03,'):
                parts = line.split(',')
                if len(parts) > 1:
                    account_number = parts[1]
                    print(f"🔢 Account Number: {account_number}")
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_recent_bai2()
