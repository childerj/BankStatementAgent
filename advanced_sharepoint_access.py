"""
Advanced SharePoint File Access
Handles SharePoint sharing links with proper authentication flows
"""

import pandas as pd
import requests
import io
import json
import re
import time
from urllib.parse import urlparse, parse_qs, unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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

def create_robust_session():
    """Create a robust session with retry strategy"""
    session = requests.Session()
    
    # Set up retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set comprehensive headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    return session

def extract_sharepoint_details(sharepoint_url):
    """Extract SharePoint site and file details from URL"""
    try:
        parsed = urlparse(sharepoint_url)
        
        # Extract tenant and site information
        host_parts = parsed.netloc.split('.')
        if len(host_parts) >= 2:
            tenant = host_parts[0]
            
        # Extract file ID from the URL
        path_parts = parsed.path.split('/')
        
        # Look for the file identifier in the URL
        file_id = None
        for part in path_parts:
            if len(part) > 20 and '-' in part:  # Likely a file ID
                file_id = part
                break
        
        # Extract from query parameters
        query_params = parse_qs(parsed.query)
        
        return {
            'tenant': tenant if 'tenant' in locals() else None,
            'host': parsed.netloc,
            'path': parsed.path,
            'file_id': file_id,
            'query_params': query_params,
            'full_url': sharepoint_url
        }
    except Exception as e:
        print(f"Error extracting SharePoint details: {e}")
        return None

def microsoft_login_flow(session, username, password):
    """Handle Microsoft/Azure AD login flow"""
    print("🔐 Starting Microsoft authentication flow...")
    
    try:
        # Step 1: Get the initial login page
        login_url = "https://login.microsoftonline.com/common/oauth2/authorize"
        
        login_params = {
            'client_id': '00000003-0000-0ff1-ce00-000000000000',
            'response_type': 'code+id_token',
            'response_mode': 'form_post',
            'resource': '00000003-0000-0ff1-ce00-000000000000',
            'scope': 'openid',
            'redirect_uri': 'https://worldacceptance-my.sharepoint.com/_forms/default.aspx'
        }
        
        print("   Getting login page...")
        response = session.get(login_url, params=login_params)
        
        if response.status_code != 200:
            print(f"   Failed to get login page: {response.status_code}")
            return False
        
        # Step 2: Extract form data from login page
        html_content = response.text
        
        # Find the login form
        form_action = None
        flow_token = None
        canary = None
        
        # Extract form action
        form_match = re.search(r'<form[^>]*action="([^"]*)"', html_content)
        if form_match:
            form_action = form_match.group(1)
        
        # Extract flow token
        flow_token_match = re.search(r'name="flowToken"[^>]*value="([^"]*)"', html_content)
        if flow_token_match:
            flow_token = flow_token_match.group(1)
        
        # Extract canary token
        canary_match = re.search(r'name="canary"[^>]*value="([^"]*)"', html_content)
        if canary_match:
            canary = canary_match.group(1)
        
        if not all([form_action, flow_token, canary]):
            print("   Could not extract required login form data")
            return False
        
        print("   Submitting credentials...")
        
        # Step 3: Submit credentials
        login_data = {
            'i13': '0',
            'login': username,
            'loginfmt': username,
            'type': '11',
            'LoginOptions': '3',
            'lrt': '',
            'lrtPartition': '',
            'hisRegion': '',
            'hisScaleUnit': '',
            'passwd': password,
            'ps': '2',
            'psRNGCDefaultType': '',
            'psRNGCEntropy': '',
            'psRNGCSLK': '',
            'canary': canary,
            'ctx': '',
            'hpgrequestid': '',
            'flowToken': flow_token,
            'PPSX': '',
            'NewUser': '1',
            'FoundMSAs': '',
            'fspost': '0',
            'i21': '0',
            'CookieDisclosure': '0',
            'IsFidoSupported': '1',
            'isSignupPost': '0',
            'i19': '12345'
        }
        
        # Update headers for form submission
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': response.url
        })
        
        auth_response = session.post(form_action, data=login_data)
        
        if auth_response.status_code == 200:
            print("   ✅ Authentication successful")
            return True
        else:
            print(f"   ❌ Authentication failed: {auth_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return False

def try_sharepoint_download_with_auth(sharepoint_url, username, password):
    """Try to download SharePoint file with proper authentication"""
    
    print("🔄 Attempting SharePoint download with authentication...")
    
    session = create_robust_session()
    
    try:
        # Step 1: Visit the SharePoint URL to trigger authentication
        print("   Visiting SharePoint URL...")
        response = session.get(sharepoint_url, allow_redirects=True)
        
        # Check if we're redirected to login
        if 'login.microsoftonline.com' in response.url:
            print("   Authentication required, starting login flow...")
            
            if not microsoft_login_flow(session, username, password):
                return None
            
            # Try the SharePoint URL again after authentication
            print("   Retrying SharePoint URL after authentication...")
            response = session.get(sharepoint_url, allow_redirects=True)
        
        # Step 2: Try to find direct download links in the page
        if response.status_code == 200:
            html_content = response.text
            
            # Look for download URLs in the HTML
            download_patterns = [
                r'"downloadUrl":"([^"]*)"',
                r'"@microsoft.graph.downloadUrl":"([^"]*)"',
                r'data-url="([^"]*download[^"]*)"',
                r'href="([^"]*download[^"]*)"'
            ]
            
            for pattern in download_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    download_url = match.replace('\\u0026', '&').replace('\\/', '/')
                    
                    print(f"   Found potential download URL: {download_url[:100]}...")
                    
                    try:
                        # Try to download from this URL
                        download_response = session.get(download_url, allow_redirects=True)
                        
                        if (download_response.status_code == 200 and 
                            len(download_response.content) > 1000 and
                            not download_response.content.startswith(b'<!DOCTYPE')):
                            
                            content_type = download_response.headers.get('content-type', '').lower()
                            print(f"   ✅ Successfully downloaded file!")
                            print(f"      Content-Type: {content_type}")
                            print(f"      Size: {len(download_response.content)} bytes")
                            
                            return download_response
                            
                    except Exception as e:
                        print(f"   Download attempt failed: {e}")
                        continue
        
        # Step 3: Try alternative download methods
        sp_details = extract_sharepoint_details(sharepoint_url)
        if sp_details:
            
            # Try converting sharing URL to direct download
            alternative_urls = []
            
            if ':x:' in sharepoint_url:
                # Method 1: Replace :x: with :u: and add download
                alt_url1 = sharepoint_url.replace(':x:', ':u:').replace('/view', '/download')
                alternative_urls.append(alt_url1)
                
                # Method 2: Use Word Online download endpoint
                alt_url2 = sharepoint_url.replace(':x:', ':w:').replace('/view', '/download')
                alternative_urls.append(alt_url2)
            
            for alt_url in alternative_urls:
                try:
                    print(f"   Trying alternative URL: {alt_url[:100]}...")
                    alt_response = session.get(alt_url, allow_redirects=True)
                    
                    if (alt_response.status_code == 200 and 
                        len(alt_response.content) > 1000 and
                        not alt_response.content.startswith(b'<!DOCTYPE')):
                        
                        print(f"   ✅ Alternative download successful!")
                        return alt_response
                        
                except Exception as e:
                    print(f"   Alternative URL failed: {e}")
                    continue
        
        print("   ❌ Could not find valid download URL")
        return None
        
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return None

def process_file_to_json(response):
    """Process downloaded file and convert to JSON"""
    
    if not response:
        return None
    
    print("\n🔄 Processing downloaded file...")
    
    try:
        # Try Excel first
        try:
            file_content = io.BytesIO(response.content)
            df = pd.read_excel(file_content)
            print(f"✅ Excel file processed: {df.shape[0]} rows × {df.shape[1]} columns")
        except Exception as excel_error:
            print(f"   Excel processing failed: {excel_error}")
            
            # Try CSV
            try:
                file_content = io.StringIO(response.content.decode('utf-8'))
                df = pd.read_csv(file_content)
                print(f"✅ CSV file processed: {df.shape[0]} rows × {df.shape[1]} columns")
            except Exception as csv_error:
                print(f"   CSV processing failed: {csv_error}")
                return None
        
        # Convert to JSON
        print(f"\n📊 DATA SUMMARY:")
        print(f"   Rows: {df.shape[0]}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Column names: {list(df.columns)}")
        
        # Create JSON in records format (most common)
        json_data = df.to_json(orient='records', indent=2, date_format='iso')
        
        # Save JSON file
        filename = "sharepoint_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"\n💾 JSON data saved to: {filename}")
        
        # Show preview
        lines = json_data.split('\n')
        print(f"\n📋 JSON PREVIEW (first 20 lines):")
        print("-" * 60)
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:3d}: {line}")
        
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print("-" * 60)
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return None

def main():
    """Main function"""
    
    print("🚀 Advanced SharePoint File Access")
    print("="*50)
    
    # Load settings
    settings = load_settings()
    
    username = settings['username']
    password = settings['password']
    sharepoint_url = settings['file_url']
    
    if not all([username, password, sharepoint_url]):
        print("❌ Missing SharePoint credentials or URL in local.settings.json")
        return None
    
    print(f"👤 Username: {username}")
    print(f"🔗 URL: {sharepoint_url}")
    print()
    
    # Try to download the file
    response = try_sharepoint_download_with_auth(sharepoint_url, username, password)
    
    if response:
        # Process and convert to JSON
        df = process_file_to_json(response)
        
        if df is not None:
            print(f"\n🎯 SUCCESS! SharePoint file accessed and converted to JSON")
            print(f"📊 Total: {df.shape[0]} rows × {df.shape[1]} columns")
            return df
        else:
            print(f"\n❌ Failed to process the downloaded file")
    else:
        print(f"\n❌ Failed to download SharePoint file")
        print(f"💡 The file might require different permissions or be in a different location")
    
    return None

if __name__ == "__main__":
    try:
        result = main()
        
        if result is not None:
            print(f"\n✅ PROCESS COMPLETED SUCCESSFULLY")
        else:
            print(f"\n❌ PROCESS FAILED")
            print(f"💡 Next steps:")
            print(f"   1. Check if the SharePoint URL is correct")
            print(f"   2. Verify your credentials have access to the file")
            print(f"   3. Try downloading the file manually from SharePoint")
            
    except KeyboardInterrupt:
        print(f"\n👋 Process cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print(f"\n🎯 Done!")
