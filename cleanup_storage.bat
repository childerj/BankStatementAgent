@echo off
REM Azure Storage Cleanup - Easy Launcher
REM 
REM This script provides an easy way to run the storage cleanup

echo.
echo ===============================================
echo Azure Storage Cleanup - Easy Launcher
echo ===============================================
echo.
echo Choose an option:
echo   1. Preview only (dry run)
echo   2. Execute cleanup (delete files)
echo   3. Help
echo   4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running in PREVIEW mode...
    python cleanup_storage.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo WARNING: This will PERMANENTLY DELETE files!
    echo Only .placeholder files will be kept.
    echo.
    set /p confirm="Are you sure? Type YES to continue: "
    if "!confirm!"=="YES" (
        echo.
        echo Running LIVE DELETION...
        python cleanup_storage.py --execute
    ) else (
        echo Operation cancelled.
    )
    goto end
)

if "%choice%"=="3" (
    echo.
    python cleanup_storage.py --help
    goto end
)

if "%choice%"=="4" (
    echo.
    echo Goodbye!
    goto end
)

echo.
echo Invalid choice. Please try again.
pause
goto start

:end
echo.
pause
