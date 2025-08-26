"""
SharePoint File Reader - Settings-Based Version
Reads credentials and file URL from local.settings.json
"""

import pandas as pd
import requests
import io
import json
import os
from urllib.parse import urlparse, parse_qs

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

def update_settings(username=None, password=None, file_url=None):
    """Update settings in local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        if username is not None:
            settings['Values']['SHAREPOINT_USERNAME'] = username
        if password is not None:
            settings['Values']['SHAREPOINT_PASSWORD'] = password
        if file_url is not None:
            settings['Values']['SHAREPOINT_FILE_URL'] = file_url
        
        with open('local.settings.json', 'w') as f:
            json.dump(settings, f, indent=2)
        
        print("✅ Settings updated in local.settings.json")
        
    except Exception as e:
        print(f"❌ Error updating settings: {e}")

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

def read_sharepoint_file():
    """
    Read SharePoint file using settings from local.settings.json
    
    Returns:
        pandas.DataFrame: File content
    """
    
    # Load settings
    settings = load_settings()
    
    username = settings['username']
    password = settings['password']
    sharepoint_url = settings['file_url']
    
    print(f"📋 Loaded settings from local.settings.json")
    print(f"   Username: {'*' * len(username) if username else '(not set)'}")
    print(f"   Password: {'*' * len(password) if password else '(not set)'}")
    print(f"   File URL: {sharepoint_url if sharepoint_url else '(not set)'}")
    
    # Check if we need to get missing information
    update_needed = False
    
    if not sharepoint_url:
        sharepoint_url = input("Enter SharePoint file URL: ")
        if sharepoint_url:
            update_settings(file_url=sharepoint_url)
            update_needed = True
    
    if not username:
        username = input("Enter SharePoint username: ")
        if username:
            update_settings(username=username)
            update_needed = True
    
    if not password:
        password = input("Enter SharePoint password: ")
        if password:
            save_pwd = input("Save password to settings? (y/n): ").strip().lower()
            if save_pwd == 'y':
                update_settings(password=password)
                update_needed = True
    
    if not username or not password or not sharepoint_url:
        print("❌ Missing required settings")
        return None
    
    print(f"\n🔄 Attempting to access SharePoint file...")
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

def show_current_settings():
    """Display current settings from local.settings.json"""
    settings = load_settings()
    
    print("\n📋 CURRENT SETTINGS")
    print("="*50)
    print(f"Username: {settings['username'] if settings['username'] else '(not set)'}")
    print(f"Password: {'*' * len(settings['password']) if settings['password'] else '(not set)'}")
    print(f"File URL: {settings['file_url'] if settings['file_url'] else '(not set)'}")
    print("="*50)

# Main execution
if __name__ == "__main__":
    print("🔗 SharePoint File Reader - Settings-Based Version")
    print("="*60)
    print("📁 Uses credentials and file URL from local.settings.json")
    
    # Show current settings
    show_current_settings()
    
    # Ask what user wants to do
    print("\n💡 Options:")
    print("1. Read file using current settings")
    print("2. Update settings and read file")
    print("3. Just update settings")
    
    try:
        choice = input("\nEnter choice (1-3, or Enter for option 1): ").strip()
        
        if choice == "3":
            # Just update settings
            username = input("Enter SharePoint username (or Enter to skip): ").strip()
            password = input("Enter SharePoint password (or Enter to skip): ").strip()
            file_url = input("Enter SharePoint file URL (or Enter to skip): ").strip()
            
            if username or password or file_url:
                update_settings(
                    username=username if username else None,
                    password=password if password else None,
                    file_url=file_url if file_url else None
                )
            
            show_current_settings()
        
        else:
            # Try to read the SharePoint file
            df = read_sharepoint_file()
            
            if df is not None:
                # Display all data
                display_all_data(df)
                
                # Ask if user wants to save
                save_choice = input("\n💾 Save data to local file? (y/n): ").strip().lower()
                if save_choice == 'y':
                    filename = input("Enter filename (default: sharepoint_data.xlsx): ").strip()
                    if not filename:
                        filename = "sharepoint_data.xlsx"
                    save_data(df, filename)
            else:
                print("\n❌ Failed to read SharePoint file")
                print("💡 Try updating your settings or downloading the file manually")
        
    except KeyboardInterrupt:
        print("\n👋 Program ended by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n🎯 Program completed!")
