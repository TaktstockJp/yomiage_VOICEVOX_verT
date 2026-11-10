"""Bot が送るメッセージと読み上げの文面。口調を変えるときはこのファイルだけを編集する。"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# フォーク元由来の文面
#
# この区画は、かみみや 氏の yomiage_VOICEVOX から引き継いだものです。
# MIT License の対象外で、フォーク元の README「利用規約的なやつ」の条件に従います。
# https://github.com/kamimiya/yomiage_VOICEVOX
# ---------------------------------------------------------------------------

JOINED = "接続したのだ。よろしくなのだ。"
LEFT = "僕はこれで失礼するのだ。ばいばーい"
COMMAND_ERROR = "コマンドが間違っているのだ"
RELOADED = "更新完了"
VOICE_CHANGED = "ボイスの変更を行いました"
VOICE_NOT_FOUND = "話者が存在しない、または話者に対応するスタイルが存在しません"
ENGINE_NOT_FOUND = "指定されたソフトウェアが存在しません"
LEAVING_ALONE = "誰もいなくなったみたいだから僕もそろそろ抜けるのだ"

OMITTED = "以下略"
CODE_BLOCK = "コードブロック"
SPOILER = "ネタバレ防止"
DEFAULT_ATTACHMENT_KIND = "添付ファイル"


def member_joined(name: str) -> str:
    return f"{name}さんが入室したのだ"


def member_left(name: str) -> str:
    return f"{name}さんが退出したのだ"


def member_count(count: int) -> str:
    return f"現在{count}人接続しているのだ"


def word_limit_changed(limit: int) -> str:
    return f"文字数制限を{limit}に設定したのだ"


def setting_changed(label: str, enabled: bool) -> str:
    return f"{label}を{BOOL_LABELS[enabled]}にしたのだ"


def version_info(version: str, command_prefix: str) -> str:
    return (
        f"ずんだもんは現在起動中なのだ！(バージョン{version})\n"
        f"{command_prefix}joinで呼び出してくれたらすぐに参加するのだ！"
    )


def attachment_only(kind: str) -> str:
    return f"{kind}が貼られたのだ"


def attachment_suffix(kind: str) -> str:
    return f"かっこ、{kind}をみながら。"


BOOL_LABELS = {True: "オン", False: "オフ"}

ATTACHMENT_KINDS = {
    ".jpg": "画像ファイル",
    ".jpeg": "画像ファイル",
    ".jpe": "画像ファイル",
    ".ico": "画像ファイル",
    ".png": "画像ファイル",
    ".bmp": "画像ファイル",
    ".tif": "画像ファイル",
    ".tiff": "画像ファイル",
    ".mp3": "音声ファイル",
    ".wma": "音声ファイル",
    ".wav": "音声ファイル",
    ".mid": "音声ファイル",
    ".midi": "音声ファイル",
    ".avi": "動画ファイル",
    ".mp4": "動画ファイル",
    ".wmv": "動画ファイル",
    ".exe": "実行ファイル",
    ".dll": "実行ファイル",
    ".pdf": "PDFファイル",
    ".doc": "ワードファイル",
    ".csv": "シーエスブイファイル",
    ".xls": "エクセルファイル",
    ".ppt": "パワーポイントファイル",
    ".pps": "パワーポイントファイル",
    ".clip": "クリスタファイル",
    ".psd": "PSDファイル",
    ".txt": "テキストファイル",
    ".html": "テキストファイル",
    ".htm": "テキストファイル",
    ".shtml": "テキストファイル",
    ".css": "テキストファイル",
    ".zip": "圧縮ファイル",
    ".lzh": "圧縮ファイル",
}

TIME_SIGNALS = {
    0: "日付が変わったのだ。まだ寝ないのだ？",
    1: "ずんだもんが午前1時ぐらいをお知らせするのだ",
    2: "ずんだもんが午前2時ぐらいをお知らせするのだ。眠い・・・",
    3: "ずんだもんが午前3時ぐらいをお知らせするのだ",
    4: "おはようなのだ!朝4時に何してるのだ？",
    5: "ずんだもんが午前5時ぐらいをお知らせするのだ",
    6: "ずんだもんが午前6時ぐらいをお知らせするのだ",
    7: "ずんだもんが午前7時ぐらいをお知らせするのだ。朝ごはんの時間なのだ",
    8: "ずんだもんが午前8時ぐらいをお知らせするのだ",
    9: "ずんだもんが午前9時ぐらいをお知らせするのだ",
    10: "ずんだもんが午前10時ぐらいをお知らせするのだ",
    11: "ずんだもんが午前11時ぐらいをお知らせするのだ",
    12: "ずんだもんが正午をお知らせするのだ。作業を中断してそろそろお昼にするのだ",
    13: "ずんだもんが午後1時ぐらいをお知らせするのだ",
    14: "ずんだもんが午後2時ぐらいをお知らせするのだ",
    15: "ずんだもんが午後3時ぐらいをお知らせするのだ",
    16: "ずんだもんが午後4時ぐらいをお知らせするのだ",
    17: "ずんだもんが午後5時ぐらいをお知らせするのだ",
    18: "ずんだもんが午後6時ぐらいをお知らせするのだ",
    19: "ずんだもんが午後7時ぐらいをお知らせするのだ",
    20: "ずんだもんが午後8時ぐらいをお知らせするのだ。お腹がすいてきたから晩ごはんを食べてくるのだ",
    21: "ずんだもんが午後9時ぐらいをお知らせするのだ",
    22: "ずんだもんが午後10時ぐらいをお知らせするのだ",
    23: "ずんだもんが午後11時ぐらいをお知らせするのだ",
}

# ---------------------------------------------------------------------------
# この版で追加した文面（MIT License）
# ---------------------------------------------------------------------------

URL = "URL"

SETTING_LABELS = {
    "notify_join_leave": "入退出の通知",
    "report_member_count": "在室人数チェック",
    "auto_leave": "自動退出",
    "time_signal": "時報",
    "max_chars": "文字数制限",
}

ERROR_PRIVILEGED_INTENTS = (
    "Discord Bot の Privileged Gateway Intents が有効になっていません。\n"
    "https://discord.com/developers/applications の Bot の設定で、"
    "MESSAGE CONTENT INTENT と SERVER MEMBERS INTENT を有効にしてください。"
)
ERROR_LOGIN = "Discord Bot のトークンが間違っているか、config.toml に入力されていません。"
ERROR_NO_ENGINE = "利用できる TTS ソフトがありません。TTS ソフトを起動してから、もう一度実行してください。"

NOT_IN_VOICE = "先にボイスチャンネルに入ってほしいのだ"
NOT_CONNECTED = "ボイスチャンネルに接続していないのだ"
CONNECT_FAILED = "ボイスチャンネルに接続できなかったのだ"
STOPPED = "読み上げを止めたのだ"
UNEXPECTED_ERROR = "エラーが起きたのだ。ログを確認してほしいのだ"
WORD_NOT_FOUND = "その単語は登録されていないのだ"


def show_speakers_hint(command_prefix: str) -> str:
    return f"{command_prefix}show_speakers で、使えるソフトと話者とスタイルを確認してほしいのだ"


def word_added(word: str, reading: str) -> str:
    return f"「{word}」を「{reading}」と読むようにしたのだ"


def word_deleted(word: str) -> str:
    return f"「{word}」を単語帳から消したのだ"


def reload_failed(names: list[str]) -> str:
    return f"次のソフトは更新できなかったのだ：{'、'.join(names)}"


def param_not_found(names: list[str]) -> str:
    return f"指定できるパラメータは {', '.join(names)} なのだ"


def param_out_of_range(param: str, minimum: float, maximum: float) -> str:
    return f"{param} は {minimum} から {maximum} の間で指定してほしいのだ"


def param_changed(param: str, value: float) -> str:
    return f"{param} を {value} に変更したのだ"


def help_text(prefix: str) -> str:
    return (
        "```\n"
        "■基本コマンド\n"
        f"{prefix}join: BOTをボイスチャンネルに呼ぶ\n"
        f"{prefix}leave: BOTをボイスチャンネルから退出させる\n"
        f"{prefix}stop: 再生中の音声と、待っている読み上げをすべて止める\n"
        f"{prefix}hello: バージョン情報の確認\n"
        f"{prefix}help: このヘルプの表示\n\n"
        "■辞書コマンド\n"
        f"{prefix}wlist add A B: AをBと読ませる\n"
        f"{prefix}wlist delete A: Aの登録を消す\n"
        f"{prefix}wlist show: 登録内容をCSVファイルで確認する\n\n"
        "■調声コマンド\n"
        f"{prefix}chg_my_voice ソフト 話者 スタイル: 自分の声を変更する\n"
        f"{prefix}chg_voice_setting ソフト 話者 スタイル パラメータ 値: スタイルごとの調整\n"
        "パラメータは speed pitch intonation volume など。指定できる範囲はソフトごとに異なります\n"
        f"{prefix}show_speakers: 使えるソフトと話者とスタイルの確認\n"
        f"{prefix}reload: 話者の一覧を取り直す\n\n"
        "■各種設定\n"
        f"{prefix}inform_someone_come: 入退出の通知のオンオフ\n"
        f"{prefix}number_of_people: 在室人数チェックのオンオフ\n"
        f"{prefix}auto_leave: 無人になったときの自動退出のオンオフ\n"
        f"{prefix}time_signal: 時報のオンオフ\n"
        f"{prefix}word_count_limit N: 文字数制限の設定\n"
        f"{prefix}show_setting: 現在の設定の確認\n"
        "```"
    )
