# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect pywebview data files and submodules
webview_datas = collect_data_files('webview')
webview_hiddenimports = collect_submodules('webview')

a = Analysis(
    ['todo_widget.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('todo_widget.html', '.'),
        ('todo_data.json', '.'),
        ('todo_settings.json', '.'),
    ] + webview_datas,
    hiddenimports=webview_hiddenimports + [
        'clr',
        'webview',
        'webview.platforms.winforms',
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
    name='TodoWidget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TodoWidget',
)
