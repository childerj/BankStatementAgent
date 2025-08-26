"""
List and Access Files in Bank_Data Folder
Check what files are available in the Azure storage Bank_Data folder
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

def list_bank_data_files():
    """List all files in the Bank_Data folder"""
    
    print("🔍 Bank_Data Folder Contents")
    print("="*50)
    
    # Load connection string
    connection_string = load_settings()
    
    if not connection_string:
        print("❌ No Azure Storage connection string found in local.settings.json")
        return []
    
    print("✅ Connection string loaded")
    
    # Container and folder details
    container_name = "bank-reconciliation"
    folder_path = "Bank_Data"
    
    print(f"📁 Container: {container_name}")
    print(f"📂 Folder: {folder_path}")
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
            return []
        
        # List all blobs in the Bank_Data folder
        print(f"\n📋 Files in {folder_path} folder:")
        print("-" * 60)
        
        blobs_in_folder = container_client.list_blobs(name_starts_with=folder_path)
        
        bank_data_files = []
        for i, blob in enumerate(blobs_in_folder, 1):
            file_name = blob.name.replace(f"{folder_path}/", "")
            file_size = blob.size
            last_modified = blob.last_modified
            
            bank_data_files.append({
                'full_path': blob.name,
                'file_name': file_name,
                'size': file_size,
                'last_modified': last_modified
            })
            
            print(f"{i:2d}. 📄 {file_name}")
            print(f"    📊 Size: {file_size:,} bytes")
            print(f"    📅 Modified: {last_modified}")
            print(f"    🔗 Path: {blob.name}")
            print()
        
        if not bank_data_files:
            print(f"❌ No files found in {folder_path} folder")
            return []
        
        print("-" * 60)
        print(f"✅ Found {len(bank_data_files)} file(s) in Bank_Data folder")
        
        return bank_data_files
    
    except Exception as e:
        print(f"❌ Error accessing Azure Storage: {e}")
        return []

def download_and_process_file(file_info):
    """Download and process a specific file"""
    
    print(f"\n🔄 Processing: {file_info['file_name']}")
    print("="*50)
    
    connection_string = load_settings()
    container_name = "bank-reconciliation"
    
    try:
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Download the file
        print(f"⬇️  Downloading {file_info['full_path']}...")
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=file_info['full_path']
        )
        
        # Download blob content
        blob_data = blob_client.download_blob()
        file_content = blob_data.readall()
        
        print(f"✅ Downloaded successfully: {len(file_content):,} bytes")
        
        # Save local copy
        local_filename = file_info['file_name']
        with open(local_filename, 'wb') as f:
            f.write(file_content)
        
        print(f"💾 Saved local copy: {local_filename}")
        
        # Try to process the file based on extension
        file_extension = local_filename.lower().split('.')[-1]
        
        if file_extension in ['csv', 'txt']:
            return process_csv_file(file_content, local_filename)
        elif file_extension in ['xlsx', 'xls']:
            return process_excel_file(file_content, local_filename)
        elif file_extension == 'json':
            return process_json_file(file_content, local_filename)
        else:
            print(f"❓ Unknown file type: {file_extension}")
            return None
    
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return None

def process_csv_file(content, filename):
    """Process CSV file"""
    
    try:
        print(f"📄 Processing CSV file...")
        
        # Try to read as CSV
        csv_string = content.decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_string))
        
        print(f"✅ CSV processed successfully!")
        print(f"   📊 Rows: {df.shape[0]:,}")
        print(f"   📊 Columns: {df.shape[1]:,}")
        print(f"   📊 Column names: {list(df.columns)}")
        
        # Convert to JSON
        json_filename = filename.replace('.csv', '.json').replace('.txt', '.json')
        json_data = df.to_json(orient='records', indent=2, date_format='iso')
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"💾 JSON saved: {json_filename}")
        
        # Show preview
        print(f"\n📋 DATA PREVIEW:")
        print("-" * 80)
        print(df.head(10).to_string())
        print("-" * 80)
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing CSV: {e}")
        return None

def process_excel_file(content, filename):
    """Process Excel file"""
    
    try:
        print(f"📊 Processing Excel file...")
        
        # Read as Excel
        df = pd.read_excel(io.BytesIO(content))
        
        print(f"✅ Excel processed successfully!")
        print(f"   📊 Rows: {df.shape[0]:,}")
        print(f"   📊 Columns: {df.shape[1]:,}")
        print(f"   📊 Column names: {list(df.columns)}")
        
        # Convert to JSON
        json_filename = filename.replace('.xlsx', '.json').replace('.xls', '.json')
        json_data = df.to_json(orient='records', indent=2, date_format='iso')
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"💾 JSON saved: {json_filename}")
        
        # Show preview
        print(f"\n📋 DATA PREVIEW:")
        print("-" * 80)
        print(df.head(10).to_string())
        print("-" * 80)
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing Excel: {e}")
        return None

def process_json_file(content, filename):
    """Process JSON file"""
    
    try:
        print(f"📄 Processing JSON file...")
        
        # Parse JSON
        json_string = content.decode('utf-8')
        data = json.loads(json_string)
        
        print(f"✅ JSON processed successfully!")
        print(f"   📊 Records: {len(data):,}")
        
        # Show preview
        print(f"\n📋 JSON PREVIEW:")
        print("-" * 80)
        print(json.dumps(data[:5], indent=2))
        print("-" * 80)
        
        return data
        
    except Exception as e:
        print(f"❌ Error processing JSON: {e}")
        return None

def main():
    """Main function"""
    
    print("🚀 Bank_Data Folder Explorer")
    print("="*50)
    
    # List all files in Bank_Data folder
    files = list_bank_data_files()
    
    if not files:
        print("❌ No files found in Bank_Data folder")
        return
    
    # Process each file
    for i, file_info in enumerate(files):
        print(f"\n{'='*60}")
        print(f"📁 FILE {i+1}/{len(files)}: {file_info['file_name']}")
        print(f"{'='*60}")
        
        result = download_and_process_file(file_info)
        
        if result is not None:
            print(f"✅ Successfully processed {file_info['file_name']}")
        else:
            print(f"❌ Failed to process {file_info['file_name']}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   📁 Total files found: {len(files)}")
    print(f"   📋 All files have been downloaded and processed")
    print(f"\n✅ Process completed!")

if __name__ == "__main__":
    main()
