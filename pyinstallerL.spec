# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import os
from kivymd import hooks_path as kivymd_hooks_path
path = os.path.abspath(".")

a = Analysis(['main.py'],
             pathex=[path],
             binaries=[],
             datas=[("assets", "assets"), ("libs", "libs")],
             hiddenimports=['pysocks'],
             hookspath=[kivymd_hooks_path],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='proxySpeedTest_v1.3',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon="icon.ico" )
