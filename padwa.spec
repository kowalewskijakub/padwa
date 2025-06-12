# -*- mode: python ; coding: utf-8 -*-

import shutil
from PyInstaller.utils.hooks import copy_metadata

streamlit_path = shutil.which('streamlit')
if not streamlit_path:
    raise Exception("Could not find the 'streamlit' executable in the environment's PATH.")

datas = [
    ('src', 'src'),
    ('assets', 'assets'),
    ('.env', '.')
]

datas += copy_metadata('streamlit')
datas += copy_metadata('altair')

binaries = [
    (streamlit_path, '.')
]

a = Analysis(
    ['src/run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'altair',
        'pandas',
        'numpy',
        'pydeck',
        'streamlit.web.cli',
        'tornado.simple_httpclient',
        'cacertifi'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    windowed=False,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='padwa',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='padwa',
)
