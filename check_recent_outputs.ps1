# Check recent outputs from function execution
$connectionString = Get-Content "c:\Users\jeff.childers\Documents\Bank Statement Reconciliation\local.settings.json" | ConvertFrom-Json | Select-Object -ExpandProperty Values | Select-Object -ExpandProperty AzureWebJobsStorage

Write-Host "Checking recent BAI2 outputs..."
az storage blob list --connection-string "$connectionString" --container-name bank-reconciliation --prefix bai2-output/ --query "reverse(sort_by([], &properties.lastModified))[0:3].{name:name, lastModified:properties.lastModified}" --output table

Write-Host "`nChecking recent error files..."
az storage blob list --connection-string "$connectionString" --container-name bank-reconciliation --prefix error-files/ --query "reverse(sort_by([], &properties.lastModified))[0:3].{name:name, lastModified:properties.lastModified}" --output table

Write-Host "`nChecking recent archive files..."
az storage blob list --connection-string "$connectionString" --container-name bank-reconciliation --prefix archive/ --query "reverse(sort_by([], &properties.lastModified))[0:3].{name:name, lastModified:properties.lastModified}" --output table
