# yomiage_VOICEVOX(verT-20220924)

by かみみや

forked by タクト

## 概要

Discordのチャットを「VOICEVOXおよび同等の仕様のWebAPIを利用して動作する音声合成ソフトウェア(COEIROINK等)」および「A.I.VOICE」で読み上げるソフトです。

python読める＆python実行できる人向けです。

コマンド一覧は[command_list.html](command_list.html)を参照してください。

## 機能紹介

1. チャットの読み上げ
2. 単語の読み仮名登録
3. ユーザー毎に使用ボイスを変える
4. ボイスチャット入室時の通知（オンオフ切り替え可能）
5. 時報機能（オンオフ切り替え可能）


## ファイル構造(重要度順)

1. **readme.md**
   - これです。使い方など書いているのでお読みください。
2. **readme.html**
   - exe版を利用する場合はこちらをお読みください
3. **前バージョンからの移行方法.txt**
   - 以前のバージョンを使っていた場合はこれを参考にしてデータ（単語帳など）を引き継いでください
4. **discordbot.exe**
   - 実行ファイル
5. **discordbot.py**
   - コマンドプロンプトから実行する場合はこちらを使ってください
6. **setting.ini**
   - 各種設定ファイルです。今のところ「Botのトークン」「使用するソフトウェアの名称と使用するポート番号の組」「A.I.VOICEを使用するかどうか」「デフォルト話者とスタイルの設定」「データファイルの場所」を設定できます。
7. **command_list.html**
   - 実装されているコマンドの確認
8. **Synthax_setting.csv**
   - コマンドおよびコメントの先頭の文字を設定するファイル
9. **for_developer**
   - ソースファイル
10. **data**
   - 単語帳などが保存されるファイル。開く必要はあまりないです。
11. **get_speakers_from_VOICEVOX.bat**
   - VOICEVOXから話者の情報を取得するbatファイル。通常は編集する必要はありません。
12. **output_json_from_VOICEVOX.bat**
   - VOICEVOXでjsonファイルを作成するbatファイル。通常は編集する必要はありません。
13. **output_voice_from_VOICEVOX.bat**
   - VOICEVOXで音声を作成するbatファイル。通常は編集する必要はありません。
14. **tmp**
   - 一時的に出力されるファイル（VOICEVOXで出力した音声ファイル等）が保存されます。開く必要は全くないです。

## 注意

1. このソフトはWindows10・11上で使われることを想定しています。LinuxやMacで使う場合はbatファイルまわりと音声のopus変換まわりをいじれば多分なんとかなります。
2. Pythonほぼ触ったことない + Discord bot作るの初めてで不慣れなところがあり一部コードが汚いかもしれないです。ごめんなさい。
3. 以前のバージョンのデータを引き継ぎたい場合は**データの引き継ぎ方.txt**をご覧ください

## 導入が必要なソフト

このソフトを利用するために以下のソフト類のインストールが必要です。

1. python3のインストール
   [このサイト](https://www.python.jp/install/windows/install.html)を参考にしてください。
   
   **python3.8以上をおすすめします。**（3.7より古いものはライブラリがサポートしていない）
   
2. ffmpegのインストール
   [このサイト](https://jp.videoproc.com/edit-convert/how-to-download-and-install-ffmpeg.htm)の"**1. WindowsでFFmpegをダウンロード＆インストールする方法（Windows10対応）**"を参考にしてください。

3. discord.py, PyNaCl, pythonnetのインストール
   コマンドプロンプト（Win+Rで"ファイル名を指定して実行"をひらいて"cmd"を打ち込んだら出てくると思います）上で以下のコマンドを打ち込んで実行してください。

   ```bash
   $ pip install git+https://github.com/Rapptz/discord.py
   $ pip install PyNaCl
   $ pip install pythonnet
   ```
   
4. VOICEVOXのインストール
   [このサイト](https://voicevox.hiroshiba.jp/)から最新版をダウンロードしてください。

5. A.I.VOICEを使用する場合
   setting.iniのUseAIVoiceをTrueにし、AIVoiceDirにA.I.VOICEのあるディレクトリを記述してください。


## 起動方法


1. 上の導入が必要なソフトをすべてインストールします。

2. このフォルダ(yomiage_VOICEVOX)をわかりやすい場所に置きます。

3. DiscordのBotを作成し、招待します。（すでにチャットルームにBotを招待している場合は省略）[このサイト](https://note.com/exteoi/n/nf1c37cb26c41)の**1. Discord上のBotの作成**にある記述を参考にしてください。

   1. https://discord.com/developers/applications を開く。
   2. 右上にあるNew Applicationを押す。適当な名前を入れてCreateを押す。
   3. 管理画面が開かれる。左のメニューのBotを押し、Reset Tokenを押す。→Yes, do it!を選択（開かれない場合はDeveloper Portalから作成したアプリケーションを選択する）
   4. するとBuild-A-BotのところにTOKENの文字列が出てくる。下にあるCopyを押すとBotのTOKENがコピーできる。**のちに必要となるので保存しておく。**
   5. **その下のREQUIRES OAUTH2 CODE GRANTをオフ、Presence Intent, Server Members Intent, MESSAGE CONTENT INTENTという項目をオンにする。(灰色がオフ、青色がオン）** PUBLIC BOTは自分が運営するサーバーに導入する場合はオフでよいが、自分以外が運営するサーバーに招待する場合はオンにしておく。
   6. 左のメニューのOAuth2→URL Generatorを開き、SCOPESでbotにチェックを入れる。
   7. BOT PERMISSIONSという項目が出てくると思うのでRead Messages/ViewChannels, Send Messages, Connect, Speak, Use Slash Commands(スラッシュコマンドを利用する場合)にチェックを入れる。
   8. 一番下にあるGENERATED URLにあるリンクを開くとサーバー招待画面が出てくるので、追加したいサーバーを選択して認証する。

4. アクセストークン等を設定する（すでに設定していたら省略）

   setting.iniをテキストエディタで開いて、2-4)でコピーしていたTOKENをコピペしてください。
   A.I.VOICEを利用する場合、[A.I.VOICE Setting]のUseAIVoiceをTrueにし、AIVoiceDirにAIVoiceEditor.exeがあるディレクトリを指定してください。

5. VOICEVOXを起動します。

6. コマンドプロンプトを起動します。 （Win+Rで"ファイル名を指定して実行"をひらいて"cmd"を打ち込んだら出てくると思います）

7. チェンジディレクトリでこのフォルダの中身まで移動します。
   cd ディレクトリ名で移動できます。（https://eng-entrance.com/windows-command-cd を参照）例えば以下のようにする。

   ```bash
   $ cd C:\discord_bot\yomiage_VOICEVOX
   ```

8. コマンドプロンプトに以下を打ち込み、実行します。

   ```bash
   $ py discordbot.py
   ```

9. おつかれさまでした。

## 使用方法

1. Botを参加させたいボイスチャンネルに入室しておきます。
2. 読み上げ対象にしたいテキストチャンネル上で"!join"と打ち込みます。

## 終了方法

1. "!leave"でボイスチャンネルからBOTを退場させておきます
2. コマンドプロンプト上で"ctrl + C"をおこなって終了させます

## exeファイル化の方法

pyinstallerを使うので入ってない場合はインストールする。

```bash
$ pip install pyinstaller
```

以下のコマンドを打ち込んでexe化する（pyinstallerが使えない場合は環境変数の編集からPath[例）C:\Users\xxx\AppData\Roaming\Python\Python38\Scripts]を追加する）

```bash
$ pyinstaller discordbot.py --onefile
```

成功したら**dist**というファイルが生成され、そのなかにdiscordbot.exeがある。

### **注意**

追加機能を付けるなどで外部ライブラリを使うorPython以外でコーディングしたプログラムを用いる必要がある場合はspecファイルの書き換えを行う必要がでてくる可能性がある

[参考資料](https://qiita.com/takanorimutoh/items/53bf44d6d5b37190e7d1) 

## エラーが出た時

- アクセスが拒否されました

  ウイルスセキュリティソフトに引っかかっている可能性がある。許可する。

- Bot TOKENが設定されていません

  設定して下さい。[**起動方法4)**を参照]

- Discord BotのPrivileged Intents が有効になっていません云々のメッセージ

  BOTの設定に問題があるので確認する [**起動方法2-5)**を参照]

- ffmpegがインストールされていない云々のメッセージ

  ffmpegをインストールする [**導入が必要なソフト1)**を参照]

## 前バージョンからの引き継ぎ方法

新バージョンのdataフォルダに、旧バージョンのdataフォルダの内容を上書きしてください。

## その他

1. ほかのBOTとコマンドが被ってしまっている場合はSynthax_setting.csvの"!", ">", "voice-bot1"を適当に変更してください。
2. このBOTは改変版です。バグ報告や機能要望等は[改変者のTwitter](https://twitter.com/Taktstock_mov)にお願いします。


## 利用規約的なやつ

1. 本ソフトはオープンソースです。お金を払いたい場合はVOICEVOX様にどうぞ

   [VOICEVOX支援先](https://hiho.fanbox.cc/)

2. ソースコードの改変はご自由にどうぞ。
   ただし、改変したものを配布する場合は改変したことが分かるようにファイル名を変更して、更新履歴に変更点を追記してください。

3. VOICEVOX及び各キャラの利用規約をよく読んでから使用してください。<br>
   [VOICEVOX HP](https://voicevox.hiroshiba.jp/) <br>
   [COEIROINK HP](https://coeiroink.com/) <br>
   [LMROID HP](https://lmroidsoftware.wixsite.com/nhoshio) <br>
   [SHAREVOX HP](https://www.sharevox.app/) <br>
   [ITVOICE HP](https://booth.pm/ja/items/4374126) <br>
   [東北ずん子利用の手引き](https://zunko.jp/guideline.html)<br>
   [A.I.VOICE Editor API利用規約](https://aivoice.jp/manual/editor/api.html#termsandconditions)
   
4. 本ソフトウェアにより生じた損害・不利益について、製作者は一切の責任を負いません。

5. 改善して欲しい点などあれば言ってください。
   ある程度リクエストは受け付けたいと思っていますが、製作者に技術がないのであまり期待しないでください。

6. 何かあれば改変者の[Twitter](https://twitter.com/Taktstock_mov)か[Misskey](https://misskey.io/@Taktstock_mov)まで<br>
