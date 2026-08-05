@echo off
REM ============================================
REM extract_assets.bat
REM Extracts Morrowind BSA files using BAE
REM ============================================

set BAE_PATH=C:\Tools\BAE\BAE.exe
set MORROWIND_DATA=C:\Program Files (x86)\Steam\steamapps\common\Morrowind\Data Files
set OUTPUT_DIR=C:\Users\max\Projects\Morrowind\raw_assets

echo ======================================
echo Morrowind Asset Extraction
echo ======================================
echo.

REM Check BAE exists
if not exist "%BAE_PATH%" (
    echo ERROR: BAE not found at %BAE_PATH%
    echo Please update BAE_PATH in this script
    pause
    exit /b 1
)

REM Check Morrowind data exists
if not exist "%MORROWIND_DATA%" (
    echo ERROR: Morrowind data not found at %MORROWIND_DATA%
    echo Please update MORROWIND_DATA in this script
    pause
    exit /b 1
)

echo Extracting Morrowind.bsa...
"%BAE_PATH%" "%MORROWIND_DATA%\Morrowind.bsa" "%OUTPUT_DIR%"

echo.
echo Extracting Tribunal.bsa...
"%BAE_PATH%" "%MORROWIND_DATA%\Tribunal.bsa" "%OUTPUT_DIR%"

echo.
echo Extracting Bloodmoon.bsa...
"%BAE_PATH%" "%MORROWIND_DATA%\Bloodmoon.bsa" "%OUTPUT_DIR%"

echo.
echo ======================================
echo Extraction complete!
echo Output: %OUTPUT_DIR%
echo ======================================
pause
