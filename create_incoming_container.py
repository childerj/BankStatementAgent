#!/usr/bin/env python3
"""
Simple script to create the incoming-bank-statements container for the blob trigger
"""

from azure.storage.blob import BlobServiceClient
import os

def create_incoming_container():
    try:
        # Use the same connection string that Azure Functions uses
        connection_string = "UseDevelopmentStorage=true"
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        
        # Create the container that the blob trigger is expecting
        container_name = "incoming-bank-statements"
        
        try:
            blob_service.create_container(container_name)
            print(f"✅ Successfully created container: {container_name}")
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                print(f"✅ Container already exists: {container_name}")
            else:
                print(f"❌ Error creating container: {e}")
                return False
        
        # Also create the other containers for completeness
        other_containers = ["bai2-outputs", "archive"]
        for container in other_containers:
            try:
                blob_service.create_container(container)
                print(f"✅ Successfully created container: {container}")
            except Exception as e:
                if "ContainerAlreadyExists" in str(e):
                    print(f"✅ Container already exists: {container}")
                else:
                    print(f"❌ Error creating container {container}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Azurite: {e}")
        return False

if __name__ == "__main__":
    print("Creating containers for Azure Function blob trigger...")
    success = create_incoming_container()
    if success:
        print("✅ Container setup complete!")
    else:
        print("❌ Container setup failed!")
