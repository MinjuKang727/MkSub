# C:/Users/minju/Programming/Small_Project/MkSub
# 필요 라이브러리: ffmpeg, yt-dlp, moviepy, pygame
import json
import ast
import xml.etree.ElementTree as ET
import webvtt
import yt_dlp
from yt_dlp import YoutubeDL
from moviepy import VideoFileClip, AudioFileClip, TextClip, ColorClip, CompositeVideoClip
from tkinter import filedialog, messagebox, ttk
from tkinter import *
from pygame import mixer
from enum import Enum, auto
import logging
from pathlib import Path, WindowsPath
from glob import glob
import re

################
# ENUM 클래스들 #
################
class LoadType(Enum):  # 파일 조회 유형 Enum
    YOUTUBE = "유튜브 링크로 가져오기"
    AUTO = "저장 경로에서 찾기(자동)"
    MANUAL = "직접 경로 지정(수동)"

    def equal(self, load_type):
        if isinstance(load_type, LoadType):
            return self == load_type
        elif isinstance(load_type, str):
            return self.value == load_type
        else:
            return False
    
    def get(self, load_type):
        if self.value == load_type:
            return self
    
    @classmethod
    def get_tuple(cls):
        return (item.value for item in cls)

class PathKey(Enum):  # 경로 딕셔너리 키 Enum
    ROOT = ("ROOT", False)
    SAVE = ("SAVE", False)  # 값: (이름 , 같은 위젯 존재 여부(리스트로 저장 여부))
    AUDIO = ("AUDIO", True)
    SUB = ("SUB", True)
    YOUTUBE_URL = ("YOUTUBE_URL", False)
    SUB_DICT = ("SUB_DICT", False)
    FONT = ("FONT", False)
    FOLDER_ICON = ("FOLDER_ICON", False)
    AUDIO_ICON = ("AUDIO_ICON", False)
    SUB_ICON = ("SUB_ICON", False)

    def equal(self, key):  # key와 enum 일치 여부
        if isinstance(key, PathKey):
            return self == key
        elif isinstance(key, str):
            return self.value == key
        
        return False
    
    @classmethod
    def get(cls, key):  # enum 키 반환
        if isinstance(key, PathKey):
            return key
        
        for item in cls:
            if isinstance(key, str):
                if key.upper() == item.name:
                    return item
                
    def save_as_list(self):  # 리스트로 저장 여부
        return self.value[1]

class SubDictKey(Enum):  # 자막 딕셔너리 키 Enum
    TIME_UNIT = auto()
    JSON3 = auto()
    SRT = auto()
    SRV1 = auto()
    SRV2 = auto()
    SRV3 = auto()
    TTML = auto()
    VTT = auto()

    def equal(self, ext):  # key와 enum 일치 여부
        if isinstance(ext, SubDictKey):
            return self == ext
        elif isinstance(ext, str):
            return self.name == ext.upper()
        
    @classmethod
    def contains(cls, key):  # SubDictKey에 key 포함 여부
        if isinstance(key, SubDictKey):
            return True
        elif isinstance(key, str):
            for item in SubDictKey:
                if item.name == key.upper():
                    return True

        return False
    
    @classmethod
    def get_key_list(cls):
        return [item for item in cls if not item.equal(SubDictKey.TIME_UNIT)]
    
    @classmethod
    def get_key_names(cls):
        key_name_list = [item.name for item in cls if not item.equal(SubDictKey.TIME_UNIT)]
        return "|".join(key_name_list)
    
    @classmethod
    def get_by_path(cls, path):
        ext = Path(path).suffix[1:]
        for item in cls:
            if item.equal(ext):
                return item
            
    @classmethod        
    def get_by_ext(cls, ext):
        for item in SubDictKey:
            if item.name == ext.upper():
                return item
        return False

class TimeUnit(Enum):  # 시간 단위 Enum
    MS = "ms"
    S = "s"
    SRT = "h:m:s,ms"
    VTT = "h:m:s.ms"

    def equal(self, ext):
        return self == ext

class TkKey(Enum):  # tkinter 딕셔너리 키 Enum
    ROOT = ("ROOT", False, False)
    LOAD_TYPE = ("LOAD_TYPE", True, False)  # 값: (이름, 행번호 여부, 같은 위젯 존재 여부(리스트로 저장 여부))
    SAVE_PATH = ("SAVE_PATH", True, False)
    AUDIO_PATH = ("AUDIO_PATH", True, False)
    SUB_PATH = ("SUB_PATH", True, False)
    YOUTUBE_URL = ("YOUTUBE_URL", True, False)
    NOTEBOOK = ("NOTEBOOK", True, False)
    TAB = ("TAB", False, True)

    SELECTED_COMBOBOX = ("SELECTED_COMBOBOX", False, False)
    SELECTED_LISTBOX_ELEMENT = ("SELECTED_LISTBOX_ELEMENT", False, False)
    DISPLAYED_IN_ROOT = ("DISPLAYED_IN_ROOT", False, True)  
    DISPLAYED_IN_NOTEBOOK = ("DISPLAYED_IN_NOTEBOOK", False, True)
    # DISPLAYED_IN_TAB = ("DISPLAYED_IN_TAB", False, True)
    LISTBOX_MAX_WIDTH = ("LISTBOX_MAX_WIDTH", False, False)
    ROOT_TITLE = ("ROOT_TITLE", False, False)
    ROOT_SIZE = ("ROOT_SIZE", False, False)

    def equal(self, ext):
        return self == ext

    def has_row_num(self):
        return self.value[1]
    
    def save_as_list(self):
        return self.value[2]
    
    # @classmethod
    # def create_TkKey_list():
    #     return [TkKey.LOAD_TYPE, TkKey.SAVE_PATH, TkKey.AUDIO_PATH, TkKey.SUB_PATH, TkKey.YOUTUBE_URL, TkKey.NOTEBOOK]
    

############## 탭 삭제 메서드 다시 한번 확인 ############################
def remove_tk(widget, type):
    if type.equal(TkKey.TAB):
        widget.master.forget(widget)
    else:
        widget.destroy()

class LogLevel(Enum):  # 로그 객체 레벨 설정용 키
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    def equal(self, level):
        if isinstance(level, LogLevel):
            return self == level
        elif isinstance(level, str):
            return self.name == level.upper()
        
###################
# 딕셔너리 클래스들 #
###################
class TkDict(): # tkinter 위젯 딕셔너리 클래스
    tk_dict = None

    @classmethod
    def initialize(cls):  # tkinter 딕셔너리 초기화
        cls.tk_dict = dict()

    # @classmethod
    # def reset(cls):
    #     destroy_notebook()
    #     create_tk_widgets(TkKey.NOTEBOOK)
    #     show_tk_widgets(TkKey.NOTEBOOK)
        
    @classmethod
    def pop(cls, key):  # tkinter 딕셔너리에서 해당 키(TkKey)의 값 삭제
        if key in cls.tk_dict:
            cls.tk_dict.pop(key, None)
    
    @classmethod
    def pop_element(cls, key, value):  # tkinter 딕셔너리에서 해당 키(TkKey)의 값(리스트) 중 value 원소 삭제
        if key in cls.tk_dict and key.save_as_list():
            key_list = cls.tk_dict[key]

            if value in key_list:
                idx = key_list.index(value)
                removed_element = key_list.pop(idx)
                return removed_element == value
        
        return False
    
    @classmethod
    def get_dict(cls):  # tkinter 딕셔너리 가져오기
        return cls.tk_dict

    @classmethod
    def get(cls, key):  # tkinter 딕셔너리의 키(TkKey)의 값 가져오기
        if key in cls.tk_dict:
            return cls.tk_dict[key]
        else:
            return False

    @classmethod
    def get_element(cls, key, idx):   # tkinter 딕셔너리 키(TkKey)의 값(리스트)의 특정 위치(idx) 원소 가져오기
        if key in cls.tk_dict:
            value = cls.tk_dict[key]

            if not key.save_as_list():
                return value
            if key in cls.tk_dict:
                if idx in range(len(value) * (-1), len(value)):
                    return value[idx]
                else:
                    Log.warning("Index Out Of Range, 인덱스 범위가 sub_dict[%s]의 범위 밖입니다.", key)
                    return False
        else:
            return False
    
    @classmethod
    def get_root_whxy(cls):  # 실행창 너비, 높이, x 위치, y 위치를 튜플로 반환
        key = TkKey.ROOT_SIZE
        if key in cls.tk_dict:
            size = cls.tk_dict[key]

            pattern1 = r"(\d+)x(\d+)"
            match1 = re.search(pattern1, size)

            if match1:
                w, h = match1.groups()

            pattern2 = r"\+(\d+)\+(\d+)"
            match2 = re.search(pattern2, size)

            if match2:
                x, y = match2.groups()
                return (w, h, x, y)
            else:
                return (w, h, 0, 0)

        return ()
    
    @classmethod
    def set(cls, key, value):  # tkinter 딕셔너리 '키(위젯 이름; TkKey): 값(위젯)' 추가
        if key.save_as_list():
            if key in cls.tk_dict:
                key_list = cls.tk_dict[key]
                key_list.append(value)
                return len(key_list) - 1
            else:
                cls.tk_dict[key] = [value]
                return 0
        else:
            cls.tk_dict[key] = value
            return -1
    
    @classmethod
    def get_element_size(cls, key):  # tkinter 딕셔너리의 키(TkKey)의 값 크기 가져오기
        if key in cls.tk_dict and key.save_as_list:
            return len(cls.tk_dict[key])
        else:
            return 0


class PathDict():  # 경로 딕셔너리 클래스
    path_dict = None  # 키: PathDictKey, SubDictKey

    @classmethod
    def initialize(cls):  # 경로 딕셔너리 초기화, 기본 경로 지정(root, 폰트, 아이콘)
        cls.path_dict = dict()
        # 현재 파일이 위치한 디렉토리 경로 (절대 경로)
        root_path = Path(__file__).parent.absolute()
        font_path = Path(root_path) / "font/GothicA1-Black.ttf"
        folder_icon_path = Path(root_path) / "images/folder_icon.png"
        audio_icon_path = Path(root_path) / "images/audio_icon.png"
        sub_icon_path = Path(root_path) / "images/sub_icon.png"
        cls.set(PathKey.ROOT, root_path)
        cls.set(PathKey.SAVE, root_path)
        cls.set(PathKey.FONT, font_path)
        cls.set(PathKey.FOLDER_ICON, folder_icon_path)
        cls.set(PathKey.AUDIO_ICON, audio_icon_path)
        cls.set(PathKey.SUB_ICON, sub_icon_path)

    @classmethod
    def reset(cls):
        load_type = TkDict.get(TkKey.SELECTED_COMBOBOX)
        save_path = cls.get(PathKey.SAVE)
        audio_path = None
        sub_path = None
        youtube_url = None
        if LoadType.YOUTUBE.equal(load_type):
            youtube_url = cls.get(PathKey.YOUTUBE_URL)
        elif LoadType.MANUAL.equal(load_type):
            audio_path = cls.get(PathKey.AUDIO)
            sub_path = cls.get(PathKey.SUB)
        
        cls.initialize()
        cls.set(PathKey.SAVE, save_path)
        if LoadType.YOUTUBE.equal(load_type):
            cls.set(PathKey.YOUTUBE_URL,  youtube_url)
        if PathKey.AUDIO in cls.path_dict:
            cls.set(PathKey.AUDIO, audio_path)
        if PathKey.SUB in cls.path_dict:
            cls.set(PathKey.SUB, sub_path)
   
    @classmethod
    def get_dict(cls):  # 경로 딕셔너리 가져오기
        return cls.path_dict

    @classmethod
    def get(cls, key):  # 경로 가져오기
        if key in cls.path_dict:
            return cls.path_dict[key]
        else:
            return False
    
    @classmethod
    def set(cls, key, value):  # 경로 딕셔너리의 키(경로 이름; PathKey)에 대한 값(경로) 추가
        if SubDictKey.contains(key) or key.save_as_list():
            if key in cls.path_dict:
                cls.path_dict[key].append(value)
            else:
                cls.path_dict[key] = [value]
            # Log.debug("찾은 자막- key: %s, list:%s", key.name, cls.path_dict[key])
        else:
            cls.path_dict[key] = value

    @classmethod
    def pop(cls, key):  # 경로 딕셔너리의 키(경로 이름; PathKey) 삭제
        if key in cls.path_dict:
            cls.path_dict.pop(key, None)

            
class SubDict(): # 자막 딕셔너리 클래스
    sub_dict = None  # 자막 정보 딕셔너리 {확장자: {파일명: [자막 정보 리스트], 시간 단위: 값(보통 ms)}}

    @classmethod
    def initialize(cls, init_by_json=False):  # 자막 딕셔너리 초기화
        if init_by_json:
            save_path = PathDict.get(PathKey.SAVE)
            sub_dict_path = Path(save_path) / "sub_dict.json"

            if Path(sub_dict_path).exists() and sub_dict_path.stat().st_size != 0 :
                try:
                    with open(sub_dict_path, "r", encoding="utf-8") as f:
                        cls.sub_dict = json.load(f)
                        return
                except Exception as e:
                    Log.warning("자막 정보 json 파일 읽기 실패, 에러 원인: %s", e)
                    
        cls.sub_dict = dict()

    @classmethod
    def items(cls):  # (자막 확장자, 자막 파일명, 자막 정보 리스트) 리스트 반환
        item_list = []
        for ext, ext_dict in cls.sub_dict.items():
            for fname, sub_list in ext_dict.items():
                if SubDictKey.TIME_UNIT.equal(fname):
                    continue
                element_tuple = (ext, fname, sub_list)
                item_list.append(element_tuple)
        
        return item_list

    @classmethod
    def sort(cls, desc=False):  # 자막 딕셔너리 키로 정렬
        sorted(cls.sub_dict.keys(), key=lambda item:item, reverse=desc)
    
    @classmethod
    def empty(cls):  # 자막 딕셔너리 비었는지 확인(비었으면 True)
        # Log.debug("자막 딕셔너리: %s",cls.sub_dict)
        return not cls.sub_dict

    @classmethod    
    def get_dict(cls):  # 자막 딕셔너리 반환
        return cls.sub_dict

    @classmethod 
    def get_dict_of_ext(cls, key):  # 자막 딕셔너리의 키(확장자)에 대한 값 반환
        key = key.name
        if key in cls.sub_dict:
            return cls.sub_dict[key]
        else:
            return False
    
    @classmethod
    def get(cls, key1, key2):  # 자막 딕셔너리의 키1(확장자)에 대한 값 중 키2(파일명)에 대한 값 반환
        if key1 in SubDictKey:
            key1 = key1.name
        if key2 in SubDictKey:
            key2 = key2.name

        if key1 in cls.sub_dict and key2 in cls.sub_dict:
            return cls.sub_dict[key1][key2]
        else:
            return False    

    @classmethod
    def set(cls, key1, key2, value):  # 자막 딕셔너리의 키1(확장자)에 대한 값 중 키2(파일명)에 대한 값 추가
        if key1 in SubDictKey:
            key1 = key1.name
        if key2 in SubDictKey:
            key2 = key2.name
            
        if not key1 in cls.sub_dict:
            cls.sub_dict[key1] = dict()
            
        cls.sub_dict[key1][key2] = value
    
    @classmethod
    def write(cls):
        save_path = PathDict.get(PathKey.SAVE)
        sub_dict_path = Path(save_path) / "sub_dict.json"
        try:
            with open(sub_dict_path, "w", encoding="utf-8") as f:
                json.dump(cls.sub_dict, f, ensure_ascii=False, indent=4)
        except Exception as e:
            Log.error("자막 딕셔너리 저장 실패(원인: %s)", e)
            
##################
# 로그 기록 클래스 #
##################
class Log():
    log = None

    @classmethod
    def initialize(cls, level):  # 로그 초기화
        #로그 생성
        cls.log = logging.getLogger("MkSub")

        # 로그의 레벨(LEVEL 이상의 로그만 출력)
        if level.equal(LogLevel.DEBUG):
            cls.log.setLevel(logging.DEBUG)  # 10, 상세한 디버깅 정보 - 변수 값 추적, 함수 호출 흐름
        elif level.equal(LogLevel.INFO):
            cls.log.setLevel(logging.INFO)  # 20, 일반적인 정보 - 처리 완료 메시지, 상태 보고
        elif level.equal(LogLevel.WARNING):
            cls.log.setLevel(logging.WARNING)  # 30, 경고(문제 가능성) - 설정 누락, 예상치 못한 입력
        elif level.equal(LogLevel.ERROR):
            cls.log.setLevel(logging.ERROR)  # 40, 오류(기능 일부 실패) - 파일 없음, DB 연결 실패
        elif level.equal(LogLevel.CRITICAL):
            cls.log.setLevel(logging.CRITICAL)  # 50, 심각한 오류(프로그램 중단 가능) - 시스템 다운, 데이터 손상

        # log 출력 형식
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        cls.log.addHandler(stream_handler)

        # log를 파일에 출력
        file_handler = logging.FileHandler("MkSub.log")
        file_handler.setFormatter(formatter)
        cls.log.addHandler(file_handler)

        cls.log.info("MkSub 파일을 실행합니다.")
    
    @classmethod
    def info(cls, info, *args):  # info 로깅
        cls.log.info(info, *args)

    @classmethod
    def warning(cls, warning, *args):  # warning 로깅
        cls.log.info(warning, *args)
    
    @classmethod
    def error(cls, error, *args):  # error 로깅
        cls.log.info(error, *args)

    @classmethod
    def debug(cls, debug, *args):  # debug 로깅(출력X)
        cls.log.info(debug, *args)

def initDictNLog(log_level=LogLevel.INFO):  # TkDict, PathDict 클래스 객체 생성
    TkDict.initialize()
    PathDict.initialize()
    Log.initialize(log_level)

###############################    
# LoadType: Youtube 관련 메서드 #
###############################    
def get_youtube_info(load_type=LoadType.YOUTUBE):  # 유튜브 링크 혹은 저장된 json 파일로 유튜브 정보 가져오기(실행하는 LoadType: Youtbue, Auto)
    Log.info("[Load_type: %s] 유튜브 정보를 찾는 중...", load_type.name)
    if load_type.equal(LoadType.YOUTUBE):
        youtube_url = PathDict.get(PathKey.YOUTUBE_URL)
        init_opts = {
            'quiet': True,
            'skip_download': True,
        }
        ydl = yt_dlp.YoutubeDL(init_opts)
        youtube_info = ydl.extract_info(youtube_url, download=False)  # Keys: id, title, formats, thumbnails, thumbnail, description, channel_id, channel_url, duration, view_count, average_rating, age_limit, webpage_url, categories, tags, playable_in_embed, live_status, media_type, release_timestamp, _format_sort_fields, automatic_captions, subtitles, comment_count, chapters, heatmap, like_count, channel, channel_follower_count, creators, uploader, uploader_id, uploader_url, upload_date, timestamp, availability, original_url, webpage_url_basename, webpage_url_domain, extractor, extractor_key, playlist, playlist_index, display_id, fulltitle, duration_string, release_year, is_live, was_live, requested_subtitles, _has_drm, epoch, asr, filesize, format_id, format_note, source_preference, fps, audio_channels, height, quality, has_drm, tbr, filesize_approx, width, language, language_preference, preference, ext, vcodec, acodec, dynamic_range, container, url, available_at, downloader_options, protocol, audio_ext, video_ext, vbr, abr, resolution, aspect_ratio, http_headers, format
        title = youtube_info.get('title', "제목 없는 파일")
            
        # 저장 폴더 생성
        folder_name = re.sub(r'[\/:*?"<>|\s]', '_', title)
        folder_name = re.sub(r'_{2,}', "_", folder_name)
        save_path = PathDict.get(PathKey.SAVE)
        save_path = Path(save_path) / folder_name
        save_path.mkdir(parents=True, exist_ok=True)
        PathDict.set(PathKey.SAVE, save_path)

        try:
            with open(youtube_info_path, "w", encoding="utf-8") as f:
                f.dumps(youtube_info, ensure_ascii=False)
        except Exception as e:
            Log.error("유튜브 정보 json 파일 쓰기 실패, 에러 원인: %s", e)

        return youtube_info
    
    elif load_type.equal(LoadType.AUTO):
        save_path = PathDict.get(PathKey.SAVE)
        youtube_info_path = Path(save_path) / "youtube_info.json"
        
        if youtube_info_path.exists() and youtube_info_path.stat().st_size != 0 :
            try: 
                with open(youtube_info_path, "r", encoding="utf-8") as f:
                    youtube_info = json.load(f)

                return youtube_info
            
            except Exception as e:
                Log.warning("유튜브 정보 json 파일 읽기 실패, 에러 원인: %s", e)

        return False

def download_subtitle(youtube_info) :  # 유튜브 링크로 자막 다운로드
    Log.info("유튜브 자막을 다운로드합니다.")

    save_path = PathDict.get(PathKey.SAVE)
    youtube_url = PathDict.get(PathKey.YOUTUBE_URL)
    exist_sub = False

    if "ko" in youtube_info.get("automatic_captions"):
        auto_subs_ext_list = [caption["ext"] for caption in youtube_info.get("automatic_captions")["ko"]]
        sub_lang = "ko"
    elif "en" in youtube_info.get("automatic_captions"):
        auto_subs_ext_list = [caption["ext"] for caption in youtube_info.get("automatic_captions")["en"]]
        sub_lang = "en"
    else:
        auto_subs_ext_list = []

    for ext in auto_subs_ext_list:
        sub_path = Path(save_path) / f"subtitle.{ext}"
        if sub_path.exists():
            continue

        caption_download_opts = {
            'writeautomaticsub': True,      # 자동 생성 자막 다운로드 활성화
            'skip_download': True,          # 영상 자체는 다운로드하지 않음 (자막만 필요할 경우)
            'subtitlesformat': ext,
            'subtitleslangs': [sub_lang],       # 자막 언어 지정 (한국어는 'ko'로 변경)
            'outtmpl': f'{save_path}/subtitle'     # 저장될 파일명 형식
        }

        ydl = yt_dlp.YoutubeDL(caption_download_opts)
        ydl.download([youtube_url])
        ext = SubDictKey.get_by_ext(ext)
        PathDict.set(ext, sub_path)
        if not exist_sub:
            exist_sub = True
    
    return exist_sub

def download_audio():  # 유튜브 링크로 오디오 다운로드
    Log.info("유튜브 음원을 다운로드합니다.")
    
    save_path = PathDict.get(PathKey.SAVE)
    youtube_url = PathDict.get(PathKey.YOUTUBE_URL)
    exist_audio = False
    
    audio_download_opts = {
        'format': 'bestaudio/best', # 최고 음질 포맷 선택
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3', # 변환할 포맷
            'preferredquality': '192', # 오디오 비트레이트
        }],
        'outtmpl': f'{save_path}/audio', # 파일명을 영상 제목으로 저장
    }

    ydl = yt_dlp.YoutubeDL(audio_download_opts)
    ydl.download([youtube_url])

    audio_path = f"{audio_download_opts["outtmpl"]}.mp3"
    PathDict.set(PathKey.AUDIO, audio_path)

    if not exist_audio:
        exist_audio = True
    
    return exist_audio

#############################
# LoadType: AUTO 관련 메서드 #
#############################
def find_audio_auto():  # 저장 경로 내에서 오디오 혹은 비디오 파일 찾기(auto)
    exist_audio = False
    save_path = PathDict.get(PathKey.SAVE)
    pattern = re.compile(r'\.(mp3|wav|m4a|ogg|wma)$', re.IGNORECASE)

    for audio_path in Path(save_path).iterdir() :
        if pattern.search(audio_path.name) :
            PathDict.set(PathKey.AUDIO, audio_path)
            if not exist_audio:
                exist_audio = True
        
    if not exist_audio:
        pattern = re.compile(r"\.(mp4|avi|mov|mkv|wmv|flv|webm|ogv|gif)$", re.IGNORECASE)
        for video_path in Path(save_path).iterdir() :
            if pattern.search(audio_path.name) :
                video = VideoFileClip(video_path)
                audio_path = Path(save_path) / f"{video_path.stem}.mp3"
                video.audio.write_audiofile(audio_path)
                PathDict.set(PathKey.AUDIO, audio_path)
                if not exist_audio:
                    exist_audio = True

    return exist_audio

##################
#### 자막 전처리 ###
##################

def get_subtitle(start, dur, text, time_unit=TimeUnit.MS):  # time_unit 단위로 시간 변환하여 자막 정보 리스트 반환xxxxxxxxxxxx
    # 매개변수의 start와 dur의 단위: ms
    # text: 자막(가사)
    # time_unit은 반환하는 시간 단위

    if time_unit.equal(TimeUnit.MS) :
        start_time = start
        end_time = start + dur
    elif time_unit.equal(TimeUnit.SRT) :
        start_time = convert2str_time(start, TimeUnit.SRT)
        end_time = convert2str_time(start + dur, TimeUnit.SRT)
    elif time_unit.equal(TimeUnit.S) :
        start_time = float(start) / 1000
        end_time = float(start + dur) / 1000
    elif time_unit.equal(TimeUnit.VTT):
        start_time = convert2str_time(start, TimeUnit.VTT)
        end_time = convert2str_time(start + dur, TimeUnit.VTT)

    return [start_time, end_time, text]

def convert2str_time(ms, time_unit):  # ms 단위의 시간을 srt 또는 vtt 형식의 문자열로 변환
    if time_unit.equal(TimeUnit.SRT):
        sep = ","
    elif time_unit.equal(TimeUnit.VTT):
        sep = "."

    h, remainder = divmod(ms, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, ms = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

def convert2ms(t):  # hh:mm:ss,ms 형식의 문자열을 ms 단위의 정수로 변환
    h = 0
    pattern1 = '([0-9]{2}):([0-9]{2}):([0-9]{2})[.,]{1}([0-9]{3})'
    match1 = re.search(pattern1, t)
    if match1:
        h, m, s, ms = match1.groups()
    else:
        pattern2 = '([0-9]{2}):([0-9]{2})[.,]{1}([0-9]{3})'
        match2 = re.search(pattern2, t)
        if match2:
           m, s, ms = match2.groups()
        else:
            return -1
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)

def get_all_tag_options(srv_path):  # srv 형식 자막 태그 가져오기
    tree = ET.parse(srv_path)
    root = tree.getroot()
    all_tags = set([element.tag for element in root.iter()])  # 형식: {'transcript', 'text'}

    all_tag_options = dict()
    for tag_name in all_tags:
        for element in root.findall(f".//{tag_name}") :
            all_tag_options[tag_name] = set(element.attrib.keys())  # 형식: {'text': {'dur', 'start'}}

    return (root, all_tag_options)

def get_srv1_sub_dict(sub_path):  # srv1 형식 자막 처리
    subtitle_list = list()
    root, all_tag_options = get_all_tag_options(sub_path)
    
    if "text" in all_tag_options and set(['start', 'dur']).issubset(all_tag_options["text"]):  # srv1
        ext_num = 0
        for element in root.findall("text") :
            start = int(float(element.attrib["start"]) * 1000)
            dur = int(float(element.attrib["dur"]) * 1000)
            text = element.text
            sub_info = [len(subtitle_list), start, start + dur, text]
            subtitle_list.append(sub_info)

        SubDict.set(SubDictKey.SRV1, sub_path.name, subtitle_list)
    
    return subtitle_list

def get_srv2_sub_dict(sub_path):  # srv2 형식 자막 처리
    subtitle_list = list()
    root, all_tag_options = get_all_tag_options(sub_path)
    
    if "text" in all_tag_options and set(['d', 'r', 't', 'c', 'w']).issubset(all_tag_options["text"]):
        pre_text = ""
        text_tag_list = root.findall("text")
        for i, element in enumerate(text_tag_list) :
            start = int(element.attrib["t"])
            try:
                dur = int(element.attrib["d"])
            except Exception as e:
                if "d" not in element.attrib and element.text.isspace():
                    next_element = text_tag_list[i+1]
                    dur = int(next_element.attrib["t"])
            if "append" in element.attrib:
                text = pre_text + element.text
            else:
                text = element.text

            pre_text = text
            sub_info = [len(subtitle_list), start, start + dur, text]
            subtitle_list.append(sub_info)
            
        SubDict.set(SubDictKey.SRV2, sub_path.name, subtitle_list)
    
    return subtitle_list

def get_srv3_sub_dict(sub_path):  # srv3 형식 자막 처리
    subtitle_list = list()
    root, all_tag_options = get_all_tag_options(sub_path)
    
    if "p" in all_tag_options and set(['t', 'd', 'w']).issubset(all_tag_options["p"]): 
        p_tag_list = root.findall(".//p")
        for i, element in enumerate(p_tag_list) :
            start = int(element.attrib["t"])
            try :
                dur = int(element.attrib["d"])
            except Exception as e:
                if "d" not in element.attrib and element.text.isspace():
                    next_element = p_tag_list[i+1]
                    dur = int(next_element.attrib["t"]) - start
            end = start + dur

            pre_text = ""
            for sub_element in element.findall(".//s"):

                if "t" not in sub_element.attrib:
                    sub_start = start
                    text = sub_element.text
                else:
                    sub_start = start + int(sub_element.attrib["t"])
                    text = pre_text + sub_element.text

                dur = end - sub_start
                pre_text = text
                sub_info = [len(subtitle_list), sub_start, sub_start + dur, text]
                subtitle_list.append(sub_info)
    
    SubDict.set(SubDictKey.SRV3, sub_path.name, subtitle_list)
    
    return subtitle_list

def get_json3_sub_dict(sub_path):  # json3 형식 자막 처리
    Log.debug("json3 자막 파일 처리 중...")
    exist_sub = False
    subtitle_list = list()

    json_sub = {}
    try :
        with open(sub_path, "r", encoding="utf-8") as f:
            json_sub = json.load(f)
    except Exception as e:
        Log.error("json3 자막 파일 읽기 실패, 에러 원인: %s", e)
        return exist_sub

    for i, sub_info_dict in enumerate(json_sub["events"]):
        if i == 0:
            start_time = int(sub_info_dict["tStartMs"])
            end_time = start_time + int(sub_info_dict["dDurationMs"])
            continue
        
        start = int(sub_info_dict["tStartMs"])
        dur = 0
        if "dDurationMs" in sub_info_dict:
            dur = int(sub_info_dict["dDurationMs"])
        sub_text = ""
        for j, sub in enumerate(sub_info_dict["segs"]):
            sub_text += sub["utf8"]
            cur_start = start
            if "tOffsetMs" in sub :
                cur_start += int(sub["tOffsetMs"])
            if j > 0:
                subtitle_list[-1][2] = cur_start
            sub_info = [len(subtitle_list), cur_start, start + dur, sub_text]
            subtitle_list.append(sub_info)
    
    SubDict.set(SubDictKey.JSON3, sub_path.name, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_srt_sub_dict(sub_path):  # srt 형식 자막 처리
    exist_sub = False
    subtitle_list = list()

    try :
        with open(sub_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        Log.error("srt 자막 파일 읽기 실패, 에러 원인: %s", e)
        return exist_sub

    sub_info = []
    for i, line in enumerate(lines):
        if i % 4 == 0:
            sub_info = [i // 4]
        elif i % 4 == 1:
            str_start, str_end = tuple(line.split(" --> "))
            start = convert2ms(str_start)
            end = convert2ms(str_end)
            sub_info += [start, end]
        elif i % 4 == 2:
            sub_info.append(line.strip())
        elif i % 4 == 3:
            subtitle_list.append(sub_info)
    SubDict.set(SubDictKey.SRT, sub_path.name, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_ttml_sub_dict(sub_path):  # ttml 형식 자막 처리
    exist_sub = False
    subtitle_list = list()
        
    root, all_tag_options = get_all_tag_options(sub_path)
    p_tag = ""
    for key in all_tag_options.keys():
        pattern = r"\{[^ \t\n\r\f\v]*\}p"
        if re.search(pattern, key) :
            p_tag = key
            
    if p_tag in all_tag_options and set(['begin', 'end']).issubset(all_tag_options[p_tag]):
        p_tag_list = root.findall(f".//{p_tag}")
        
        for i, element in enumerate(p_tag_list) :
            start = convert2ms(element.attrib["begin"])
            end = convert2ms(element.attrib["end"])
            sub_text = element.text
            sub_info = [len(subtitle_list), start, end, sub_text]
            subtitle_list.append(sub_info)
        SubDict.set(SubDictKey.TTML, sub_path.name, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_vtt_sub_dict(sub_path):  # vtt 형식 자막 처리
    exist_sub = False
    subtitle_list = list()
    # VTT 파일 읽기
    vtt = webvtt.read(sub_path)

    # 캡션 루프 돌며 시간과 텍스트 추출
    for i, caption in enumerate(vtt):

        start = convert2ms(caption.start)
        end = convert2ms(caption.end)
        txt = caption.text
        sub_info = [i, start, end, txt]
        subtitle_list.append(sub_info)
    SubDict.set(SubDictKey.VTT, sub_path.name, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_whisper_sub_list():  # whisper 자막 데이터 불러오기
    save_path = PathDict.get(PathKey.SAVE)
    whisper_sub_path = Path(save_path) / "audio.json"

    try:
        with open(whisper_sub_path, "r", encoding="utf-8") as f:
            whisper_json = json.load(f)
    except Exception as e:
        Log.error("whisper 자막 데이터 읽기 실패, 에러 원인: %s", e)
    print(whisper_json["segments"])
    whisper_subs_list = [[sub["start"], sub["end"] - sub["start"], sub["text"]] for sub in whisper_json["segments"]]
    return whisper_subs_list

def init_sub_info():  # 저장한 자막 경로 확장자 별로 자막 전처리 실행
    Log.info("조회된 자막 파일 경로의 자막 전처리 중...")
    exist_sub = False
    ext_list = SubDictKey.get_key_list()
    time_unit = TimeUnit.MS.value
    for ext in ext_list:
        sub_path_list = PathDict.get(ext)
        # Log.debug("자막 경로 리스트: %s(확장자: %s)", sub_path_list, ext)
            
        if not sub_path_list:
            continue

        SubDict.set(ext, SubDictKey.TIME_UNIT, time_unit)
        cur_sub_exist = False
        for sub_path in sub_path_list:
            # Log.debug("자막 처리 확장자: %s, 경로: %s",ext.name, sub_path)
            
            sub_path = Path(str(sub_path))
            if SubDict.get(ext, sub_path.name):
                exist_sub = True
                continue
            
            if SubDictKey.JSON3.equal(ext):
                cur_sub_exist = get_json3_sub_dict(sub_path)
            elif SubDictKey.SRT.equal(ext):
                Log.info("SRT 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_srt_sub_dict(sub_path)
            elif SubDictKey.SRV1.equal(ext):
                Log.info("SRV1 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_srv1_sub_dict(sub_path)
            elif SubDictKey.SRV2.equal(ext):
                Log.info("SRV2 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_srv2_sub_dict(sub_path)
            elif SubDictKey.SRV3.equal(ext):
                Log.info("SRV3 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_srv3_sub_dict(sub_path)
            elif SubDictKey.TTML.equal(ext):
                Log.info("TTML 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_ttml_sub_dict(sub_path)
            elif SubDictKey.VTT.equal(ext):
                Log.info("VTT 자막 처리 중...(%s)",ext)
                cur_sub_exist = get_vtt_sub_dict(sub_path)

            if not exist_sub:
                exist_sub = exist_sub or cur_sub_exist
        if cur_sub_exist:        
            SubDict.write()

    return exist_sub

###############
# 비디오 만들기 #
###############
def get_sub_clip(txt, start, duration, v_position, h_position="left"):  # 비디오 만들 때, 사용하는 TextClip 반환 메서드
    # font_path = PathDict.get(PathKey.FONT)

    # # TextClip 설정 (한글 사용 시 폰트 경로 지정 필수)
    # return TextClip(
    #     font_path,  # 한글 폰트 (고딕 A1)
    #     text = txt,
    #     font_size=24,
    #     color='white',
    #     method='label'
    # ).with_start(start).with_duration(duration).with_position(h_position, v_position)
    pass

def save_video(subtitles):  # 비디오 만들어서 저장
    # # subtitles : [[start, dur, text], ...]

    # # 1. 오디오 파일 불러오기
    # audio_path = PathDict.get(PathKey.AUDIO)
    # audio_clip = AudioFileClip(audio_path)

    # # 2. 자막을 영상에 입히는 함수
    

    # # 3. 배경 이미지/영상 클립 생성
    # # (여기서는 검은색 화면을 오디오 길이에 맞춰 생성)
    # background_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=audio_clip.duration)

    # # 4. .srt 파일 파싱 및 자막 클립 생성 (간단한 예시)
    # # 실제 프로젝트에서는 pysrt 라이브러리 등을 사용해 .srt 파일을 읽어오는 것을 권장합니다.
    # # position = ["top", "center", "bottom"]
    # # cur = -1
    # # for key, value in caption_dict.items():
    # #     cur += 1
    # #     cur_position = position[cur]
    # #     subtitle_clips = []
    # #     for caption in value["caption_list"]:
    # #             subtitle_clips.append(make_subtitle_clip(caption["text"], caption["start"], caption["dur"], cur_position, "left"))
    # #     caption_dict[key]["subtitle_clips"] = subtitle_clips

    # subtitle_clips = []
    # for start, dur, text in subtitles:
    #     sub_clip = get_sub_clip(text, start, dur, "bottom", "left")
    #     subtitle_clips.append(sub_clip)

    # # 5. 배경 + 자막 병합
    # video_clip = CompositeVideoClip([background_clip, *subtitle_clips])

    # # 6. 영상에 오디오 적용 및 최종
    # save_path = PathDict.get(PathKey.SAVE)
    # video_path = f'{save_path}/whisper_sub_apply.mp4'
    # final_video = video_clip.with_audio(audio_clip)
    # final_video.write_videofile(
    #     video_path,
    #     fps=24,
    #     codec='libx264',
    #     audio_codec='aac'
    # )

    # # 클립 종료
    # audio_clip.close()
    # final_video.close()
    pass

def display_video_and_sub_by_html(video_path, sub_path):  # 비디오 혹은 오디오 + 자막 HTML로 표시
    # 1. 자막(HTML) 객체 생성 및 표시
    # video_html = HTML(f"""
    # <video autoplay muted loop playsinline width="640" controls>
    # <source src="{video_path}" type="video/mp4">
    # <track src="{sub_path}" kind="subtitles" srclang="ko" label="한국어" default>
    # 지원하지 않는 브라우저입니다.
    # </video>
    # """)
    # display(video_html)
    pass

def display_ranged_audio(audio_path, start, end):  # 정해진 구간 재생(시간 단위, 초) with HTML
    # audio_html = HTML(f"""
    # <audio controls>
    #     <source src="{audio_path}#t={start},{end}" type="audio/mpeg">
    #     지원하지 않는 브라우저입니다.
    # </audio>
    # """)
    # display(audio_html)
    pass

######################
# TKINTER 관련 메서드 #
######################
def on_select_combo(event):  # LoadType combobox 선택 시 실행
    load_type = TkDict.get(TkKey.LOAD_TYPE)[1].get()
    # Log.debug("콤보 박스 값 변경: %s", load_type)
    TkDict.set(TkKey.SELECTED_COMBOBOX, load_type)
    show_widgets_keys = []
    hide_widgets_keys = []

    if LoadType.YOUTUBE.equal(load_type):
        Log.debug("콤보 박스 값 변경(LoadType: YOUTUBE)") 
        show_widgets_keys = [TkKey.SAVE_PATH, TkKey.YOUTUBE_URL]
        hide_widgets_keys = [TkKey.AUDIO_PATH, TkKey.SUB_PATH, TkKey.NOTEBOOK]

    elif LoadType.AUTO.equal(load_type):
        Log.debug("콤보 박스 값 변경(LoadType: AUTO)")
        show_widgets_keys = [TkKey.SAVE_PATH]
        hide_widgets_keys = [TkKey.AUDIO_PATH, TkKey.SUB_PATH, TkKey.YOUTUBE_URL, TkKey.NOTEBOOK]

    elif LoadType.MANUAL.equal(load_type):
        Log.debug("콤보 박스 값 변경(LoadType: MANUAL)")
        show_widgets_keys = [TkKey.SAVE_PATH, TkKey.AUDIO_PATH, TkKey.SUB_PATH]
        hide_widgets_keys = [TkKey.YOUTUBE_URL, TkKey.NOTEBOOK]
    
    for key in hide_widgets_keys:
        hide_tk_widgets(key)

    for key in show_widgets_keys:
        show_tk_widgets(key)

def select_folder():  # 저장 경로 폴더 선택
    key = PathKey.SAVE
    # 폴더 선택 대화상자 호출
    save_path = str(PathDict.get(key))
    path = filedialog.askdirectory(initialdir=save_path)
    
    if path:
        PathDict.set(key, path)
        set_dir_entry(key, path)

def select_file(key):  # 오디오 및 자막 파일 경로 선택 
    if key.equal(PathKey.AUDIO):
        Log.debug("오디오 파일 경로 지정 버튼 클릭")
        filetype_list = [("오디오 파일", "*.mp3 *.wav *.m4a *.ogg *.wma"), ("비디오 파일", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.ogv *.gif")]
    elif key.equal(PathKey.SUB):
        Log.debug("자막 파일 경로 지정 버튼 클릭")
        filetype_list = [("자막 파일", "*.json3 *.srt *.srv1 *.srv2 *.srv3 *.ttml *.vtt")]

    save_path = str(PathDict.get(PathKey.SAVE))
    path = filedialog.askopenfilename(title="오디오 혹은 비디오 파일을 선택하세요.",
                                        initialdir=save_path,
                                        filetypes=filetype_list)
    
    if path:
        PathDict.set(key, path)
        set_dir_entry(key, path)

def set_dir_entry(key, value):  # 경로 키 Enum으로 엔트리 값 수정
    if key == PathKey.SAVE:
        w1, w2, entry_widget = TkDict.get(TkKey.SAVE_PATH)
    elif key == PathKey.AUDIO:
        w1, w2, entry_widget = TkDict.get(TkKey.AUDIO_PATH)
    elif key == PathKey.SUB:
        w1, w2, entry_widget = TkDict.get(TkKey.SUB_PATH)

    # 선택한 경로를 활용한 추가 작업 수행
    entry_widget.config(state="normal")
    entry_widget.delete(0,"end")
    entry_widget.insert(0, value)
    entry_widget.config(state="readonly")

def get_youtube_url():  # 유튜브 링크 가져오기
    url = TkDict.get(TkKey.YOUTUBE_URL)[-1].get()
    save_path = TkDict.get(TkKey.SAVE_PATH)[-1].get()
    PathDict.set(PathKey.SAVE, save_path)

    if url.startswith("https://youtu.be/") :
        return get_video_id_with_startswith("https://youtu.be/", url)
    elif url.startswith("https://www.youtube.com/watch?v="):
        return get_video_id_with_startswith("https://www.youtube.com/watch?v=", url)
    elif url.startswith("https://www.youtube.com/embed/"):
        return get_video_id_with_startswith("https://www.youtube.com/embed/", url)
    
    return (False, url)

def get_video_id_with_startswith(start_url, url):  # 유튜브 링크 유형에 따라 video id 추출하여 기본 url로 변환
    video_id = url[len(start_url):].split("?")[0].split("&")[0]
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    entry_youtube_url = TkDict.get(TkKey.YOUTUBE_URL)
    entry_youtube_url.delete(0,"end")
    entry_youtube_url.insert(0, youtube_url)
    PathDict.set(PathKey.YOUTUBE_URL, youtube_url)
    return (True, youtube_url)

def play_mkSub():  # 파일 조회 및 자막 전처리 실행
    exist_sub = False
    exist_audio = False
    load_type = TkDict.get(TkKey.SELECTED_COMBOBOX)
    PathDict.reset()

    if LoadType.YOUTUBE.equal(load_type):
        Log.debug("mkSub 실행 (LoadType: 유튜브 링크)")
        SubDict.initialize()   
        download_youtube()
    
    elif LoadType.AUTO.equal(load_type):
        Log.debug("mkSub 실행 (LoadType: 자동 파일 조회)")
        init_by_subDict_json = True
        SubDict.initialize(init_by_subDict_json)
        exist_sub, exist_audio = find_files_auto()
    
    elif LoadType.MANUAL.equal(load_type):
        Log.debug("mkSub 실행 (LoadType: 지정 파일 로드)")
        SubDict.initialize()
        exist_sub, exist_audio = find_files_manual()
    
    if exist_sub:
        exist_sub = init_sub_info()
        update_tab()

def download_youtube():  # 유튜브 링크로 오디오, 자막 다운로드
    youtube_url = get_youtube_url()

    if not youtube_url[0]:
        if youtube_url[1] == "":
            Log.warning("[LoadType: 유튜브 링크] 실행 종료-유튜브 링크 미입력")
            messagebox.showwarning("경고", "유튜브 링크가 입력되지 않았습니다.\n유튜브 링크를 입력한 후 '실행' 버튼을 클릭해 주십시오.")
        else:
            Log.warning("[LoadType: 유튜브 링크] 실행 종료-유효하지 않은 유튜브 링크")
            messagebox.showwarning("경고", "입력하신 유튜브 링크가 유효하지 않습니다.\n유튜브 링크를 다시 입력해 주십시오.")
        return
        
    youtube_info = get_youtube_info(LoadType.YOUTUBE)
    if youtube_info is None:
        Log.warning("[LoadType: 유튜브 링크] 유튜브 영상 정보를 가져오지 못했습니다.")
        messagebox.showwarning("경고", "유튜브 영상 정보를 가져올 수 없습니다.")
        return
        
    exist_sub = download_subtitle(youtube_info)
    if not exist_sub:
        Log.warning("[LoadType: 유튜브 링크] 자막 다운로드 실패")
        keep_going = messagebox.askyesno("경고", "자막 다운로드가 실패하였습니다.\n오디오 파일 다운로드를 계속 진행하시겠습니까?")
        if not keep_going:
            return
            
    exist_audio = download_audio()
    if not exist_audio:
        Log.warning("[LoadType: 유튜브 링크] 오디오 다운로드 실패")
        messagebox.showwarning("경고", "오디오 파일 다운로드가 실패하였습니다.")

    Log.info("유튜브 다운로드 완료")
    return (exist_sub, exist_audio)

def find_files_auto():  # 저장 경로에서 오디오, 자막 찾기(auto)
    Log.info("[LoadType: AUTO] 파일 찾는 중...")
    youtube_info = get_youtube_info(LoadType.AUTO)
    exist_sub = False
    exist_audio = False
    if youtube_info:  
        Log.info("[LoadType: AUTO] 경로 내 유튜브 정보 파일 존재")
        download_files = messagebox.askyesno("경로 내에 'youtube_info.json' 파일이 존재합니다.\n유튜브 링크로부터 자막과 오디오 파일을 다운로드 받으시겠습니까?")
        if download_files:
            exist_sub = download_subtitle(youtube_info)
            exist_audio = download_subtitle(youtube_info)
        
    exist_sub = exist_sub or find_sub_auto()
    if not exist_sub:
        Log.warning("[LoadType: AUTO] There isn't a sub file.")
        keep_going = messagebox.askyesno("경고", "해당 경로 내에 자막 파일이 존재하지 않습니다.\n자막 파일 경로를 다시 설정해 주십시오.(지원 확장자:json3, srt, srv1, srv2, srv3, ttml, vtt)\n다음 오디오 파일 조회 작업을 계속 진행하시겠습니까?")
        if not keep_going:
            return (exist_sub, exist_audio)
                
    exist_audio = exist_audio or find_audio_auto()    
    audio_path = PathDict.get(PathKey.AUDIO)
    Log.debug("[LoadType: AUTO] Found Audio file list: %s", audio_path)
    if not exist_audio and not audio_path:
        Log.warning("[LoadType: AUTO] There isn't an audio file.")
        keep_going = messagebox.askyesno("경고", "해당 경로 내에 오디오나 비디오 파일이 존재하지 않습니다.\n파일 조회를 종료합니다.")
        if not keep_going:
            return
    elif len(audio_path) > 1:
        Log.warning("[LoadType: AUTO] There are many audio files.")
        select_first = messagebox.askyesno("경고", f"경로 내 오디오 파일이 2개 이상 존재합니다.\n[존재하는 오디오 파일]\n{'\n'.join([path.name for path in audio_path])}\n{audio_path[0].name} 파일로 작업하시려면 '확인'을 클릭하시고 다른 파일을 지정하려면 '취소'를 클릭하세요.\n'파일 가져오는 방법'으로 (수동)을 선택하면 오디오 경로를 직접 지정할 수 있습니다.")
        if select_first:
            audio_path = audio_path[0]
            PathDict.pop(PathKey.AUDIO)
            PathDict.set(PathKey.AUDIO, audio_path)
        else:
            exist_audio = False
    
    
    # Log.debug("[LoadType:AUTO] 파일 찾기 결과 - 자막: %s, 오디오: %s",exist_sub, exist_audio)
    return (exist_sub, exist_audio)

def find_files_manual():  # 지정한 경로의 오디오, 자막 파일 확인(manual)
    exist_audio = False
    exist_sub = False

    w1, w2, entry_sub_path = TkDict.get(TkKey.SUB_PATH)
    sub_path = entry_sub_path.get()
    Log.debug("sub_path: %s", sub_path)
    if not Path(sub_path).exists() or not Path(sub_path).is_file():
        Log.warning("[LoadType: MANUAL] There isn't a sub file.")
        keep_going = messagebox.askyesno("경고", "자막 파일이 유효하지 않습니다.\n다음 오디오 파일 확인 작업을 계속 진행하시겠습니까?")
        if not keep_going:
            return (exist_sub, exist_audio)
    else:
        ext = Path(sub_path).suffix[1:]
        sub_dict_key = SubDictKey.get_by_ext(ext)
        PathDict.set(sub_dict_key, sub_path)
        # Log.debug("Check SUB file path: %s", PathDict.get(sub_dict_key))
        exist_sub = True

    w1, w2, entry_audio_path = TkDict.get(TkKey.AUDIO_PATH)
    audio_path = entry_audio_path.get()
    if Path(audio_path).exists() and Path(audio_path).is_file():
        PathDict.set(PathKey.AUDIO, audio_path)
        # Log.debug("Check AUDIO file path: %s", PathDict.get(PathKey.AUDIO))
        exist_audio = True
    else:
        Log.warning("[LoadType: MANUAL] There isn't an audio file.")
    
    return (exist_sub, exist_audio)

def find_sub_auto():  # 저장 경로에서 자막 찾기(auto)
    save_path = PathDict.get(PathKey.SAVE)
    exist_sub = False
    pattern = re.compile(f'.({SubDictKey.get_key_names()})$', re.IGNORECASE)
    for path in Path(save_path).iterdir() :
        if pattern.search(path.name) :
            ext = SubDictKey.get_by_path(path)
            PathDict.set(ext, path)

            if not exist_sub:
                exist_sub = True
    
    return exist_sub

def set_root_size(size):  # 너비, 높이, x, y 위치 주고 size값 저장 및 문자열 가져오기
    width, height, loc_x, loc_y = size
    str_size = f"{width}x{height}+{loc_x}+{loc_y}"
    TkDict.set(TkKey.ROOT_SIZE, str_size)
    root = TkDict.get(TkKey.ROOT)
    root.geometry(str_size)
    return str_size

def create_tk_root(title, size):  # Tk 객체 생성 및 초기화
    tk = Tk()
    tk.title(title)
    TkDict.set(TkKey.ROOT, tk)
    TkDict.set(TkKey.ROOT_TITLE, title)
    set_root_size(size)
    return tk

def create_tk_widgets(key):  # 위젯 생성(종류: LOAD_TYPE, SAVE_PATH, AUDIO_PATH, SUB_PATH, YOUTUBE_URL, NOTEBOOK)
    root = TkDict.get(TkKey.ROOT)

    if key == TkKey.LOAD_TYPE:  # LOAD_TYPE 행 위젯 생성
        combobox_list = list(LoadType.get_tuple())
        label_load_type = Label(root, text="파일 가져오는 방법: ", anchor="e")  # font: (글꼴, 글자 크기, 스타일), fg: 글자색, bg: 글자 배경색
        combobox_load_type = ttk.Combobox(root, values=combobox_list, state="readonly")
        combobox_load_type.set(LoadType.YOUTUBE.value)
        combobox_load_type.bind("<<ComboboxSelected>>", on_select_combo)
        btn_play_mk_sub = Button(root, text="실행", command=play_mkSub)
        created_widgets = (label_load_type, combobox_load_type, btn_play_mk_sub)

    elif key == TkKey.SAVE_PATH:  # 저장 폴더 경로 지정 행 위젯 생성
        label_save_path = Label(root, text="저장 경로: ", anchor="e")
        folder_img = PhotoImage(file=PathDict.get(PathKey.FOLDER_ICON))
        btn_save_path = Button(root, image=folder_img, width=40, command=select_folder)
        btn_save_path.image = folder_img
        entry_save_path = Entry(root, width=50)
        save_path = str(PathDict.get(PathKey.SAVE))
        entry_save_path.insert(0, save_path)
        entry_save_path.config(state="readonly")
        created_widgets = (label_save_path, btn_save_path, entry_save_path)

    elif key == TkKey.AUDIO_PATH:  # 오디오 파일 경로 지정 행 위젯 생성
        label_audio_path = Label(root, text="오디오 경로: ", anchor="e")
        audio_file_img = PhotoImage(file=PathDict.get(PathKey.AUDIO_ICON))
        btn_audio_path = Button(root, image=audio_file_img, width=40, command=lambda: select_file(PathKey.AUDIO))
        btn_audio_path.image = audio_file_img
        entry_audio_path = Entry(root, width=50)
        entry_audio_path.insert(0, "")
        entry_audio_path.config(state="readonly")
        created_widgets = (label_audio_path, btn_audio_path, entry_audio_path)
    
    elif key == TkKey.SUB_PATH:  # 자막 파일 경로 지정 행 위젯 생성
        label_sub_path = Label(root, text="자막 경로: ", anchor="e")
        sub_file_img = PhotoImage(file=PathDict.get(PathKey.SUB_ICON))
        btn_sub_path = Button(root, image=sub_file_img, width=40, command=lambda: select_file(PathKey.SUB))
        btn_sub_path.image = sub_file_img
        entry_sub_path = Entry(root, width=50)
        entry_sub_path.insert(0, "")
        entry_sub_path.config(state="readonly")
        created_widgets =  (label_sub_path, btn_sub_path, entry_sub_path)

    elif key == TkKey.YOUTUBE_URL:  # 유튜브 링크 입력 행 위젯 생성
        label_youtube_url = Label(root, text="유튜브 링크: ", anchor="e")
        entry_youtube_url = Entry(root, width=50)
        created_widgets = (label_youtube_url, entry_youtube_url)

    elif key == TkKey.NOTEBOOK:  # 자막 정보 행 위젯 생성
        created_widgets = ttk.Notebook(root)
    TkDict.set(key, created_widgets)

    return created_widgets

def show_tk_widgets(key):  # 위젯 보이게
    widgets = TkDict.get(key)
    row_num = TkDict.get_element_size(TkKey.DISPLAYED_IN_ROOT)
    
    if key == TkKey.LOAD_TYPE:
        label_load_type, combobox_load_type, btn_play_mk_sub = widgets
        label_load_type.grid(row=row_num,column=0,columnspan=2,padx=5,sticky="nsew")
        combobox_load_type.grid(row=row_num,column=2,columnspan=3,sticky="ew")
        btn_play_mk_sub.grid(row=row_num,column=5,padx=5,sticky="nsw")

    elif key == TkKey.SAVE_PATH:
        label_save_path, btn_save_path, entry_save_path = widgets
        label_save_path.grid(row=row_num,column=0,columnspan=2,padx=5,sticky="nsew")
        btn_save_path.grid(row=row_num,column=2,sticky="nsew")
        entry_save_path.grid(row=row_num,column=3,columnspan=4,padx=5,sticky="ew")

    elif key == TkKey.AUDIO_PATH:
        label_audio_path, btn_audio_path, entry_audio_path = widgets
        label_audio_path.grid(row=row_num,column=0,columnspan=2,padx=5,sticky="nsew")
        btn_audio_path.grid(row=row_num,column=2,sticky="nsew")
        entry_audio_path.grid(row=row_num,column=3,columnspan=4,padx=5,sticky="ew")

    elif key == TkKey.SUB_PATH:
        label_sub_path, btn_sub_path, entry_sub_path = widgets
        label_sub_path.grid(row=row_num,column=0,columnspan=2,padx=5,sticky="nsew")
        btn_sub_path.grid(row=row_num,column=2,sticky="nsew")
        entry_sub_path.grid(row=row_num,column=3,columnspan=4,padx=5,sticky="ew")

    elif key == TkKey.YOUTUBE_URL:
        label_youtube_url, entry_youtube_url = widgets
        label_youtube_url.grid(row=row_num,column=0,columnspan=2,padx=5,sticky="nsew")
        entry_youtube_url.grid(row=row_num,column=2,columnspan=5,padx=5,sticky="ew")
    
    elif key == TkKey.NOTEBOOK:
        widgets.grid(row=row_num,column=0,columnspan=7,padx=5,pady=10,sticky="nsew")
    TkDict.set(TkKey.DISPLAYED_IN_ROOT, widgets)

def hide_tk_widgets(key):  # 위젯 숨기기
    widgets = TkDict.get(key)
    if key == TkKey.LOAD_TYPE:
        label_load_type, combobox_load_type, btn_play_mk_sub = widgets
        label_load_type.grid_forget()
        combobox_load_type.grid_forget()
        btn_play_mk_sub.grid_forget()

    elif key == TkKey.SAVE_PATH:
        label_save_path, btn_save_path, entry_save_path = widgets
        label_save_path.grid_forget()
        btn_save_path.grid_forget()
        entry_save_path.grid_forget()

    elif key == TkKey.AUDIO_PATH:
        label_audio_path, btn_audio_path, entry_audio_path = widgets
        label_audio_path.grid_forget()
        btn_audio_path.grid_forget()
        entry_audio_path.grid_forget()

    elif key == TkKey.SUB_PATH:
        label_sub_path, btn_sub_path, entry_sub_path = widgets
        label_sub_path.grid_forget()
        btn_sub_path.grid_forget()
        entry_sub_path.grid_forget()

    elif key == TkKey.YOUTUBE_URL:
        label_youtube_url, entry_youtube_url = widgets
        label_youtube_url.grid_forget()
        entry_youtube_url.grid_forget()
    
    elif key == TkKey.NOTEBOOK:
        widgets.grid_forget()
    TkDict.pop_element(TkKey.DISPLAYED_IN_ROOT, widgets)


########## 수정 중 ###############3
def edit_sub():  # 자막 편집 위젯 (수정 중)
        # notebook = get_tk_dict("notebook")
        # cur_tab_idx = notebook.index("current")
        # cur_listbox_idx = get_tk_dict("selected")
        
        # selected = []
        # if not isinstance(cur_listbox_idx, int):
        #     selected = [0, ]
        # else:
        #     widgets = get_tk_dict("tab", cur_tab_idx)
        #     listbox_tuple = widgets[3]

        # for listbox in listbox_tuple[1:]:
        #     selected_value = listbox.get(cur_listbox_idx)
        #     selected.append(selected_value)
        
        # entry_list = []
        # for i, value in enumerate(selected):
        #     entry_edit = Entry(tk, text=value, anchor="w")
        #     entry_edit.grid(row=5,column=i)
        #     entry_list.append(entry_edit)
        pass

def sync_scroll(listbox_tuple, scrollbar, *args):  # 리스트 박스의 스크롤을 연동
    scrollbar.set(*args)
    for listbox in listbox_tuple:
        listbox.yview_moveto(args[0])

def sync_selected(event, listbox_num, listbox_tuple):  # 리스트 박스의 원소 선택을 연동(동일한 인덱스의 다른 리스트 박스의 원소도 함께 선택)
    idx = listbox_tuple[listbox_num].curselection()
    
    for listbox in listbox_tuple:
        listbox.selection_clear(0, END)
        listbox.selection_set(idx)
    TkDict.set(TkKey.SELECTED_LISTBOX_ELEMENT, idx)

def reset_notebook():  # tkinter notebook 삭제
    notebook = TkDict.get(TkKey.NOTEBOOK)
    if notebook:
        notebook.destroy()
    TkDict.pop(TkKey.TAB)
    TkDict.pop(TkKey.NOTEBOOK)
    create_tk_widgets(TkKey.NOTEBOOK)
    show_tk_widgets(TkKey.NOTEBOOK)

def create_tab(tab_txt, label1_txt, label2_txt_list = [], sub_list = []):  # 탭 생성
    # Log.debug("탭 생성")
    # 탭 
    notebook = TkDict.get(TkKey.NOTEBOOK)
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=tab_txt)
    # saved_tabs = TkDict.get(TkKey.TAB)

    # 파일 이름 라벨 생성
    if len(label1_txt) > 35:
        label1_txt = label1_txt[:35] + "..."
    label1 = Label(tab, anchor="w",text=label1_txt)
    label1.grid(row=0,column=0,columnspan=8,sticky="ew")

    # btn_edit_sub = Button(tk, text="자막 수정", command=edit_sub)
    # btn_edit_sub.grid(row=0,column=5)
    
    # 리스트 박스 타이틀 라벨 생성
    label2_tuple = (Label(tab), Label(tab), Label(tab), Label(tab))

    if label2_txt_list:
        for i, label2 in enumerate(label2_tuple):
            cur_anchor = "center"
            if i == 3:
                cur_anchor = "w"
            label2.config(fg="black", 
                            bg="lightgray", 
                            anchor=cur_anchor, 
                            highlightbackground="gray",  # 테두리 색
                            highlightthickness=1, 
                            text=label2_txt_list[i])
            label2.grid(row=1,column=i,sticky="ew")

    # 리스트 박스 생성
    listbox1 = Listbox(tab, width=5)
    listbox2 = Listbox(tab, width=10)
    listbox3 = Listbox(tab, width=10)
    listbox4 = Listbox(tab, width=20)
    scrollbar = Scrollbar(tab)
    listbox_tuple = (listbox1, listbox2, listbox3, listbox4)

    if sub_list:
        for i, listbox in enumerate(listbox_tuple):
            listbox.config(height=25, 
                            selectmode="single", 
                            exportselection=False,
                            yscrollcommand=lambda *args, l=listbox_tuple, s=scrollbar: sync_scroll(l, s, *args))
            listbox.bind('<<ListboxSelect>>', lambda event, idx=i, l=listbox_tuple: sync_selected(event,idx,l))
            if i == 3:
                listbox.grid(row=2,column=i,columnspan=4,sticky="ew")
                continue
            listbox.grid(row=2,column=i,sticky="ew")
        scrollbar.config(command=lambda *args: [listbox.yview(*args) for listbox in listbox_tuple])
        scrollbar.grid(row=2,column=7,sticky="ns")

        listbox_max_width = TkDict.get(TkKey.LISTBOX_MAX_WIDTH)
        for sub_info in sub_list:
            for i, info in enumerate(sub_info):
                insert_str = str(info)
                if i == 0:
                    insert_str = f"{insert_str:>6}"
                elif i in [1, 2]:
                    insert_str = f"{insert_str:>13}"

                listbox_tuple[i].insert(END, insert_str)
            listbox_max_width = max(listbox_max_width, len(sub_info[-1]))
                    
        TkDict.set(TkKey.LISTBOX_MAX_WIDTH, listbox_max_width)

    new_widgets = (tab, label1, label2_tuple, listbox_tuple, scrollbar)
    TkDict.set(TkKey.TAB, new_widgets)

    return new_widgets

def show_tab():  # 탭 보이기
    # notebook = TkDict.get(TkKey.NOTEBOOK)
    # tab_widgets = TkDict.get_element(TkKey.TAB, idx)
    # if not tab_widgets:
    #     tab_widgets = create_tab(notebook)

    # tab, label1, label2_tuple, listbox_tuple, scrollbar = tab_widgets
    # notebook.add(tab)
    # notebook.tab(tab, text=tab_txt)
    # label1.config(text=label1_txt)
    # label1.grid(row=0,column=0,columnspan=4,sticky="ew")

    # if label2_txt_list:
    #     for i, label2 in enumerate(label2_tuple):
    #         label2.config(text=label2_txt_list[i])
    #         label2.grid(row=1,column=i,sticky="ew")

    # if sub_list:
    #     for i, listbox in enumerate(listbox_tuple):
    #         if i == 3:
    #             listbox.grid(row=2,column=i,columnspan=4,sticky="ew")
    #             continue
    #         listbox.grid(row=2,column=i,sticky="ew")
    #     scrollbar.grid(row=2,column=7,sticky="ns")
    
    #     listbox_max_width = TkDict.get(TkKey.LISTBOX_MAX_WIDTH)
    #     for sub_info in sub_list:
    #         for i, info in enumerate(sub_info):
    #             insert_str = str(info)
    #             if i == 0:
    #                 insert_str = f"{insert_str:>6}"
    #             elif i in [1, 2]:
    #                 insert_str = f"{insert_str:>13}"

    #             listbox_tuple[i].insert(END, insert_str)
    #         listbox_max_width = max(listbox_max_width, round(len(sub_info[-1])*1.5))
                    
    #     TkDict.set(TkKey.LISTBOX_MAX_WIDTH, listbox_max_width)
    # TkDict.set(TkKey.DISPLAYED_IN_NOTEBOOK, tab_widgets)
    pass

def hide_tab(idx):  # 탭 숨김
    # notebook = TkDict.get(TkKey.NOTEBOOK)
    # tab_widgets = TkDict.get_element(TkKey.TAB, idx)
    # if not tab_widgets:
    #     return
    # tab, label1, label2_tuple, listbox_tuple, scrollbar = tab_widgets
    # notebook.hide(idx)
    # label1.grid_forget()

    # for label2 in label2_tuple:
    #     label2.grid_forget()

    # for listbox in listbox_tuple:
    #     listbox.delete(0, END)  # 리스트 박스 원소 모두 삭제
    #     listbox.grid_forget()
    # scrollbar.grid_forget()
    
    # TkDict.pop_element(TkKey.DISPLAYED_IN_NOTEBOOK, tab_widgets)
    pass

def destroy_tab(tab): # 탭 삭제
    tab.destroy()
    TkDict.pop_element(TkKey.TAB, tab)

def set_listboxNroot_width():  # 자막 길이에 따라 리스트 박스, 전체 실행창 너비 조정
    tk = TkDict.get(TkKey.ROOT)
    max_width = TkDict.get(TkKey.LISTBOX_MAX_WIDTH)
    tabs = TkDict.get(TkKey.TAB)
    
    for widgets in tabs:
        # tab, label1, btn_edit_sub, label2_tuple, listbox_tuple, scrollbar = widgets
        tab, label1, label2_tuple, listbox_tuple, scrollbar = widgets

        for i, width in enumerate([5, 10, 10, max_width]):
            listbox_tuple[i].config(height=25,width=width)
            label2_tuple[i].config(width=width)


    w, h, x, y = TkDict.get_root_whxy()
    w = max(w, max_width + 400)
    size = (w, h, x, y)
    set_root_size(size) 

def update_tab():  # 탭 업데이트
    Log.debug("탭 업데이트 중...")
    reset_notebook()
    
    if SubDict.empty():
        create_tab("자막", "자막이 존재하지 않습니다.")

    else:
        SubDict.sort()
        
        for (ext, fname, sub_list) in SubDict.items():
            time_unit = SubDict.get(ext, SubDictKey.TIME_UNIT)
            label2_txt_list = ["NUM", f"START({time_unit})", f"END({time_unit})", "LYRIC"]
            create_tab(ext, fname, label2_txt_list, sub_list)

        set_listboxNroot_width()  # 네번째 리스트 박스 최대 길이 적용하여 전체 실행창 크기 조정
      
def init_audio():  # 오디오 파일 초기 설정(아직 미완)
    # mixer.init()

    # audio_path = PathDict.get(PathKey.AUDIO)
    # if len(audio_path) > 1:
    #     audio_path = audio_path[0]
    #     messagebox.showwarning("경고", f"해당 경로에 오디오 파일이 2개 이상 존재합니다.\n{audio_path.name} 를 오디오 파일로 사용합니다.\n만약 이 오디오 파일로 작업을 원하지 않으시면\n해당 경로에 오디오 파일을 한 개만 두십시오.")
    #     Log.warning(f"해당 경로에 오디오 파일이 여러개 존재합니다. {audio_path.name} 파일로 작업을 진행합니다.")
    
    # mixer.music.load(audio_path)
    pass

def play_audio(start_sec, end):  # 오디오 파일 실행(아직 미완)
    # tk = TkDict.get(TkKey.ROOT)
    # mixer.music.play(start=start_sec)
    # tk.after(end, mixer.music.stop)
    # update_time_label()
    pass

def create_window():  # 실행창 생성
    initDictNLog(LogLevel.DEBUG)
    tk_title = "노래방 자막 만들기"
    tk_size = (550, 600, 0, 0)
    tk = create_tk_root(tk_title, tk_size)

    create_list = (TkKey.LOAD_TYPE, TkKey.SAVE_PATH, TkKey.YOUTUBE_URL, TkKey.AUDIO_PATH, TkKey.SUB_PATH, TkKey.NOTEBOOK)
    for key in create_list:
        create_tk_widgets(key)

    show_list = (TkKey.LOAD_TYPE, TkKey.SAVE_PATH, TkKey.YOUTUBE_URL)
    for i, key in enumerate(show_list):
        show_tk_widgets(key)
    
    tk.mainloop()

def main():
    create_window()

if __name__ == "__main__":
    main()