#!/usr/bin/env python3
"""
Azure Storage Cleanup Program
Deletes all files except .placeholder files from archive and bai2-outputs folders
in the bank-reconciliation container
"""

import os
import sys
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import json

def load_storage_settings():
    """Load Azure Storage connection settings"""
    try:
        # Try to load from local.settings.json first
        if os.path.exists('local.settings.json'):
            with open('local.settings.json', 'r') as f:
                settings = json.load(f)
                connection_string = settings.get('Values', {}).get('AzureWebJobsStorage')
                if connection_string:
                    print("✅ Using connection string from local.settings.json")
                    return connection_string
        
        # Fallback to environment variable
        connection_string = os.environ.get('AzureWebJobsStorage')
        if connection_string:
            print("✅ Using connection string from environment variable")
            return connection_string
        
        print("❌ No Azure Storage connection string found")
        print("   Please set AzureWebJobsStorage in local.settings.json or environment")
        return None
        
    except Exception as e:
        print(f"❌ Error loading storage settings: {e}")
        return None

def list_and_delete_files(blob_service_client, container_name, folder_prefix, dry_run=True):
    """List and optionally delete files in a folder (except .placeholder files)"""
    
    print(f"\n📁 Processing folder: {folder_prefix}")
    print("=" * 60)
    
    try:
        container_client = blob_service_client.get_container_client(container_name)
        
        # List all blobs in the folder
        blobs = list(container_client.list_blobs(name_starts_with=folder_prefix))
        
        if not blobs:
            print(f"   📂 Folder '{folder_prefix}' is empty")
            return 0, 0
        
        total_files = 0
        files_to_delete = 0
        placeholder_files = 0
        
        print(f"   📊 Found {len(blobs)} files in '{folder_prefix}'")
        print()
        
        for blob in blobs:
            total_files += 1
            blob_name = blob.name
            file_name = blob_name.split('/')[-1]  # Get just the filename
            
            if file_name == '.placeholder':
                placeholder_files += 1
                print(f"   ✅ KEEP: {blob_name} (placeholder file)")
            else:
                files_to_delete += 1
                if dry_run:
                    print(f"   🗑️  WOULD DELETE: {blob_name}")
                else:
                    try:
                        container_client.delete_blob(blob_name)
                        print(f"   ❌ DELETED: {blob_name}")
                    except Exception as e:
                        print(f"   ⚠️  ERROR deleting {blob_name}: {e}")
        
        print()
        print(f"   📈 Summary for '{folder_prefix}':")
        print(f"      Total files: {total_files}")
        print(f"      Placeholder files (kept): {placeholder_files}")
        print(f"      Files to delete: {files_to_delete}")
        
        return total_files, files_to_delete
        
    except Exception as e:
        print(f"   ❌ Error processing folder '{folder_prefix}': {e}")
        return 0, 0

def cleanup_storage_folders(dry_run=True):
    """Main cleanup function"""
    
    print("🧹 Azure Storage Cleanup Program")
    print("=" * 60)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE DELETION'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load connection settings
    connection_string = load_storage_settings()
    if not connection_string:
        return False
    
    try:
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = "bank-reconciliation"
        
        print(f"\n🔗 Connected to Azure Storage")
        print(f"📦 Container: {container_name}")
        
        # Folders to clean
        folders_to_clean = [
            "archive/",
            "bai2-outputs/"
        ]
        
        total_files_all = 0
        total_to_delete_all = 0
        
        # Process each folder
        for folder in folders_to_clean:
            total_files, files_to_delete = list_and_delete_files(
                blob_service_client, 
                container_name, 
                folder, 
                dry_run
            )
            total_files_all += total_files
            total_to_delete_all += files_to_delete
        
        # Final summary
        print(f"\n🎯 FINAL SUMMARY")
        print("=" * 60)
        print(f"📊 Total files found: {total_files_all}")
        print(f"🗑️  Files to delete: {total_to_delete_all}")
        print(f"✅ Placeholder files kept: {total_files_all - total_to_delete_all}")
        
        if dry_run:
            print(f"\n⚠️  This was a DRY RUN - no files were actually deleted")
            print(f"   Run without --dry-run to perform actual deletion")
        else:
            print(f"\n✅ Cleanup completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def main():
    """Main program entry point"""
    
    # Check command line arguments
    dry_run = False  # Default to live deletion
    if len(sys.argv) > 1:
        if '--dry-run' in sys.argv or '--preview' in sys.argv:
            dry_run = True
            print("👀 DRY RUN MODE ENABLED (preview only)")
        elif '--help' in sys.argv or '-h' in sys.argv:
            print("Azure Storage Cleanup Program")
            print("Usage:")
            print("  python cleanup_storage.py           # Live deletion (default)")
            print("  python cleanup_storage.py --dry-run # Preview only (safe)")
            print("  python cleanup_storage.py --preview # Preview only (safe)")
            print("  python cleanup_storage.py --help    # Show this help")
            return
    
    # Confirmation prompt for live deletion
    if not dry_run:
        print("⚠️  LIVE DELETION MODE")
        response = input("\n❓ Are you sure you want to delete files? Type 'YES' to confirm: ")
        if response != 'YES':
            print("❌ Operation cancelled")
            return
    
    # Run cleanup
    success = cleanup_storage_folders(dry_run)
    
    if success:
        print(f"\n🎉 Program completed successfully!")
    else:
        print(f"\n💥 Program failed - check errors above")
        sys.exit(1)

if __name__ == "__main__":
    main()
