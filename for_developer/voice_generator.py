import os
import clr
import json
from abc import ABCMeta, abstractmethod
from for_developer.discordbot_setting import *
from for_developer.voice_speaker import AbstractVoiceSpeaker, VoiceVoxVoiceSpeaker, AIVoiceVoiceSpeaker, VoiceStyle

class AbstractVoiceGenerator(metaclass=ABCMeta):
    def __init__(self,
                 name:str,
                 minSpeed:float,
                 maxSpeed:float,
                 defaultSpeed:float,
                 minPitch:float,
                 maxPitch:float,
                 defaultPitch:float,
                 minIntonation:float,
                 maxIntonation:float,
                 defaultIntonation:float,
                 minVolume:float,
                 maxVolume:float,
                 defaultVolume:float):
        self.name = name
        self.minSpeed = minSpeed
        self.maxSpeed = maxSpeed
        self.defaultSpeed = defaultSpeed
        self.minPitch = minPitch
        self.maxPitch = maxPitch
        self.defaultPitch = defaultPitch
        self.minIntonation = minIntonation
        self.maxIntonation = maxIntonation
        self.defaultIntonation = defaultIntonation
        self.minVolume = minVolume
        self.maxVolume = maxVolume
        self.defaultVolume = defaultVolume
        self.speakers = {}

    @abstractmethod
    def generate(self, character_name:str, style_name:str, query:str):
        raise NotImplementedError()

    def getSpeakersStr(self) -> str:
        ret = "【" + self.name + "】\n"
        
        for speaker_name in self.speakers:
            ret += self.speakers[speaker_name].getStylesStr() + "\n"
        
        return ret
    
    def hasSpeaker(self, name) -> bool:
        if name in self.speakers.keys():
            return True
        else:
            return False
    
    def getSpeaker(self, name) -> AbstractVoiceSpeaker:
        return self.speakers[name]
    
    def hasStyle(self, speaker_name, style_name) -> bool:
        if self.hasSpeaker(speaker_name):
            speaker = self.speakers[speaker_name]
            if speaker.hasStyle(style_name):
                return True
        
        return False
    
    def getName(self) -> str:
        return self.name
    
    def getSpeakersDict(self) -> dict:
        return self.speakers

    def getDefaultSpeed(self) -> float:
        return self.defaultSpeed
    
    def getDefaultPitch(self) -> float:
        return self.defaultPitch
    
    def getDefaultIntonation(self) -> float:
        return self.defaultIntonation
    
    def getDefaultVolume(self) -> float:
        return self.defaultVolume

    def setSpeed(self, character_name:str, styleName:str, speed:float) -> str:
        if not self.hasSpeaker(character_name):
            return f"{self.name}には{character_name}というキャラクターは存在しません。"
        if speed < self.minSpeed or self.maxSpeed < speed:
            return f"{self.name}のSpeedは{self.minSpeed}と{self.maxSpeed}の間で入力してください。"
        
        return self.speakers[character_name].setSpeed(styleName, speed)
    
    def setPitch(self, character_name:str, styleName:str, pitch:float) -> str:
        if not self.hasSpeaker(character_name):
            return f"{self.name}には{character_name}というキャラクターは存在しません。"
        if pitch < self.minPitch or self.maxPitch < pitch:
            return f"{self.name}のPitchは{self.minPitch}と{self.maxPitch}の間で入力してください。"
        
        return self.speakers[character_name].setPitch(styleName, pitch)
    
    def setIntonation(self, character_name:str, styleName:str, intonation:float) -> str:
        if not self.hasSpeaker(character_name):
            return f"{self.name}には{character_name}というキャラクターは存在しません。"
        if intonation < self.minIntonation or self.maxIntonation < intonation:
            return f"{self.name}のIntonationは{self.minIntonation}と{self.maxIntonation}の間で入力してください。"
        
        return self.speakers[character_name].setIntonation(styleName, intonation)
    
    def setVolume(self, character_name:str, styleName:str, volume:float) -> str:
        if not self.hasSpeaker(character_name):
            return f"{self.name}には{character_name}というキャラクターは存在しません。"
        if volume < self.minVolume or self.maxVolume < volume:
            return f"{self.name}のVolumeは{self.minVolume}と{self.maxVolume}の間で入力してください。"
        
        return self.speakers[character_name].setVolume(styleName, volume)
    
class VoiceVoxVoiceGenerator(AbstractVoiceGenerator):
    def __init__(self, name:str, port:str):
        super().__init__(name, 0.5, 2.0, 1.2, -0.15, 0.15, 0.0, 0.0, 2.0, 1.0, 0.0, 2.0, 1.0)
        # インスタンス変数の指定
        self.port = port

        try:
            # VOICEVOX（あるいは互換ソフト）から、話者の一覧をJsonで取得する
            command = bat_speakers + ' ' + port
            os.system(command)

            #Jsonを解析して話者の情報を動的に取得する
            print("Jsonの解析開始")
            with open('tmp/speakers.json', 'r', encoding="utf-8_sig") as json_open:
                json_load = json.load(json_open)
                for speaker in json_load:
                    speaker_name = speaker['name']
                    speaker_styles = speaker['styles']
                    style_dict = {}

                    for style in speaker_styles:
                        styleObj = VoiceStyle(style['name'], str(style['id']), self.defaultSpeed, self.defaultPitch, self.defaultIntonation, self.defaultVolume)
                        style_dict[style['name']] = styleObj
                    self.speakers[speaker_name] = VoiceVoxVoiceSpeaker(speaker_name, style_dict)

            print("Jsonの解析完了")
            print(self.getSpeakersStr())
        except Exception as e:
            raise e
            
    def generate(self, character_name:str, style_name:str, query:str):
        # チャットの内容をutf-8でエンコードする
        text = query.encode('utf-8')

        # HTTP POSTで投げられるように形式を変える
        arg = ''
        for item in text:
            arg += '%'
            arg += hex(item)[2:].upper()

        character = self.speakers[character_name]
        # コマンドの設定
        style = character.getStyle(style_name)
        style_id_str = style.getStyleId()
        command1 = bat_json + ' ' + self.port + ' ' + arg + ' ' + style_id_str
        command2 = bat_voice + ' ' + self.port + ' ' + style_id_str

        # リクエスト用Jsonの生成
        os.system(command1)

        # jsonファイルのかきかえ
        with open(json_file, encoding="utf-8") as f:
            data_lines = f.read()
            data_lines = data_lines.replace('"speedScale":1.0'     , '"speedScale":'     +str(style.getSpeed()))
            data_lines = data_lines.replace('"pitchScale":0.0'     , '"pitchScale":'     +str(style.getPitch()))
            data_lines = data_lines.replace('"intonationScale":1.0', '"intonationScale":'+str(style.getIntonation()))
            data_lines = data_lines.replace('"volumeScale":1.0'    , '"volumeScale":'    +str(style.getVolume()))
        # 同じファイル名で保存
        with open(json_file, mode="w", encoding="utf-8") as f:
            f.write(data_lines)

        # wavファイルの生成
        os.system(command2)
    
    def getSpeakerWithStyleId(self, id:str) -> VoiceVoxVoiceSpeaker:
        for speaker in self.speakers.values():
            if speaker.hasStyleId(id):
                return speaker
        return None
    
class AIVoiceVoiceGenerator(AbstractVoiceGenerator):
    def __init__(self, aivoiceDir:str):
        super().__init__('A.I.VOICE', 0.5, 4.0, 1.2, 0.5, 2.0, 1.0, 0.0, 2.0, 1.0, 0.0, 2.0, 1.0)
        if not os.path.isfile(aivoiceDir + 'AI.Talk.Editor.Api.dll'):
            print('所定のディレクトリにA.I.VOICEが存在しません。')
            raise Exception('所定のディレクトリにA.I.VOICEが存在しません。')

        clr.AddReference(aivoiceDir + 'AI.Talk.Editor.Api.dll')
        from AI.Talk.Editor.Api import TtsControl, HostStatus

        # エディタの初期化
        self.tts_control = TtsControl()
        host_name = self.tts_control.GetAvailableHostNames()[0]
        self.tts_control.Initialize(host_name)

        # エディタの起動
        if self.tts_control.Status == HostStatus.NotRunning:
            self.tts_control.StartHost()
        
        #エディタへ接続
        self.tts_control.Connect()
        host_version = self.tts_control.Version
        print(f"{host_name} (v{host_version}へ接続しました。)")

        # 話者の取得
        for speakerName in self.tts_control.VoiceNames:
            styleDict = {}
            presetRaw = self.tts_control.GetVoicePreset(speakerName)
            
            json_load = json.loads(presetRaw)
            styles = json_load['Styles']

            styleObj = VoiceStyle('普通', '', self.defaultSpeed, self.defaultPitch, self.defaultIntonation, self.defaultVolume)
            styleDict['普通'] = styleObj

            for oneStyle in styles:
                tmpStyleName = ""
                if oneStyle['Name'] == 'J':
                    if speakerName == "タンゲ コトエ":
                        tmpStyleName = "ハイテンション"
                    else:
                        tmpStyleName = "喜び"
                elif oneStyle['Name'] == 'A':
                    tmpStyleName = "怒り"
                elif oneStyle['Name'] == 'S':
                    if speakerName == "タンゲ コトエ":
                        tmpStyleName = "ローテンション"
                    else:
                        tmpStyleName = "悲しみ"
                styleObj = VoiceStyle(tmpStyleName, oneStyle['Name'], self.defaultSpeed, self.defaultPitch, self.defaultIntonation, self.defaultVolume)
                styleDict[tmpStyleName] = styleObj
                
            self.speakers[speakerName] = AIVoiceVoiceSpeaker(speakerName, styleDict)
        
        print(self.getSpeakersStr())
    
    def generate(self, character_name:str, style_name:str, query:str):
        character = self.speakers[character_name]
        style = character.getStyle(style_name)
        style_str = style.getStyleId()
        presetRaw = self.tts_control.GetVoicePreset(character_name)
        json_load = json.loads(presetRaw)
        json_load['Speed'] = style.getSpeed()
        json_load['Pitch'] = style.getPitch()
        json_load['PitchRange'] = style.getIntonation()
        json_load['Volume'] = style.getVolume()

        for oneStyle in json_load['Styles']:
            if oneStyle['Name'] == style_str:
                oneStyle['Value'] = 1.0
            else:
                oneStyle['Value'] = 0.0
        
        presetEdited = json.dumps(json_load, ensure_ascii=False)
        self.tts_control.Text = query
        self.tts_control.CurrentVoicePresetName = character_name
        self.tts_control.SetVoicePreset(presetEdited)
        self.tts_control.SaveAudioToFile(".\\tmp\\tmp_voice.wav")