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
