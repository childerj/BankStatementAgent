# Azure Function Execution Monitor
# This script shows detailed execution history of your function

param(
    [int]$Hours = 24  # Default to last 24 hours
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "  AZURE FUNCTION EXECUTION LOG" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$functionName = "BankStatementAgent"
$resourceGroup = "Azure_AI_RG"

Write-Host "📊 Function: $functionName" -ForegroundColor Yellow
Write-Host "🕒 Showing executions from last $Hours hours" -ForegroundColor Yellow
Write-Host ""

# Get function execution history
Write-Host "🔍 RECENT FUNCTION EXECUTIONS:" -ForegroundColor Cyan

try {
    # Get the function app details
    $functionApp = az functionapp show --name $functionName --resource-group $resourceGroup | ConvertFrom-Json
    Write-Host "✅ Function App Status: $($functionApp.state)" -ForegroundColor Green
    Write-Host "📍 Location: $($functionApp.location)" -ForegroundColor Gray
    Write-Host ""
    
    # Check if there are any functions
    $functions = az functionapp function list --function-app-name $functionName --resource-group $resourceGroup | ConvertFrom-Json
    
    Write-Host "📋 DEPLOYED FUNCTIONS:" -ForegroundColor Blue
    foreach ($func in $functions) {
        Write-Host "   • $($func.name) - $($func.config.bindings[0].type)" -ForegroundColor White
    }
    Write-Host ""
    
} catch {
    Write-Host "❌ Error accessing function app: $($_.Exception.Message)" -ForegroundColor Red
}

# Check recent blob activity as a proxy for function executions
Write-Host "📁 RECENT BLOB STORAGE ACTIVITY:" -ForegroundColor Magenta

$storageAccount = "waazuse1aistorage"
$containerName = "bank-reconciliation"
$accountKey = "YOUR_STORAGE_ACCOUNT_KEY_HERE"

# Get recent BAI2 files (these indicate successful function executions)
$recentFiles = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "bai2-outputs/" --account-key $accountKey --query "[?name != 'bai2-outputs/.placeholder'] | sort_by(@, &properties.lastModified) | reverse(@) | [0:5]" | ConvertFrom-Json

Write-Host "🆕 MOST RECENT PROCESSING (Last 5):" -ForegroundColor Green
foreach ($file in $recentFiles) {
    $fileName = $file.name -replace "bai2-outputs/", ""
    $size = [math]::Round($file.properties.contentLength / 1024, 1)
    $time = [DateTime]::Parse($file.properties.lastModified).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "   ✅ $fileName ($size KB) - $time" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "💡 TIP: For real-time monitoring, run:" -ForegroundColor Yellow
Write-Host "   az webapp log tail --name $functionName --resource-group $resourceGroup" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 For Application Insights (after 5-10 minutes):" -ForegroundColor Yellow
Write-Host "   Visit: https://portal.azure.com → BankStatementAgent-AppInsights → Logs" -ForegroundColor Gray
