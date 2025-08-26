"""
SharePoint to JSON Converter
Downloads SharePoint file and converts to JSON format
Uses credentials from local.settings.json
"""

import pandas as pd
import requests
import io
import json
import os
from urllib.parse import urlparse, parse_qs
from requests_ntlm import HttpNtlmAuth
import base64

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

def try_sharepoint_api_methods(sharepoint_url, username, password):
    """Try SharePoint REST API methods to get the file"""
    
    print("🔄 Trying SharePoint REST API methods...")
    
    try:
        # Extract file information from the URL
        if ':x:' in sharepoint_url:
            # This is a sharing URL, try to convert to REST API call
            parts = sharepoint_url.split('/')
            for i, part in enumerate(parts):
                if 'sharepoint.com' in part:
                    base_url = '/'.join(parts[:i+1])
                    break
            
            # Try different API endpoints
            api_endpoints = [
                f"{base_url}/_api/web/GetFileByServerRelativeUrl",
                f"{base_url}/_api/web/lists/getbytitle('Documents')/items",
                f"{base_url}/_api/search/query"
            ]
            
            session = requests.Session()
            session.auth = HttpNtlmAuth(username, password)
            session.headers.update({
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            for endpoint in api_endpoints:
                try:
                    print(f"   Trying API endpoint: {endpoint}")
                    response = session.get(endpoint)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        return response
                        
                except Exception as e:
                    print(f"   API endpoint failed: {e}")
                    continue
    
    except Exception as e:
        print(f"❌ SharePoint API methods failed: {e}")
    
    return None

def try_direct_download_methods(sharepoint_url, username, password):
    """Try multiple direct download methods"""
    
    print("🔄 Trying direct download methods...")
    
    methods = []
    
    # Method 1: Convert sharing URL to download URL
    if ':x:' in sharepoint_url:
        download_url1 = sharepoint_url.replace(':x:', ':u:').replace('/view', '/download')
        methods.append(("SharePoint direct download", download_url1))
    
    # Method 2: Try to get direct file URL by adding download parameter
    if '?' in sharepoint_url:
        download_url2 = sharepoint_url + "&download=1"
    else:
        download_url2 = sharepoint_url + "?download=1"
    methods.append(("Download parameter method", download_url2))
    
    # Method 3: Try Excel Online REST API
    excel_api_url = sharepoint_url.replace(':x:', ':u:').replace('sharepoint.com/', 'sharepoint.com/_api/v2.0/')
    methods.append(("Excel Online API", excel_api_url))
    
    # Method 4: Try original URL with different auth
    methods.append(("Original URL with auth", sharepoint_url))
    
    for method_name, url in methods:
        try:
            print(f"   Trying {method_name}...")
            
            session = requests.Session()
            
            # Add comprehensive headers
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, application/json, text/csv, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            
            # Try different authentication methods
            auth_methods = [
                ('NTLM', HttpNtlmAuth(username, password)),
                ('Basic', requests.auth.HTTPBasicAuth(username, password)),
                ('None', None)
            ]
            
            for auth_name, auth in auth_methods:
                try:
                    print(f"     Using {auth_name} auth...")
                    session.auth = auth
                    
                    response = session.get(url, allow_redirects=True, timeout=30)
                    
                    print(f"     Status: {response.status_code}")
                    print(f"     Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"     Size: {len(response.content)} bytes")
                    
                    # Check if we got actual file content (not HTML)
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if (response.status_code == 200 and 
                        len(response.content) > 1000 and
                        'html' not in content_type and
                        not response.content.startswith(b'<!DOCTYPE') and
                        not response.content.startswith(b'<html')):
                        
                        print(f"✅ Successfully downloaded file using {method_name} with {auth_name} auth!")
                        return response
                        
                except Exception as e:
                    print(f"     {auth_name} auth failed: {e}")
                    continue
            
        except Exception as e:
            print(f"   {method_name} failed: {e}")
            continue
    
    return None

def convert_to_json(df, output_format='records'):
    """
    Convert DataFrame to JSON in various formats
    
    Args:
        df (pandas.DataFrame): DataFrame to convert
        output_format (str): JSON format - 'records', 'index', 'values', 'split', 'table'
    
    Returns:
        str: JSON string
    """
    
    if df is None:
        return None
    
    try:
        # Handle different JSON formats
        if output_format == 'records':
            # Each row as a separate object in an array
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
        elif output_format == 'index':
            # Index as keys, columns as nested objects
            json_data = df.to_json(orient='index', indent=2, date_format='iso')
        elif output_format == 'values':
            # Just the values as arrays
            json_data = df.to_json(orient='values', indent=2, date_format='iso')
        elif output_format == 'split':
            # Separate index, columns, and data
            json_data = df.to_json(orient='split', indent=2, date_format='iso')
        elif output_format == 'table':
            # Table schema format
            json_data = df.to_json(orient='table', indent=2, date_format='iso')
        else:
            # Default to records
            json_data = df.to_json(orient='records', indent=2, date_format='iso')
        
        return json_data
    
    except Exception as e:
        print(f"❌ Error converting to JSON: {e}")
        return None

def save_json_file(json_data, filename="sharepoint_data.json"):
    """Save JSON data to file"""
    
    if not json_data:
        print("❌ No JSON data to save")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        print(f"💾 JSON data saved to: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")
        return False

def display_json_preview(json_data, max_lines=50):
    """Display a preview of the JSON data"""
    
    if not json_data:
        print("❌ No JSON data to display")
        return
    
    print("\n" + "="*80)
    print("📋 JSON DATA PREVIEW")
    print("="*80)
    
    lines = json_data.split('\n')
    total_lines = len(lines)
    
    print(f"📊 Total JSON lines: {total_lines}")
    print(f"📄 Showing first {min(max_lines, total_lines)} lines:")
    print("-" * 80)
    
    for i in range(min(max_lines, total_lines)):
        print(f"{i+1:4d}: {lines[i]}")
    
    if total_lines > max_lines:
        print(f"... ({total_lines - max_lines} more lines)")
    
    print("-" * 80)
    print(f"📏 Total JSON size: {len(json_data)} characters")

def main():
    """Main function to download SharePoint file and convert to JSON"""
    
    print("🔗 SharePoint to JSON Converter")
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
    
    # Try SharePoint API methods first
    response = try_sharepoint_api_methods(sharepoint_url, username, password)
    
    # If API methods fail, try direct download
    if not response:
        response = try_direct_download_methods(sharepoint_url, username, password)
    
    if not response:
        print("❌ All download methods failed")
        print("💡 Try downloading the file manually from SharePoint")
        return None
    
    # Try to read the file content
    try:
        print("\n🔄 Processing downloaded content...")
        
        # Try to read as Excel file first
        try:
            file_content = io.BytesIO(response.content)
            df = pd.read_excel(file_content)
            print(f"✅ Excel file processed: {df.shape[0]} rows × {df.shape[1]} columns")
        except Exception as excel_error:
            print(f"   Excel processing failed: {excel_error}")
            
            # Try to read as CSV
            try:
                file_content = io.StringIO(response.content.decode('utf-8'))
                df = pd.read_csv(file_content)
                print(f"✅ CSV file processed: {df.shape[0]} rows × {df.shape[1]} columns")
            except Exception as csv_error:
                print(f"   CSV processing failed: {csv_error}")
                
                # Save raw content for manual inspection
                with open('sharepoint_raw_download.bin', 'wb') as f:
                    f.write(response.content)
                print(f"📁 Raw content saved as 'sharepoint_raw_download.bin'")
                print(f"   Content preview: {response.content[:200]}...")
                return None
        
        # Convert to JSON in multiple formats
        print(f"\n📊 DATA SUMMARY:")
        print(f"   Rows: {df.shape[0]}")
        print(f"   Columns: {df.shape[1]}")
        print(f"   Column names: {list(df.columns)}")
        
        # Offer different JSON formats
        print(f"\n💾 JSON FORMAT OPTIONS:")
        print("1. Records format (array of objects)")
        print("2. Index format (indexed objects)")
        print("3. Values format (arrays only)")
        print("4. Table format (with schema)")
        print("5. All formats")
        
        try:
            choice = input("\nEnter choice (1-5, or Enter for option 1): ").strip()
        except:
            choice = "1"
        
        formats = {
            '1': [('records', 'sharepoint_data_records.json')],
            '2': [('index', 'sharepoint_data_index.json')],
            '3': [('values', 'sharepoint_data_values.json')],
            '4': [('table', 'sharepoint_data_table.json')],
            '5': [
                ('records', 'sharepoint_data_records.json'),
                ('index', 'sharepoint_data_index.json'),
                ('values', 'sharepoint_data_values.json'),
                ('table', 'sharepoint_data_table.json')
            ]
        }
        
        selected_formats = formats.get(choice, formats['1'])
        
        for format_type, filename in selected_formats:
            print(f"\n🔄 Converting to {format_type} format...")
            json_data = convert_to_json(df, format_type)
            
            if json_data:
                # Save JSON file
                if save_json_file(json_data, filename):
                    print(f"✅ {format_type.capitalize()} JSON saved successfully")
                
                # Show preview for first format
                if format_type == selected_formats[0][0]:
                    display_json_preview(json_data)
        
        return df
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return None

if __name__ == "__main__":
    try:
        df = main()
        
        if df is not None:
            print(f"\n🎯 SUCCESS! SharePoint file converted to JSON")
            print(f"📊 Processed {df.shape[0]} rows and {df.shape[1]} columns")
        else:
            print(f"\n❌ FAILED to download or convert SharePoint file")
            
    except KeyboardInterrupt:
        print(f"\n👋 Process cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print(f"\n🎯 Process completed!")
