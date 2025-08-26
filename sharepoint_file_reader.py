"""
SharePoint File Reader
Accesses SharePoint files and returns all rows and columns
Supports Excel files (.xlsx, .xls) and CSV files
"""

import pandas as pd
import requests
from requests_ntlm import HttpNtlmAuth
import os
from urllib.parse import urlparse, parse_qs
import io
import getpass
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

class SharePointFileReader:
    def __init__(self, username=None, password=None):
        """
        Initialize SharePoint file reader
        
        Args:
            username (str): SharePoint username (if None, will prompt)
            password (str): SharePoint password (if None, will prompt)
        """
        self.username = username or input("Enter SharePoint username: ")
        self.password = password or getpass.getpass("Enter SharePoint password: ")
        
    def extract_sharepoint_info(self, sharepoint_url):
        """
        Extract SharePoint site URL and file path from SharePoint link
        
        Args:
            sharepoint_url (str): SharePoint file URL
            
        Returns:
            tuple: (site_url, file_path, file_name)
        """
        try:
            # Parse the URL
            parsed_url = urlparse(sharepoint_url)
            
            # Extract site URL (everything before the file part)
            if 'sharepoint.com' in parsed_url.netloc:
                # Handle personal OneDrive URLs
                if '-my.sharepoint.com' in parsed_url.netloc:
                    site_url = f"{parsed_url.scheme}://{parsed_url.netloc}/personal/"
                    # Extract user and file info from path
                    path_parts = parsed_url.path.split('/')
                    if len(path_parts) > 3:
                        user_part = path_parts[3]
                        site_url += user_part
                else:
                    # Handle regular SharePoint sites
                    site_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    
                # Extract file path from query parameters
                query_params = parse_qs(parsed_url.query)
                if 'file' in query_params:
                    file_path = query_params['file'][0]
                elif 'id' in query_params:
                    file_path = query_params['id'][0]
                else:
                    # Try to extract from path
                    file_path = parsed_url.path
                    
                file_name = os.path.basename(file_path)
                
                return site_url, file_path, file_name
                
        except Exception as e:
            print(f"Error parsing SharePoint URL: {e}")
            return None, None, None
    
    def read_file_method1_direct_download(self, sharepoint_url):
        """
        Method 1: Direct download using requests (works for public/accessible files)
        
        Args:
            sharepoint_url (str): SharePoint file URL
            
        Returns:
            pandas.DataFrame: File content as DataFrame
        """
        try:
            # Try to convert SharePoint URL to direct download URL
            if 'sharepoint.com' in sharepoint_url and '?e=' in sharepoint_url:
                # Extract the file ID and convert to download URL
                base_url = sharepoint_url.split('?')[0]
                download_url = base_url.replace(':x:', ':u:').replace('/view', '/download')
                
                # Download the file
                response = requests.get(download_url, auth=HttpNtlmAuth(self.username, self.password))
                response.raise_for_status()
                
                # Determine file type and read accordingly
                file_content = io.BytesIO(response.content)
                
                if sharepoint_url.lower().endswith(('.xlsx', '.xls')) or 'excel' in response.headers.get('content-type', '').lower():
                    df = pd.read_excel(file_content)
                elif sharepoint_url.lower().endswith('.csv') or 'csv' in response.headers.get('content-type', '').lower():
                    df = pd.read_csv(file_content)
                else:
                    # Try Excel first, then CSV
                    try:
                        df = pd.read_excel(file_content)
                    except:
                        file_content.seek(0)
                        df = pd.read_csv(file_content)
                
                return df
                
        except Exception as e:
            print(f"Method 1 failed: {e}")
            return None
    
    def read_file_method2_office365_api(self, sharepoint_url):
        """
        Method 2: Using Office365 REST API
        
        Args:
            sharepoint_url (str): SharePoint file URL
            
        Returns:
            pandas.DataFrame: File content as DataFrame
        """
        try:
            site_url, file_path, file_name = self.extract_sharepoint_info(sharepoint_url)
            
            if not site_url or not file_path:
                raise ValueError("Could not parse SharePoint URL")
            
            # Authenticate with SharePoint
            ctx_auth = AuthenticationContext(site_url)
            if ctx_auth.acquire_token_for_user(self.username, self.password):
                ctx = ClientContext(site_url, ctx_auth)
                
                # Get the file
                response = File.open_binary(ctx, file_path)
                
                # Read file content
                file_content = io.BytesIO(response.content)
                
                # Determine file type and read accordingly
                if file_name.lower().endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_content)
                elif file_name.lower().endswith('.csv'):
                    df = pd.read_csv(file_content)
                else:
                    # Try Excel first, then CSV
                    try:
                        df = pd.read_excel(file_content)
                    except:
                        file_content.seek(0)
                        df = pd.read_csv(file_content)
                
                return df
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            print(f"Method 2 failed: {e}")
            return None
    
    def read_file_method3_manual_download(self, file_path):
        """
        Method 3: Read manually downloaded file
        
        Args:
            file_path (str): Local file path
            
        Returns:
            pandas.DataFrame: File content as DataFrame
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type and read accordingly
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
            
            return df
            
        except Exception as e:
            print(f"Method 3 failed: {e}")
            return None
    
    def read_sharepoint_file(self, sharepoint_url):
        """
        Main method to read SharePoint file - tries multiple methods
        
        Args:
            sharepoint_url (str): SharePoint file URL
            
        Returns:
            pandas.DataFrame: File content as DataFrame
        """
        print(f"Attempting to read SharePoint file: {sharepoint_url}")
        
        # Method 1: Direct download
        print("\n🔄 Trying Method 1: Direct download...")
        df = self.read_file_method1_direct_download(sharepoint_url)
        if df is not None:
            print("✅ Method 1 successful!")
            return df
        
        # Method 2: Office365 API
        print("\n🔄 Trying Method 2: Office365 API...")
        df = self.read_file_method2_office365_api(sharepoint_url)
        if df is not None:
            print("✅ Method 2 successful!")
            return df
        
        # Method 3: Ask user to download manually
        print("\n❌ Automatic methods failed.")
        print("Please download the file manually and provide the local path:")
        local_path = input("Enter local file path: ")
        
        if local_path.strip():
            print(f"\n🔄 Trying Method 3: Reading local file...")
            df = self.read_file_method3_manual_download(local_path.strip())
            if df is not None:
                print("✅ Method 3 successful!")
                return df
        
        print("❌ All methods failed. Could not read the file.")
        return None
    
    def display_file_info(self, df):
        """
        Display information about the DataFrame
        
        Args:
            df (pandas.DataFrame): DataFrame to analyze
        """
        if df is None:
            print("No data to display")
            return
        
        print("\n" + "="*60)
        print("📊 FILE INFORMATION")
        print("="*60)
        print(f"📐 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"📋 Columns: {list(df.columns)}")
        print(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        print("\n" + "="*60)
        print("🔍 DATA PREVIEW (First 10 rows)")
        print("="*60)
        print(df.head(10).to_string())
        
        print("\n" + "="*60)
        print("📈 COLUMN INFORMATION")
        print("="*60)
        print(df.info())
        
        print("\n" + "="*60)
        print("📊 SUMMARY STATISTICS")
        print("="*60)
        print(df.describe(include='all'))
    
    def save_to_local(self, df, output_file="sharepoint_data.xlsx"):
        """
        Save DataFrame to local file
        
        Args:
            df (pandas.DataFrame): DataFrame to save
            output_file (str): Output file name
        """
        if df is None:
            print("No data to save")
            return
        
        try:
            if output_file.lower().endswith('.xlsx'):
                df.to_excel(output_file, index=False)
            elif output_file.lower().endswith('.csv'):
                df.to_csv(output_file, index=False)
            else:
                df.to_excel(f"{output_file}.xlsx", index=False)
                output_file = f"{output_file}.xlsx"
            
            print(f"✅ Data saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")


def main():
    """
    Main function to demonstrate SharePoint file reading
    """
    print("🔗 SharePoint File Reader")
    print("="*40)
    
    # Get SharePoint URL
    sharepoint_url = input("Enter SharePoint file URL: ").strip()
    
    if not sharepoint_url:
        print("❌ No URL provided")
        return
    
    # Initialize reader
    reader = SharePointFileReader()
    
    # Read the file
    df = reader.read_sharepoint_file(sharepoint_url)
    
    if df is not None:
        # Display file information
        reader.display_file_info(df)
        
        # Ask if user wants to save locally
        save_choice = input("\n💾 Save data to local file? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_name = input("Enter output filename (default: sharepoint_data.xlsx): ").strip()
            if not output_name:
                output_name = "sharepoint_data.xlsx"
            reader.save_to_local(df, output_name)
        
        return df
    else:
        print("❌ Failed to read SharePoint file")
        return None


if __name__ == "__main__":
    # Example usage
    df = main()
    
    # If you want to use this programmatically:
    """
    # Direct usage example:
    reader = SharePointFileReader(username="your_username", password="your_password")
    df = reader.read_sharepoint_file("your_sharepoint_url")
    if df is not None:
        print("All rows and columns:")
        print(df)
    """
