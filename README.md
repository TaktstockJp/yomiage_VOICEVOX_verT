# yomiage_VOICEVOX (verT)

by かみみや / forked by タクト

Discord のテキストチャットを TTS ソフトで音声合成して、ボイスチャットで読み上げる Bot です。マイクで話せないときの代わりに使えます。

サーバーではなく、利用者の Windows PC で起動します。1つの Bot が担当する Discord サーバーは1つを想定しています。

## 対応している TTS ソフト

| ソフト | 接続方式 | 確認したバージョン |
|---|---|---|
| VOICEVOX（および同じ API を持つソフト） | REST API | 0.26.2 |
| COEIROINK v2 | REST API | 2.13.0 |
| A.I.VOICE | A.I.VOICE Editor API | 1.4.11 |
| Voicepeak | コマンドライン | 1.2.19 |
| VoiSona Talk | REST API（1.3.7 以上が必要） | 1.3.10 |

## セットアップ

### 1. Discord Bot を作る

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成します。
2. **Bot** の画面でトークンを発行して控えます。トークンは他の人に見せないでください。
3. 同じ画面の **Privileged Gateway Intents** で、**MESSAGE CONTENT INTENT** と **SERVER MEMBERS INTENT** を有効にします。

### 2. Bot をサーバーに招待する

**OAuth2** の **URL Generator** で次の項目にチェックを入れ、生成された URL を開いてサーバーに招待します。

- SCOPES：`bot`、`applications.commands`
- BOT PERMISSIONS：`View Channels`、`Send Messages`、`Attach Files`、`Connect`、`Speak`

### 3. ダウンロードして設定する

1. [Releases](https://github.com/TaktstockJp/yomiage_VOICEVOX_verT/releases) から zip をダウンロードして展開します。
2. `config.example.toml` をコピーして、同じフォルダに `config.toml` を作ります。
3. `config.toml` の `[discord]` の `token` に、Bot のトークンを書きます。
4. 使う TTS ソフトの設定をします（次の項目を参照）。

`config.toml` にはトークンなどの秘密情報が入るので、他の人に渡さないでください。

### 4. TTS ソフトごとの設定

使うソフトを先に起動してから Bot を起動してください（A.I.VOICE と Voicepeak は Bot が呼び出します）。起動できなかったソフトは使わずに続行し、1つも使えない場合は終了します。

**VOICEVOX と互換ソフト**

`[[engines.voicevox]]` をソフトの数だけ書きます。`name` はコマンドで使う名前です。

```toml
[[engines.voicevox]]
name = "VOICEVOX"
port = 50021

[[engines.voicevox]]
name = "AivisSpeech"
port = 10101
```

**COEIROINK v2**

`[engines.coeiroink]` の `enabled` を `true` にします。

**A.I.VOICE**

1. `[engines.aivoice]` の `enabled` を `true` にします。
2. A.I.VOICE Editor の音声保存の設定で、**「音声ファイルパスの指定方法」を「ファイル保存ダイアログで選択する」** にします。ファイル命名規則のままだと、音声が別の場所に保存されて読み上げに失敗します。

**Voicepeak**

`[engines.voicepeak]` の `enabled` を `true` にします。1文の合成に数秒かかり、Bot の起動にも30秒ほど長くかかります。

**VoiSona Talk**

1. VoiSona Talk の設定画面の API タブで API を有効にし、API 用のパスワードを決めます。
2. `[engines.voisona]` の `enabled` を `true` にし、`user` に登録メールアドレス、`password` に API 用のパスワードを書きます。

### 5. 起動する

`yomiage.exe` を実行します。読み上げてほしいテキストチャンネルで、VCに入った状態で `!join` か `/join` を送ってください。

## コマンド

`!` で始まるコマンドと、同じ名前のスラッシュコマンドの両方が使えます。`!` の部分は設定で変更できます。名前に空白が入るものは `"` で囲んでください。

| コマンド | 内容 |
|---|---|
| `!join` | 実行した人がいるVCに参加し、そのテキストチャンネルを読み上げる |
| `!leave` | VCから退出する |
| `!stop` | 再生中の音声と、待っている読み上げをすべて止める |
| `!hello` | バージョンを表示する |
| `!help` | コマンドの一覧を表示する |
| `!wlist add 単語 読み` | 単語の読みを登録する |
| `!wlist delete 単語` | 単語の登録を消す |
| `!wlist show` | 登録内容を CSV ファイルで受け取る |
| `!chg_my_voice ソフト 話者 スタイル` | 自分の声を変更する |
| `!chg_voice_setting ソフト 話者 スタイル パラメータ 値` | スタイルごとの話速などを変更する |
| `!show_speakers` | 使えるソフトと話者とスタイルを表示する |
| `!reload` | 話者の一覧を取り直す |
| `!inform_someone_come` | 入退出の通知のオンオフ |
| `!number_of_people` | 在室人数チェックのオンオフ |
| `!auto_leave` | 無人になったときの自動退出のオンオフ |
| `!time_signal` | 時報のオンオフ |
| `!word_count_limit 数` | 読み上げる文字数の上限を設定する |
| `!show_setting` | 現在の設定を表示する |

パラメータはソフトごとに異なります。

| ソフト | パラメータと範囲 |
|---|---|
| VOICEVOX 互換、COEIROINK | `speed` 0.5〜2.0、`pitch` -0.15〜0.15、`intonation` 0〜2、`volume` 0〜2 |
| A.I.VOICE | `speed` 0.5〜4、`pitch` 0.5〜2、`intonation` 0〜2、`volume` 0〜2 |
| Voicepeak | `speed` 50〜200、`pitch` -300〜300 |
| VoiSona Talk | `speed` 0.2〜5、`pitch` -600〜600、`intonation` 0〜2、`volume` -8〜8 |

## 読み上げのルール

- `>` で始まる発言と、他の Bot 用の記号（初期値は `$` と `?`）で始まる発言は読みません。記号は `config.toml` で変更できます。
- 他の Bot の発言は読みません。
- コードは「コードブロック」、`||伏せ字||` は「ネタバレ防止」、URL は「URL」と読みます。
- スタンプ、メンション、カスタム絵文字は名前を読みます。
- 添付ファイルは、拡張子から種類を判定して読みます。

## ソースから実行する

Python 3.12 が必要です。

```bash
py -3.12 -m venv .venv
```

```bash
.venv\Scripts\python -m pip install -e ".[dev]"
```

```bash
.venv\Scripts\python -m yomiage
```

テストは `.venv\Scripts\python -m pytest` で実行できます。FFmpeg は `config.toml` の `[ffmpeg]` の `path`、`ffmpeg/ffmpeg.exe`、PATH の順に探します。

`v` で始まるタグを push すると、GitHub Actions が zip をビルドして Releases に添付します。

## ライセンスと利用規約

- このソフトウェアは [MIT License](LICENSE) です。ただし、フォーク元から引き継いだ文面は例外です。詳しくは LICENSE を参照してください。
- フォーク元は、かみみや 氏の [yomiage_VOICEVOX](https://github.com/kamimiya/yomiage_VOICEVOX) です。改変版を配布する場合は、フォーク元の README の条件にも従ってください。
- 同梱のソフトウェアについては [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
- 各 TTS ソフトと各キャラクターの利用規約をよく読んでから使用してください。
- このソフトウェアにより生じた損害や不利益について、製作者は一切の責任を負いません。
