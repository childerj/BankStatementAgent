#!/usr/bin/env powershell
# Copy Bank Statement Function files to repository
param(
    [Parameter(Mandatory=$true)]
    [string]$DestinationPath
)

Write-Host "📋 Copying Bank Statement Function files..."

# Source directory
$SourceDir = "c:\Users\jeff.childers\Documents\Bank Statement Reconciliation"

# Essential files to copy
$FilesToCopy = @(
    "function_app.py",
    "requirements.txt", 
    "host.json",
    "local.settings.json",
    ".gitignore",
    "README.md"
)

# Essential folders to copy
$FoldersToInclude = @()

# Test files (optional)
$TestFiles = @(
    "test_*.py",
    "*.ps1"
)

# Create destination if it doesn't exist
if (!(Test-Path $DestinationPath)) {
    New-Item -ItemType Directory -Path $DestinationPath -Force
    Write-Host "✅ Created directory: $DestinationPath"
}

# Copy main files
foreach ($file in $FilesToCopy) {
    $sourcePath = Join-Path $SourceDir $file
    if (Test-Path $sourcePath) {
        Copy-Item $sourcePath $DestinationPath -Force
        Write-Host "✅ Copied: $file"
    } else {
        Write-Host "⚠️ Not found: $file"
    }
}

# Copy test files
Write-Host "📋 Copying test files..."
Get-ChildItem -Path $SourceDir -Filter "test_*.py" | ForEach-Object {
    Copy-Item $_.FullName $DestinationPath -Force
    Write-Host "✅ Copied: $($_.Name)"
}

Get-ChildItem -Path $SourceDir -Filter "*.ps1" | ForEach-Object {
    Copy-Item $_.FullName $DestinationPath -Force
    Write-Host "✅ Copied: $($_.Name)"
}

Write-Host "🎉 Copy complete! Files copied to: $DestinationPath"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. cd '$DestinationPath'"
Write-Host "2. git add ."
Write-Host "3. git commit -m 'Add Azure Function Bank Statement Processing'"
Write-Host "4. git push"
