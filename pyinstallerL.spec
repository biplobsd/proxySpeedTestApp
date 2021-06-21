# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
import os
from kivymd import hooks_path as kivymd_hooks_path
path = os.path.abspath(".")

from kivy.utils import platform

import re
VERSIONFILE="main.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    verstr = ""
    

a = Analysis(['main.py'],
             pathex=[path],
             binaries=[],
             datas=[("assets", "assets"), ("libs", "libs"), ("LICENSE", ".")],
             hiddenimports=['pysocks'],
             hookspath=[kivymd_hooks_path],
             runtime_hooks=[],
             excludes=['numpy', 'enchant', 'cv2'],
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
          name=f'proxySpeedTest_{platform}_v{verstr}',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          icon="icon.ico" )
