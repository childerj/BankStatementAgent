"""
Robust File Processor for SharePoint Downloads
Handles various file formats and encoding issues
"""

import pandas as pd
import requests
import io
import json
import chardet
import mimetypes
from pathlib import Path

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

def analyze_file_content(content):
    """Analyze downloaded content to determine file type and encoding"""
    
    print("🔍 Analyzing downloaded content...")
    
    # Save raw content for inspection
    with open('downloaded_file_raw.bin', 'wb') as f:
        f.write(content)
    
    print(f"   File size: {len(content)} bytes")
    print(f"   First 100 bytes: {content[:100]}")
    
    # Check if it's HTML (error page)
    if content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
        print("   ❌ Content appears to be HTML (likely an error page)")
        return None, None, None
    
    # Detect encoding for text files
    encoding = None
    if len(content) > 0:
        try:
            detected = chardet.detect(content)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)
            print(f"   Detected encoding: {encoding} (confidence: {confidence:.2f})")
        except:
            encoding = 'utf-8'
    
    # Check file signature/magic bytes
    file_type = None
    
    # Excel formats
    if content.startswith(b'PK\x03\x04') and b'xl/' in content[:1000]:
        file_type = 'xlsx'
        print("   📊 File appears to be Excel (.xlsx)")
    elif content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        file_type = 'xls'
        print("   📊 File appears to be Excel (.xls)")
    
    # CSV/Text formats
    elif encoding and all(ord(char) < 128 for char in content[:1000].decode(encoding, errors='ignore')):
        # Check if it looks like CSV
        sample_text = content[:2000].decode(encoding, errors='ignore')
        comma_count = sample_text.count(',')
        semicolon_count = sample_text.count(';')
        tab_count = sample_text.count('\t')
        newline_count = sample_text.count('\n')
        
        if newline_count > 0:
            avg_commas_per_line = comma_count / newline_count
            avg_semicolons_per_line = semicolon_count / newline_count
            avg_tabs_per_line = tab_count / newline_count
            
            if avg_commas_per_line > 1:
                file_type = 'csv_comma'
                print(f"   📄 File appears to be CSV (comma-separated)")
            elif avg_semicolons_per_line > 1:
                file_type = 'csv_semicolon'
                print(f"   📄 File appears to be CSV (semicolon-separated)")
            elif avg_tabs_per_line > 1:
                file_type = 'csv_tab'
                print(f"   📄 File appears to be CSV (tab-separated)")
            else:
                file_type = 'text'
                print(f"   📄 File appears to be plain text")
    
    # JSON format
    elif encoding:
        try:
            sample_text = content[:1000].decode(encoding, errors='ignore').strip()
            if (sample_text.startswith('{') and sample_text.endswith('}')) or \
               (sample_text.startswith('[') and sample_text.endswith(']')):
                file_type = 'json'
                print("   📄 File appears to be JSON")
        except:
            pass
    
    if not file_type:
        print("   ❓ Could not determine file type")
    
    return file_type, encoding, content

def try_read_excel(content, file_type):
    """Try to read Excel file with various engines"""
    
    print("📊 Attempting to read as Excel file...")
    
    engines = ['openpyxl', 'xlrd']
    
    for engine in engines:
        try:
            print(f"   Trying engine: {engine}")
            file_obj = io.BytesIO(content)
            
            if file_type == 'xlsx':
                df = pd.read_excel(file_obj, engine=engine)
            elif file_type == 'xls':
                df = pd.read_excel(file_obj, engine=engine)
            else:
                df = pd.read_excel(file_obj, engine=engine)
            
            print(f"   ✅ Success with {engine}: {df.shape[0]} rows × {df.shape[1]} columns")
            return df
            
        except Exception as e:
            print(f"   ❌ {engine} failed: {e}")
            continue
    
    return None

def try_read_csv(content, encoding, file_type):
    """Try to read CSV file with various separators and settings"""
    
    print("📄 Attempting to read as CSV file...")
    
    # Determine separator
    separators = {
        'csv_comma': ',',
        'csv_semicolon': ';',
        'csv_tab': '\t',
        'text': ','  # Default to comma
    }
    
    separator = separators.get(file_type, ',')
    
    # Try different separators if not specified
    if file_type == 'text':
        separators_to_try = [',', ';', '\t', '|']
    else:
        separators_to_try = [separator]
    
    encodings_to_try = [encoding, 'utf-8', 'cp1252', 'iso-8859-1', 'utf-16']
    
    for enc in encodings_to_try:
        if not enc:
            continue
            
        for sep in separators_to_try:
            try:
                print(f"   Trying encoding: {enc}, separator: '{sep}'")
                
                text_content = content.decode(enc, errors='ignore')
                file_obj = io.StringIO(text_content)
                
                # Try various CSV reading parameters
                csv_params = [
                    {'sep': sep},
                    {'sep': sep, 'quotechar': '"'},
                    {'sep': sep, 'quotechar': "'"},
                    {'sep': sep, 'skipinitialspace': True},
                    {'sep': sep, 'engine': 'python'},
                    {'sep': sep, 'engine': 'python', 'error_bad_lines': False}
                ]
                
                for params in csv_params:
                    try:
                        file_obj.seek(0)
                        df = pd.read_csv(file_obj, **params)
                        
                        if df.shape[0] > 0 and df.shape[1] > 1:
                            print(f"   ✅ Success with encoding {enc}, separator '{sep}': {df.shape[0]} rows × {df.shape[1]} columns")
                            return df
                            
                    except Exception as param_error:
                        continue
                        
            except Exception as e:
                continue
    
    return None

def try_read_json(content, encoding):
    """Try to read JSON file"""
    
    print("📄 Attempting to read as JSON file...")
    
    encodings_to_try = [encoding, 'utf-8', 'cp1252', 'iso-8859-1']
    
    for enc in encodings_to_try:
        if not enc:
            continue
            
        try:
            print(f"   Trying encoding: {enc}")
            text_content = content.decode(enc, errors='ignore')
            json_data = json.loads(text_content)
            
            # Convert to DataFrame
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                df = pd.DataFrame([json_data])
            else:
                df = pd.DataFrame({'data': [json_data]})
            
            print(f"   ✅ Success: {df.shape[0]} rows × {df.shape[1]} columns")
            return df
            
        except Exception as e:
            print(f"   ❌ Encoding {enc} failed: {e}")
            continue
    
    return None

def robust_file_processor(content):
    """Process downloaded content with multiple fallback methods"""
    
    if not content or len(content) == 0:
        print("❌ No content to process")
        return None
    
    # Analyze the content
    file_type, encoding, content = analyze_file_content(content)
    
    if not file_type:
        print("❌ Could not determine file type")
        return None
    
    # Try appropriate reader based on file type
    df = None
    
    if file_type in ['xlsx', 'xls']:
        df = try_read_excel(content, file_type)
    
    if not df and file_type in ['csv_comma', 'csv_semicolon', 'csv_tab', 'text']:
        df = try_read_csv(content, encoding, file_type)
    
    if not df and file_type == 'json':
        df = try_read_json(content, encoding)
    
    # If specific type failed, try all methods
    if not df:
        print("🔄 Specific method failed, trying all methods...")
        
        # Try Excel
        df = try_read_excel(content, 'unknown')
        
        # Try CSV
        if not df:
            df = try_read_csv(content, encoding, 'text')
        
        # Try JSON
        if not df:
            df = try_read_json(content, encoding)
    
    return df

def download_and_process():
    """Download SharePoint file and process it"""
    
    print("🚀 Robust SharePoint File Processor")
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
    
    # Download the file (simplified approach)
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Try the :u: conversion method
        download_url = sharepoint_url.replace(':x:', ':u:').replace('/view', '/download')
        
        print(f"🔄 Downloading from: {download_url}")
        response = session.get(download_url, allow_redirects=True)
        
        if response.status_code == 200:
            print(f"✅ Download successful: {len(response.content)} bytes")
            
            # Process the content
            df = robust_file_processor(response.content)
            
            if df is not None:
                print(f"\n📊 FILE PROCESSED SUCCESSFULLY!")
                print(f"   Rows: {df.shape[0]}")
                print(f"   Columns: {df.shape[1]}")
                print(f"   Column names: {list(df.columns)}")
                
                # Convert to JSON
                json_data = df.to_json(orient='records', indent=2, date_format='iso')
                
                # Save JSON
                with open('sharepoint_data.json', 'w', encoding='utf-8') as f:
                    f.write(json_data)
                
                print(f"\n💾 JSON saved to: sharepoint_data.json")
                
                # Show preview
                print(f"\n📋 DATA PREVIEW:")
                print("-" * 80)
                print(df.head(10).to_string())
                print("-" * 80)
                
                return df
            else:
                print(f"\n❌ Could not process the downloaded file")
                return None
        else:
            print(f"❌ Download failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    try:
        result = download_and_process()
        
        if result is not None:
            print(f"\n🎯 SUCCESS! File processed and converted to JSON")
        else:
            print(f"\n❌ FAILED to process file")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print(f"\n✅ Process completed!")
