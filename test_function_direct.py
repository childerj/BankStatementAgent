#!/usr/bin/env python3
"""
Direct test of the bank statement processing function
This bypasses the Azure Functions runtime and tests the core functionality directly
"""

import os
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Mock Azure Functions InputStream for testing
class MockInputStream:
    def __init__(self, file_path, name):
        self.file_path = file_path
        self.name = name
        
    def read(self):
        with open(self.file_path, 'rb') as f:
            return f.read()

def test_with_sample_file():
    """Test the function with a sample PDF file"""
    
    # Set up environment variables for testing
    os.environ["DOCINTELLIGENCE_ENDPOINT"] = "test-endpoint"
    os.environ["DOCINTELLIGENCE_KEY"] = "test-key"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "test-endpoint"
    os.environ["AZURE_OPENAI_KEY"] = "test-key"
    os.environ["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4o-mini"
    os.environ["AzureWebJobsStorage"] = "YOUR_STORAGE_CONNECTION_STRING_HERE"
    
    # Import the function after setting environment variables
    try:
        from function_app import process_new_file
        print("✅ Successfully imported process_new_file function")
    except Exception as e:
        print(f"❌ Failed to import function: {e}")
        return
    
    # Find a test PDF file
    test_docs_dir = current_dir / "Test Docs"
    pdf_files = list(test_docs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in Test Docs directory")
        return
    
    test_file = pdf_files[0]
    print(f"📄 Using test file: {test_file.name}")
    
    # Create mock blob input
    mock_blob = MockInputStream(test_file, f"bank-reconcilitation/incoming-bank-statements/{test_file.name}")
    
    # Test the function
    try:
        print("🚀 Starting function test...")
        result = process_new_file(mock_blob)
        print("✅ Function completed successfully!")
        if result:
            print(f"📋 Result: {result}")
    except Exception as e:
        print(f"❌ Function failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Bank Statement Processing Function")
    print("=" * 50)
    test_with_sample_file()
