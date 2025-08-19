# Bank Statement Processing Log Checker
# This script shows you a summary of all processed files

Write-Host "========================================" -ForegroundColor Green
Write-Host "  BANK STATEMENT PROCESSING LOG" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$storageAccount = "waazuse1aistorage"
$containerName = "bank-reconciliation"
$accountKey = "YOUR_STORAGE_ACCOUNT_KEY_HERE"

Write-Host "📋 RECENT PROCESSING ACTIVITY:" -ForegroundColor Yellow
Write-Host ""

# Check BAI2 outputs (successful processing)
Write-Host "✅ SUCCESSFULLY PROCESSED FILES:" -ForegroundColor Green
$bai2Files = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "bai2-outputs/" --account-key $accountKey --query "[?name != 'bai2-outputs/.placeholder'].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" --output table
Write-Host $bai2Files
Write-Host ""

# Check archived files
Write-Host "📁 ARCHIVED ORIGINAL FILES:" -ForegroundColor Blue
$archivedFiles = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "archive/" --account-key $accountKey --query "[?name != 'archive/.placeholder'].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" --output table
Write-Host $archivedFiles
Write-Host ""

# Check any files waiting to be processed
Write-Host "⏳ FILES WAITING FOR PROCESSING:" -ForegroundColor Yellow
$pendingFiles = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "incoming-bank-statements/" --account-key $accountKey --query "[?name != 'incoming-bank-statements/.placeholder'].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" --output table
if ($pendingFiles) {
    Write-Host $pendingFiles
} else {
    Write-Host "No files waiting for processing." -ForegroundColor Gray
}
Write-Host ""

# Summary
$bai2Count = (az storage blob list --account-name $storageAccount --container-name $containerName --prefix "bai2-outputs/" --account-key $accountKey --query "[?name != 'bai2-outputs/.placeholder']" | ConvertFrom-Json).Count
$archivedCount = (az storage blob list --account-name $storageAccount --container-name $containerName --prefix "archive/" --account-key $accountKey --query "[?name != 'archive/.placeholder']" | ConvertFrom-Json).Count

Write-Host "📊 SUMMARY:" -ForegroundColor Cyan
Write-Host "   Total BAI2 files created: $bai2Count" -ForegroundColor White
Write-Host "   Total files archived: $archivedCount" -ForegroundColor White
Write-Host "   Processing success rate: $(if($archivedCount -gt 0) {[math]::Round(($bai2Count/$archivedCount)*100,1)} else {0})%" -ForegroundColor White

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "To run this again, use: .\check_processing_log.ps1" -ForegroundColor Gray
