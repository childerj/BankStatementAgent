"""
Improved SharePoint Direct Download with Authentication
Handles authentication flow for direct download URLs
"""

import json
import requests
import pandas as pd
import io
from urllib.parse import urlparse, parse_qs
import time

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

def authenticate_and_download():
    """Authenticate with SharePoint and download the file"""
    
    print("🚀 SharePoint Authentication & Download")
    print("="*60)
    
    # Load settings
    settings = load_settings()
    
    download_url = settings.get('download_url', '')
    username = settings.get('username', '')
    password = settings.get('password', '')
    
    if not all([download_url, username, password]):
        print("❌ Missing required settings in local.settings.json")
        return None
    
    print(f"👤 Username: {username}")
    print(f"🔗 Download URL: {download_url}")
    print()
    
    # Create session with persistent cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        # Step 1: Initial request to get authentication challenge
        print("🔄 Step 1: Initial authentication request...")
        response = session.get(download_url, allow_redirects=True)
        
        print(f"   Status: {response.status_code}")
        print(f"   Final URL: {response.url}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        # Check if we're at a login page
        if 'login.microsoftonline.com' in response.url or 'signin' in response.url.lower():
            print("   📝 Authentication required - found login page")
            
            # Look for authentication form
            content = response.text
            
            # Try to find the login form
            if 'loginfmt' in content:
                print("🔄 Step 2: Submitting username...")
                
                # This is a simplified approach - real implementation would need
                # to parse the form properly and handle all hidden fields
                print("   ⚠️  Complex authentication flow detected")
                print("   💡 Recommendation: Use browser automation or manual download")
                
                return None
        
        # Step 2: Check if we got the actual file
        content = response.content
        content_type = response.headers.get('content-type', '').lower()
        
        print(f"\n🔍 Content Analysis:")
        print(f"   Size: {len(content):,} bytes")
        print(f"   Content-Type: {content_type}")
        print(f"   First 100 bytes: {content[:100]}")
        
        # Check for various file types
        if content.startswith(b'PK\x03\x04'):
            print("   ✅ Appears to be Excel/ZIP file!")
            return process_excel_file(content)
        
        elif 'application/vnd.ms-excel' in content_type or 'application/vnd.openxmlformats' in content_type:
            print("   ✅ Excel content type detected!")
            return process_excel_file(content)
        
        elif content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
            print("   ❌ Still getting HTML page - authentication failed")
            
            # Save HTML for inspection
            with open('auth_page.html', 'w', encoding='utf-8') as f:
                f.write(content.decode('utf-8', errors='ignore'))
            print("   💾 Saved HTML to: auth_page.html")
            
            return None
        
        else:
            print("   ❓ Unknown content type")
            # Try to process as CSV anyway
            try:
                csv_string = content.decode('utf-8', errors='ignore')
                if ',' in csv_string or ';' in csv_string:
                    print("   📄 Attempting CSV processing...")
                    return process_csv_content(csv_string)
            except:
                pass
            
            return None
    
    except Exception as e:
        print(f"❌ Error during authentication/download: {e}")
        return None

def process_excel_file(content):
    """Process Excel file content"""
    
    try:
        print("📊 Processing Excel file...")
        
        # Read as Excel
        df = pd.read_excel(io.BytesIO(content))
        
        print(f"   ✅ Excel processed successfully!")
        print(f"   📊 Rows: {df.shape[0]:,}")
        print(f"   📊 Columns: {df.shape[1]:,}")
        print(f"   📊 Column names: {list(df.columns)}")
        
        # Save files
        excel_filename = "sharepoint_download.xlsx"
        with open(excel_filename, 'wb') as f:
            f.write(content)
        
        json_filename = "sharepoint_download.json"
        json_data = df.to_json(orient='records', indent=2, date_format='iso')
        with open(json_filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"\n💾 Files saved:")
        print(f"   📄 {excel_filename}")
        print(f"   📄 {json_filename}")
        
        # Show preview
        print(f"\n📋 DATA PREVIEW:")
        print("-" * 80)
        print(df.head(10).to_string())
        print("-" * 80)
        
        return df
        
    except Exception as e:
        print(f"   ❌ Error processing Excel: {e}")
        return None

def process_csv_content(csv_string):
    """Process CSV content"""
    
    try:
        print("📄 Processing CSV content...")
        
        # Try different separators
        for sep in [',', ';', '\t']:
            try:
                df = pd.read_csv(io.StringIO(csv_string), sep=sep)
                if df.shape[1] > 1:  # More than one column suggests correct separator
                    print(f"   ✅ CSV processed with separator '{sep}'!")
                    print(f"   📊 Rows: {df.shape[0]:,}")
                    print(f"   📊 Columns: {df.shape[1]:,}")
                    print(f"   📊 Column names: {list(df.columns)}")
                    
                    # Save files
                    csv_filename = "sharepoint_download.csv"
                    with open(csv_filename, 'w', encoding='utf-8') as f:
                        f.write(csv_string)
                    
                    json_filename = "sharepoint_download.json"
                    json_data = df.to_json(orient='records', indent=2, date_format='iso')
                    with open(json_filename, 'w', encoding='utf-8') as f:
                        f.write(json_data)
                    
                    print(f"\n💾 Files saved:")
                    print(f"   📄 {csv_filename}")
                    print(f"   📄 {json_filename}")
                    
                    # Show preview
                    print(f"\n📋 DATA PREVIEW:")
                    print("-" * 80)
                    print(df.head(10).to_string())
                    print("-" * 80)
                    
                    return df
            except:
                continue
        
        print("   ❌ Could not parse as CSV")
        return None
        
    except Exception as e:
        print(f"   ❌ Error processing CSV: {e}")
        return None

def alternative_solutions():
    """Show alternative solutions"""
    
    print("\n" + "="*60)
    print("ALTERNATIVE SOLUTIONS")
    print("="*60)
    print()
    print("Since direct download requires complex authentication,")
    print("here are alternative approaches:")
    print()
    print("1. MANUAL DOWNLOAD (Fastest)")
    print("   - Open browser, go to SharePoint URL")
    print("   - Sign in and download manually")
    print("   - Use process_local_file.py to convert")
    print()
    print("2. BROWSER AUTOMATION")
    print("   - Use browser_automation.py (requires Selenium)")
    print("   - Automates the browser authentication")
    print()
    print("3. MICROSOFT GRAPH API")
    print("   - Enterprise solution with app registration")
    print("   - Requires admin permissions")
    print()
    print("4. CHECK FOR SIMPLER DOWNLOAD URL")
    print("   - Some SharePoint links work with ?download=1")
    print("   - Others require full authentication flow")
    print()

def main():
    """Main function"""
    
    result = authenticate_and_download()
    
    if result is not None:
        print(f"\n🎯 SUCCESS! File downloaded and processed")
    else:
        print(f"\n❌ Authentication/download failed")
        alternative_solutions()
    
    print(f"\n✅ Process completed!")

if __name__ == "__main__":
    main()
