"""
Browser-Based SharePoint File Downloader
Uses Selenium WebDriver to authenticate and download SharePoint files
"""

import json
import time
import os
from pathlib import Path
import pandas as pd

def load_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        return {
            'username': values.get('SHAREPOINT_USERNAME', ''),
            'password': values.get('SHAREPOINT_PASSWORD', ''),
            'file_url': values.get('SHAREPOINT_FILE_URL', '')
        }
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return {'username': '', 'password': '', 'file_url': ''}

def manual_download_instructions():
    """Provide instructions for manual download"""
    
    print("\n" + "="*80)
    print("📋 MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*80)
    print()
    print("SharePoint shared links require browser-based authentication.")
    print("Please follow these steps to download the file manually:")
    print()
    print("1. Open your web browser")
    print("2. Go to the SharePoint URL:")
    
    settings = load_settings()
    sharepoint_url = settings['file_url']
    print(f"   {sharepoint_url}")
    print()
    print("3. Sign in with your credentials if prompted:")
    print(f"   Username: {settings['username']}")
    print("   Password: [your password]")
    print()
    print("4. Once the file opens in Excel Online:")
    print("   - Click 'File' in the top menu")
    print("   - Click 'Download'")
    print("   - Choose 'Download a copy'")
    print()
    print("5. Save the file to this directory:")
    print(f"   {os.getcwd()}")
    print()
    print("6. Name the file: 'sharepoint_data.xlsx' (or .csv)")
    print()
    print("7. Run the local file processor:")
    print("   python process_local_file.py")
    print()
    print("="*80)

def create_local_processor():
    """Create a script to process locally downloaded files"""
    
    processor_code = '''"""
Local File Processor for SharePoint Downloads
Processes manually downloaded SharePoint files
"""

import pandas as pd
import json
import os
from pathlib import Path

def find_downloaded_file():
    """Find the most recently downloaded SharePoint file"""
    
    current_dir = Path('.')
    
    # Look for common file patterns
    patterns = [
        'sharepoint_data.*',
        'sharepoint.*',
        '*.xlsx', 
        '*.xls',
        '*.csv'
    ]
    
    files_found = []
    
    for pattern in patterns:
        files = list(current_dir.glob(pattern))
        for file in files:
            if file.is_file() and file.stat().st_size > 0:
                files_found.append((file, file.stat().st_mtime))
    
    if not files_found:
        return None
    
    # Return the most recent file
    files_found.sort(key=lambda x: x[1], reverse=True)
    return files_found[0][0]

def process_file(file_path):
    """Process the downloaded file"""
    
    print(f"Processing file: {file_path}")
    print(f"   File size: {file_path.stat().st_size} bytes")
    
    # Determine file type by extension
    extension = file_path.suffix.lower()
    
    df = None
    
    try:
        if extension in ['.xlsx', '.xls']:
            print("Reading Excel file...")
            df = pd.read_excel(file_path)
        elif extension == '.csv':
            print("Reading CSV file...")
            # Try different separators
            for sep in [',', ';', '\\t']:
                try:
                    df = pd.read_csv(file_path, sep=sep)
                    if df.shape[1] > 1:  # More than one column suggests correct separator
                        break
                except:
                    continue
        else:
            print(f"Unknown file type: {extension}")
            return None
        
        if df is not None and not df.empty:
            print(f"File processed successfully!")
            print(f"   Rows: {df.shape[0]}")
            print(f"   Columns: {df.shape[1]}")
            print(f"   Column names: {list(df.columns)}")
            
            # Convert to JSON
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
            
            # Save JSON
            json_file = 'sharepoint_data.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
            
            print(f"\\nJSON saved to: {json_file}")
            
            # Show preview
            print(f"\\nDATA PREVIEW:")
            print("-" * 80)
            print(df.head(10).to_string())
            print("-" * 80)
            
            return df
        else:
            print("File appears to be empty or could not be read")
            return None
            
    except Exception as e:
        print(f"Error processing file: {e}")
        return None

def main():
    """Main processing function"""
    
    print("Local SharePoint File Processor")
    print("="*50)
    
    # Find the file
    file_path = find_downloaded_file()
    
    if not file_path:
        print("No suitable files found in current directory")
        print("\\nLooking for files with these patterns:")
        print("  - sharepoint_data.* ")
        print("  - *.xlsx, *.xls")
        print("  - *.csv")
        print("\\nPlease ensure you have downloaded the file manually first.")
        return None
    
    print(f"Found file: {file_path}")
    
    # Process the file
    result = process_file(file_path)
    
    if result is not None:
        print(f"\\nSUCCESS! File processed and converted to JSON")
        return result
    else:
        print(f"\\nFAILED to process file")
        return None

if __name__ == "__main__":
    main()
'''
    
    with open('process_local_file.py', 'w', encoding='utf-8') as f:
        f.write(processor_code)
    
    print("✅ Created local file processor: process_local_file.py")

def main():
    """Main function"""
    
    print("🚀 SharePoint File Access Solution")
    print("="*50)
    
    # Load settings and show current configuration
    settings = load_settings()
    
    if not all([settings['username'], settings['password'], settings['file_url']]):
        print("❌ Missing SharePoint credentials or URL in local.settings.json")
        return
    
    print(f"👤 Username: {settings['username']}")
    print(f"🔗 URL: {settings['file_url']}")
    print()
    
    print("⚠️  PROGRAMMATIC ACCESS LIMITATION")
    print("-" * 50)
    print("SharePoint shared links require browser-based authentication.")
    print("Automated downloads are blocked by Microsoft's security measures.")
    print("The downloaded content is an HTML redirect/error page, not the actual file.")
    print()
    
    # Create the local processor
    create_local_processor()
    
    # Show manual instructions
    manual_download_instructions()

if __name__ == "__main__":
    main()
