# Azure Function Diagnostic Script
# This script will help identify why your Bank Statement Agent isn't processing files

Write-Host "========================================" -ForegroundColor Green
Write-Host "  AZURE FUNCTION DIAGNOSTIC TOOL" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host "Checking Bank Statement Agent status..." -ForegroundColor Yellow
Write-Host ""

$functionAppName = "BankStatementAgent"
$resourceGroup = "Azure_AI_RG"
$storageAccount = "waazuse1aistorage"
$containerName = "bank-reconciliation"

# Check if Azure CLI is logged in
Write-Host "🔍 Step 1: Checking Azure CLI authentication..." -ForegroundColor Cyan
try {
    $account = az account show --query "user.name" -o tsv 2>$null
    if ($account) {
        Write-Host "✅ Logged in as: $account" -ForegroundColor Green
    } else {
        Write-Host "❌ Not logged into Azure CLI" -ForegroundColor Red
        Write-Host "Please run: az login" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Azure CLI not found or not logged in" -ForegroundColor Red
    Write-Host "Please install Azure CLI and run: az login" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check Function App status
Write-Host "🔍 Step 2: Checking Function App status..." -ForegroundColor Cyan
try {
    $functionStatus = az functionapp show --name $functionAppName --resource-group $resourceGroup --query "{state:state,status:availabilityState}" -o json | ConvertFrom-Json
    
    if ($functionStatus.state -eq "Running" -and $functionStatus.status -eq "Normal") {
        Write-Host "✅ Function App is running normally" -ForegroundColor Green
    } else {
        Write-Host "❌ Function App issue detected:" -ForegroundColor Red
        Write-Host "   State: $($functionStatus.state)" -ForegroundColor Yellow
        Write-Host "   Status: $($functionStatus.status)" -ForegroundColor Yellow
        
        if ($functionStatus.state -ne "Running") {
            Write-Host "🔧 Try starting the function app:" -ForegroundColor Blue
            Write-Host "   az functionapp start --name $functionAppName --resource-group $resourceGroup" -ForegroundColor White
        }
    }
} catch {
    Write-Host "❌ Could not check Function App status" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "🔧 Check if the function app exists:" -ForegroundColor Blue
    Write-Host "   az functionapp list --resource-group $resourceGroup --output table" -ForegroundColor White
}

Write-Host ""

# Check storage account and containers
Write-Host "🔍 Step 3: Checking storage containers..." -ForegroundColor Cyan
try {
    $accountKey = az storage account keys list --resource-group $resourceGroup --account-name $storageAccount --query "[0].value" -o tsv
    
    if ($accountKey) {
        Write-Host "✅ Storage account accessible" -ForegroundColor Green
        
        # Check containers
        $containers = az storage container list --account-name $storageAccount --account-key $accountKey --query "[].name" -o tsv
        
        if ($containers -contains $containerName) {
            Write-Host "✅ Main container '$containerName' exists" -ForegroundColor Green
            
            # Check folder structure
            $folders = @("incoming-bank-statements", "bai2-outputs", "archive")
            foreach ($folder in $folders) {
                $blobs = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "$folder/" --account-key $accountKey --query "length(@)" -o tsv
                if ($blobs -gt 0) {
                    Write-Host "✅ Folder '$folder' exists" -ForegroundColor Green
                } else {
                    Write-Host "⚠️  Folder '$folder' may not exist or is empty" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "❌ Container '$containerName' not found" -ForegroundColor Red
            Write-Host "🔧 Create containers by calling the setup endpoint:" -ForegroundColor Blue
            Write-Host "   curl https://$functionAppName.azurewebsites.net/api/setup" -ForegroundColor White
        }
    } else {
        Write-Host "❌ Could not access storage account" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Storage check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check for files waiting to be processed
Write-Host "🔍 Step 4: Checking for pending files..." -ForegroundColor Cyan
try {
    if ($accountKey) {
        $pendingFiles = az storage blob list --account-name $storageAccount --container-name $containerName --prefix "incoming-bank-statements/" --account-key $accountKey --query "[?name != 'incoming-bank-statements/.placeholder']" | ConvertFrom-Json
        
        if ($pendingFiles.Count -gt 0) {
            Write-Host "📁 Found $($pendingFiles.Count) file(s) waiting for processing:" -ForegroundColor Yellow
            foreach ($file in $pendingFiles) {
                $fileName = $file.name -replace "incoming-bank-statements/", ""
                $sizeKB = [math]::Round($file.properties.contentLength / 1024, 1)
                $uploadTime = $file.properties.lastModified
                Write-Host "   📄 $fileName ($sizeKB KB) - uploaded $uploadTime" -ForegroundColor White
            }
            Write-Host "❗ Files are waiting but not being processed - this indicates a trigger issue" -ForegroundColor Red
        } else {
            Write-Host "✅ No files waiting for processing" -ForegroundColor Green
            Write-Host "💡 Try uploading a test file to trigger processing" -ForegroundColor Blue
        }
    }
} catch {
    Write-Host "❌ Could not check pending files: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check recent function logs
Write-Host "🔍 Step 5: Checking recent function logs..." -ForegroundColor Cyan
try {
    # Try to get Application Insights logs first
    $appInsightsName = "$functionAppName-AppInsights"
    
    Write-Host "   Checking Application Insights logs..." -ForegroundColor Gray
    $logQuery = "traces | where cloud_RoleName == '$functionAppName' | where timestamp > ago(2h) | order by timestamp desc | take 10 | project timestamp, message, severityLevel"
    
    $logs = az monitor app-insights query --app $appInsightsName --analytics-query $logQuery --resource-group $resourceGroup 2>$null
    
    if ($logs) {
        $logData = $logs | ConvertFrom-Json
        if ($logData.tables -and $logData.tables[0].rows.Count -gt 0) {
            Write-Host "✅ Found recent logs in Application Insights:" -ForegroundColor Green
            foreach ($row in $logData.tables[0].rows) {
                $timestamp = $row[0]
                $message = $row[1]
                $level = $row[2]
                $levelColor = if ($level -eq 3) { "Red" } elseif ($level -eq 2) { "Yellow" } else { "White" }
                Write-Host "   [$timestamp] $message" -ForegroundColor $levelColor
            }
        } else {
            Write-Host "⚠️  No recent logs found in Application Insights" -ForegroundColor Yellow
            Write-Host "   This might indicate the function isn't executing" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  Could not access Application Insights logs" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Log check failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""

# Check function app configuration
Write-Host "🔍 Step 6: Checking function configuration..." -ForegroundColor Cyan
try {
    $config = az functionapp config appsettings list --name $functionAppName --resource-group $resourceGroup --query "[].{name:name, value:value}" -o json | ConvertFrom-Json
    
    $requiredSettings = @(
        "AzureWebJobsStorage",
        "DOCINTELLIGENCE_ENDPOINT", 
        "DOCINTELLIGENCE_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_DEPLOYMENT"
    )
    
    $missingSettings = @()
    foreach ($setting in $requiredSettings) {
        $found = $config | Where-Object { $_.name -eq $setting }
        if ($found -and $found.value) {
            Write-Host "✅ $setting is configured" -ForegroundColor Green
        } else {
            Write-Host "❌ $setting is missing or empty" -ForegroundColor Red
            $missingSettings += $setting
        }
    }
    
    if ($missingSettings.Count -gt 0) {
        Write-Host ""
        Write-Host "🔧 Missing configuration detected. Set these values:" -ForegroundColor Blue
        foreach ($setting in $missingSettings) {
            Write-Host "   az functionapp config appsettings set --name $functionAppName --resource-group $resourceGroup --settings '$setting=<your-value>'" -ForegroundColor White
        }
    }
} catch {
    Write-Host "❌ Configuration check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check if function deployment is current
Write-Host "🔍 Step 7: Checking function deployment..." -ForegroundColor Cyan
try {
    $deploymentInfo = az functionapp deployment source show --name $functionAppName --resource-group $resourceGroup 2>$null
    if ($deploymentInfo) {
        Write-Host "✅ Function app has deployment configuration" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No deployment information found" -ForegroundColor Yellow
        Write-Host "   You may need to deploy your function code:" -ForegroundColor Gray
        Write-Host "   func azure functionapp publish $functionAppName --python" -ForegroundColor White
    }
} catch {
    Write-Host "⚠️  Could not check deployment status" -ForegroundColor Yellow
}

Write-Host ""

# Provide summary and next steps
Write-Host "📋 DIAGNOSTIC SUMMARY & NEXT STEPS" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 IMMEDIATE ACTIONS TO TRY:" -ForegroundColor Yellow

Write-Host ""
Write-Host "1. 📁 Test the trigger by uploading a file:" -ForegroundColor Blue
Write-Host "   az storage blob upload --account-name $storageAccount --container-name $containerName --name 'incoming-bank-statements/test.pdf' --file 'path-to-your-pdf' --account-key <storage-key>" -ForegroundColor White

Write-Host ""
Write-Host "2. 🔄 Restart the function app:" -ForegroundColor Blue
Write-Host "   az functionapp restart --name $functionAppName --resource-group $resourceGroup" -ForegroundColor White

Write-Host ""
Write-Host "3. 📊 Monitor real-time activity:" -ForegroundColor Blue
Write-Host "   .\monitor_realtime.ps1" -ForegroundColor White

Write-Host ""
Write-Host "4. 🔍 Stream live logs:" -ForegroundColor Blue
Write-Host "   az functionapp log tail --name $functionAppName --resource-group $resourceGroup" -ForegroundColor White

Write-Host ""
Write-Host "5. 🌐 Test HTTP endpoint:" -ForegroundColor Blue
Write-Host "   curl https://$functionAppName.azurewebsites.net/api/setup" -ForegroundColor White

Write-Host ""
Write-Host "💡 COMMON ISSUES & SOLUTIONS:" -ForegroundColor Yellow
Write-Host "   • Function not triggering: Check blob trigger configuration and storage connection" -ForegroundColor White
Write-Host "   • Missing environment variables: Verify all API keys and endpoints are set" -ForegroundColor White
Write-Host "   • Code not deployed: Run 'func azure functionapp publish $functionAppName --python'" -ForegroundColor White
Write-Host "   • Storage issues: Ensure containers exist and permissions are correct" -ForegroundColor White
Write-Host "   • Runtime errors: Check Application Insights for detailed error messages" -ForegroundColor White

Write-Host ""
Write-Host "🔄 Re-run this diagnostic after making changes to verify fixes!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
