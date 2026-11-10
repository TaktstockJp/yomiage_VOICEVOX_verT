# サードパーティのソフトウェア

配布用の zip には、次のソフトウェアが含まれています。

## FFmpeg

このソフトウェアは、[FFmpeg](https://ffmpeg.org/) の LGPL ビルドを別プロセスとして呼び出して使用しています。
FFmpeg は LGPL のもとで配布されており、ライセンスの全文は同梱の `ffmpeg/LICENSE.txt` にあります。

| 項目 | 内容 |
|---|---|
| バージョン | n8.1.3-27-g8dca1586f4（win64 / LGPL） |
| ビルドの入手先 | [BtbN/FFmpeg-Builds autobuild-2026-10-31-12-59](https://github.com/BtbN/FFmpeg-Builds/releases/tag/autobuild-2026-10-31-12-59) |
| ソースコード | [FFmpeg/FFmpeg commit 8dca1586f4](https://github.com/FFmpeg/FFmpeg/commit/8dca1586f4) |
| ビルドスクリプト | [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) |

## Python と Python パッケージ

Python 本体と、実行時に使う Python パッケージ（discord.py、aiohttp、PyNaCl、pythonnet など）のライセンスの全文は、同梱の `licenses/` フォルダにパッケージごとに入っています。
discord.py に含まれる libopus のライセンスは、`licenses/discord-py-*/COPYING` にあります。

`davey` の配布物にはライセンスファイルが含まれていないため、全文を次に記載します。

```text
MIT License

Copyright (c) 2025-present Snazzah

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## PyInstaller

実行ファイルの作成に [PyInstaller](https://pyinstaller.org/) を使用しています。PyInstaller のブートローダーは、生成物の配布を認める例外条項付きの GPL のもとで配布されています。
