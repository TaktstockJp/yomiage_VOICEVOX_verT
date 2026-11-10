"""PyInstaller でビルドするときの起動スクリプト。"""

import sys

from yomiage.app import main

code = main()
if code != 0:
    # ダブルクリックで起動した場合に、エラーを読む前に画面が閉じないようにする
    input("Enter キーを押すと終了します。")
sys.exit(code)
