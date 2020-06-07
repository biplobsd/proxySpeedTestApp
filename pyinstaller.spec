# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.building.build_main import *
import sys


path = os.path.abspath(".")
kivymd_repo_path = path.split("ProxySpeedTestV2")[0]
sys.path.insert(0, kivymd_repo_path)

from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

a = Analysis(
    ["main.py"],
    pathex=[path],
    binaries=[],
    datas=[("assets\\", "assets\\"), ("libs\\", "libs\\")],
    hookspath=[kivymd_hooks_path],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    hiddenimports=['pkg_resources.py2_warn','kivy_garden.zbarcam', 'win32file', 'win32timezone', 'pysocks'],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    debug=False,
    strip=False,
    upx=True,
    name="proxy_speed_test",
    console=True,
    icon="icon.ico",
)
