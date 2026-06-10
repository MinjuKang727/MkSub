# 필요 라이브러리: ffmpeg, yt-dlp, moviepy, pygame
import json
import xml.etree.ElementTree as ET
import webvtt
import yt_dlp
from yt_dlp import YoutubeDL
from moviepy import VideoFileClip, AudioFileClip, TextClip, ColorClip, CompositeVideoClip
from tkinter import filedialog, messagebox, ttk
from tkinter import *
from pygame import mixer
import logging
from pathlib import Path, WindowsPath
from glob import glob
import re


log = None

title = ""
auto_subs_ext_list = []
sub_lang = ""
path_dict = {}
sub_dict = {}
tk_dict = {}

# 경로 딕셔너리 초기화
def init_path_dict():
    global path_dict

    log.info("경로 딕셔너리를 초기화합니다.")
    path_dict = dict()

# 경로 딕셔너리 값 가져오기
def get_path_dict(key=""):
    global path_dict

    if key == "":
        return path_dict
    elif key in path_dict:
        return path_dict[key]
    else:
        return False

# 경로 딕셔너리 값 추가
def set_path_dict(key, value):
    global path_dict
    
    if key in path_dict:
        if isinstance(path_dict[key], list):
            path_dict[key].append(value)
        elif key in ("save_path", "audio_path"):
            path_dict[key] = value
        else:
            temp = path_dict[key]
            path_dict[key] = [temp, value]
    else:
        path_dict[key] = value
    
# 자막 딕셔너리 초기화
def init_sub_dict():
    log.info("자막 딕셔너리를 초기화 합니다.")
    global sub_dict

    sub_dict = dict()


# 자막 정보가 저장된 json 파일에서 자막 정보를 불러오기    
def get_sub_dict(keys=("", "")): 
    global sub_dict
    key1, key2 = keys
    save_path = get_path_dict("save_path")

    if keys.count("") == 2:
        if len(sub_dict) > 0 :
            return sub_dict

        sub_dict_path = Path(save_path) / "sub_dict.json"

        if Path(sub_dict_path).exists() and sub_dict_path.stat().st_size != 0 :
            try:
                with open(sub_dict_path, "r", encoding="utf-8") as f:
                    sub_dict = json.load(f)
            except Exception as e:
                log.warning("자막 정보 json 파일 읽기 실패, 에러 원인: %s", e)
                sub_dict= dict()

        return sub_dict
    elif key1 in sub_dict and key2 in sub_dict[key1]:
        return sub_dict[key1][key2]

    return False

def set_sub_dict(key1, key2, value):
    sub_dict = get_sub_dict()

    if key1 in sub_dict:
        sub_dict[key1][key2] = value
    else:
        sub_dict[key1] = dict()
        sub_dict[key1][key2] = value

def init_sub_info():
    exist_sub = False
    ext_list = [("json3", "ms"), ("srt", "ms"), ("srv1", "ms"), ("srv2", "ms"), ("srv3", "ms"), ("ttml", "ms"), ("vtt", "ms")]
    for ext, time_unit in ext_list:
        temp = get_path_dict(ext)

        if isinstance(temp, WindowsPath):
            sub_path_list = [Path(str(temp))]
        elif isinstance(temp, list):
            sub_path_list = temp
            
        if not sub_path_list:
            return exist_sub

        set_sub_dict(ext, "time_unit", time_unit)
        cur_sub_exist = False
        for sub_path in sub_path_list:
            
            sub_path = Path(str(sub_path))
            if get_sub_dict((ext, sub_path.stem)):
                exist_sub = True
                continue
            
            if ext == "json3":
                cur_sub_exist = get_json3_sub_dict(sub_path, ext)
            elif ext == "srt":
                cur_sub_exist = get_srt_sub_dict(sub_path, ext)
            elif ext == "srv1":
                cur_sub_exist = get_srv1_sub_dict(sub_path, ext)
            elif ext == "srv2":
                cur_sub_exist = get_srv2_sub_dict(sub_path, ext)
            elif ext == "srv3":
                cur_sub_exist = get_srv3_sub_dict(sub_path, ext)
            elif ext == "ttml":
                cur_sub_exist = get_ttml_sub_dict(sub_path, ext)
            elif ext == "vt":
                cur_sub_exist = get_vtt_sub_dict(sub_path, ext)

            if not exist_sub:
                exist_sub = exist_sub or cur_sub_exist
        if cur_sub_exist:        
            sub_dict_path = get_path_dict("sub_dict_path")
            sub_dict = get_sub_dict()
            try:
                with open(sub_dict_path, "w", encoding="utf-8") as f:
                    json.dump(sub_dict, f, ensure_ascii=False, indent=4)
            except Exception as e:
                log.error("자막 정보 json 파일에 쓰기 실패, 에러 원인: %s", e)

    return exist_sub

## 로그 기록 ##
def initLog():
    global log
    #로그 생성
    log = logging.getLogger("MkSub")

    #로그의 레벨
    log.setLevel(logging.INFO)

    # log 출력 형식
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    # log를 파일에 출력
    file_handler = logging.FileHandler("MkSub.log")
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    log.info("MkSub 파일을 실행합니다.")

# 유튜브 링크로 유튜브 정보 가져오기
def init_youtube_info(load_type=False):
    log.info("유튜브 정보를 가져옵니다.")
    save_path = get_path_dict("save_path")
    video_url = get_path_dict("video_url")
    youtube_info_path = Path(save_path) / "youtube_info.json"

    if load_type:
        if youtube_info_path.exists() and youtube_info_path.stat().st_size != 0 :
            try: 
                with open(youtube_info_path, "r", encoding="utf-8") as f:
                    youtube_info = json.load(f)
    
                return youtube_info
            
            except Exception as e:
                log.error("유튜브 정보 json 파일 읽기 실패, 에러 원인: %s", e)
        elif not video_url:
            log.warning("해당 경로에 유튜브 정보가 존재하지 않습니다.")
        return None

    init_opts = {
        'quiet': True,
        'skip_download': True,
    }
    ydl = yt_dlp.YoutubeDL(init_opts)
    youtube_info = ydl.extract_info(video_url, download=False)  # Keys: id, title, formats, thumbnails, thumbnail, description, channel_id, channel_url, duration, view_count, average_rating, age_limit, webpage_url, categories, tags, playable_in_embed, live_status, media_type, release_timestamp, _format_sort_fields, automatic_captions, subtitles, comment_count, chapters, heatmap, like_count, channel, channel_follower_count, creators, uploader, uploader_id, uploader_url, upload_date, timestamp, availability, original_url, webpage_url_basename, webpage_url_domain, extractor, extractor_key, playlist, playlist_index, display_id, fulltitle, duration_string, release_year, is_live, was_live, requested_subtitles, _has_drm, epoch, asr, filesize, format_id, format_note, source_preference, fps, audio_channels, height, quality, has_drm, tbr, filesize_approx, width, language, language_preference, preference, ext, vcodec, acodec, dynamic_range, container, url, available_at, downloader_options, protocol, audio_ext, video_ext, vbr, abr, resolution, aspect_ratio, http_headers, format
    title = youtube_info.get('title', "제목 없는 파일")
        
    # 저장 폴더 생성
    folder_name = re.sub(r'[\/:*?"<>|\s]', '_', title)
    folder_name = re.sub(r'_{2,}', "_", folder_name)
    save_path = Path(save_path) / folder_name
    save_path.mkdir(parents=True, exist_ok=True)
    set_path_dict("save_path", save_path)

    try:
        with open(youtube_info_path, "w", encoding="utf-8") as f:
            f.dumps(youtube_info, ensure_ascii=False)
    except Exception as e:
        log.error("유튜브 정보 json 파일 쓰기 실패, 에러 원인: %s", e)

    return youtube_info


# 유튜브 링크로 자막 다운로드
def download_subtitle(youtube_info) :
    log.info("유튜브 자막을 다운로드합니다.")

    save_path = get_path_dict("save_path")
    video_url = get_path_dict("video_url")
    exist_sub = False
    if video_url:
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
            ydl.download([video_url])
            set_path_dict(ext, sub_path)
            if not exist_sub:
                exist_sub = True

    elif youtube_info is None:
        exist_sub = find_sub()
        if not exist_sub:
            log.warning("해당 경로 내에 자막 파일이 존재하지 않습니다.")
            return exist_sub
    else:
        log.warning("유튜브 링크가 존재하지 않습니다.")
        return exist_sub
    
    exist_sub = init_sub_info()
    return exist_sub


# 유튜브 링크로 오디오 다운로드
def download_audio():
    log.info("유튜브 음원을 다운로드합니다.")
    
    save_path = get_path_dict("save_path")
    video_url = get_path_dict("video_url")
    exist_audio = False
    if not video_url:
        pattern = re.compile(r'\.(mp3|wav|m4a|ogg|wma)$', re.IGNORECASE)

        for audio_path in Path(save_path).iterdir() :
            if pattern.search(audio_path.name) :
                set_path_dict("audio_path", audio_path)
                exist_audio = True
                return exist_audio
        if not exist_audio:
            pattern = re.compile(r"\.(mp4|avi|mov|mkv|wmv|flv|webm|ogv|gif)$", re.IGNORECASE)
            for video_path in Path(save_path).iterdir() :
                if pattern.search(audio_path.name) :
                    video = VideoFileClip(video_path)
                    audio_path = Path(save_path) / f"{video_path.stem}.mp3"
                    video.audio.write_audiofile(audio_path)
                    set_path_dict("audio_path", audio_path)
                    exist_audio = True
                    return exist_audio

    else:
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
        ydl.download([video_url])

        audio_path = f"{audio_download_opts["outtmpl"]}.mp3"
        set_path_dict("audio_path", audio_path)

        if not exist_audio:
            exist_audio = True
    
    return exist_audio


# ms 단위의 시간을 srt 또는 vtt 형식의 문자열로 변환
def convert2str_time(ms, sep="."):
    h, remainder = divmod(ms, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, ms = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"

# hh:mm:ss,ms 형식의 문자열을 ms 단위의 정수로 변환
def convert2ms(t):
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


# 매개변수로 받은 데이터로 자막 정보 리스트 반환
# 매개변수의 start와 dur의 단위: ms
# time_unit은 반환하는 시간 단위
def get_subtitle(start, dur, text, time_unit="ms"):
    if time_unit.lower() == "ms":
        start_time = start
        end_time = start + dur
    elif time_unit.lower() == "srt" :
        start_time = convert2str_time(start, "srt")
        end_time = convert2str_time(start + dur, "srt")
    elif time_unit.lower() == "s" :
        start_time = float(start) / 1000
        end_time = float(start + dur) / 1000
    elif time_unit.lower() == "vtt":
        start_time = convert2str_time(start, "vtt")
        end_time = convert2str_time(start + dur, "vtt")

    return [start_time, end_time, text]

def find_sub():
    save_path = get_path_dict("save_path")
    exist_sub = False
    pattern = re.compile(r'\.(json3|srt|srv1|srv2|srv3|ttml|vtt)$', re.IGNORECASE)
    for path in Path(save_path).iterdir() :
        if pattern.search(path.name) :
            sub_path = path
            sub_suffix = sub_path.suffix[1:]
            set_path_dict(sub_suffix, sub_path)

            if not exist_sub:
                exist_sub = True
    
    return exist_sub


def get_all_tag_options(srv_path):
    tree = ET.parse(srv_path)
    root = tree.getroot()
    all_tags = set([element.tag for element in root.iter()])  # 형식: {'transcript', 'text'}

    all_tag_options = dict()
    for tag_name in all_tags:
        for element in root.findall(f".//{tag_name}") :
            all_tag_options[tag_name] = set(element.attrib.keys())  # 형식: {'text': {'dur', 'start'}}

    return (root, all_tag_options)


# 자막 전처리
def get_srv1_sub_dict(sub_path, ext):
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

        set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    return subtitle_list


def get_srv2_sub_dict(sub_path, ext):
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
            
        set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    return subtitle_list


def get_srv3_sub_dict(sub_path, ext):
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
    
    set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    return subtitle_list


def get_json3_sub_dict(sub_path, ext):
    exist_sub = False
    subtitle_list = list()

    json_sub = {}
    try :
        with open(sub_path, "r", encoding="utf-8") as f:
            json_sub = json.load(f)
    except Exception as e:
        log.error("json3 자막 파일 읽기 실패, 에러 원인: %s", e)
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
    
    set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_srt_sub_dict(sub_path, ext):
    exist_sub = False
    subtitle_list = list()

    try :
        with open(sub_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log.error("srt 자막 파일 읽기 실패, 에러 원인: %s", e)
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
    set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub

def get_ttml_sub_dict(sub_path, ext):
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
        set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub


def get_vtt_sub_dict(sub_path, ext):
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
    set_sub_dict(ext, sub_path.stem, subtitle_list)
    
    if len(subtitle_list) > 0:
        exist_sub = True

    return exist_sub


# # whisper 자막 데이터 불러오기
# def get_whisper_sub_list(save_path):
#     whisper_sub_path = Path(save_path) / "audio.json"

#     try:
#         with open(whisper_sub_path, "r", encoding="utf-8") as f:
#             whisper_json = json.load(f)
#     except Exception as e:
#         log.error("whisper 자막 데이터 읽기 실패, 에러 원인: %s", e)
#     print(whisper_json["segments"])
#     whisper_subs_list = [[sub["start"], sub["end"] - sub["start"], sub["text"]] for sub in whisper_json["segments"]]
#     return whisper_subs_list

# # 비디오 만들 때, 사용하는 TextClip 반환 메서드
# def get_sub_clip(txt, start, duration, v_position, h_position="left"):
#     global font_path

#     # TextClip 설정 (한글 사용 시 폰트 경로 지정 필수)
#     return TextClip(
#         font_path,  # 한글 폰트 (고딕 A1)
#         text = txt,
#         font_size=24,
#         color='white',
#         method='label'
#     ).with_start(start).with_duration(duration).with_position(h_position, v_position)

# # 비디오 만들어서 저장
# # subtitles : [[start, dur, text], ...]
# def save_video(save_path, subtitles):
#     # 1. 오디오 파일 불러오기
#     audio_path = Path(save_path) / "audio.mp3"
#     audio_clip = AudioFileClip(audio_path)

#     # 2. 자막을 영상에 입히는 함수
    

#     # 3. 배경 이미지/영상 클립 생성
#     # (여기서는 검은색 화면을 오디오 길이에 맞춰 생성)
#     background_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=audio_clip.duration)

#     # 4. .srt 파일 파싱 및 자막 클립 생성 (간단한 예시)
#     # 실제 프로젝트에서는 pysrt 라이브러리 등을 사용해 .srt 파일을 읽어오는 것을 권장합니다.
#     # position = ["top", "center", "bottom"]
#     # cur = -1
#     # for key, value in caption_dict.items():
#     #     cur += 1
#     #     cur_position = position[cur]
#     #     subtitle_clips = []
#     #     for caption in value["caption_list"]:
#     #             subtitle_clips.append(make_subtitle_clip(caption["text"], caption["start"], caption["dur"], cur_position, "left"))
#     #     caption_dict[key]["subtitle_clips"] = subtitle_clips

#     subtitle_clips = []
#     for start, dur, text in subtitles:
#         sub_clip = get_sub_clip(text, start, dur, "bottom", "left")
#         subtitle_clips.append(sub_clip)

#     # 5. 배경 + 자막 병합
#     video_clip = CompositeVideoClip([background_clip, *subtitle_clips])

#     # 6. 영상에 오디오 적용 및 최종
#     video_path = f'{save_path}/whisper_sub_apply.mp4'
#     final_video = video_clip.with_audio(audio_clip)
#     final_video.write_videofile(
#         video_path,
#         fps=24,
#         codec='libx264',
#         audio_codec='aac'
#     )

#     # 클립 종료
#     audio_clip.close()
#     final_video.close()

# # 비디오 혹은 오디오 + 자막 HTML로 표시
# def display_video_and_sub_by_html(video_path, sub_path):
#     # 1. 자막(HTML) 객체 생성 및 표시
#     video_html = HTML(f"""
#     <video autoplay muted loop playsinline width="640" controls>
#     <source src="{video_path}" type="video/mp4">
#     <track src="{sub_path}" kind="subtitles" srclang="ko" label="한국어" default>
#     지원하지 않는 브라우저입니다.
#     </video>
#     """)
#     display(video_html)

# # 정해진 구간 재생(시간 단위, 초)
# def display_ranged_audio(audio_path, start, end):
#     audio_html = HTML(f"""
#     <audio controls>
#         <source src="{audio_path}#t={start},{end}" type="audio/mpeg">
#         지원하지 않는 브라우저입니다.
#     </audio>
#     """)
#     display(audio_html)



## GUI ##
def create_window():
    
    global path_dict
    # 현재 파일이 위치한 디렉토리 경로 (절대 경로)
    current_dir = Path(__file__).parent.absolute()
    save_path = current_dir
    font_path = Path(save_path) / "font/GothicA1-Black.ttf"
    folder_icon_path = Path(save_path) / "images/folder_icon.png"
    set_path_dict("save_path", save_path)
    set_path_dict("font_path", font_path)
    set_path_dict("folder_icon_path", folder_icon_path)
    
    def select_folder():
        # 폴더 선택 대화상자 호출
        save_path = filedialog.askdirectory(initialdir=str(current_dir))
        
        if save_path:
            set_path_dict("save_path", save_path)
            # 선택한 경로를 활용한 추가 작업 수행
            entry_save_path.config(state="normal")
            entry_save_path.delete(0,"end")
            entry_save_path.insert(0, save_path)
            entry_save_path.config(state="readonly")


    def get_video_url():
        init_path_dict()
        init_sub_dict()
        url = entry_video_url.get()
        save_path = entry_save_path.get()
        set_path_dict("save_path", save_path)
        sub_dict_path = Path(save_path) / "sub_dict.json"
        set_path_dict("sub_dict_path", sub_dict_path)

        if url.startswith("https://youtu.be/") :
            return get_video_id_with_startswith("https://youtu.be/", url)
        elif url.startswith("https://www.youtube.com/watch?v="):
            return get_video_id_with_startswith("https://www.youtube.com/watch?v=", url)
        elif url.startswith("https://www.youtube.com/embed/"):
            return get_video_id_with_startswith("https://www.youtube.com/embed/", url)
        
        load_type = get_by_video_url.get()
        return  load_type or False

    def get_video_id_with_startswith(start_url, url):
        video_id = url[len(start_url):].split("?")[0].split("&")[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        entry_video_url.delete(0,"end")
        entry_video_url.insert(0, video_url)
        set_path_dict("video_url", video_url)
        
        return True

    def download_youtube():
        load_type = get_by_video_url.get()
        youtube_info = init_youtube_info(load_type)
        exist_sub = download_subtitle(youtube_info)
        exist_audio = download_audio()
        if not exist_sub and exist_audio:
            messagebox.showarning("경고", "해당 경로 내에 자막 파일 및 오디오 파일이 존재하지 않습니다.")
        elif not exist_sub:
            messagebox.showwarning("경고", "해당 경로 내에 자막 파일이 존재하지 않습니다.")
        elif not exist_audio:
            messagebox.showwarning("경고", "해당 경로 내에 오디오 파일이 존재하지 않습니다.")
        else:
            log.info("유튜브 다운로드 완료")
        update_sub()
    

    def init_tk_dict():
        global tk_dict

        if len(tk_dict) > 0 and "notebook" in tk_dict:
            tk_dict["notebook"].destroy()
        tk_dict = dict()

        return tk_dict
            

    def get_tk_dict(key="", idx = -999):
        global tk_dict

        if key == "":
            return tk_dict

        elif key in tk_dict:
            if key == "notebook":
                return tk_dict[key]
            
            key_list = tk_dict[key]
            if idx == -999:
                return key_list
            elif idx in range(len(key_list) * (-1), len(key_list)):
                return key_list[idx]
        
        return False

    def set_tk_dict(key, value):
        tk_dict = get_tk_dict()
        idx = -1

        if key in ("notebook", "selected"):
            tk_dict[key] = value
        elif key in tk_dict:
            idx = len(tk_dict[key])
            tk_dict[key].append(value)
        else:
            tk_dict[key] = [value]
            idx = 0

        return idx
        
        
    def init_notebook():
        init_tk_dict()
        notebook = ttk.Notebook(tk)
        notebook.grid(row=3,column=0,columnspan=4,pady=10,sticky="nsew")
        set_tk_dict("notebook", notebook)


    # 리스트 박스의 스크롤을 연동합니다.
    def sync_scroll(listbox_tuple, scrollbar, *args):
        scrollbar.set(*args)
        for listbox in listbox_tuple:
            listbox.yview_moveto(args[0])

    def sync_selected(event, listbox_num, listbox_tuple):
        idx = listbox_tuple[listbox_num].curselection()
        
        for listbox in listbox_tuple:
            listbox.selection_clear(0, END)
            listbox.selection_set(idx)
        set_tk_dict("selected", idx)


    # def edit_sub():
    #         notebook = get_tk_dict("notebook")
    #         cur_tab_idx = notebook.index("current")
    #         cur_listbox_idx = get_tk_dict("selected")
            
    #         selected = []
    #         if not isinstance(cur_listbox_idx, int):
    #             selected = [0, ]
    #         else:
    #             widgets = get_tk_dict("tab", cur_tab_idx)
    #             listbox_tuple = widgets[3]

    #         for listbox in listbox_tuple[1:]:
    #             selected_value = listbox.get(cur_listbox_idx)
    #             selected.append(selected_value)
            
    #         entry_list = []
    #         for i, value in enumerate(selected):
    #             entry_edit = Entry(tk, text=value, anchor="w")
    #             entry_edit.grid(row=5,column=i)
    #             entry_list.append(entry_edit)


            # return

    def create_tab(tab_txt, label1_txt, label2_txt_list, widgets_hidden=(False, False, False, False)):
        # 탭 
        notebook = get_tk_dict("notebook")
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=tab_txt)
        saved_tabs = get_tk_dict("tab")

        if not saved_tabs:
            idx = 0
        else:
            idx = len(saved_tabs)
        if widgets_hidden[0]:
            notebook.hide(idx)

        # 파일 이름 라벨 생성
        label1 = Label(tab, text=label1_txt, anchor="w")
        
        if widgets_hidden[1]:
            label1.grid_forget()
        else:
            label1.grid(row=0,column=0,columnspan=4,sticky="ew")

        # btn_edit_sub = Button(tk, text="자막 수정", command=edit_sub)
        # btn_edit_sub.grid(row=0,column=5)
        
        # 리스트 박스 타이틀 라벨 생성
        label2_tuple = (Label(tab), Label(tab), Label(tab), Label(tab))
        if widgets_hidden[2]:
            for label2 in label2_tuple:
                label2.grid_forget()
        else:
            for i, label2 in enumerate(label2_tuple):
                cur_anchor = "center"
                if i == 3:
                    cur_anchor = "w"
                label2.config(text=label2_txt_list[i], 
                              fg="black", 
                              bg="lightgray", 
                              anchor=cur_anchor, 
                              highlightbackground="gray",  # 테두리 색
                              highlightthickness=1)
                label2.grid(row=1,column=i,sticky="ew")

        # 리스트 박스 생성
        listbox1 = Listbox(tab, width=5)
        listbox2 = Listbox(tab, width=10)
        listbox3 = Listbox(tab, width=10)
        listbox4 = Listbox(tab, width=20)
        scrollbar = Scrollbar(tab)
        listbox_tuple = (listbox1, listbox2, listbox3, listbox4)

        for i, listbox in enumerate(listbox_tuple):
            listbox.config(height=25, 
                           selectmode="single", 
                           exportselection=False,
                           yscrollcommand=lambda *args, l=listbox_tuple, s=scrollbar: sync_scroll(l, s, *args))
            listbox.bind('<<ListboxSelect>>', lambda event, idx=i, l=listbox_tuple: sync_selected(event,idx,l))
        scrollbar.config(command=lambda *args: [listbox.yview(*args) for listbox in listbox_tuple])

        if widgets_hidden[3]:
            for listbox in listbox_tuple:
                listbox.grid_forget()
            scrollbar.forget()
        else:
            for i, listbox in enumerate(listbox_tuple):
                if i == 3:
                    listbox.grid(row=2,column=i,columnspan=4,sticky="ew")
                    continue
                listbox.config()
                listbox.grid(row=2,column=i,sticky="ew")
            scrollbar.grid(row=2,column=7,sticky="ns")
        
        
        # new_widgets = (tab, label1, btn_edit_sub, label2_tuple, listbox_tuple, scrollbar)
        new_widgets = (tab, label1, label2_tuple, listbox_tuple, scrollbar)
        set_tk_dict("tab", new_widgets)

        return new_widgets

    def update_sub():
        init_notebook()
        sub_dict = get_sub_dict()

        if len(sub_dict) == 0:
            create_tab("자막", "자막이 존재하지 않습니다.", [""] * 4, (False, False, True, True))
        else:
            sorted(sub_dict.keys())
            max_sub_len = 20
            for ext, ext_dict in sub_dict.items():
                for fname, sub_list in ext_dict.items():
                    if fname == "time_unit":
                        continue
                    label1_txt = f"{fname}.{ext}"
                    label2_txt_list = ["NUM", f"START({get_sub_dict((ext,"time_unit"))})", f"END({get_sub_dict((ext,"time_unit"))})", "LYRIC"]
                    widgets = create_tab(ext, label1_txt, label2_txt_list)
                    listbox_tuple = widgets[3]
                    
                    for sub_info in sub_list:
                        for i, info in enumerate(sub_info):
                            insert_str = str(info)
                            if i == 0:
                                insert_str = f"{insert_str:>6}"
                            elif i in [1, 2]:
                                insert_str = f"{insert_str:>13}"

                            listbox_tuple[i].insert(END, insert_str)
                        max_sub_len = max(max_sub_len, round(len(sub_info[-1])*1.5))
                        
            tabs = get_tk_dict("tab")
            
            for widgets in tabs:
                tab, label1, btn_edit_sub, label2_tuple, listbox_tuple, scrollbar = widgets

                for i, width in enumerate([5, 10, 10, max_sub_len]):
                    listbox_tuple[i].config(height=25,width=width)
                    label2_tuple[i].config(width=width)
            tk.geometry(f"{max_sub_len*7 + 245}x800+0+0")

    # def init_audio():
    #     mixer.init()

    #     audio_path = get_path_dict("audio_path")
    #     if len(audio_path) > 1:
    #         audio_path = audio_path[0]
    #         messagebox.showwarning("경고", f"해당 경로에 오디오 파일이 2개 이상 존재합니다.\n{audio_path.name} 를 오디오 파일로 사용합니다.\n만약 이 오디오 파일로 작업을 원하지 않으시면\n해당 경로에 오디오 파일을 한 개만 두십시오.")
    #         log.warning(f"해당 경로에 오디오 파일이 여러개 존재합니다. {audio_path.name} 파일로 작업을 진행합니다.")
        
    #     mixer.music.load(audio_path)

    # def play_audio(start_sec, end):
    #     mixer.music.play(start=start_sec)
    #     tk.after(end, mixer.music.stop)
    #     update_time_label()
        
                

    # GUI 창 생성
    tk = Tk()
    tk.title("노래방 자막 만들기")
    tk.geometry("600x800+0+0")

    # 폴더 선택 버튼 생성
    label_get_sub_method = Label(tk, text="자막 가져오는 방법: ", anchor="e", font=("GothicA1-Black", 10, "bold"), fg="white", bg="black")  # font: (글꼴, 글자 크기, 스타일), fg: 글자색, bg: 글자 배경색
    label_get_sub_method.grid(row=0,column=0,sticky="nsew")
    get_by_video_url = BooleanVar(value=False)
    radio_save_path = Radiobutton(tk, text="저장 경로", anchor="w", value=True, variable=get_by_video_url)
    radio_save_path.grid(row=0,column=1,columnspan=2,sticky="w")
    radio_video_url = Radiobutton(tk, text="유튜브 링크", anchor="w", value=False, variable=get_by_video_url)
    radio_video_url.grid(row=0,column=3,columnspan=2,sticky="w")

    label_select_save_path = Label(tk, text="저장 경로: ", anchor="e", font=("GothicA1-Black", 10, "bold"), fg="black", bg="gold")
    label_select_save_path.grid(row=1,column=0,sticky="nsew")
    folder_img = PhotoImage(file=get_path_dict("folder_icon_path"))
    btn_select_save_path = Button(tk, image=folder_img, width=5, command=select_folder)
    btn_select_save_path.grid(row=1,column=1,padx=5,sticky="nsew")
    entry_save_path = Entry(tk, width=50)
    entry_save_path.insert(0, str(current_dir))
    entry_save_path.config(state="readonly")
    entry_save_path.grid(row=1,column=2,columnspan=4,sticky="nsew")
    

    label_video_url = Label(tk, text="유튜브 링크: ", anchor="e", font=("GothicA1-Black", 10, "bold"), fg="white", bg="red")
    label_video_url.grid(row=2,column=0,sticky="nsew")
    btn_download = Button(tk, text="실행",width=5, command=lambda: download_youtube() if get_video_url() else messagebox.showwarning("경고", "유튜브 링크를 먼저 입력해 주십시오."))
    btn_download.grid(row=2,column=1,padx=5,sticky="nsew")
    entry_video_url = Entry(tk, width=50)
    entry_video_url.grid(row=2,column=2,columnspan=4,sticky="nsew")
    

    
    tk.mainloop()

def main():
    initLog()
    create_window()

if __name__ == "__main__":
    main()