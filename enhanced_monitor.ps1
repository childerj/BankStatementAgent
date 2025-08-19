# Enhanced Azure Function Monitor with Direct API Access
# This script uses the Azure REST API to get function execution history

param(
    [int]$Hours = 24
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ENHANCED AZURE FUNCTION MONITOR" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$functionName = "BankStatementAgent"
$resourceGroup = "Azure_AI_RG"
$storageAccount = "waazuse1aistorage"
$containerName = "bank-reconciliation"
$accountKey = "YOUR_STORAGE_ACCOUNT_KEY_HERE"

# Function to get recent activity from blob timestamps
function Get-RecentActivity {
    Write-Host "🔍 ANALYZING RECENT PROCESSING ACTIVITY:" -ForegroundColor Cyan
    Write-Host ""
    
    # Get all BAI2 files sorted by date
    $bai2Files = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "bai2-outputs/" --account-key $accountKey --query "[?name != 'bai2-outputs/.placeholder'] | sort_by(@, &properties.lastModified) | reverse(@)" | ConvertFrom-Json
    
    # Get cutoff time for recent activity
    $cutoffTime = (Get-Date).AddHours(-$Hours)
    
    $recentCount = 0
    foreach ($file in $bai2Files) {
        $fileTime = [DateTime]::Parse($file.properties.lastModified)
        if ($fileTime -gt $cutoffTime) {
            $recentCount++
            $fileName = $file.name -replace "bai2-outputs/", ""
            $size = [math]::Round($file.properties.contentLength / 1024, 1)
            $timeFormatted = $fileTime.ToString("yyyy-MM-dd HH:mm:ss")
            $ageMinutes = [math]::Round(((Get-Date) - $fileTime).TotalMinutes, 1)
            
            Write-Host "✅ $timeFormatted ($ageMinutes min ago) - $fileName ($size KB)" -ForegroundColor Green
        }
    }
    
    if ($recentCount -eq 0) {
        Write-Host "   No activity in the last $Hours hours" -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "📊 Total recent processing events: $recentCount" -ForegroundColor White
    }
    Write-Host ""
}

# Function to check for errors by looking at patterns
function Check-ForErrors {
    Write-Host "🔍 CHECKING FOR POTENTIAL ISSUES:" -ForegroundColor Magenta
    Write-Host ""
    
    # Check for files stuck in incoming folder
    $stuckFiles = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "incoming-bank-statements/" --account-key $accountKey --query "[?name != 'incoming-bank-statements/.placeholder']" | ConvertFrom-Json
    
    if ($stuckFiles.Count -gt 0) {
        Write-Host "⚠️  WARNING: $($stuckFiles.Count) file(s) in incoming folder (may be processing or stuck):" -ForegroundColor Yellow
        foreach ($file in $stuckFiles) {
            $fileName = $file.name -replace "incoming-bank-statements/", ""
            $fileTime = [DateTime]::Parse($file.properties.lastModified)
            $ageMinutes = [math]::Round(((Get-Date) - $fileTime).TotalMinutes, 1)
            Write-Host "   📄 $fileName (uploaded $ageMinutes min ago)" -ForegroundColor White
        }
    } else {
        Write-Host "✅ No files stuck in incoming folder" -ForegroundColor Green
    }
    
    # Check for mismatched counts (BAI2 vs Archive)
    $bai2Count = (az storage blob list --account-name $storageAccount --container-name $containerName --prefix "bai2-outputs/" --account-key $accountKey --query "[?name != 'bai2-outputs/.placeholder']" | ConvertFrom-Json).Count
    $archivedCount = (az storage blob list --account-name $storageAccount --container-name $containerName --prefix "archive/" --account-key $accountKey --query "[?name != 'archive/.placeholder']" | ConvertFrom-Json).Count
    
    if ($bai2Count -ne $archivedCount) {
        $difference = [math]::Abs($bai2Count - $archivedCount)
        Write-Host "⚠️  COUNT MISMATCH: $bai2Count BAI2 files vs $archivedCount archived files (difference: $difference)" -ForegroundColor Yellow
        Write-Host "   This may indicate partial processing or errors" -ForegroundColor Gray
    } else {
        Write-Host "✅ File counts match: $bai2Count BAI2 files = $archivedCount archived files" -ForegroundColor Green
    }
    Write-Host ""
}

# Function to show function app health
function Show-FunctionHealth {
    Write-Host "🏥 FUNCTION APP HEALTH CHECK:" -ForegroundColor Blue
    Write-Host ""
    
    try {
        $functionApp = az functionapp show --name $functionName --resource-group $resourceGroup | ConvertFrom-Json
        Write-Host "✅ Function App: $($functionApp.name)" -ForegroundColor Green
        Write-Host "✅ Status: $($functionApp.state)" -ForegroundColor Green
        Write-Host "✅ Location: $($functionApp.location)" -ForegroundColor Green
        Write-Host "✅ URL: $($functionApp.defaultHostName)" -ForegroundColor Green
        
        # Check functions
        Write-Host ""
        Write-Host "📋 DEPLOYED FUNCTIONS:" -ForegroundColor White
        $functions = az functionapp function list --resource-group $resourceGroup --name $functionName | ConvertFrom-Json
        foreach ($func in $functions) {
            $triggerType = $func.config.bindings | Where-Object { $_.direction -eq "IN" } | Select-Object -First 1
            Write-Host "   • $($func.config.name) ($($triggerType.type))" -ForegroundColor White
        }
        
    } catch {
        Write-Host "❌ Error checking function app: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# Main execution
Show-FunctionHealth
Get-RecentActivity
Check-ForErrors

# Try to get Application Insights data
Write-Host "💡 TRYING APPLICATION INSIGHTS:" -ForegroundColor Yellow
Write-Host ""

try {
    Write-Host "🔍 Querying Application Insights for recent traces..." -ForegroundColor Gray
    $aiQuery = "traces | where timestamp > ago(1h) | where cloud_RoleName == 'BankStatementAgent' | order by timestamp desc | limit 10"
    $aiResult = az monitor app-insights query --app "BankStatementAgent-AppInsights" --resource-group $resourceGroup --analytics-query $aiQuery 2>$null
    
    if ($aiResult) {
        Write-Host "✅ Application Insights data available!" -ForegroundColor Green
        $aiData = $aiResult | ConvertFrom-Json
        if ($aiData.tables -and $aiData.tables.rows) {
            Write-Host "📋 Recent log entries:" -ForegroundColor White
            foreach ($row in $aiData.tables.rows[0..4]) {  # Show first 5 entries
                $timestamp = [DateTime]::Parse($row[0]).ToString("yyyy-MM-dd HH:mm:ss")
                $message = $row[1]
                Write-Host "   [$timestamp] $message" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "⏳ Application Insights data not yet available (may take 5-15 minutes after first deployment)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⏳ Application Insights not ready yet (this is normal for new deployments)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "💡 TIPS FOR BETTER LOGGING:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Application Insights Portal:" -ForegroundColor White
Write-Host "   https://portal.azure.com → BankStatementAgent-AppInsights → Logs" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Real-time monitoring:" -ForegroundColor White
Write-Host "   .\monitor_realtime.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Function URLs for testing:" -ForegroundColor White
Write-Host "   Setup: https://bankstatementagent-e8f3ddc9bwgjfvar.eastus-01.azurewebsites.net/api/setup" -ForegroundColor Gray
