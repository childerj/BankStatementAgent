"""
SharePoint File Reader - Direct Credentials Version
You can hardcode your credentials in this version for easier testing
"""

import pandas as pd
import requests
import io
import sys
from urllib.parse import urlparse, parse_qs

# ==========================================
# ENTER YOUR CREDENTIALS HERE (OPTIONAL)
# ==========================================
SHAREPOINT_USERNAME = ""  # e.g., "jeff.childers@worldacceptance.com"
SHAREPOINT_PASSWORD = ""  # Enter your password here if you want to skip prompts

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
            if method_name != "Public access" and username and password:
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

def read_sharepoint_file(sharepoint_url, username=None, password=None):
    """
    Read SharePoint file with flexible credential input
    
    Args:
        sharepoint_url (str): Your SharePoint file URL
        username (str): SharePoint username
        password (str): SharePoint password
    
    Returns:
        pandas.DataFrame: File content
    """
    
    # Use hardcoded credentials if available
    if not username and SHAREPOINT_USERNAME:
        username = SHAREPOINT_USERNAME
        print(f"👤 Using hardcoded username: {username}")
    
    if not password and SHAREPOINT_PASSWORD:
        password = SHAREPOINT_PASSWORD
        print(f"🔑 Using hardcoded password")
    
    # Get credentials from user if not provided
    if not username:
        username = input("Enter SharePoint username: ")
    
    if not password:
        password = input("Enter SharePoint password: ")
    
    if not username or not password:
        print("❌ Username and password are required")
        return None
    
    print(f"🔄 Attempting to access SharePoint file...")
    print(f"📋 URL: {sharepoint_url}")
    print(f"👤 User: {username}")
    
    try:
        # Try multiple download methods
        response = try_multiple_download_methods(sharepoint_url, username, password)
        
        if response and response.status_code == 200:
            print("✅ File downloaded successfully!")
            
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
                        print(f"📁 Raw content saved as 'sharepoint_download_debug.bin' for inspection")
                        print(f"   Content preview: {response.content[:200]}...")
                        return None
        else:
            print("❌ All download methods failed")
            return None
            
    except Exception as e:
        print(f"❌ Error accessing SharePoint: {e}")
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
    print("🔗 SharePoint File Reader - Direct Credentials Version")
    print("="*60)
    
    # Your SharePoint URL
    sharepoint_url = "https://worldacceptance-my.sharepoint.com/:x:/p/jeff_childers/EU4h9XwapzZJi-e4dyYJb0YBZwxc7MOub-iR77WMS-Fr6A?e=BLmOuR"
    
    print(f"📋 Target file: {sharepoint_url}")
    
    # Check if credentials are hardcoded
    if SHAREPOINT_USERNAME and SHAREPOINT_PASSWORD:
        print("🔑 Using hardcoded credentials")
        username, password = SHAREPOINT_USERNAME, SHAREPOINT_PASSWORD
    else:
        print("\n💡 You can edit this file and set SHAREPOINT_USERNAME and SHAREPOINT_PASSWORD")
        print("   at the top to avoid entering credentials each time")
        print("\n" + "="*60)
        username, password = None, None
    
    # Try to read the SharePoint file
    df = read_sharepoint_file(sharepoint_url, username, password)
    
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
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\n" + "="*60)
        print("❌ FAILED TO ACCESS FILE")
        print("="*60)
        print("💡 Possible solutions:")
        print("1. Check your username and password")
        print("2. Download the file manually from SharePoint")
        print("3. Check file permissions")
        print("4. Try accessing the file in a browser first")
    
    print("\n🎯 Program completed!")
