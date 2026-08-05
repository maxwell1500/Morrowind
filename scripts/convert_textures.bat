@echo off
REM ============================================
REM convert_textures.bat
REM Batch converts upscaled PNGs to Starfield DDS
REM ============================================

set TEXCONV_PATH=C:\Tools\texconv.exe
set INPUT_DIR=C:\Users\max\Projects\Morrowind\converted_assets\textures\upscaled
set OUTPUT_DIR=C:\Users\max\Projects\Morrowind\converted_assets\textures

echo ======================================
echo Texture Conversion to Starfield DDS
echo ======================================
echo.

REM Check texconv exists
if not exist "%TEXCONV_PATH%" (
    echo ERROR: texconv not found at %TEXCONV_PATH%
    echo Please download from: https://github.com/Microsoft/DirectXTex/releases
    pause
    exit /b 1
)

REM Check input directory
if not exist "%INPUT_DIR%" (
    echo ERROR: Input directory not found: %INPUT_DIR%
    echo Please upscale textures first and place PNGs in the input folder.
    pause
    exit /b 1
)

echo Converting textures to R8G8B8A8_UNORM_SRGB format...
echo Input:  %INPUT_DIR%
echo Output: %OUTPUT_DIR%
echo.

for %%f in ("%INPUT_DIR%\*.png") do (
    echo Converting: %%~nxf
    "%TEXCONV_PATH%" -f R8G8B8A8_UNORM_SRGB -o "%OUTPUT_DIR%" "%%f"
)

echo.
echo ======================================
echo Conversion complete!
echo Check %OUTPUT_DIR% for DDS files
echo ======================================
pause
