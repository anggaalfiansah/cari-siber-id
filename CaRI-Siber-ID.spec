# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files from packages that have static templates or models
datas = [
    ('resources', 'resources'),
    ('cari_siber/ui_dist', 'cari_siber/ui_dist'),
]

datas += collect_data_files('sentence_transformers')
datas += collect_data_files('bertopic')
datas += collect_data_files('wordcloud')
datas += collect_data_files('sklearn')
datas += collect_data_files('keyring')

hiddenimports = [
    'pywebview',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'clr',
    'pythonnet',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'sentence_transformers',
    'bertopic',
    'hdbscan',
    'umap',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'sklearn.utils._heap',
    'sklearn.utils._sorting',
    'sklearn.utils._vector_sentinel',
    'scipy.special.cython_special',
    'scipy.spatial.transform._rotation',
    'pandas',
    'numpy',
    'openpyxl',
    'wordcloud',
    'matplotlib',
    'seaborn',
    'requests',
    'google.genai',
    'openai',
    'pydantic',
    'youtube_comment_downloader',
    'instaloader',
]

hiddenimports += collect_submodules('cari_siber')
hiddenimports += collect_submodules('pywebview')
hiddenimports += collect_submodules('keyring')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CaRI-Siber-ID',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sembunyikan terminal (windowed GUI mode murni)
    icon='resources/icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CaRI-Siber-ID',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='CaRI-Siber-ID.app',
        icon=None,
        bundle_identifier='id.carisiber.desktop',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleDisplayName': 'CaRI-Siber ID',
            'CFBundleName': 'CaRI-Siber-ID',
            'CFBundleShortVersionString': '1.0.0',
            'LSMinimumSystemVersion': '11.0.0',
        },
    )
