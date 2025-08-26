#!/usr/bin/env python
"""
Simple script to create the required Azure Storage containers for Azurite (local storage emulator).
"""
from azure.storage.blob import BlobServiceClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use direct endpoint URL instead of connection string for Azurite
blob_service_client = BlobServiceClient(
    account_url="http://127.0.0.1:10000/devstoreaccount1",
    credential=("devstoreaccount1", "Eby8vdM02xNOcfz1c+hQr5UjCGr7Tm6+UqKz2N8lDpvwO8jBJx3vXJ4f7XJqjn9rUk1+0j/VKqGF2L+1fQJz/rw==")
)

def create_containers():
    """Create the required containers if they don't exist."""
    try:        
        # List of containers to create
        containers = [
            "incoming-bank-statements",
            "processed-bank-statements", 
            "failed-bank-statements"
        ]
        
        for container_name in containers:
            try:
                # Try to create the container
                container_client = blob_service_client.create_container(container_name)
                logger.info(f"✅ Created container: {container_name}")
            except Exception as e:
                if "ContainerAlreadyExists" in str(e):
                    logger.info(f"✅ Container already exists: {container_name}")
                else:
                    logger.error(f"❌ Failed to create container {container_name}: {e}")
                    
        # List all containers to verify
        logger.info("\n📋 Current containers:")
        containers = blob_service_client.list_containers()
        for container in containers:
            logger.info(f"  - {container.name}")
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to blob service: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_containers()
