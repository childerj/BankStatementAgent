# Azure Storage Cleanup Programs

This folder contains programs to clean up old files from the Azure Storage container while preserving important .placeholder files.

## Files Included

- **`cleanup_storage.py`** - Python version of the cleanup program
- **`cleanup_storage.ps1`** - PowerShell version of the cleanup program  
- **`cleanup_storage.bat`** - Windows batch file for easy launching
- **`cleanup_storage_README.md`** - This documentation file

## What It Does

The cleanup programs will:

✅ **KEEP**: All `.placeholder` files (these are important for folder structure)
❌ **DELETE**: All other files in the following folders:
   - `archive/` - Old PDF bank statements
   - `bai2-outputs/` - Generated BAI2 files

## Safety Features

- **Dry Run Mode**: By default, shows what WOULD be deleted without actually deleting
- **Confirmation Prompts**: Requires explicit confirmation for live deletion
- **Detailed Logging**: Shows exactly what files are found and what actions are taken
- **Error Handling**: Gracefully handles connection issues and file access problems

## Usage Options

### Option 1: Python Script (Recommended)

```bash
# Preview what would be deleted (safe)
python cleanup_storage.py

# Actually delete files (requires confirmation)
python cleanup_storage.py --execute

# Show help
python cleanup_storage.py --help
```

### Option 2: PowerShell Script

```powershell
# Preview what would be deleted (safe)
.\cleanup_storage.ps1

# Actually delete files (requires confirmation)  
.\cleanup_storage.ps1 -Execute

# Show help
.\cleanup_storage.ps1 -Help
```

### Option 3: Easy Batch Launcher

```cmd
# Run the interactive menu
cleanup_storage.bat
```

## Prerequisites

### For Python Version:
- Python 3.6 or later
- Azure Storage SDK: `pip install azure-storage-blob`
- Connection string in `local.settings.json` or `AzureWebJobsStorage` environment variable

### For PowerShell Version:
- PowerShell 5.1 or later
- Azure PowerShell module: `Install-Module Az.Storage`
- Connection string in `local.settings.json` or `AzureWebJobsStorage` environment variable

## Connection Configuration

The programs look for the Azure Storage connection string in this order:

1. **local.settings.json** file (preferred):
   ```json
   {
     "Values": {
       "AzureWebJobsStorage": "DefaultEndpointsProtocol=https;AccountName=..."
     }
   }
   ```

2. **Environment variable**: `AzureWebJobsStorage`

## Example Output

```
🧹 Azure Storage Cleanup Program
============================================================
Mode: DRY RUN (preview only)
Time: 2025-08-26 11:28:07
✅ Using connection string from local.settings.json

🔗 Connected to Azure Storage
📦 Container: bank-reconciliation

📁 Processing folder: archive/
============================================================
   📊 Found 3 files in 'archive/'
   ✅ KEEP: archive/.placeholder (placeholder file)
   🗑️  WOULD DELETE: archive/WACBAI2_20250825.pdf
   🗑️  WOULD DELETE: archive/WACBAI_20250825.pdf

📁 Processing folder: bai2-outputs/
============================================================
   📊 Found 3 files in 'bai2-outputs/'
   ✅ KEEP: bai2-outputs/.placeholder (placeholder file)
   🗑️  WOULD DELETE: bai2-outputs/WACBAI2_20250825.bai
   🗑️  WOULD DELETE: bai2-outputs/WACBAI_20250825.bai

🎯 FINAL SUMMARY
============================================================
📊 Total files found: 6
🗑️  Files to delete: 4
✅ Placeholder files kept: 2

⚠️  This was a DRY RUN - no files were actually deleted
   Run with --execute to perform actual deletion
```

## Safety Recommendations

1. **Always run in dry run mode first** to preview what will be deleted
2. **Backup important files** before running live deletion
3. **Verify connection string** is pointing to the correct storage account
4. **Check the container name** is "bank-reconciliation" 
5. **Monitor the output** to ensure only expected files are being deleted

## Troubleshooting

**Connection Issues:**
- Verify your connection string is correct
- Check that the storage account exists and is accessible
- Ensure proper permissions on the storage account

**Module Installation Issues:**
- Python: `pip install azure-storage-blob`
- PowerShell: `Install-Module Az.Storage -Force -Scope CurrentUser`

**Permission Issues:**
- Ensure the connection string has delete permissions
- Check that your account has proper Azure Storage roles

## Security Notes

- Connection strings contain sensitive information - keep them secure
- The programs only access the specified container and folders
- No data is transmitted outside of your Azure environment
- All operations are logged for audit purposes
