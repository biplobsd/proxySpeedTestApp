# -*- mode: python ; coding: utf-8 -*-

import os, re
path = os.path.abspath(".")
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy_deps import sdl2, glew, angle
from kivymd import hooks_path as kivymd_hooks_path
from kivy.tools.packaging.pyinstaller_hooks import runtime_hooks
from kivy.utils import platform

VERSIONFILE="main.py"
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    verstr = ""

a = Analysis(
    ["main.py"],
    pathex=[path],
    binaries=[],
    datas=[("assets\\", "assets\\"), ("libs\\", "libs\\"), ("LICENSE", ".")],
    hookspath=[kivymd_hooks_path],
    runtime_hooks=runtime_hooks(),
    excludes=['numpy', 'enchant', 'cv2', 'win32com', 'altgraph', 'pyinstaller', 'docutils'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    hiddenimports=['socks', 'sockshandler'],
)
excluded_binaries = [
        'VCRUNTIME140.dll',
        'msvcp140.dll',
        'mfc140u.dll',
		'libcrypto-1_1.dll',
		'unicodedata.pyd',
		'ucrtbase.dll',
		'SDL2.dll']
a.binaries = TOC([x for x in a.binaries if x[0] not in excluded_binaries])

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins+ angle.dep_bins)],
    debug=False,
    strip=False,
    upx=True,
    name=f'proxySpeedTest_{platform}_v{verstr}',
    console=True,
    icon="icon.ico",
)
