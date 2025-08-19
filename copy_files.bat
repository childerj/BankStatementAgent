@echo off
echo 📋 Bank Statement Function File Copy Utility
echo.

if "%1"=="" (
    echo Usage: copy_files.bat "C:\path\to\your\repository"
    echo Example: copy_files.bat "C:\Users\jeff\source\repos\BankStatementFunction"
    pause
    exit /b 1
)

set "DEST=%~1"
set "SOURCE=%~dp0"

echo Source: %SOURCE%
echo Destination: %DEST%
echo.

if not exist "%DEST%" (
    mkdir "%DEST%"
    echo ✅ Created directory: %DEST%
)

echo 📋 Copying essential files...
copy "%SOURCE%function_app.py" "%DEST%\" >nul 2>&1 && echo ✅ Copied: function_app.py || echo ❌ Failed: function_app.py
copy "%SOURCE%requirements.txt" "%DEST%\" >nul 2>&1 && echo ✅ Copied: requirements.txt || echo ❌ Failed: requirements.txt
copy "%SOURCE%host.json" "%DEST%\" >nul 2>&1 && echo ✅ Copied: host.json || echo ❌ Failed: host.json
copy "%SOURCE%.gitignore" "%DEST%\" >nul 2>&1 && echo ✅ Copied: .gitignore || echo ❌ Failed: .gitignore
copy "%SOURCE%README.md" "%DEST%\" >nul 2>&1 && echo ✅ Copied: README.md || echo ❌ Failed: README.md

echo.
echo 📋 Copying test files...
for %%f in ("%SOURCE%test_*.py") do (
    copy "%%f" "%DEST%\" >nul 2>&1 && echo ✅ Copied: %%~nxf || echo ❌ Failed: %%~nxf
)

for %%f in ("%SOURCE%*.ps1") do (
    copy "%%f" "%DEST%\" >nul 2>&1 && echo ✅ Copied: %%~nxf || echo ❌ Failed: %%~nxf
)

echo.
echo 🎉 Copy complete! Files copied to: %DEST%
echo.
echo Next steps:
echo 1. cd "%DEST%"
echo 2. git add .
echo 3. git commit -m "Add Azure Function Bank Statement Processing"
echo 4. git push
echo.
pause
