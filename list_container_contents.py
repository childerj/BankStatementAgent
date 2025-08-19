import os
from azure.storage.blob import BlobServiceClient

# Load environment variables from local.settings.json
import json
print("✅ Loading settings from local.settings.json")
with open("local.settings.json", "r") as f:
    settings = json.load(f)

# Set environment variables
for key, value in settings["Values"].items():
    os.environ[key] = value
    if "AzureWebJobsStorage" in key:
        print(f"{key}: {value[:50]}...")

# Get connection string
connection_string = os.environ.get("AzureWebJobsStorage")
print(f"\n✅ BlobServiceClient created successfully")

# Create blob service client
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Check containers
containers_to_check = ["bai2-outputs", "archive", "bank-reconciliation"]

for container_name in containers_to_check:
    print(f"\n📁 Contents of '{container_name}' container:")
    try:
        container_client = blob_service_client.get_container_client(container_name)
        blobs = list(container_client.list_blobs())
        
        if blobs:
            for blob in blobs:
                print(f"  📄 {blob.name} ({blob.size} bytes, modified: {blob.last_modified})")
        else:
            print("  (empty)")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Check incoming-bank-statements specifically
print(f"\n📁 Contents of 'bank-reconciliation/incoming-bank-statements' folder:")
try:
    container_client = blob_service_client.get_container_client("bank-reconciliation")
    blobs = list(container_client.list_blobs(name_starts_with="incoming-bank-statements/"))
    
    if blobs:
        for blob in blobs:
            print(f"  📄 {blob.name} ({blob.size} bytes, modified: {blob.last_modified})")
    else:
        print("  (empty)")
except Exception as e:
    print(f"  ❌ Error: {e}")
