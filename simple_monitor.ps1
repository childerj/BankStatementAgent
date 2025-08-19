# Simple Function Monitor
# This script continuously monitors your Azure Function activity

Write-Host "========================================" -ForegroundColor Green
Write-Host "  AZURE FUNCTION MONITOR" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

$storageAccount = "jeffchildersa6d3"

# Track last known state
$lastBai2Count = 0
$lastArchivedCount = 0

# Function to get blob count safely
function Get-BlobCount {
    param($containerName)
    try {
        $result = az storage blob list --account-name $storageAccount --container-name $containerName --auth-mode login --only-show-errors 2>$null | ConvertFrom-Json
        if ($result) {
            return $result.Count
        } else {
            return 0
        }
    } catch {
        return 0
    }
}

# Get initial counts
Write-Host "Getting initial state..." -ForegroundColor Cyan
$initialBai2 = Get-BlobCount "bai2-outputs"
$initialArchived = Get-BlobCount "archive"
$initialPending = Get-BlobCount "incoming-bank-statements"

Write-Host "Initial state: $initialBai2 BAI2 files, $initialArchived archived files, $initialPending pending files" -ForegroundColor Gray
Write-Host ""

$lastBai2Count = $initialBai2
$lastArchivedCount = $initialArchived

$iteration = 0

while ($true) {
    Start-Sleep -Seconds 15  # Check every 15 seconds
    $iteration++
    
    # Get current counts
    $currentBai2 = Get-BlobCount "bai2-outputs"
    $currentArchived = Get-BlobCount "archive"
    $currentPending = Get-BlobCount "incoming-bank-statements"
    
    # Check for new activity
    if ($currentBai2 -gt $lastBai2Count -or $currentArchived -gt $lastArchivedCount) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        if ($currentBai2 -gt $lastBai2Count) {
            $newFiles = $currentBai2 - $lastBai2Count
            Write-Host "[$timestamp] SUCCESS! NEW BAI2 FILE CREATED! Total: $currentBai2 (+$newFiles)" -ForegroundColor Green
        }
        
        if ($currentArchived -gt $lastArchivedCount) {
            $newArchived = $currentArchived - $lastArchivedCount
            Write-Host "[$timestamp] SUCCESS! ORIGINAL FILE ARCHIVED! Total: $currentArchived (+$newArchived)" -ForegroundColor Blue
        }
        
        $lastBai2Count = $currentBai2
        $lastArchivedCount = $currentArchived
        Write-Host ""
    } else {
        # Show status every 4 iterations (1 minute)
        if ($iteration % 4 -eq 0) {
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] Monitoring... BAI2: $currentBai2, Archived: $currentArchived, Pending: $currentPending" -ForegroundColor DarkGray
        }
    }
    
    # Alert if files are waiting
    if ($currentPending -gt 0) {
        if ($iteration % 2 -eq 0) {  # Every 30 seconds
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Host "[$timestamp] WAITING: $currentPending file(s) in incoming folder..." -ForegroundColor Yellow
        }
    }
}
