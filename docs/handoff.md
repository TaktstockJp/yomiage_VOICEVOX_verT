# 引き継ぎ資料：Discord読み上げBot オーバーホール

このファイルは Claude Code に作業を引き継ぐための初期コンテキストです。
作業を始める前に最後まで読み、「7. 作業計画」の順に進めてください。
不明点は「9. 未決事項」を参照し、判断が必要なものはユーザーに確認してください。

---

## 1. 目的

既存の読み上げBot（`TaktstockJp/yomiage_VOICEVOX_verT`）を、**同じリポジトリの新ブランチ**上で、フォルダ構成とコードの両面からリファクタリング・オーバーホールする。

ユーザーが最も問題視している点：
- リリースを作っておらず、`discordbot.exe`（約12MB）などのバイナリがリポジトリに直接コミットされている
- 並列処理とクラス構成がフォーク元からほとんど変わっておらず、機能を足すたびにコードが読みづらくなっている

## 2. 要件

- テキストチャットの内容を読み取り、TTSソフトで音声を合成して、ボイスチャットで再生する（マイクで発話できないときの代替。既存Botの「Shovel」に相当）
- 日本語圏での利用を想定
- サーバーで動かすのではなく、利用者のPCでローカルに起動する方式。**1つのBotが担当するDiscordサーバーは1つ**でよい
- 対応するTTS：
  | TTS | 呼び出し方式 |
  |---|---|
  | VOICEVOX（および同じAPIを持つ互換ソフト） | REST API |
  | COEIROINK（v2） | REST API |
  | Voicepeak | コマンドライン実行 |
  | A.I.VOICE | A.I.VOICE Editor API（.NETアセンブリ / COM） |
  | VoiSona Talk | REST API |
  - 旧版が対応していないため**新規実装**するのは、Voicepeak と VoiSona Talk の2つ
- 実行環境は Windows（A.I.VOICE と Voicepeak がWindowsのデスクトップアプリのため）

## 3. 確定した技術方針

| 項目 | 決定内容 | 理由・注意 |
|---|---|---|
| 言語 | Python 3.12 | ユーザーに既存の実装経験がある。A.I.VOICEを pythonnet で直接呼べる |
| Discordライブラリ | `discord.py[voice] >= 2.7` と `davey >= 0.1.7, < 0.2` | davey 0.2.0 と discord.py 2.7.1 の組み合わせでは DAVE セッションが準備完了にならず、0.1.7 では準備完了になることを 2026-11-10 に実機で確認した。discord.py が 0.2 系に対応するまで固定する。2026年3月1日から、ボイスチャンネルへの接続に**DAVE（音声のE2E暗号化）への対応が必須**。discord.py は 2.7.0 で対応した。旧版はコミット `d34a884` に固定されているため、**現状ではVCに接続できない** |
| FFmpeg | **LGPLビルドの ffmpeg.exe をリリース物に同梱**する（リポジトリにはコミットしない） | 条件：LGPLの全文を同梱し、FFmpegを使っている旨を表示し、使ったバージョンのソースの入手先を示す。GPLビルドとnonfreeビルドは使わない。ffmpeg.exe は別プロセスとして呼び出す |
| コマンド | `!` で始まるプレフィックスコマンドとスラッシュコマンドの**両方に対応**（`commands.hybrid_command` / `hybrid_group` を使い、1つの実装で両方を受ける） | 現在の使い方を維持するため |
| 旧データとの互換性 | **不要**。旧CSVからの移行ツールは作らない | |
| 配布方法 | GitHub Actions で、タグをpushしたら Windows 上で PyInstaller ビルド → FFmpeg を同梱 → zip にして Releases に添付 | |

## 4. 既存リポジトリの現状

リポジトリ：https://github.com/TaktstockJp/yomiage_VOICEVOX_verT （最新コミット `39a00f0`、2023-06-13）

```
discordbot.py                 # 287行。エントリーポイント、イベント処理、スラッシュコマンド
discordbot.exe                # ★バイナリ。削除する
for_developer/
  discordbot_functions.py     # 596行。room_information クラス（何でも入っているクラス）
  discordbot_setting.py       # 156行。import した時点で setting.ini を読む。定数、メッセージ、ヘルプ文
  voice_generator.py          # 331行。VOICEVOX / COEIROINKv2 / A.I.VOICE の合成処理
  voice_speaker.py            # 127行。話者とスタイルのクラス（Java風の getter/setter）
bat/*.bat                     # curl で VOICEVOX / COEIROINK を叩くためのbat。削除する
data/*.csv                    # voice_list / flag_list / word_list / style_setting
setting.ini                   # トークン、ポート、A.I.VOICEのパス、コマンドの先頭文字、デフォルト話者
readme.md, readme.html, command_list.html, CHANGELOG.md, 前バージョンからの引継ぎ方法について.txt
tmp/css/style.css
requirements.txt              # discord.py をコミット固定、PyNaCl、pythonnet
```
※ **LICENSEファイルがない**（フォーク元は かみみや 氏の yomiage_VOICEVOX）。ライセンスの扱いはユーザーに確認すること（「9. 未決事項」）。

### 4.1 構造上の問題
1. **並列処理**
   - 合成が `os.system` → bat → `curl` という同期処理で、asyncio のイベントループを止める（A.I.VOICEの呼び出しも同期処理）
   - 中間ファイルが `tmp/query.json` と `tmp/tmp_voice.wav` の固定名で、処理が重なると上書きされる
   - 順番待ちを `now_loading` フラグや `is_playing()` を0.05秒ごとに確認するループで行っている
   - asyncio環境なのに、スレッド用の `queue.Queue` を使っている
2. **クラス構成**
   - `room_information` に、状態管理、コマンドの解釈、CSVの保存、合成・再生がすべて入っている
   - `from ... import *` が連鎖しており、グローバル変数に依存している。設定の読み込みが import した時点で実行される
   - `!` コマンド（`execute_commands` の長い if-elif 文）とスラッシュコマンドで、同じ処理が重複している
   - `AbstractVoiceGenerator` のコンストラクタが、13個の数値を順番に並べて受け取る形になっている
   - 使われていない残骸がある：`SE_file`, `image_file`, `pie_data`, `auto_fire`, `SE_on`, `from asyncio.windows_events import NULL`, `from __future__ import generators`
3. **エラー処理**：`except:` → `print(sys.exc_info())` でエラーを握りつぶしている。logging を使っていない
4. **Intents**：`Intents.all()` を使っているため、不要な Presence Intent まで要求している

### 4.2 既存の不具合（新実装で解消されていることを確認する）
- `!stop`：`message.guild.voice_bot.stop()` を呼んでいるが、この属性は存在しないので**再生が止まらない**（エラーは握りつぶされる）
- `!help` / `!hello`：`self.execute_help` をメソッドとして呼ばずに、メソッドオブジェクトのまま送信している
- `!chg_voice_setting`：引数を4つしか渡していないのに、関数側は5つ必要なので TypeError になる
- `on_voice_state_update` の `if not room_info_tmp.text_room_id_exist:` は、メソッドを呼んでいない（`()` がない）ため判定が常に通過する
- `!chg_voice_setting` の説明文の中で、コマンド名が `!chg_speed` になっている
- 正規表現 `[^```]*` や `[^||]*` は、文字クラスの誤用（意図した動作はしていない）
- スタンプと添付ファイルは、それぞれ先頭の1件しか処理していない

## 5. 新バージョンの機能

### 5.1 残す機能
| 機能 | 旧コマンド | 備考 |
|---|---|---|
| VCへの参加・退出 | `!join` / `!leave` | 実行者がいるVCに参加し、コマンドを打ったテキストチャンネルを読み上げ対象にする |
| 読み上げの停止 | `!stop` | **再生中の音声と、待っている読み上げをすべて破棄する**（旧版の不具合を修正） |
| バージョン表示・ヘルプ | `!hello` / `!help` | discord.py 標準の help コマンドは無効化する |
| 単語帳 | `!wlist add A B` / `delete A` / `show` | 長い単語から順に置換する。`show` はCSVファイルとして返す |
| 自分の声の変更 | `!chg_my_voice 話者 スタイル [ソフト名]` | 旧版の2つのスラッシュコマンドを1つにまとめる（ソフト名は省略可能）。スラッシュ版には自動補完を付ける |
| スタイルごとのパラメータ | `!chg_voice_setting ソフト 話者 スタイル パラメータ 値` | 指定できる値の範囲はエンジンごとに定義する |
| 話者一覧 | `!show_speakers` | Discordのメッセージ長制限（2000文字）を超える場合は分割するか、ファイルにして送る |
| 設定一覧 | `!show_setting` | |
| 文字数制限 | `!word_count_limit N` | 初期値は50。超えた分は削って「以下略」を付ける |
| 話者情報の再読み込み | `!reload` | 各エンジンから話者一覧を取り直す |
| **入退室の通知と人数表示** | `!inform_someone_come` / `!number_of_people` / `!auto_leave` | ユーザーが残すと決めた機能。VCが無人になったら自動で退出する機能も含む |
| **時報** | `!time_signal` | ユーザーが残すと決めた機能。メッセージは旧版の `time_signal_dict` を引き継ぐ |

### 5.2 廃止する機能
- 名前読み上げ（`!read_name`）
- Botのステータスに接続中のVC名を表示する機能（`!inform_tmp_room`、`change_presence` まわり）
- 旧CSVの取り込み（移行処理）と、旧データの形式との互換
- 上に挙げた残骸すべて

### 5.3 読み上げ前のテキスト処理（旧版の動作を引き継ぐ）
- `>`（コメントとして扱う記号）で始まるメッセージは読まない。他のBot用の記号（初期値は `$`, `?`）で始まるメッセージも読まない。どちらの記号も設定で変えられるようにする
- 他のBotの発言は読まない。自分の発言も読まない（入退室の通知や時報は、テキスト送信とは別に読み上げキューへ直接追加する）
- 読み上げ対象のテキストチャンネル以外の発言は読まない
- 置換のルール：
  - スタンプ → スタンプ名
  - ユーザーへのメンション → 表示名、ロール → ロール名、チャンネル → チャンネル名（正規表現で探すのではなく、`message.mentions` などに入っている解決済みのオブジェクトを使う）
  - カスタム絵文字 → 絵文字名
  - コードブロックとインラインコード → 「コードブロック」
  - `||...||`（ネタバレ防止の伏せ字） → 「ネタバレ防止」
  - URL → 「URL」（旧版では「URLが貼られたのだ」）
  - 添付ファイル → 拡張子から種類を判定する（旧版の `extension_dict` を引き継ぐ）。本文がなければ「〇〇ファイルが貼られたのだ」、本文があれば最後に「かっこ、〇〇ファイルをみながら。」を付ける
  - 単語帳による置換（長い単語から順に）
  - 文字数制限 → 改行で区切って、1文ずつ読み上げキューに入れる
- Botのメッセージは、ずんだもん口調のものを1つのモジュール（例：`messages.py`）にまとめ、後から差し替えやすくする

## 6. 目標とするアーキテクチャ

### 6.1 フォルダ構成（案）
```
pyproject.toml
config.example.toml          # 本物の config.toml は .gitignore に入れる（トークンを含むため）
src/yomiage/
  __main__.py                # python -m yomiage で起動できるようにする
  app.py                     # Bot の生成、Cog の読み込み、エンジンの初期化、起動
  config.py                  # TOML（tomllib）を型付きの dataclass に読み込む
  messages.py                # Botが送るメッセージ、時報のメッセージ、拡張子の対応表
  cogs/
    voice.py                 # join / leave / stop / hello / help
    dictionary.py            # wlist グループ
    speaker.py               # chg_my_voice / chg_voice_setting / show_speakers / reload（自動補完付き）
    settings.py              # 設定の切り替え、word_count_limit、show_setting
    notify.py                # 入退室の通知、人数表示、自動退出、時報（tasks.loop）
  reading/
    normalizer.py            # テキスト処理の各ステップを順につなぐ形（純粋な関数にしてテストする）
    session.py               # ReadingSession：ギルド単位の読み上げの状態を持つ
  tts/
    base.py                  # TTSEngine の基底クラス / Speaker / Style / ParamSpec / VoiceParams
    registry.py              # エンジンの登録と、「ソフト・話者・スタイル」から声を探す処理
    voicevox.py              # VOICEVOX 互換（名前とポートの組を複数登録できる）
    coeiroink.py             # COEIROINK v2
    aivoice.py
    voicepeak.py
    voisona.py
  audio.py                   # WAVのバイト列 → discord.FFmpegOpusAudio(pipe=True)
  storage.py                 # SQLite（標準ライブラリの sqlite3）
tests/                       # normalizer、storage、registry、各エンジンのリクエスト組み立て（HTTPはモック）
.github/workflows/release.yml
README.md / CHANGELOG.md / THIRD_PARTY_NOTICES.md（FFmpegのライセンスなど）
```

### 6.2 並列処理のモデル
- `ReadingSession` に次の2つのキューと、それを処理する2つのワーカーを持たせる：
  - `text_queue: asyncio.Queue[Utterance]`
  - `audio_queue: asyncio.Queue[AudioClip]`（`maxsize=2`）
  - **合成ワーカー**：`text_queue` から取り出して合成し、`audio_queue` に入れる。これで常に1〜2件先まで合成しておける
  - **再生ワーカー**：`audio_queue` から取り出して `vc.play(source, after=...)` で再生する。再生完了は `after` コールバックから `loop.call_soon_threadsafe(event.set)` で受け取り、`await event.wait()` で待つ。**一定間隔で状態を確認するループは使わない**
- `Utterance` には、キューに入れた時点で決まった声（エンジン・話者・スタイル・パラメータ）を持たせる
- `stop()`：両方のキューを空にし、世代番号を進めて、合成中の音声が後から再生されないようにし、`vc.stop()` を呼ぶ
- エンジンごとの呼び出し方：
  - HTTP系（VOICEVOX、COEIROINK、VoiSona）：`aiohttp.ClientSession` を共有して呼ぶ。中間ファイルは作らず、バイト列のまま扱う
  - A.I.VOICE：**専用のスレッド1本**（`ThreadPoolExecutor(max_workers=1)`）上で、同期APIを1件ずつ呼ぶ
  - Voicepeak：`asyncio.create_subprocess_exec` と `asyncio.Lock` で1件ずつ実行する。出力先は一時ファイル（ファイル名は呼び出しごとに変える）
- 1つのBotが担当するサーバーは1つだが、`ReadingSession` は `dict[guild_id, ReadingSession]` で管理しておく（実装の手間はほぼ変わらない）

### 6.3 TTSエンジンの共通インターフェース（案）
```python
@dataclass(frozen=True)
class ParamSpec:
    min: float
    max: float
    default: float

class TTSEngine(ABC):
    name: str                                  # 設定ファイルでの名前（例: "VOICEVOX", "SHAREVOX"）
    param_specs: Mapping[str, ParamSpec]       # speed / pitch / intonation / volume のうち対応するもの

    async def start(self) -> None: ...         # 接続を確認し、話者一覧を取得する
    async def close(self) -> None: ...
    def speakers(self) -> Sequence[Speaker]: ...  # Speaker(name, styles: list[Style(name, id)])
    async def synthesize(self, text: str, speaker: str, style: str,
                         params: Mapping[str, float]) -> bytes: ...  # WAVのバイト列を返す
```
- 起動に失敗したエンジンはログを出して登録しないだけにし、Bot自体は起動を続ける。利用できるエンジンが1つもない場合だけ終了する（旧版と同じ動作）
- ユーザーが指定した声やデフォルトの声が見つからない場合は、最初に登録されたエンジンの最初の声で読む（旧版と同じ動作）

### 6.4 エンジンごとのメモ
| エンジン | 呼び出し方 | パラメータの範囲（min〜max、初期値） | 注意 |
|---|---|---|---|
| VOICEVOX 互換 | `GET /speakers`、`POST /audio_query?text=&speaker=`、`POST /synthesis?speaker=`（本体にクエリJSON） | speed 0.5〜2.0（1.2）、pitch -0.15〜0.15（0）、intonation 0〜2（1）、volume 0〜2（1） | 旧版の初期ポート：VOICEVOX 50021、COEIROINK(v1) 50031、LMROID 50073、SHAREVOX 50025、ITVOICE 49540。設定は `[[engines.voicevox]] name=..., port=...` の形で複数書けるようにする |
| COEIROINK v2 | ポート 50032、`GET /v1/speakers`（`speakerName` / `speakerUuid` / `styles[].styleName` / `styleId`）、`POST /v1/synthesis`（`speakerUuid`, `styleId`, `text`, `speedScale`, `volumeScale`, `pitchScale`, `intonationScale`, `prePhonemeLength`, `postPhonemeLength`, `outputSamplingRate`） | VOICEVOX と同じ値 | 旧版の `voice_generator.py` の `CoeiroinkV2VoiceGenerator` を参考にする |
| A.I.VOICE | pythonnet で `AI.Talk.Editor.Api.dll` を読む（初期パス `C:\Program Files\AI\AIVoice\AIVoiceEditor\`）。`TtsControl` → `GetAvailableHostNames()[0]` で `Initialize` → 起動していなければ `StartHost()` → `Connect()` | Speed 0.5〜4（1.2）、Pitch 0.5〜2（1）、PitchRange（抑揚に対応）0〜2（1）、Volume 0〜2（1） | API操作が10分間ないと接続が切れるため、合成の前に毎回 `Status` を確認して再接続する。スタイルの対応：プリセットJSONの `Styles` の J＝喜び、A＝怒り、S＝悲しみ（タンゲ コトエだけ J＝ハイテンション、S＝ローテンション）。それとは別に「普通」スタイルを追加する。合成のときは `MasterControl.SentencePause` を一時的に0にして、終わったら元に戻す。`SaveAudioToFile` で出力する |
| Voicepeak（新規） | `voicepeak.exe -s <文> -n <ナレーター> -o <out.wav> -e <感情=値,...> --speed <n> --pitch <n>`。一覧の取得は `--list-narrator` と `--list-emotion <ナレーター>` | speed 50〜200（100）、pitch -300〜300（0） | **1回の入力は140文字まで**。超える場合は句読点で分割して合成し、`wave` モジュールで連結する。同時実行はしない。「感情」をスタイルとして扱い、「標準」（感情の指定なし）を追加する。exeのパスは設定で指定する |
| VoiSona Talk（新規） | REST API（ベータ版）。初期ポートは 32766。Basic認証：ユーザー名は登録メールアドレス、パスワードはVoiSonaの設定画面で決めたAPI用のもの。合成は、リクエストを送ったあと状態を確認して結果を取りに行く非同期の流れ | 第三者製のCLIの説明による参考値：speed 0.2〜5、pitch -600〜600（セント）、intonation 0〜2、volume -8〜8（dB） | **エンドポイントのパスと値の範囲は、公式マニュアルで必ず確認すること**（未検証）。1.3.7（2026年4月、REST API 0.9.1）でWAVデータを取得するエンドポイントが追加されたので、このバージョン以上を前提にする |

### 6.5 保存するデータ（SQLite）
- `user_voices(user_id PK, engine, speaker, style)`
- `style_params(engine, speaker, style, param, value, PK(engine, speaker, style, param))`：初期値から変更したものだけ保存する
- `dictionary(word PK, reading)`
- `settings(key PK, value)`：`notify_join_leave`、`report_member_count`、`auto_leave`、`time_signal`、`max_chars`

### 6.6 設定ファイル `config.toml`（案）
```toml
[discord]
token = ""
command_prefix = "!"
comment_prefix = ">"
ignore_prefixes = ["$", "?"]

[default_voice]
engine = "VOICEVOX"
speaker = "ずんだもん"
style = "あまあま"

[ffmpeg]
path = ""        # 空なら exe と同じ場所の ffmpeg/ffmpeg.exe → PATH の順で探す

[[engines.voicevox]]
name = "VOICEVOX"
port = 50021

[engines.coeiroink]
enabled = false
port = 50032

[engines.aivoice]
enabled = false
dir = 'C:\Program Files\AI\AIVoice\AIVoiceEditor\'

[engines.voicepeak]
enabled = false
exe = 'C:\Program Files\VOICEPEAK\voicepeak.exe'

[engines.voisona]
enabled = false
port = 32766
user = ""
password = ""
```

### 6.7 Intents とエラー処理
- 使う Intents：`guilds`、`guild_messages`、`message_content`（特権）、`voice_states`、`members`（特権。VC内の人数を正しく数えるため）。Presence Intent は使わない
- 特権 Intent が有効になっていない場合（`PrivilegedIntentsRequired`）と、トークンが間違っている場合（`LoginFailure`）は、旧版と同じく分かりやすい日本語のメッセージを出す
- ログは `logging` を使い、コンソールと `logs/` 以下のファイルに出す

### 6.8 リリース用ワークフロー（`.github/workflows/release.yml`）
- 起動条件：`v*` 形式のタグをpushしたとき。実行環境は `windows-latest`、Python 3.12
- PyInstaller は `--onedir` でビルドする（`--onefile` は起動が遅く、ウイルス対策ソフトに誤検知されやすいため）。`davey` と discord.py 同梱の opus DLL、pythonnet の実行時ファイルが確実に含まれるようにする（`--collect-all` を使うか、.spec ファイルに書く）
- FFmpeg は **BtbN/FFmpeg-Builds の LGPL ビルド（win64、lgpl）をバージョン固定で**ダウンロードし、`ffmpeg/ffmpeg.exe` に置く。LICENSE と、使ったバージョンのソースのURLを `THIRD_PARTY_NOTICES.md` に書いて同梱する
- zip にまとめて Release に添付する（`softprops/action-gh-release` など）

## 7. 作業計画
1. **ブランチの作成**：`main` から新ブランチを作る（名前の案：`overhaul`）。**`main` には直接pushしない。履歴の書き換えもしない**
2. **旧ファイルの削除**：`discordbot.exe`、`bat/`、`for_developer/`、`data/*.csv`、`tmp/`、`setting.ini`、`readme.html`、`command_list.html`、`前バージョンからの引継ぎ方法について.txt`、`requirements.txt` を削除する。`.gitignore` を整備する（`config.toml`、`*.db`、`logs/`、`dist/`、`build/`、`ffmpeg/`）
3. **土台**：`pyproject.toml`、`config.py`、`messages.py`、`storage.py`、logging の設定
4. **`reading/normalizer.py` とそのテスト**
5. **`tts/base.py`、`registry.py`、`voicevox.py`、`coeiroink.py`** とテスト（HTTPはモックする）
6. **`reading/session.py`** と `audio.py`
7. **Cog の実装**（voice → speaker → dictionary → settings → notify）。help の文面も新しいコマンドに合わせて更新する
8. **`aivoice.py`**（旧版のコードを移植。スレッド1本で実行する形に変える）
9. **`voicepeak.py`、`voisona.py`**（新規。VoiSona はエンドポイントを確認してから実装する）
10. **リリース用ワークフロー**、`README.md`（セットアップ手順。Botの作成、特権 Intent の有効化、招待URL、`config.toml` の書き方）、`CHANGELOG.md`、`THIRD_PARTY_NOTICES.md`

### 完了の条件
- `python -m yomiage` で起動し、VOICEVOX だけの構成で「参加 → 読み上げ → `!stop` で即座に止まる → 退出」が動く（DAVEが有効なVCで確認する）
- 連続して投稿しても、順番が入れ替わったり音声が重なったりせず、合成中もBotが応答し続ける
- 4.2 の不具合がすべて再現しない
- `pytest` が通る
- リポジトリにバイナリが含まれていない

## 8. 作業時の注意
- 作業するPCでは、実際の動作確認に Discord のBotトークンと、起動中の各TTSソフトが必要になる。A.I.VOICE と Voicepeak は Windows でしか確認できない
- トークンなどの秘密情報はコミットしない
- コミットは段階ごとに小さく分ける。pushする前にユーザーに確認する

## 9. 未決事項（ユーザーに確認する）
1. ~~**LICENSE**~~：**決定済み**。`LICENSE` は MIT とし、著作権者はタクト（TaktstockJp）とする。ただし、かみみや 氏が書いた部分（`time_signal_dict`、`extension_dict`、ずんだもん口調のBotメッセージと読み上げの文言のうち旧版から引き継ぐもの）は `messages.py` の「フォーク元由来の文面」の区画にまとめ、フォーク元の README「利用規約的なやつ」の条件に従うものとして、LICENSE と README に例外として明記する。フォーク元の条件（改変版を配布するときはファイル名を変え、更新履歴に変更点を追記する）は、新しいファイル名と `CHANGELOG.md` への追記で満たす。手順10で反映する
2. ~~**スラッシュコマンドのグループ名**~~：**決定済み**。グループは廃止し、`/join` と `!join` の形にする（旧版の `SlashSyntax` に相当する設定は作らない）
3. **`main` へ統合する時期**（ブランチは `overhaul` に決定済み。`origin/main` と同じ `39a00f0` から分岐している）
4. **VoiSona のパラメータ**：確定した範囲と、スタイル（感情の比率）を扱うかどうか
