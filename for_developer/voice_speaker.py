from abc import ABCMeta, abstractmethod

class AbstractVoiceSpeaker(metaclass=ABCMeta):
    def __init__(self, name:str, styles:dict) -> None:
        self.name = name
        self.styles = styles

    def hasStyle(self, style_name:str) -> bool:
        if style_name in self.styles.keys() :
            return True
        else:
            return False

    def getStylesStr(self) -> str:
        ret = "[" + self.name + "]:"

        for oneKey in list(self.styles.keys()):
            ret += oneKey + ", "
        
        return ret[:-2]
    
    def getName(self) -> str:
        return self.name
    
    def getStylesDict(self) -> dict:
        return self.styles

    def getStyle(self, style_name):
        return self.styles[style_name]

    def getStyleId(self, style_name:str) -> str:
        return self.styles[style_name].getStyleId()

    def setSpeed(self, style_name:str, speed:float) -> str:
        if style_name not in self.styles.keys():
            return f"{self.name}には{style_name}という名前のスタイルは存在しません。"
        
        self.styles[style_name].setSpeed(speed)
        return f"{self.name} {style_name}のSpeedを{str(speed)}に設定しました"

    def setPitch(self, style_name:str, pitch:float) -> str:
        if style_name not in self.styles.keys():
            return f"{self.name}には{style_name}という名前のスタイルは存在しません。"
        
        self.styles[style_name].setPitch(pitch)
        return f"{self.name} {style_name}のPitchを{str(pitch)}に設定しました"

    def setIntonation(self, style_name:str, intonation:float) -> str:
        if style_name not in self.styles.keys():
            return f"{self.name}には{style_name}という名前のスタイルは存在しません。"
        
        self.styles[style_name].setIntonation(intonation)
        return f"{self.name} {style_name}のIntonationを{str(intonation)}に設定しました"

    def setVolume(self, style_name:str, volume:float) -> str:
        if style_name not in self.styles.keys():
            return f"{self.name}には{style_name}という名前のスタイルは存在しません。"
        
        self.styles[style_name].setVolume(volume)
        return f"{self.name} {style_name}のVolumeを{str(volume)}に設定しました"

class VoiceVoxVoiceSpeaker(AbstractVoiceSpeaker):
    def __init__(self, name:str, styles:dict):
        super().__init__(name, styles)
    
    def hasStyleId(self, style_id:str) -> bool:
        ret = False

        for style in self.styles:
            if style_id == style.getStyleId():
                ret = True
        
        return ret
    
    def getStyleNameWithId(self, style_id:str) -> str:
        for k, v in self.styles.items():
            if style_id == v.getStyleId():
                return k
        
        return None

class CoeiroinkV2VoiceSpeaker(AbstractVoiceSpeaker):
    def __init__(self, name: str, uuid: str, styles: dict) -> None:
        super().__init__(name, styles)
        self.uuid = uuid

class AIVoiceVoiceSpeaker(AbstractVoiceSpeaker):
    def __init__(self, name:str, styles:dict):
        super().__init__(name, styles)

class VoiceStyle:
    def __init__(self, styleName:str, styleId:str, speed:float, pitch:float, intonation:float, volume:float):
        self.styleName = styleName
        self.styleId = styleId
        self.speed = speed
        self.pitch = pitch
        self.intonation = intonation
        self.volume = volume
    
    def getStyleName(self) -> str:
        return self.styleName
    
    def getStyleId(self) -> str:
        return self.styleId
    
    def getSpeed(self) -> float:
        return self.speed
    
    def setSpeed(self, speed:float):
        self.speed = speed
    
    def getPitch(self) -> float:
        return self.pitch
    
    def setPitch(self, pitch:float):
        self.pitch = pitch
    
    def getIntonation(self) -> float:
        return self.intonation
    
    def setIntonation(self, intonation:float):
        self.intonation = intonation
    
    def getVolume(self) -> float:
        return self.volume
    
    def setVolume(self, volume:float):
        self.volume = volume