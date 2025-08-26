"""
SharePoint File Reader - Non-Interactive Version
This version can work with manually downloaded files or with hardcoded credentials
"""

import pandas as pd
import os

def read_downloaded_file(file_path):
    """
    Read a file that was manually downloaded from SharePoint
    
    Args:
        file_path (str): Path to the downloaded file
    
    Returns:
        pandas.DataFrame: File content
    """
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        print(f"📂 Reading file: {file_path}")
        
        # Determine file type and read accordingly
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
            print(f"✅ Excel file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
            print(f"✅ CSV file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
        else:
            # Try Excel first, then CSV
            try:
                df = pd.read_excel(file_path)
                print(f"✅ Excel file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
            except:
                df = pd.read_csv(file_path)
                print(f"✅ CSV file read successfully: {df.shape[0]} rows × {df.shape[1]} columns")
        
        return df
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def display_complete_data(df):
    """
    Display all rows and columns with detailed information
    
    Args:
        df (pandas.DataFrame): DataFrame to display
    """
    if df is None:
        print("❌ No data to display")
        return
    
    print("\n" + "="*100)
    print("📊 COMPLETE FILE ANALYSIS")
    print("="*100)
    
    # Basic info
    print(f"📐 Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    print(f"📋 Column names: {list(df.columns)}")
    
    # Data types
    print("\n🔍 COLUMN DATA TYPES:")
    print("-" * 50)
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].count()
        null_count = df[col].isnull().sum()
        print(f"  {col}: {dtype} ({non_null} non-null, {null_count} null)")
    
    # Display all data
    print("\n📋 ALL ROWS AND COLUMNS:")
    print("="*100)
    
    # Set pandas options to display everything
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 100)
    
    print(df)
    
    # Reset pandas options
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')
    
    print("="*100)
    print(f"✅ Displayed complete dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    
    # Summary statistics
    print("\n📈 SUMMARY STATISTICS:")
    print("-" * 50)
    try:
        summary = df.describe(include='all')
        print(summary)
    except Exception as e:
        print(f"Could not generate summary statistics: {e}")

def save_to_excel(df, filename="sharepoint_complete_data.xlsx"):
    """
    Save DataFrame to Excel with formatting
    
    Args:
        df (pandas.DataFrame): Data to save
        filename (str): Output filename
    """
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"💾 Data saved to Excel file: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving to Excel: {e}")

# Check for common file names in the current directory
def find_potential_files():
    """Look for Excel or CSV files in the current directory"""
    current_dir = os.getcwd()
    potential_files = []
    
    for file in os.listdir(current_dir):
        if file.lower().endswith(('.xlsx', '.xls', '.csv')):
            potential_files.append(file)
    
    return potential_files

# Main execution
if __name__ == "__main__":
    print("📁 SharePoint File Reader - Downloaded File Version")
    print("="*60)
    
    # Look for potential files
    potential_files = find_potential_files()
    
    if potential_files:
        print(f"🔍 Found {len(potential_files)} potential data files in current directory:")
        for i, file in enumerate(potential_files, 1):
            file_size = os.path.getsize(file) / 1024  # KB
            print(f"  {i}. {file} ({file_size:.1f} KB)")
        
        print(f"\n📋 You can:")
        print("1. Specify a file number from above")
        print("2. Enter a custom file path")
        print("3. Download your SharePoint file to this directory first")
        
        choice = input(f"\nEnter file number (1-{len(potential_files)}) or custom path: ").strip()
        
        # Check if it's a number
        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(potential_files):
                selected_file = potential_files[file_index]
            else:
                print("❌ Invalid file number")
                selected_file = choice
        except ValueError:
            selected_file = choice
    else:
        print("🔍 No Excel or CSV files found in current directory")
        print("\n💡 Options:")
        print("1. Download your SharePoint file to this directory")
        print("2. Specify the full path to your downloaded file")
        
        selected_file = input("\nEnter file path: ").strip()
    
    if selected_file:
        # Remove quotes if present
        selected_file = selected_file.strip('"\'')
        
        print(f"\n🔄 Processing file: {selected_file}")
        
        # Read the file
        df = read_downloaded_file(selected_file)
        
        if df is not None:
            # Display complete data
            display_complete_data(df)
            
            # Ask if user wants to save to Excel
            print(f"\n💾 Save formatted version to Excel?")
            save_choice = input("Enter 'y' to save, or press Enter to skip: ").strip().lower()
            
            if save_choice == 'y':
                output_name = input("Enter output filename (default: sharepoint_complete_data.xlsx): ").strip()
                if not output_name:
                    output_name = "sharepoint_complete_data.xlsx"
                if not output_name.endswith('.xlsx'):
                    output_name += '.xlsx'
                save_to_excel(df, output_name)
        
        else:
            print("❌ Failed to read the file")
    
    else:
        print("❌ No file specified")
    
    print(f"\n🎯 Process completed!")
    print(f"📁 Current directory: {os.getcwd()}")
