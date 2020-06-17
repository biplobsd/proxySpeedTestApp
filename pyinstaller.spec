# -*- mode: python ; coding: utf-8 -*-

import os, re
path = os.path.abspath(".")
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy_deps import sdl2, glew, angle
from kivymd import hooks_path as kivymd_hooks_path
from kivy.tools.packaging.pyinstaller_hooks import runtime_hooks

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
    excludes=['numpy', 'enchant', 'cv2', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    hiddenimports=['pysocks'],
)

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
    name=f"proxy_speed_test_v{verstr}",
    console=True,
    icon="icon.ico",
)
