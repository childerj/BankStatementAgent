"""
Final SharePoint Download Solution
Comprehensive approach using the new download URL
"""

import json
import requests
import pandas as pd
import io
import os

def load_settings():
    """Load settings from local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        return {
            'username': values.get('SHAREPOINT_USERNAME', ''),
            'password': values.get('SHAREPOINT_PASSWORD', ''),
            'file_url': values.get('SHAREPOINT_FILE_URL', ''),
            'download_url': values.get('DOWNLOAD_URL', '')
        }
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return {}

def try_simple_download():
    """Try the simplest download approach first"""
    
    print("🔄 Trying simple download approach...")
    
    settings = load_settings()
    download_url = settings.get('download_url', '')
    
    if not download_url:
        print("❌ No download URL found")
        return None
    
    try:
        # Try without any special headers first
        response = requests.get(download_url, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Size: {len(response.content):,} bytes")
        
        # Quick check if it's actual file content
        content = response.content
        
        if content.startswith(b'PK\x03\x04'):
            print("   ✅ Got Excel/ZIP file!")
            return process_file_content(content, 'excel')
        elif content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            print("   ❌ Got HTML page (authentication required)")
            return None
        else:
            # Try as CSV
            try:
                text_content = content.decode('utf-8', errors='ignore')
                if ',' in text_content[:1000] or ';' in text_content[:1000]:
                    print("   📄 Might be CSV, trying to process...")
                    return process_file_content(content, 'csv')
            except:
                pass
            
            print("   ❓ Unknown content type")
            return None
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def try_authenticated_download():
    """Try download with authentication headers"""
    
    print("🔄 Trying authenticated download...")
    
    settings = load_settings()
    download_url = settings.get('download_url', '')
    username = settings.get('username', '')
    password = settings.get('password', '')
    
    if not all([download_url, username, password]):
        print("❌ Missing credentials")
        return None
    
    try:
        # Use session with authentication
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        # Try basic auth first
        session.auth = (username, password)
        
        response = session.get(download_url, timeout=30)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Size: {len(response.content):,} bytes")
        
        content = response.content
        
        if content.startswith(b'PK\x03\x04'):
            print("   ✅ Got Excel/ZIP file with auth!")
            return process_file_content(content, 'excel')
        elif content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            print("   ❌ Still getting HTML (complex auth required)")
            return None
        else:
            try:
                text_content = content.decode('utf-8', errors='ignore')
                if ',' in text_content[:1000] or ';' in text_content[:1000]:
                    print("   📄 Got CSV with auth!")
                    return process_file_content(content, 'csv')
            except:
                pass
            
            print("   ❓ Unknown content with auth")
            return None
    
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return None

def process_file_content(content, file_type):
    """Process the downloaded file content"""
    
    print(f"📊 Processing {file_type} content...")
    
    try:
        if file_type == 'excel':
            # Process as Excel
            df = pd.read_excel(io.BytesIO(content))
        elif file_type == 'csv':
            # Process as CSV
            text_content = content.decode('utf-8', errors='ignore')
            
            # Try different separators
            df = None
            for sep in [',', ';', '\t']:
                try:
                    test_df = pd.read_csv(io.StringIO(text_content), sep=sep)
                    if test_df.shape[1] > 1:  # More than one column
                        df = test_df
                        break
                except:
                    continue
            
            if df is None:
                print("   ❌ Could not parse CSV")
                return None
        else:
            print("   ❌ Unknown file type")
            return None
        
        print(f"   ✅ File processed successfully!")
        print(f"   📊 Rows: {df.shape[0]:,}")
        print(f"   📊 Columns: {df.shape[1]:,}")
        print(f"   📊 Column names: {list(df.columns)}")
        
        # Save files
        if file_type == 'excel':
            data_filename = "US_Bank_List_Real.xlsx"
            with open(data_filename, 'wb') as f:
                f.write(content)
        else:
            data_filename = "US_Bank_List_Real.csv"
            with open(data_filename, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        # Save JSON
        json_filename = "US_Bank_List_Real.json"
        json_data = df.to_json(orient='records', indent=2, date_format='iso')
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"\n💾 Files saved:")
        print(f"   📄 {data_filename}")
        print(f"   📄 {json_filename}")
        
        # Show preview
        print(f"\n📋 DATA PREVIEW:")
        print("-" * 80)
        print(df.head(10).to_string())
        print("-" * 80)
        if df.shape[0] > 10:
            print(f"... and {df.shape[0] - 10} more rows")
        
        return df
        
    except Exception as e:
        print(f"   ❌ Processing error: {e}")
        return None

def provide_instructions():
    """Provide clear instructions for manual download"""
    
    print("\n" + "="*70)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("="*70)
    
    settings = load_settings()
    
    print("\nSince automated download failed, here's the manual approach:")
    print()
    print("1. Open your web browser")
    print("2. Go to the direct download URL:")
    print(f"   {settings.get('download_url', 'No URL found')}")
    print()
    print("3. If prompted, sign in with:")
    print(f"   Username: {settings.get('username', 'No username found')}")
    print("   Password: [your password]")
    print()
    print("4. The file should download automatically")
    print("5. Save it in this directory as 'US_Bank_List_Real.xlsx' or 'US_Bank_List_Real.csv'")
    print()
    print("6. Then run:")
    print("   python process_local_file.py")
    print()
    print("This will process the file and convert it to JSON format.")
    print("="*70)

def main():
    """Main function"""
    
    print("🚀 Final SharePoint Download Solution")
    print("="*60)
    
    settings = load_settings()
    
    print(f"📋 Configuration:")
    print(f"   Username: {settings.get('username', 'Not set')}")
    print(f"   Download URL: {settings.get('download_url', 'Not set')}")
    print()
    
    # Try different approaches
    result = None
    
    # Approach 1: Simple download
    if not result:
        result = try_simple_download()
    
    # Approach 2: Authenticated download
    if not result:
        result = try_authenticated_download()
    
    # Show results
    if result is not None:
        print(f"\n🎯 SUCCESS!")
        print(f"✅ File downloaded and processed successfully")
        print(f"📊 Data contains {result.shape[0]} rows and {result.shape[1]} columns")
        print(f"💾 Files saved: US_Bank_List_Real.xlsx/.csv and .json")
    else:
        print(f"\n❌ Automated download failed")
        provide_instructions()
    
    print(f"\n✅ Process completed!")

if __name__ == "__main__":
    main()
