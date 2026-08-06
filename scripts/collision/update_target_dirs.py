"""Update TARGET_DIR to TARGET_DIRS in all collision scripts."""
import os
import re

SCRIPTS = [
    "clone_box.py",
    "clone_convex_ramp.py",
    "clone_static.py",
    "encode_static_box.py",
    "reshape_static.py",
]

OLD = r'TARGET_DIR = r"C:\XboxGames\Starfield\Content\Data\meshes\morrowind"'
NEW = '''TARGET_DIRS = [
    r"C:\\Users\\max\\Projects\\Morrowind\\converted_assets\\meshes",
    r"C:\\XboxGames\\Starfield\\Content\\Data\\meshes\\morrowind",
]
TARGET_DIR = TARGET_DIRS[1]'''

for script in SCRIPTS:
    path = os.path.join("scripts/collision", script)
    if not os.path.exists(path):
        print(f"SKIP: {script} not found")
        continue
    with open(path, "r") as f:
        content = f.read()
    if "TARGET_DIRS" in content:
        print(f"SKIP: {script} already has TARGET_DIRS")
        continue
    content = content.replace(OLD, NEW)
    # Update target list comprehensions
    content = content.replace(
        '''targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in sorted(os.listdir(TARGET_DIR))
            if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2")
        ])''',
        '''targets = []
        for tdir in TARGET_DIRS:
            if os.path.exists(tdir):
                for f in sorted(os.listdir(tdir)):
                    if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2"):
                        targets.append(os.path.join(tdir, f))'''
    )
    content = content.replace(
        '''targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in sorted(os.listdir(TARGET_DIR))
            if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2")
               and f.lower().replace(".nif", "") in STAIR_NAMES
        ])''',
        '''targets = []
        for tdir in TARGET_DIRS:
            if os.path.exists(tdir):
                for f in sorted(os.listdir(tdir)):
                    if f.lower().endswith(".nif") and not f.endswith(".bak") and not f.endswith(".bak2") and f.lower().replace(".nif", "") in STAIR_NAMES:
                        targets.append(os.path.join(tdir, f))'''
    )
    content = content.replace(
        '''targets = sorted([
            os.path.join(TARGET_DIR, f)
            for f in sorted(os.listdir(TARGET_DIR))
            if f.lower().endswith(".nif") and not f.endswith(".bak")
        ])''',
        '''targets = []
        for tdir in TARGET_DIRS:
            if os.path.exists(tdir):
                for f in sorted(os.listdir(tdir)):
                    if f.lower().endswith(".nif") and not f.endswith(".bak"):
                        targets.append(os.path.join(tdir, f))'''
    )
    with open(path, "w") as f:
        f.write(content)
    print(f"UPDATED: {script}")
