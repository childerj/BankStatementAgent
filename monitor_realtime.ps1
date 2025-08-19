# Real-time Function Monitor
# This script continuously monitors your Azure Function activity

Write-Host "========================================" -ForegroundColor Green
Write-Host "  REAL-TIME FUNCTION MONITOR" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

$storageAccount = "jeffchildersa6d3"

# Track last known state
$lastBai2Count = 0
$lastArchivedCount = 0

# Get initial counts using separate containers (not nested)
$initialBai2 = (az storage blob list --account-name $storageAccount --container-name "bai2-outputs" --auth-mode login --only-show-errors --query "[?name != '.placeholder']" | ConvertFrom-Json).Count
$initialArchived = (az storage blob list --account-name $storageAccount --container-name "archive" --auth-mode login --only-show-errors --query "[?name != '.placeholder']" | ConvertFrom-Json).Count

Write-Host "🔄 Starting monitor..." -ForegroundColor Cyan
Write-Host "📊 Initial state: $initialBai2 BAI2 files, $initialArchived archived files" -ForegroundColor Gray
Write-Host ""

$lastBai2Count = $initialBai2
$lastArchivedCount = $initialArchived

while ($true) {
    Start-Sleep -Seconds 10  # Check every 10 seconds
    
    # Get current counts using separate containers
    $currentBai2 = (az storage blob list --account-name $storageAccount --container-name "bai2-outputs" --auth-mode login --only-show-errors --query "[?name != '.placeholder']" | ConvertFrom-Json).Count
    $currentArchived = (az storage blob list --account-name $storageAccount --container-name "archive" --auth-mode login --only-show-errors --query "[?name != '.placeholder']" | ConvertFrom-Json).Count
    
    # Check for new activity
    if ($currentBai2 -gt $lastBai2Count -or $currentArchived -gt $lastArchivedCount) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        if ($currentBai2 -gt $lastBai2Count) {
            Write-Host "[$timestamp] 🎉 NEW BAI2 FILE CREATED! Total: $currentBai2 (+$($currentBai2 - $lastBai2Count))" -ForegroundColor Green
            
            # Get the newest file
            $newestBai2 = az storage blob list --account-name $storageAccount --container-name "bai2-outputs" --auth-mode login --only-show-errors --query "[?name != '.placeholder'] | sort_by(@, &properties.lastModified) | reverse(@) | [0]" | ConvertFrom-Json
            if ($newestBai2) {
                $fileName = $newestBai2.name
                $size = [math]::Round($newestBai2.properties.contentLength / 1024, 1)
                Write-Host "[$timestamp] 📄 File: $fileName ($size KB)" -ForegroundColor White
            }
        }
        
        if ($currentArchived -gt $lastArchivedCount) {
            Write-Host "[$timestamp] 📁 ORIGINAL FILE ARCHIVED! Total: $currentArchived (+$($currentArchived - $lastArchivedCount))" -ForegroundColor Blue
        }
        
        $lastBai2Count = $currentBai2
        $lastArchivedCount = $currentArchived
        Write-Host ""
    } else {
        # Show heartbeat every minute
        if ((Get-Date).Second -eq 0) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] 💓 Monitoring... (BAI2: $currentBai2, Archived: $currentArchived)" -ForegroundColor DarkGray
        }
    }
    
    # Check for pending files
    $pendingFiles = (az storage blob list --account-name $storageAccount --container-name "incoming-bank-statements" --auth-mode login --only-show-errors --query "[?name != '.placeholder']" | ConvertFrom-Json).Count
    if ($pendingFiles -gt 0) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "[$timestamp] ⏳ $pendingFiles file(s) waiting for processing..." -ForegroundColor Yellow
    }
}
