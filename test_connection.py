import os
import json
from azure.storage.blob import BlobServiceClient

# Load settings from local.settings.json like Azure Functions does
try:
    with open("local.settings.json", "r") as f:
        settings = json.load(f)
        for key, value in settings["Values"].items():
            os.environ[key] = value
    print("✅ Loaded settings from local.settings.json")
except Exception as e:
    print(f"❌ Error loading settings: {e}")

# Test reading the connection string
print("Environment variables:")
connection_string = os.environ.get("AzureWebJobsStorage", "NOT_FOUND")
print(f"AzureWebJobsStorage: {connection_string[:50]}...")

# Test creating BlobServiceClient
try:
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    print("✅ BlobServiceClient created successfully")
    
    # Test listing containers
    containers = list(blob_service.list_containers())
    print(f"✅ Found {len(containers)} containers:")
    for container in containers:
        print(f"  - {container.name}")
        
    # Test connecting to the specific container
    container_client = blob_service.get_container_client("bank-reconcilitation")
    print(f"✅ Connected to bank-reconcilitation container")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
