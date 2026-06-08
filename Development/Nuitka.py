import json
import os
import shutil
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile

from useful_functions import clear_pycache, get_hash, get_version

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(PROJECT_ROOT)

app_version = get_version()
clear_pycache()

nuitka_cmd = [
    sys.executable,
    '-m',
    'nuitka',
    '--assume-yes-for-downloads',
    '--plugin-enable=pyqt5',
    '--include-package=mouse',
    '--standalone',
    '--windows-console-mode=disable',
    '--windows-icon-from-ico=src/OverlayIcon.ico',
    '--include-data-dir=src=src',
    '--include-data-dir=Layouts=Layouts',
    '--include-data-file=SCOFunctions/SC2Dictionaries/*.csv=SCOFunctions/SC2Dictionaries/',
    '--include-data-file=SCOFunctions/SC2Dictionaries/*.txt=SCOFunctions/SC2Dictionaries/',
    'SCO.py',
]

print('Running Nuitka build...')
result = subprocess.run(nuitka_cmd, cwd=PROJECT_ROOT)
if result.returncode != 0:
    sys.exit(
        'Nuitka build failed. Install build deps in your venv:\n'
        '  pip install nuitka ordered-set zstandard'
    )

dist_dir = os.path.join(PROJECT_ROOT, 'SCO.dist')
if not os.path.isdir(dist_dir):
    sys.exit(f'Build finished but output folder is missing: {dist_dir}')

# Copy readme and user-editable timeline file beside the exe
shutil.copy(
    os.path.join(PROJECT_ROOT, 'Read me (Github).url'),
    os.path.join(dist_dir, 'Read me (Github).url'),
)
timelines_src = os.path.join(PROJECT_ROOT, 'MissionTimelines.json')
if os.path.isfile(timelines_src):
    shutil.copy(timelines_src, os.path.join(dist_dir, 'MissionTimelines.json'))

shutil.copytree(
    os.path.join(PROJECT_ROOT, 'venv/Lib/site-packages/s2protocol'),
    os.path.join(dist_dir, 's2protocol'),
)

# Copy QtWebEngineProcess.exe if it wasn't included automatically (depends on package versions)
webengine_path_venv = os.path.join(
    PROJECT_ROOT, 'venv/Lib/site-packages/PyQt5/Qt/bin/QtWebEngineProcess.exe'
)
webengine_path_pack = os.path.join(dist_dir, 'QtWebEngineProcess.exe')
if not os.path.isfile(webengine_path_pack):
    print('Copying QtWebEngineProcess.exe')
    shutil.copy(webengine_path_venv, webengine_path_pack)

# Delete custom
for f in ('custom.css', 'custom.js'):
    path = os.path.join(dist_dir, 'Layouts', f)
    if os.path.isfile(path):
        os.remove(path)

# Zip
file_name = f'SC2CoopOverlay ({app_version // 100}.{app_version % 100}).zip'

to_zip = []
for root, directories, files in os.walk(dist_dir):
    for file in files:
        to_zip.append(os.path.join(root, file))

print('Compressing files...')
with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip:
    for file in to_zip:
        zip.write(file, os.path.relpath(file, dist_dir))

# Cleanup
for item in ('SCO.build', 'SCO.dist', 'dist'):
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
