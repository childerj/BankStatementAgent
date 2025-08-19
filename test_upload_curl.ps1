# PowerShell script to upload a test file using curl
$testFile = "C:\Users\jeff.childers\Documents\Bank Statement Reconciliation\Test Docs\811.pdf"
$containerName = "incoming-bank-statements"
$blobName = "test-811.pdf"

# Check if test file exists
if (!(Test-Path $testFile)) {
    Write-Host "❌ Test file not found: $testFile"
    exit 1
}

Write-Host "📄 Using test file: 811.pdf"
Write-Host "📤 Uploading $blobName to $containerName container..."

# Try to upload using curl with proper authorization headers
# Using the Azurite shared key
$accountName = "devstoreaccount1"
$accountKey = "Eby8vdM02xNOcfz1c+hQr5UjCGr7Tm6+UqKz2N8lDpvwO8jBJx3vXJ4f7XJqjn9rUk1+0j/VKqGF2L+1fQJz/rw=="
$url = "http://127.0.0.1:10000/$accountName/$containerName/$blobName"

# Get current date for authorization header
$date = [DateTime]::UtcNow.ToString("R")

Write-Host "🔍 Attempting upload to: $url"

# Create authorization signature (simplified for testing)
$stringToSign = "PUT`n`n`n" + (Get-Item $testFile).Length + "`n`n`napplication/octet-stream`n`n`n`n`n`nx-ms-blob-type:BlockBlob`nx-ms-date:$date`nx-ms-version:2020-10-02`n/$accountName/$containerName/$blobName"

Write-Host "📝 Date: $date"

# Use curl to upload
curl -X PUT $url `
    -H "x-ms-date: $date" `
    -H "x-ms-version: 2020-10-02" `
    -H "x-ms-blob-type: BlockBlob" `
    -H "Content-Type: application/octet-stream" `
    --data-binary "@$testFile" `
    -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Successfully uploaded $blobName"
    Write-Host "🔍 Watch the function logs for trigger activity..."
} else {
    Write-Host "❌ Failed to upload file"
}
