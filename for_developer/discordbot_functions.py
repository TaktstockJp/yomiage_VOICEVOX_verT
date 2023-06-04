
# 設定ファイルの読み込み
from __future__ import generators
import discord
import os
import csv
import re
import asyncio
import queue
import sys
import traceback
import configparser
from for_developer.discordbot_setting import *
from for_developer.voice_generator import VoiceVoxVoiceGenerator, AIVoiceVoiceGenerator

# 関数の定義
# 以下、引数のmessage_tmpはdiscord.message型を入れる。
# 非同期関数 (async関数) はawaitで呼び出すこと。

# 単語帳 (dict) を単語の長さ順にソートする
def sort_dict(dict):
    keys = sorted(dict.keys(), key=len, reverse=True)
    for k in keys:
        dict[k] = dict.pop(k)


# 単語帳 (dict) を単語の長さ順にソートして書き換える
def revise_dict(dict, file):
    # キーの文字長順でソートする
    sort_dict(dict)
    # word_list.csvを更新する
    with open(file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, lineterminator='\n')
        for k, v in dict.items():
            writer.writerow([k, v])


# 他の音源が再生されている間スリープする
async def already_playing_plz_sleep(message_tmp):
    while True:
        if message_tmp.guild.voice_client is None:
            break
        else:
            if message_tmp.guild.voice_client.is_playing():
                await asyncio.sleep(0.05)
            else:
                break

# データ書き込み
def output_data(filename, listname):
    with open(filename, 'w', encoding='utf-8') as f:  
        writer = csv.writer(f)
        for k, v in listname.items():
            writer.writerow([k, v])
    return

# チャンネル情報クラス
class room_information():
    def __init__(self, bot = None, TEXT_ROOM_ID=0, TEXT_ROOM_NAME='', VOICE_ROOM_ID=0, VOICE_ROOM_NAME='', GUILD_ID=0):
        self.bot = None
        self.game = discord.Game('待機中')
        self.text_room_id = TEXT_ROOM_ID
        self.text_room_name = TEXT_ROOM_NAME
        self.voice_room_id = VOICE_ROOM_ID
        self.voice_room_name = VOICE_ROOM_NAME
        self.guild_id = GUILD_ID
        # 各種ファイル
        self.vlist_file = ""            # ユーザ毎のボイスリスト
        self.flist_file = ""            # フラグリスト
        self.wlist_file = ""            # 単語帳リスト
        self.style_setting_file = ""    # スタイル別設定値ファイルのパス
        # 各種リスト
        self.generators = {}  # 使用するソフトウェアとその情報
        self.voice_dict = {}  # 使用ボイスの管理
        self.word_dict = {}  # 単語帳の管理
        self.flag_valid_dict = {command_inform_someone_come: inform_someone_come, command_inform_tmp_room: inform_tmp_room,
                                command_time_signal: time_signal,
                                command_read_name: read_name, command_number_of_people: number_of_people,
                                command_auto_leave: auto_leave, 
                                command_word_count_limit: word_count_limit}
        self.image_list = {}  # 画像と呼び出しコマンドの管理
        # キュー処理用
        self.speaking_queue = queue.Queue()
        self.now_loading = False
        # デフォルト値
        self.default_generator = ""
        self.default_speaker = ""
        self.default_style = ""

    def text_room_id_exist(self):
        if self.text_room_id == 0:
            return False
        else:
            return True

    # 人数カウント+自動退出
    async def count_number_of_people(self, text_channel, voice_channel):
        user_count = sum(1 for member in voice_channel.members if not member.bot)
        await text_channel.send('>現在' + str(user_count) + '人接続しているのだ')
        if(user_count == 0 and self.flag_valid_dict[command_auto_leave]):
            await text_channel.send('>誰もいなくなったみたいだから僕もそろそろ抜けるのだ')
            await voice_channel.guild.voice_client.disconnect()
            # 切断に成功したことの報告
            print(self.voice_room_name + "から切断しました")
            # チャンネル情報を初期化
            self.text_room_name = ''
            self.text_room_id = 0
            self.voice_room_name = ''
            self.voice_room_id = 0
            self.guild_id = 0

    # sentenceで得たメッセージをVOICEVOXで音声ファイルに変換しそれを再生する
    def play_voice(self, sentence, message_tmp):
        # batファイルを呼び起こしてwavファイルを作成する
        try:
            if message_tmp.author.id in self.voice_dict.keys():
                voice_data = self.voice_dict.get(message_tmp.author.id)
                self.generators[voice_data[0]].generate(voice_data[1], voice_data[2], sentence)
            else:
                self.generators[self.default_generator].generate(self.default_speaker, self.default_style, sentence)
        except KeyError:
            # ユーザーが指定しているスタイルが辞書に存在しない場合
            self.generators[self.default_generator].generate(self.default_speaker, self.default_style, sentence)
            traceback.print_exc()
        except Exception as e:
            print(type(e))
            traceback.print_exc()
        
        # wavの再生
        # ffmpegがインストールされていない場合エラーを出す。
        try:
            tmp = discord.FFmpegOpusAudio(voice_file)
        except discord.errors.ClientException:
            print(" ")
            print(" ")
            print("[エラーメッセージ(by かみみや)]")
            print("ffmpegがインストールされていないです（またはPathが通っていないです）")
            print("そのため、音声再生ができません。")
            print("詳しくはreadmeの導入が必要なソフト1.をご覧ください")
            print(" ")
            print(" ")
        
        try:
            tmp = discord.FFmpegOpusAudio(voice_file)
            message_tmp.guild.voice_client.play(tmp)
        except:
            print("再生時エラー")
        return

    # 他の読み込み処理が行われている間スリープする
    async def already_loading_plz_sleep(self):
        while True:
            if self.now_loading:
                await asyncio.sleep(0.05)  
            else:       
                break 

    # 投げられたメッセージの辞書置換から再生までまとめた関数
    async def plz_speak(self, sentence, message_tmp):
        # 読み上げ制限
        if len(sentence) > int(self.flag_valid_dict[command_word_count_limit]):
            sentence = sentence[0:int(self.flag_valid_dict[command_word_count_limit]) - 1] + "以下略"
            
        # 音声の再生
        for item in re.split('\n|;', sentence):
            # 空白の場合無視
            if not item:
                continue

            # word_dictに含まれる場合は置換する
            for key in self.word_dict.keys():
                item = item.replace(key, self.word_dict[key])
            # 他の音源が再生されている間スリープする
            await already_playing_plz_sleep(message_tmp)
            
            if ('http' in item) or ('https' in item):
                self.play_voice("URLが貼られたのだ", message_tmp)  # 音声の再生
            else:
                self.play_voice(item, message_tmp)  # 音声の再生

    # キューに投げ込まれた文章を逐次再生する
    async def queuing(self, message_tmp):
        while not self.speaking_queue.empty():
            item = self.speaking_queue.get()
            await self.plz_speak(item, message_tmp)
            
    # キューを初期化する
    def queue_clear(self):
        while not self.speaking_queue.empty():
            self.speaking_queue.get()
            self.now_loading = False

    async def reload(self):        
        # setting.iniの読み込み
        ini = configparser.ConfigParser()
        ini.optionxform = str
        ini.read('./setting.ini', 'UTF-8')
        self.default_generator = ini.get('Default Value Setting', 'DefaultGenerator')
        self.default_speaker = ini.get('Default Value Setting', 'DefaultSpeaker')
        self.default_style = ini.get('Default Value Setting', 'DefaultStyle')
        self.vlist_file = ini.get('Data Location', 'VoiceList')
        self.flist_file = ini.get('Data Location', 'FlagList')
        self.wlist_file = ini.get('Data Location', 'WordList')
        self.style_setting_file = ini.get('Data Location', 'StyleSetting')

        # ソフトウェア情報の読み込み
        self.generators = {}
        for k in ini['Using Setting']:
            print(k)
            print(ini.get('Using Setting', k))
            self.createVoiceVoxGenerator(k, ini.get('Using Setting', k))
        
        # A.I.VOICEのセッティング
        if ini.get('A.I.VOICE Setting', 'UseAIVoice').lower() == 'true':
            self.createAIVoiceGenerator(ini.get('A.I.VOICE Setting', 'AIVoiceDir'))

        if not any(self.generators):
            print("音声合成ソフトウェアの初期化に失敗しました。プログラムを終了します。")
            sys.exit(1)

        # スタイルごとの情報の読み取り
        tmp_style_setting_dict = {}
        migrate_style_setting_dict = {}
        with open(self.style_setting_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0] == 'software' or row[0] == 'name':
                    continue
                    
                if len(row) == 7:
                    parameter_dict = {}
                    parameter_dict['speed'] = float(row[3])
                    parameter_dict['pitch'] = float(row[4])
                    parameter_dict['intonation'] = float(row[5])
                    parameter_dict['volume'] = float(row[6])
                    tmp_style_setting_dict[(row[0], row[1], row[2])] = parameter_dict
                elif len(row) == 6:
                    parameter_dict = {}
                    parameter_dict['speed'] = float(row[2])
                    parameter_dict['pitch'] = float(row[3])
                    parameter_dict['intonation'] = float(row[4])
                    parameter_dict['volume'] = float(row[5])
                    migrate_style_setting_dict[(row[0], row[1])] = parameter_dict
        
        # 各スタイルのパラメータの適用
        for generator in self.generators.values():
            for speaker in generator.getSpeakersDict().values():
                for style_name in speaker.getStylesDict().keys():
                    if (generator.getName(), speaker.getName(), style_name) in tmp_style_setting_dict.keys():
                        generator.setSpeed(speaker.getName(), style_name, tmp_style_setting_dict[(generator.getName(), speaker.getName(), style_name)]['speed'])
                        generator.setPitch(speaker.getName(), style_name, tmp_style_setting_dict[(generator.getName(), speaker.getName(), style_name)]['pitch'])
                        generator.setIntonation(speaker.getName(), style_name, tmp_style_setting_dict[(generator.getName(), speaker.getName(), style_name)]['intonation'])
                        generator.setVolume(speaker.getName(), style_name, tmp_style_setting_dict[(generator.getName(), speaker.getName(), style_name)]['volume'])
                    elif (speaker.getName(), style_name) in migrate_style_setting_dict.keys():
                        generator.setSpeed(speaker.getName(), style_name, migrate_style_setting_dict[(speaker.getName(), style_name)]['speed'])
                        generator.setPitch(speaker.getName(), style_name, migrate_style_setting_dict[(speaker.getName(), style_name)]['pitch'])
                        generator.setIntonation(speaker.getName(), style_name, migrate_style_setting_dict[(speaker.getName(), style_name)]['intonation'])
                        generator.setVolume(speaker.getName(), style_name, migrate_style_setting_dict[(speaker.getName(), style_name)]['volume'])

        self.writeStyleSettingDict()

        # voice_dict情報を読み込む
        with open(self.vlist_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue

                if len(row) == 4:
                    self.voice_dict[int(row[0])] = [row[1], row[2], row[3]]
                else:
                    continue
        self.writeVoiceDict()

        # word_dict情報を読み込む
        with open(self.wlist_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                self.word_dict[row[0]] = row[1]
        # flag_list情報を読み込む
        with open(self.flist_file,'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue  # rowが空の場合はスキップ
                if row[0] in self.flag_valid_dict.keys(): # 設定項目がflag_valid_dictに含まれる場合
                    if row[1] == 'True':
                        self.flag_valid_dict[row[0]] = True
                    elif row[1] == 'False':
                        self.flag_valid_dict[row[0]] = False
                    else:
                        self.flag_valid_dict[row[0]] = float(row[1])
            f.close()
            
        print('更新完了')
    
    # VOICEVOXとその派生ソフトウェアのオブジェクトを作成して返す
    # エラー時にgeneratorsにオブジェクトを格納させないためのコンストラクタのラッパ
    def createVoiceVoxGenerator(self, name:str, port:str):
        try:
            tmpVVGenerator = VoiceVoxVoiceGenerator(name, port)
            self.generators[name] = tmpVVGenerator
        except Exception as e:
            print(name + "の初期化に失敗しました。")
            print(name + "が起動されていない可能性があります。")
            print(type(e))
            traceback.print_exc()
    
    # A.I.VOICEのオブジェクトを作成してgeneratorsに格納する
    # エラー時にgeneratorsにオブジェクトを格納させないためのコンストラクタのラッパ
    def createAIVoiceGenerator(self, aivoiceDir:str):
        try:
            tmpAVGenerator = AIVoiceVoiceGenerator(aivoiceDir)
            self.generators['A.I.VOICE'] = tmpAVGenerator
        except Exception as e:
            print('A.I.VOICEの初期化に失敗しました。')
            print(type(e))
            traceback.print_exc()

    # コマンドを実行する
    async def execute_commands(self, message_tmp):
        # ボイスチャンネルに接続
        if message_tmp.content == command_join:
            # message_tmpの送信者がいるボイスチャンネルに接続
            await self.execute_join(message_tmp.author.voice.channel, message_tmp.channel, message_tmp.guild.id)
            await message_tmp.channel.send(comment_dict['message_join'])

        # ボイスチャンネルから切断
        elif message_tmp.content == command_leave:
            await self.execute_leave(message_tmp.guild.voice_client)
            await message_tmp.channel.send(comment_dict['message_leave'])
            
        # helpコマンド
        elif message_tmp.content == command_help:
            await message_tmp.channel.send(self.execute_help)
        
        # helloコマンド
        elif message_tmp.content == command_hello:
            await message_tmp.channel.send(self.execute_hello)
        
        # ボイスの変更
        elif message_tmp.content.startswith(command_chg_my_voice):
            voice_tmp = message_tmp.content.split()
            if len(voice_tmp) == 3:
                await message_tmp.channel.send(await self.execute_chg_my_voice(message_tmp.author.id, voice_tmp[1], voice_tmp[2]))
            elif len(voice_tmp) == 4:
                await message_tmp.channel.send(await self.execute_chg_my_voice_with_software(message_tmp.author.id, voice_tmp[1], voice_tmp[2], voice_tmp[3]))
            else:
                await message_tmp.channel.send(comment_dict['message_err'])

        # ワードリスト関連
        elif message_tmp.content.startswith(command_wlist):
            wlist_tmp = message_tmp.content.split()
            if (len(wlist_tmp) == 4) and (wlist_tmp[1] == "add"):                # エラーチェック
                await message_tmp.channel.send(await self.execute_wlist_add(wlist_tmp[2], wlist_tmp[3]))
            elif (len(wlist_tmp) == 3) and (wlist_tmp[1] == "delete"):           # エラーチェック
                await message_tmp.channel.send(await self.execute_wlist_delete(wlist_tmp[2]))
            elif (len(wlist_tmp) == 2) and (wlist_tmp[1] == "show"):             # エラーチェック
                await message_tmp.channel.send(file=await self.execute_wlist_show())
            else:  # 例外処理
                await message_tmp.channel.send(comment_dict['message_err'])
        
        # スタイル別の読み上げ時の値の設定
        elif message_tmp.content.startswith(command_chg_voice_setting):
            command_tmp = message_tmp.content.split()
            # 要素数エラー
            if len(command_tmp) != 5:
                await message_tmp.channel.send(comment_Synthax + command_chg_voice_setting + " 話者名 スタイル名 変更するパラメータ 変更後の値 と入力してください")
                await message_tmp.channel.send(comment_Synthax + "変更するパラメータには speed, pitch, intonation, volume が指定できます")
                return
            else:
                await message_tmp.channel.send(await self.execute_chg_voice_setting(command_tmp[1], command_tmp[2], command_tmp[3], command_tmp[4]))
                return

        # 文字数制限の設定
        elif message_tmp.content.startswith(command_word_count_limit):
            command_tmp = message_tmp.content.split()
            # 要素数エラー
            if len(command_tmp) != 2:
                await message_tmp.channel.send(comment_dict['message_err'])
                return            
            # 2つめの要素がintでなければエラー
            try:
                self.flag_valid_dict[command_word_count_limit] = int(command_tmp[1])
                await message_tmp.channel.send(comment_Synthax + "文字数制限を"+command_tmp[1]+'に設定したのだ')            #設定の更新
                output_data(self.flist_file, self.flag_valid_dict)
            except ValueError:
                await message_tmp.channel.send(comment_dict['message_err'])
            return
            
        # 各種設定の変更
        elif message_tmp.content in self.flag_valid_dict.keys():
            self.flag_valid_dict[message_tmp.content] = not self.flag_valid_dict[message_tmp.content]
            await message_tmp.channel.send(comment_Synthax + flag_name_dict[message_tmp.content] + "を" + bool_name_dict[self.flag_valid_dict[message_tmp.content]] + "にしたのだ")
            #設定の更新
            output_data(self.flist_file, self.flag_valid_dict)
            # inform_tmp_roomの設定を反映させる
            if self.flag_valid_dict[command_inform_tmp_room]:
                await self.bot.change_presence(status=None, activity=self.game)
            else:
                await self.bot.change_presence(status=None, activity=None)
            
        # 現在の設定の確認
        elif message_tmp.content == command_show_setting:
            sentence = '```'
            for flag in self.flag_valid_dict.keys():
                if type(self.flag_valid_dict[flag]) == bool:
                    sentence = sentence + flag_name_dict[flag] + ';' + bool_name_dict[self.flag_valid_dict[flag]] + "\n"
                else:
                    sentence = sentence + flag_name_dict[flag] + ';' + str(self.flag_valid_dict[flag]) + "\n"
            sentence = sentence + '```'
            await message_tmp.channel.send(sentence)

        # 話者リストの表示
        elif message_tmp.content == command_show_speakers:
            await message_tmp.channel.send(await self.execute_show_speakers())

        # 情報の再読み込み
        elif message_tmp.content == command_reload:
            await self.reload()
            
        # 例外処理
        else:
            await message_tmp.channel.send(comment_dict['message_err'])
    
    def writeVoiceDict(self):
        with open(self.vlist_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator='\n')
            for k, v in self.voice_dict.items():
                tmpList = v.copy()
                tmpList.insert(0, k)
                writer.writerow(tmpList)
    
    def writeStyleSettingDict(self):
        tmp_arr = []
        with open(self.style_setting_file, 'r', encoding='utf-8') as f:
            for l in f.read().splitlines():
                if not l or 'name' not in l:
                    tmp_arr.append(l)

        with open(self.style_setting_file, 'w', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(['software', 'name', 'style', 'speed', 'pitch', 'intonation', 'volume'])
            for generator in self.generators.values():
                for speaker in generator.getSpeakersDict().values():
                    for style in speaker.getStylesDict().values():
                        writer.writerow(
                            [generator.getName(), 
                             speaker.getName(), 
                             style.getStyleName(), 
                             str(style.getSpeed()), 
                             str(style.getPitch()), 
                             str(style.getIntonation()), 
                             str(style.getVolume())]
                        )
                    tmp_arr = [l for l in tmp_arr if speaker.getName() not in l and style.getStyleName() not in l]
            
            for l in tmp_arr:
                writer.writerow(l.split(","))
    
    async def execute_join(self, voiceChannel:discord.VoiceChannel, textChannel:discord.TextChannel, guild_id:int):
        # コマンドの実行者がいるボイスチャンネルに接続
        await voiceChannel.connect()
        # 接続先のチャンネル情報の記録
        self.text_room_name  = str(textChannel)
        self.text_room_id    = int(textChannel.id)
        self.voice_room_name = str(voiceChannel)
        self.voice_room_id   = int(voiceChannel.id)
        self.guild_id        = guild_id
        # statusの更新
        self.game = discord.Game(self.voice_room_name)
        await self.bot.change_presence(status=None, activity=self.game)
        # 接続に成功したことの報告
        print(self.voice_room_name + "に接続しました")
    
    async def execute_leave(self, protocol:discord.VoiceProtocol):
        # ボイスチャンネルから切断
        await protocol.disconnect()
        # 切断に成功したことの報告
        print(self.voice_room_name + "から切断しました")
        # チャンネル情報の初期化
        self.text_room_name  = ''
        self.text_room_id    = 0
        self.voice_room_name = ''
        self.voice_room_id   = 0
        self.guild_id        = 0
        # statusの初期化
        self.game = discord.Game("待機中")
        await self.bot.change_presence(status=None, activity=self.game)
    
    async def execute_help(self) -> str:
        return help_message
    
    async def execute_hello(self) -> str:
        return version_info
    
    async def execute_chg_my_voice(self, author_id:int, speaker_name:str, style_name:str) -> str:
        # generatorsを前から順番に探す
        for generator in self.generators.values():
            if generator.hasStyle(speaker_name, style_name):
                self.voice_dict[author_id] = [generator.getName(), speaker_name, style_name]
                self.writeVoiceDict()
                return comment_dict['message_chg_voice']
        return comment_dict['message_not_actualized'] + "\n" + comment_dict['message_prompt_command']
    
    async def execute_chg_my_voice_with_software(self, author_id:int, speaker_name:str, style_name:str, generator_name:str = '') -> str:
        # ソフト名を指定して対応するボイスを探す
        if generator_name in self.generators.keys():
            generator = self.generators[generator_name]
            if generator.hasStyle(speaker_name, style_name):
                self.voice_dict[author_id] = [generator.getName(), speaker_name, style_name]
                self.writeVoiceDict()
                return comment_dict['message_chg_voice']
            else:
                return comment_dict['message_not_actualized_in_software'] + "\n" + comment_dict['message_prompt_command']
        else:
            return comment_dict['message_invalid_software'] + "\n" + comment_dict['message_prompt_command']
    
    async def execute_wlist_add(self, word:str, how_to_read:str) -> str:
        if word and how_to_read:
            self.word_dict[word] = how_to_read
            revise_dict(self.word_dict, self.wlist_file)
            return comment_Synthax + word + "を" + how_to_read + "として追加しました"
        else:
            return comment_Synthax + "単語か読み仮名のどちらかが指定されていません"
    
    async def execute_wlist_delete(self, word:str) -> str:
        if word and word in self.word_dict.keys():
            self.word_dict.pop(word)
            revise_dict(self.word_dict, self.wlist_file)
            return comment_Synthax + word + "を削除しました"
        elif word:
            return comment_Synthax + word + "は読み仮名が指定されていません"
        else:
            return comment_Synthax + "単語が指定されていません"
    
    async def execute_wlist_show(self) -> discord.File:
        return discord.File(self.wlist_file)
    
    async def execute_chg_voice_setting(self, software_name:str, speaker_name:str, style_name:str, parameter_name:str, value:str) -> str:
        # 引数のどれかが空かNoneの場合エラー
        if not software_name or not speaker_name or not style_name or not parameter_name or not value:
            return comment_Synthax + command_chg_voice_setting + " ソフトウェア名 話者名 スタイル名 変更するパラメータ 変更後の値 と入力してください\n" +\
                   comment_Synthax + "変更するパラメータには speed, pitch, intonation, volume が指定できます"
        
        # ソフトウェア名チェック
        if not software_name in self.generators.keys():
            return comment_Synthax + "指定されたソフトウェア名が存在しません。"

        # 各種状態の変更
        try:
            ret = ""
            generator = self.generators[software_name]
            value_tmp = '{:3}'.format(value)
            if parameter_name.lower() == 'speed':
                ret = comment_Synthax + generator.setSpeed(speaker_name, style_name, float(value_tmp))
            elif parameter_name.lower() == 'pitch':
                ret = comment_Synthax + generator.setPitch(speaker_name, style_name, float(value_tmp))
            elif parameter_name.lower() == 'intonation':
                ret = comment_Synthax + generator.setIntonation(speaker_name, style_name, float(value_tmp))
            elif parameter_name.lower() == 'volume':
                ret = comment_Synthax + generator.setVolume(speaker_name, style_name, float(value_tmp))
            else:
                ret = comment_Synthax + "変更するパラメータには speed, pitch, intonation, volume を指定してください"
            self.writeStyleSettingDict()
            return ret
        except ValueError:
            return comment_dict['message_err']
        except Exception:
            traceback.print_exc()
            return comment_dict['message_err']
    
    async def execute_show_speakers(self) -> str:
        sentence = '```'
        for generator in self.generators.values():
            sentence += generator.getSpeakersStr()
        sentence += '```'
        return sentence