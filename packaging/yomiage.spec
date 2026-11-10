# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller の設定。リポジトリのルートで pyinstaller packaging/yomiage.spec を実行する。"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []
# 動的に読み込まれるファイル（davey の拡張モジュール、discord.py の opus、pythonnet の実行時ファイル）を確実に含める
for package in ("discord", "davey", "pythonnet", "clr_loader"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

analysis = Analysis(
    ["entry.py"],
    pathex=["../src"],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="yomiage",
    console=True,
)
coll = COLLECT(exe, analysis.binaries, analysis.datas, name="yomiage")
