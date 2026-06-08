"""
This script makes packaging with Pyinstaller easier
Run the pyinstaller, cleans up, zips files.

"""

import json
import os
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

from useful_functions import get_hash, get_version, clear_pycache

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

app_version = get_version()
clear_pycache()

# Run pyinstaller
pyinstaller_cmd = [
    sys.executable,
    '-m',
    'PyInstaller',
    '--noconfirm',
    '--clean',
    '--windowed',
    '--name=SCO',
    '--contents-directory=.',
    '--icon=src/OverlayIcon.ico',
    '--hidden-import=mouse',
    '--hidden-import=mss',
    '--hidden-import=pytesseract',
    f'--add-data=src{os.pathsep}src',
    f'--add-data=Layouts{os.pathsep}Layouts',
    f'--add-data=MissionTimelines.json{os.pathsep}.',
    f'--add-data=Read me (Github).url{os.pathsep}.',
    f'--add-data=SCOFunctions/SC2Dictionaries/*.csv{os.pathsep}SCOFunctions/SC2Dictionaries',
    f'--add-data=SCOFunctions/SC2Dictionaries/*.txt{os.pathsep}SCOFunctions/SC2Dictionaries',
    'SCO.py',
]

print('Running PyInstaller build...')
result = subprocess.run(pyinstaller_cmd, cwd=PROJECT_ROOT)
if result.returncode != 0:
    sys.exit('PyInstaller build failed.')

# Zip
file_name = f"SC2CoopOverlay ({app_version // 100}.{app_version % 100}).zip"
dist_dir = os.path.join(PROJECT_ROOT, 'dist', 'SCO')
if not os.path.isdir(dist_dir):
    sys.exit(f'Build finished but output folder is missing: {dist_dir}')

# Delete custom
for f in ("custom.css", "custom.js"):
    f = os.path.join(dist_dir, 'Layouts', f)
    if os.path.isfile(f):
        os.remove(f)

to_zip = []
for root, directories, files in os.walk(dist_dir):
    for file in files:
        to_zip.append(os.path.join(root, file))

print('Compressing files...')
with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip:
    for file in to_zip:
        zip.write(file, os.path.relpath(file, dist_dir))

# Cleanup
for item in ('SCO.spec',):
    item_path = os.path.join(PROJECT_ROOT, item)
    if os.path.isfile(item_path):
        os.remove(item_path)
for item in ('build', 'dist'):
    item_path = os.path.join(PROJECT_ROOT, item)
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)

# Hash
with open('version.txt', 'r') as f:
    version_data = json.load(f)

version_data['hash'] = get_hash(file_name, sha=True)
version_data['version'] = app_version

with open('version.txt', 'w') as f:
    json.dump(version_data, f, indent=2)
