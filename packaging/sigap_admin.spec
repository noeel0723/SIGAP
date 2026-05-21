# sigap_admin.spec
# Konfigurasi PyInstaller untuk build Admin (Kelurahan/Kecamatan/Kota)
# Jalankan dari ROOT proyek: pyinstaller packaging/sigap_admin.spec

# -*- mode: python ; coding: utf-8 -*-

import os
import customtkinter

block_cipher = None

# Path root proyek (satu level di atas folder packaging/)
ROOT_DIR = os.path.abspath(os.path.join(SPECPATH, '..'))
CTK_DIR = os.path.dirname(customtkinter.__file__)

a = Analysis(
    [os.path.join(ROOT_DIR, 'main.py')],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        (os.path.join(ROOT_DIR, 'assets'), 'assets'),
        (os.path.join(ROOT_DIR, 'config'), 'config'),
        (CTK_DIR, 'customtkinter'),
    ],
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.plugins',
        'mysql.connector.plugins.caching_sha2_password',
        'mysql.connector.plugins.mysql_native_password',
        'bcrypt',
        'bcrypt._bcrypt',
        'customtkinter',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'numpy',
        'PIL',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='SIGAP_Admin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Tanpa console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=os.path.join(ROOT_DIR, 'assets', 'icons', 'sigap_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SIGAP_Admin',
)
