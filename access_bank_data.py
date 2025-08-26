"""
Azure Storage Blob Access Script
Access US_Bank_List_Real.csv from bank-reconciliation container
"""

import json
import pandas as pd
from azure.storage.blob import BlobServiceClient
import io

def load_settings():
    """Load Azure storage connection from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        # Try different connection string keys
        connection_string = (
            values.get('AzureWebJobsStorage') or 
            values.get('DEPLOYMENT_STORAGE_CONNECTION_STRING') or
            values.get('AZURE_STORAGE_CONNECTION_STRING')
        )
        
        return connection_string
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return None

def access_bank_data_file():
    """Access the US_Bank_List_Real.csv file from Azure storage"""
    
    print("🔍 Azure Storage Blob Access")
    print("="*50)
    
    # Load connection string
    connection_string = load_settings()
    
    if not connection_string:
        print("❌ No Azure Storage connection string found in local.settings.json")
        return None
    
    print("✅ Connection string loaded")
    
    # Container and file details
    container_name = "bank-reconciliation"
    folder_path = "Bank_Data"
    file_name = "US_Bank_List_Real.csv"
    blob_path = f"{folder_path}/{file_name}"
    
    print(f"📁 Container: {container_name}")
    print(f"📂 Folder: {folder_path}")
    print(f"📄 File: {file_name}")
    print(f"🔗 Blob path: {blob_path}")
    print()
    
    try:
        # Create blob service client
        print("🔌 Connecting to Azure Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get container client
        container_client = blob_service_client.get_container_client(container_name)
        
        # Check if container exists
        try:
            container_properties = container_client.get_container_properties()
            print(f"✅ Container '{container_name}' found")
        except Exception as e:
            print(f"❌ Container '{container_name}' not found: {e}")
            return None
        
        # List blobs in the Bank_Data folder to verify
        print(f"\n📋 Listing files in {folder_path} folder:")
        blobs_in_folder = container_client.list_blobs(name_starts_with=folder_path)
        
        bank_data_files = []
        for blob in blobs_in_folder:
            bank_data_files.append(blob.name)
            print(f"   📄 {blob.name}")
        
        if not bank_data_files:
            print(f"❌ No files found in {folder_path} folder")
            return None
        
        # Check if our target file exists
        if blob_path not in bank_data_files:
            print(f"\n❌ File '{blob_path}' not found")
            print("Available files:")
            for file in bank_data_files:
                print(f"   📄 {file}")
            return None
        
        # Download the file
        print(f"\n⬇️  Downloading {blob_path}...")
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_path
        )
        
        # Get blob properties
        blob_properties = blob_client.get_blob_properties()
        file_size = blob_properties.size
        last_modified = blob_properties.last_modified
        
        print(f"   Size: {file_size:,} bytes")
        print(f"   Last modified: {last_modified}")
        
        # Download blob content
        blob_data = blob_client.download_blob()
        file_content = blob_data.readall()
        
        print(f"✅ Downloaded successfully: {len(file_content):,} bytes")
        
        # Save local copy
        local_filename = "US_Bank_List_Real.csv"
        with open(local_filename, 'wb') as f:
            f.write(file_content)
        
        print(f"💾 Saved local copy: {local_filename}")
        
        # Read as DataFrame
        print(f"\n📊 Processing CSV data...")
        try:
            # Try to read as CSV
            csv_string = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_string))
            
            print(f"✅ CSV processed successfully!")
            print(f"   Rows: {df.shape[0]:,}")
            print(f"   Columns: {df.shape[1]:,}")
            print(f"   Column names: {list(df.columns)}")
            
            # Convert to JSON
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
            
            # Save JSON
            json_filename = "US_Bank_List_Real.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            print(f"💾 JSON saved: {json_filename}")
            
            # Show preview
            print(f"\n📋 DATA PREVIEW:")
            print("-" * 80)
            print(df.head(10).to_string())
            print("-" * 80)
            
            if df.shape[0] > 10:
                print(f"... and {df.shape[0] - 10} more rows")
            
            return df
            
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            print("Raw content preview:")
            print(file_content[:500].decode('utf-8', errors='ignore'))
            return None
    
    except Exception as e:
        print(f"❌ Error accessing Azure Storage: {e}")
        return None

def main():
    """Main function"""
    
    print("🚀 Bank Data File Access")
    print("="*50)
    
    # Check if azure-storage-blob is installed
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("❌ Azure Storage Blob library not installed")
        print("Run: pip install azure-storage-blob")
        return
    
    # Access the file
    result = access_bank_data_file()
    
    if result is not None:
        print(f"\n🎯 SUCCESS! Bank data accessed and processed")
        print(f"Files created:")
        print(f"  📄 US_Bank_List_Real.csv (local copy)")
        print(f"  📄 US_Bank_List_Real.json (JSON format)")
    else:
        print(f"\n❌ FAILED to access bank data")
    
    print(f"\n✅ Process completed!")

if __name__ == "__main__":
    main()
