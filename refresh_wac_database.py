#!/usr/bin/env python3
"""
Refresh local WAC Bank Information.json with all records from Azure Storage Excel file
"""

import json
import os
from azure.storage.blob import BlobServiceClient
import pandas as pd
from io import BytesIO

def load_settings():
    """Load local settings for Azure Storage connection"""
    with open('local.settings.json', 'r') as f:
        settings = json.load(f)
    return settings['Values']

def refresh_wac_database():
    """Download Excel file from Azure Storage and update local JSON"""
    
    print("🔄 Refreshing local WAC database from Azure Storage...")
    
    # Load settings
    settings = load_settings()
    connection_string = settings['DEPLOYMENT_STORAGE_CONNECTION_STRING']
    
    # Initialize blob client
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_name = "bank-reconciliation"
    blob_name = "Bank_Data/WAC Bank Information.xlsx"
    
    try:
        print(f"📥 Downloading {blob_name} from Azure Storage...")
        
        # Download blob
        blob_client = blob_service_client.get_blob_client(
            container=container_name, 
            blob=blob_name
        )
        
        blob_data = blob_client.download_blob().readall()
        print(f"✅ Downloaded {len(blob_data):,} bytes")
        
        # Read Excel file
        print("📊 Reading Excel data...")
        excel_file = BytesIO(blob_data)
        df = pd.read_excel(excel_file)
        
        print(f"✅ Loaded {len(df)} rows from Excel file")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Convert to JSON format
        print("🔄 Converting to JSON format...")
        bank_data = []
        
        for index, row in df.iterrows():
            entry = {}
            for col in df.columns:
                # Handle NaN values
                value = row[col]
                if pd.isna(value):
                    entry[col] = None
                elif isinstance(value, (int, float)):
                    # Convert numeric values to appropriate type
                    if col in ['Account Number', 'Routing Number']:
                        entry[col] = str(int(value)) if not pd.isna(value) else None
                    else:
                        entry[col] = value
                else:
                    entry[col] = str(value)
            
            bank_data.append(entry)
        
        # Save to local JSON file
        print(f"💾 Saving {len(bank_data)} entries to local WAC Bank Information.json...")
        
        with open('WAC Bank Information.json', 'w') as f:
            json.dump(bank_data, f, indent=2)
        
        print("✅ Local WAC database refreshed successfully!")
        
        # Show summary
        print(f"\n📊 SUMMARY:")
        print(f"Total entries: {len(bank_data)}")
        
        # Check for accounts ending in 518
        accounts_518 = [entry for entry in bank_data if str(entry.get('Account Number', '')).endswith('518')]
        if accounts_518:
            print(f"\n🎯 Found {len(accounts_518)} account(s) ending in 518:")
            for entry in accounts_518:
                print(f"  Bank: {entry.get('Bank Name')}")
                print(f"  Account: {entry.get('Account Number')}")
                print(f"  Routing: {entry.get('Routing Number')}")
        else:
            print("\n❌ No accounts ending in 518 found")
        
        # Check for Palmetto Bank
        palmetto_accounts = [entry for entry in bank_data if 'palmetto' in str(entry.get('Bank Name', '')).lower()]
        if palmetto_accounts:
            print(f"\n🏦 Found {len(palmetto_accounts)} Palmetto Bank account(s):")
            for entry in palmetto_accounts:
                print(f"  Bank: {entry.get('Bank Name')}")
                print(f"  Account: {entry.get('Account Number')}")
                print(f"  Routing: {entry.get('Routing Number')}")
        else:
            print("\n❌ No Palmetto Bank accounts found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error refreshing WAC database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    refresh_wac_database()
