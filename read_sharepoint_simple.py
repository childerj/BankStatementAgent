"""
Simple SharePoint File Reader
Quick script to access your specific SharePoint file
"""

import pandas as pd
import requests
import io
import sys
from urllib.parse import urlparse, parse_qs
import base64

def get_credentials():
    """Get SharePoint credentials with better error handling"""
    try:
        username = input("Enter SharePoint username (e.g., user@company.com): ")
        # Use regular input instead of getpass for better compatibility
        password = input("Enter SharePoint password: ")
        return username, password
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return None, None
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        return None, None

def try_multiple_download_methods(sharepoint_url, username, password):
    """Try multiple methods to download the SharePoint file"""
    
    methods = []
    
    # Method 1: Direct URL replacement
    if ':x:' in sharepoint_url:
        download_url1 = sharepoint_url.replace(':x:', ':u:').replace('/view', '/download')
        methods.append(("Direct download (method 1)", download_url1))
    
    # Method 2: Add download parameter
    if '?' in sharepoint_url:
        download_url2 = sharepoint_url + "&download=1"
    else:
        download_url2 = sharepoint_url + "?download=1"
    methods.append(("Download parameter", download_url2))
    
    # Method 3: Try original URL
    methods.append(("Original URL", sharepoint_url))
    
    # Method 4: Try without authentication (public link)
    methods.append(("Public access", sharepoint_url))
    
    for method_name, url in methods:
        try:
            print(f"🔄 Trying {method_name}...")
            
            session = requests.Session()
            
            # Add various headers
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, text/csv, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9'
            })
            
            # Try with authentication for first 3 methods
            if method_name != "Public access":
                session.auth = (username, password)
            
            response = session.get(url, allow_redirects=True, timeout=30)
            
            print(f"   Status code: {response.status_code}")
            print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Content length: {len(response.content)} bytes")
            
            if response.status_code == 200 and len(response.content) > 100:
                return response
            elif response.status_code == 302 or response.status_code == 301:
                print(f"   Redirect detected, following...")
                continue
            else:
                print(f"   Method failed")
                
        except Exception as e:
            print(f"   Error with {method_name}: {e}")
            continue
    
    return None

def read_sharepoint_file_simple(sharepoint_url, username=None, password=None):
    """
    Enhanced method to read SharePoint file with multiple fallback options
    
    Args:
        sharepoint_url (str): Your SharePoint file URL
        username (str): SharePoint username (optional)
        password (str): SharePoint password (optional)
    
    Returns:
        pandas.DataFrame: File content
    """
    
    # Get credentials if not provided
    if not username or not password:
        print("SharePoint authentication required...")
        username, password = get_credentials()
        if not username or not password:
            return None
    
    print(f"🔄 Attempting to access SharePoint file...")
    print(f"📋 URL: {sharepoint_url}")
    print(f"👤 User: {username}")
    
    try:
        # Try multiple download methods
        response = try_multiple_download_methods(sharepoint_url, username, password)
        
        if response and response.status_code == 200:
            print("✅ File downloaded successfully!")
            
            # Determine file type from content-type header or URL
            content_type = response.headers.get('content-type', '').lower()
            
            # Try to read as Excel file first
            try:
                file_content = io.BytesIO(response.content)
                df = pd.read_excel(file_content)
                print(f"📊 Excel file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
                return df
            except Exception as excel_error:
                print(f"   Excel read failed: {excel_error}")
                
                # Try to read as CSV
                try:
                    # Try UTF-8 first
                    file_content = io.StringIO(response.content.decode('utf-8'))
                    df = pd.read_csv(file_content)
                    print(f"📊 CSV file (UTF-8) read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
                    return df
                except:
                    try:
                        # Try different encoding
                        file_content = io.StringIO(response.content.decode('cp1252'))
                        df = pd.read_csv(file_content)
                        print(f"📊 CSV file (CP1252) read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
                        return df
                    except Exception as csv_error:
                        print(f"   CSV read failed: {csv_error}")
                        
                        # Save the raw content for inspection
                        with open('sharepoint_download_debug.bin', 'wb') as f:
                            f.write(response.content)
                        print(f"� Raw content saved as 'sharepoint_download_debug.bin' for inspection")
                        print(f"   Content preview: {response.content[:200]}...")
                        return None
        else:
            print("❌ All download methods failed")
            return None
            
    except Exception as e:
        print(f"❌ Error accessing SharePoint: {e}")
        return None

def read_local_file(file_path):
    """
    Read a locally downloaded file
    
    Args:
        file_path (str): Path to local file
    
    Returns:
        pandas.DataFrame: File content
    """
    try:
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            # Try Excel first, then CSV
            try:
                df = pd.read_excel(file_path)
            except:
                df = pd.read_csv(file_path)
        
        print(f"✅ Local file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
        return df
        
    except Exception as e:
        print(f"❌ Error reading local file: {e}")
        return None

def display_all_data(df):
    """
    Display all rows and columns of the DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame to display
    """
    if df is None:
        print("❌ No data to display")
        return
    
    print("\n" + "="*80)
    print("📋 ALL ROWS AND COLUMNS")
    print("="*80)
    print(f"📐 Total Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"📝 Column Names: {list(df.columns)}")
    print("\n📊 COMPLETE DATA:")
    print("-"*80)
    
    # Set pandas options to display all rows and columns
    with pd.option_context('display.max_rows', None, 
                          'display.max_columns', None, 
                          'display.width', None, 
                          'display.max_colwidth', 50):
        print(df)
    
    print("-"*80)
    print(f"✅ Displayed all {df.shape[0]} rows and {df.shape[1]} columns")

def save_data(df, filename="sharepoint_data.xlsx"):
    """
    Save DataFrame to local file
    
    Args:
        df (pandas.DataFrame): Data to save
        filename (str): Output filename
    """
    if df is None:
        print("❌ No data to save")
        return
    
    try:
        if filename.lower().endswith('.xlsx'):
            df.to_excel(filename, index=False)
        elif filename.lower().endswith('.csv'):
            df.to_csv(filename, index=False)
        else:
            df.to_excel(f"{filename}.xlsx", index=False)
            filename = f"{filename}.xlsx"
        
        print(f"💾 Data saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")

# Main execution
if __name__ == "__main__":
    print("🔗 SharePoint File Reader - Enhanced Version")
    print("="*50)
    
    # Your SharePoint URL
    sharepoint_url = "https://worldacceptance-my.sharepoint.com/:x:/p/jeff_childers/EU4h9XwapzZJi-e4dyYJb0YBZwxc7MOub-iR77WMS-Fr6A?e=BLmOuR"
    
    print(f"📋 Target file: {sharepoint_url}")
    print("\n" + "="*50)
    
    # Try to read the SharePoint file
    df = read_sharepoint_file_simple(sharepoint_url)
    
    if df is not None:
        # Display all data
        display_all_data(df)
        
        # Ask if user wants to save
        try:
            save_choice = input("\n💾 Save data to local file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = input("Enter filename (default: sharepoint_data.xlsx): ").strip()
                if not filename:
                    filename = "sharepoint_data.xlsx"
                save_data(df, filename)
        except KeyboardInterrupt:
            print("\n👋 Program ended by user")
    else:
        print("\n" + "="*50)
        print("💡 ALTERNATIVE OPTIONS:")
        print("="*50)
        print("1. Download the file manually from your browser:")
        print("   - Open the SharePoint URL in your browser")
        print("   - Sign in if prompted")
        print("   - Click 'Download' or 'Save As'")
        print("   - Save to this folder and run the script again")
        print()
        print("2. Try with different credentials")
        print("3. Check if the file permissions allow access")
        print()
        
        try:
            manual_choice = input("Would you like to specify a local file path? (y/n): ").strip().lower()
            if manual_choice == 'y':
                local_path = input("Enter local file path: ").strip()
                if local_path:
                    df = read_local_file(local_path)
                    if df is not None:
                        display_all_data(df)
                        
                        save_choice = input("\n💾 Save data to different file? (y/n): ").strip().lower()
                        if save_choice == 'y':
                            filename = input("Enter filename (default: sharepoint_data.xlsx): ").strip()
                            if not filename:
                                filename = "sharepoint_data.xlsx"
                            save_data(df, filename)
        except KeyboardInterrupt:
            print("\n👋 Program ended by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    print("\n🎯 Program completed!")
