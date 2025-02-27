import csv
import configparser

voibox_version = 'verT-20230613'

# アクセストークンの読み取り
ini = configparser.ConfigParser()
ini.optionxform = str
ini.read('./setting.ini', 'UTF-8')
TOKEN = ini.get('Token Setting', 'Token')

command_syntax = ini.get('Syntax Setting', 'CommandSyntax')
comment_syntax = ini.get('Syntax Setting', 'CommentSyntax')
other_bots_syntax  = ini.get('Syntax Setting', 'OtherBotsSyntax').split(',')
slash_syntax  = ini.get('Syntax Setting', 'SlashSyntax')

# VOICEVOX用のbatファイルのパス
bat_json = "bat\output_json_from_VOICEVOX.bat"
bat_voice = "bat\output_voice_from_VOICEVOX.bat"
bat_speakers = "bat\get_speakers_from_VOICEVOX.bat"

# COEIROINK用のbatファイルのパス
bat_voice_cv2 = "bat\output_voice_from_COEIROINKv2.bat"
bat_speakers_cv2 = "bat\get_speakers_from_COEIROINKv2.bat"

#各種ファイルへのパス(discordbot.pyからみた相対パス)
voice_file = "tmp/tmp_voice.wav"              # VOICEVOX音声の保存先
json_file = 'tmp/query.json'                  # jsonファイルへのパス
clist_file = "data/command_list.txt"          # コマンドリスト
SE_file = "SE_list.csv"                       # SEリスト
image_file = "image_list.csv"                 # 画像リスト
pie_data = 'pie_data.txt'                     # パイ練り記録

# 各種フラグのデフォルト値
inform_tmp_room     = True     # 入退出の通知
inform_someone_come = True     # 入退出の通知
time_signal         = True     # 時報
read_name           = False    # 話者の名前を読み上げる。
number_of_people    = True    # 在室人数チェック
auto_leave          = True    # ボイスチャンネルから自動的に退出する
SE_on               = True    # SE機能をオンにする
auto_fire           = True   # 自動発火機能
word_count_limit = 50

# 各種コマンド(変更した場合はcommand_list.txtを書き換えてください。)
command_hello               = command_syntax + 'hello'
command_help                = command_syntax + 'help'
command_join                = command_syntax + 'join'
command_leave               = command_syntax + 'leave'
command_wlist               = command_syntax + 'wlist'
command_chg_my_voice        = command_syntax + 'chg_my_voice'
command_inform_tmp_room     = command_syntax + 'inform_tmp_room'
command_inform_someone_come = command_syntax + 'inform_someone_come'
command_time_signal         = command_syntax + 'time_signal'
command_read_name           = command_syntax + 'read_name'
command_number_of_people    = command_syntax + 'number_of_people'
command_auto_leave          = command_syntax + 'auto_leave'
command_word_count_limit    = command_syntax + 'word_count_limit'
command_chg_voice_setting   = command_syntax + 'chg_voice_setting'
command_show_setting        = command_syntax + 'show_setting'
command_reload              = command_syntax + 'reload'
command_stop                = command_syntax + 'stop'
command_show_speakers       = command_syntax + 'show_speakers'

# テンプレートコメントリスト
comment_dict = {'message_reload': comment_syntax + '更新完了',
                'message_err': comment_syntax + 'コマンドが間違っているのだ',
                'message_join': comment_syntax + "接続したのだ。よろしくなのだ。",
                'message_leave': comment_syntax + "僕はこれで失礼するのだ。ばいばーい",
                'message_chg_voice': comment_syntax + "ボイスの変更を行いました",
                'message_not_actualized': comment_syntax + "話者が存在しない、または話者に対応するスタイルが存在しません",
                'message_not_actualized_in_software': comment_syntax + "そのソフトウェアには入力された話者が存在しない、または話者に対応するスタイルが存在しません",
                'message_invalid_software': comment_syntax + "指定されたソフトウェアが存在しません",
                'message_prompt_command': comment_syntax + command_syntax + "show_speakersコマンドを入力して、使用できるソフトウェア、話者、スタイルをご確認ください",}

# 拡張子リスト
extension_dict = {".jpg": "画像ファイル", ".jpng": "画像ファイル", ".jpe": "画像ファイル", ".ico": "画像ファイル",
                  ".png": "画像ファイル", ".bmp": "画像ファイル", ".tif": "画像ファイル", ".tiff": "画像ファイル",
                  ".mp3": "音声ファイル", ".wma": "音声ファイル", ".wav": "音声ファイル", ".mid": "音声ファイル",".midi": "音声ファイル",
                  ".avi": "動画ファイル", ".mp4": "動画ファイル", ".wmv": "動画ファイル",
                  ".exe": "実行ファイル", ".dll": "実行ファイル", 
                  ".pdf": "PDFファイル", ".doc": "ワードファイル", ".csv": "シーエスブイファイル",  ".xls": "エクセルファイル", ".ppt": "パワーポイントファイル", ".pps": "パワーポイントファイル",
                  ".clip": "クリスタファイル", ".psd": "PSDファイル",
                  ".txt": "テキストファイル", ".html": "テキストファイル",".htm": "テキストファイル",
                  ".shtml": "テキストファイル", ".css": "テキストファイル",
                  ".zip": "圧縮ファイル", ".lzh": "圧縮ファイル"}

# 時報のセリフリスト
time_signal_dict = {'00:00': '日付が変わったのだ。まだ寝ないのだ？',
                    '01:00': 'ずんだもんが午前1時ぐらいをお知らせするのだ',
                    '02:00': 'ずんだもんが午前2時ぐらいをお知らせするのだ。眠い・・・',
                    '03:00': 'ずんだもんが午前3時ぐらいをお知らせするのだ',
                    '04:00': 'おはようなのだ!朝4時に何してるのだ？',
                    '05:00': 'ずんだもんが午前5時ぐらいをお知らせするのだ',
                    '06:00': 'ずんだもんが午前6時ぐらいをお知らせするのだ',
                    '07:00': 'ずんだもんが午前7時ぐらいをお知らせするのだ。朝ごはんの時間なのだ',
                    '08:00': 'ずんだもんが午前8時ぐらいをお知らせするのだ',
                    '09:00': 'ずんだもんが午前9時ぐらいをお知らせするのだ',
                    '10:00': 'ずんだもんが午前10時ぐらいをお知らせするのだ',
                    '11:00': 'ずんだもんが午前11時ぐらいをお知らせするのだ',
                    '12:00': 'ずんだもんが正午をお知らせするのだ。作業を中断してそろそろお昼にするのだ',
                    '13:00': 'ずんだもんが午後1時ぐらいをお知らせするのだ',
                    '14:00': 'ずんだもんが午後2時ぐらいをお知らせするのだ',
                    '15:00': 'ずんだもんが午後3時ぐらいをお知らせするのだ',
                    '16:00': 'ずんだもんが午後4時ぐらいをお知らせするのだ',
                    '17:00': 'ずんだもんが午後5時ぐらいをお知らせするのだ',
                    '18:00': 'ずんだもんが午後6時ぐらいをお知らせするのだ',
                    '19:00': 'ずんだもんが午後7時ぐらいをお知らせするのだ',
                    '20:00': 'ずんだもんが午後8時ぐらいをお知らせするのだ。お腹がすいてきたから晩ごはんを食べてくるのだ',
                    '21:00': 'ずんだもんが午後9時ぐらいをお知らせするのだ',
                    '22:00': 'ずんだもんが午後10時ぐらいをお知らせするのだ',
                    '23:00': 'ずんだもんが午後11時ぐらいをお知らせするのだ'}



# コマンドリスト
help_message = "```"+\
                       "■基本コマンド \n" +\
                       command_syntax + "join: BOTをボイスチャンネルに呼ぶ \n" + \
                       command_syntax + "leave: BOTをボイスチャンネルから退出させる \n" +\
                       command_syntax + "stop: 音声ストップ \n" +\
                       command_syntax + "hello: バージョン情報確認 \n\n" +\
                       "■辞書コマンド \n" +\
                       command_syntax + "wlist add A B: 読み仮名の登録。AをBと読ませる。 \n" + \
                       command_syntax + "wlist delete A: 辞書登録の削除。 \n" +\
                       command_syntax + "wlist show: 辞書登録の確認 \n\n" +\
                       "■調声コマンド \n" +\
                       command_syntax + "chg_my_voice: ボイス変更。!chg_my_voice A B [C] \n" + \
                       "Aは話者名、Bはスタイル名です。show_speakersコマンドからご確認ください。\n" +\
                       "Cはソフトウェア名です。オプションなので入れなくてもいいです。\n" +\
                       "複数のソフトウェアに、話者名とスタイル名が同一のキャラクターが実装されている場合にお使いください。\n" +\
                       command_syntax + "chg_voice_setting: スタイル毎の話速などの変更。!chg_speed A B C D E\n" +\
                       "Aはソフトウェア名、Bは話者名、Cはスタイル名です。show_speakersコマンドからご確認ください。\n" +\
                       "Dはspeed pitch intonation volume のいずれか。それぞれ話速・音高・抑揚・音量。に対応。\n" +\
                       "Eはソフトウェア・パラメータの種類によって入力可能な値の範囲が異なります。\n\n" +\
                       "■各種設定 \n" +\
                       command_syntax + "inform_tmp_room: botが入室しているボイスチャンネル名の表示オンオフ。 \n" + \
                       command_syntax + "inform_someone_come: 入退出通知のオンオフ。 \n" + \
                       command_syntax + "time_signal: 時報のオンオフ \n" +\
                       command_syntax + "read_name: 名前読み上げのオンオフ \n" +\
                       command_syntax + "number_of_people: 接続人数のチェックオンオフ\n" +\
                       command_syntax + "auto_leave: BOTの自動退出のオンオフ\n" +\
                       command_syntax + "word_count_limit A: 文字数制限の設定\n" +\
                       command_syntax + "show_setting: 現在の設定の確認\n" +\
                       command_syntax + "show_speakers: 現在使用可能な話者の確認\n" +\
                       "```"
version_info = comment_syntax + 'ずんだもんは現在起動中なのだ！(バージョン' + voibox_version + ')\n' +\
               comment_syntax + command_syntax + 'joinで呼び出してくれたらすぐに参加するのだ！'
               
               
flag_name_dict = {command_inform_someone_come: "入退出の通知", command_inform_tmp_room: "botが入室しているボイスチャットの表示",
                  command_time_signal: "時報", command_read_name: "名前読み上げ",
                  command_number_of_people: "在室人数チェック", command_auto_leave: "自動退出", 
                  command_word_count_limit: "文字数制限"}  # フラグの名前
bool_name_dict = {True: "オン", False: "オフ"}  # フラグオンオフ通知用

