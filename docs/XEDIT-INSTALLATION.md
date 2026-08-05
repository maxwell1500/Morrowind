# xEdit Installation Guide

## What is xEdit?

xEdit (also called SSEEdit) is a free tool for editing Starfield/Skyrim/Fallout plugin files (.esp/.esm). It's essential for our automation workflow.

## Installation Options

### Option A: Manual Download (Recommended)

1. **Download xEdit**
   - Official Site: https://skyrim.es/
   - GitHub Releases: https://github.com/xEdit/xEdit/releases
   - Direct Download (if available): Look for `xedit-win-x64-*.zip` or `SSEEditPortable.exe`

2. **Extract/Install**
   ```powershell
   # Create installation directory
   New-Item -ItemType Directory -Force -Path "C:\XboxGames\Starfield\Content\Tools\xEdit"
   
   # If downloaded as ZIP:
   Expand-Archive -Path "C:\path\to\xedit-win-x64-*.zip" -DestinationPath "C:\XboxGames\Starfield\Content\Tools\xEdit"
   
   # If downloaded as EXE:
   # Just place the exe in the directory
   ```

3. **Verify Installation**
   ```powershell
   & "C:\XboxGames\Starfield\Content\Tools\xEdit\xedit.exe" --version
   ```

### Option B: Python ESP Library (Alternative)

Install the Python ESP parser/writer:
```powershell
pip install bethesda-strings-editor
```

This provides a Python API for reading/writing ESP files.

### Option C: Custom Python Script

If neither option works, we can create a custom ESP generator using raw binary file operations.

---

## Post-Installation: xEdit Scripts

We'll need these xEdit Pascal scripts for automation:

1. **Starfield - AddFaunaFromCSVs.pas** - CSV-driven record creation
   - Source: https://github.com/goarray/StarfieldScripts
   - Path: `xedit/Edit Scripts/Starfield - AddFaunaFromCSVs.pas`

2. **BlenderJSON-Export.pas** - JSON export/import for cells
   - Source: https://github.com/fre-sch/starfield-toolbox
   - Path: `xedit/Edit Scripts/BlenderJSON-Export.pas`

To install scripts:
```powershell
# Copy .pas files to xEdit's Edit Scripts folder
Copy-Item -Path "C:\path\to\StarfieldScripts\xEdit\*.pas" -Destination "C:\XboxGames\Starfield\Content\Tools\xEdit\Edit Scripts\" -Force
```

---

## Troubleshooting

### Download Issues
- **GitHub blocked:** Try using a VPN or download on a different network
- **Site down:** Check https://skyrim.es/ status
- **Mirror:** Try Nexus Mods (search for "SSEEdit")

### xEdit Crashes on Startup
- Run as Administrator
- Ensure Starfield.esm is accessible at `C:\XboxGames\Starfield\Content\Data\Starfield.esm`

### Script Execution Errors
- Ensure .pas files are in `Edit Scripts` subfolder
- Restart xEdit after adding scripts
- Check script syntax

---

## Verification

After installation, test with:
```powershell
# Launch xEdit
& "C:\XboxGames\Starfield\Content\Tools\xEdit\xedit.exe"

# In xEdit:
# 1. File → Load → Starfield.esm
# 2. File → Load → TheElderStarSystem Magnus.esp
# 3. Check that both load without errors
```

---

## Alternative: Python ESP Generator

If xEdit installation fails, we can use a custom Python script to generate ESP files directly. The script will:
1. Read placement CSVs
2. Generate REFR records with positions/rotations
3. Create CELL records
4. Output a valid .esp file

See `scripts/generate_esp.py` (to be created).

---

## Next Steps

1. Install xEdit (follow instructions above)
2. Download and install xEdit Pascal scripts
3. Run the automation script to generate `SeydaNeen.esp`
4. Test in Creation Kit
