import io
import wave
import subprocess
import requests
import time
import sys
import os
import configparser
import pyaudio
import pygame
from faster_whisper import WhisperModel

# ==================== 【真．絕對路徑鎖定晶片】 ====================
BASE_DIR = r"C:\Users\h_yue\DCS-AI-BOT"
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
MAPPING_PATH = os.path.join(BASE_DIR, "mapping.txt")
# =================================================================

# 1. 動態讀取設定檔 (config.ini)
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    print(f"[致命錯誤] 找不到核心設定檔 config.ini！")
    sys.exit()

config.read(CONFIG_PATH, encoding="utf-8")

try:
    TARGET_DEVICE_NAME = config.get("HARDWARE", "target_device_name").strip().lower()
    TARGET_BTN_ID = config.getint("HARDWARE", "target_btn_id")
    OLLAMA_URL = config.get("NETWORK", "ollama_url")
    VA_PATH = config.get("PATHS", "va_path")
    
    raw_prefixes = config.get("ROUTING", "radio_prefixes")
    RADIO_TARGET_PREFIXES = {prefix.strip().lower() for prefix in raw_prefixes.split(",") if prefix.strip()}
except Exception as config_err:
    print(f"[設定檔錯誤] config.ini 格式解析崩潰: {config_err}")
    sys.exit()

# 2. 動態加載外部發音修正表 (mapping.txt)
def load_phrase_mapping():
    mapping = {}
    if os.path.exists(MAPPING_PATH):
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                wrong_phrase, right_phrase = line.split("=", 1)
                mapping[wrong_phrase.strip().lower()] = right_phrase.strip().lower()
    return mapping

def find_joystick_by_name(target_name):
    pygame.joystick.quit()
    pygame.joystick.init()
    count = pygame.joystick.get_count()
    for i in range(count):
        try:
            temp_joy = pygame.joystick.Joystick(i)
            temp_joy.init()
            if target_name in temp_joy.get_name().lower():
                return temp_joy
        except Exception:
            pass
    return None

pygame.init()
joy = find_joystick_by_name(TARGET_DEVICE_NAME)

if joy is None:
    print(f"[致命錯誤] 系統內完全找不到名字包含 [{TARGET_DEVICE_NAME}] 的實體搖桿裝置！")
    sys.exit()

print(f"已成功透過【實體硬體名稱鎖】精準對接油門: {joy.get_name()}")

pygame.event.pump()
blacklist = set()
for i in range(joy.get_numbuttons()):
    if joy.get_button(i) and i != TARGET_BTN_ID:
        blacklist.add(i)
print(f"[硬體隔離] 已成功將背景 {len(blacklist)} 個常駐開關列入黑名單。")

print("正在加載書房桌機 Faster-Whisper 語音神經網路 (small.en)...")
stt_model = WhisperModel("small.en", device="cpu", compute_type="int8")

print(f"\n【DCS AI Chatbot: 真．戰術字首喀嚓完全體正式點火】")
print(f"【實戰操作】: 請直接按住油門實體發話鍵 [Button {TARGET_BTN_ID}] 開始發話...")

p = pyaudio.PyAudio()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

while True:
    try:
        pygame.event.pump()
        if joy.get_button(TARGET_BTN_ID):
            print("\n[座艙無線電通話中]... 正在收集 Barracuda X 音訊流...")
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            
            last_pressed_time = time.time()
            DEBOUNCE_DELAY = 0.5  
            
            while True:
                pygame.event.pump()
                if joy.get_button(TARGET_BTN_ID):
                    last_pressed_time = time.time()
                if time.time() - last_pressed_time > DEBOUNCE_DELAY:
                    break
                frames.append(stream.read(CHUNK))
                
            print("[錄音結束] >> 正在執行 0.2 秒神經網路語意補償轉字...")
            stream.stop_stream()
            stream.close()
            
            wav_buffer = io.BytesIO()
            wf = wave.open(wav_buffer, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            wav_buffer.seek(0)
            
            segments, _ = stt_model.transcribe(wav_buffer, beam_size=5)
            pilot_text = "".join([segment.text for segment in segments]).strip()
            if not pilot_text:
                continue
                
            print(f"\n[油門發話辨識成功] -> \"{pilot_text}\"")
            
            cleaned_command = pilot_text.replace(",", "").replace(".", "").replace("!", "").strip().lower()

            phrase_map = load_phrase_mapping()
            for wrong, right in phrase_map.items():
                if wrong in cleaned_command:
                    cleaned_command = cleaned_command.replace(wrong, right)

            # 即時重讀一次 config.ini 內的 radio_prefixes，達成熱更新
            try:
                config.read(CONFIG_PATH, encoding="utf-8")
                raw_prefixes = config.get("ROUTING", "radio_prefixes")
                active_prefixes = {prefix.strip().lower() for prefix in raw_prefixes.split(",") if prefix.strip()}
            except Exception:
                active_prefixes = RADIO_TARGET_PREFIXES
                
            is_radio_command = False
            matched_prefix = None
            
            for prefix in active_prefixes:
                if prefix in cleaned_command:
                    is_radio_command = True
                    matched_prefix = prefix
                    break

            # ─── 【智慧分流：全新戰術字首「喀嚓」晶片】 ───
            if is_radio_command:
                # 【核心破關】從字串中剔除抓到的前綴詞，並自動移除多餘空格，還原成純淨口令
                # 例如: "atc request startup" ➔ 變更為 "request startup"
                final_va_command = cleaned_command.replace(matched_prefix, "").strip()
                
                print(f"[智慧分流] -> 攔截成功！話語中包含 \"{matched_prefix}\"，已執行物理喀嚓！")
                print(f"[最終引數] -> 準備發送純淨指令: \"{final_va_command}\" 至 VoiceAttack...")
                
                try:
                    subprocess.Popen([VA_PATH, "-command", final_va_command], creationflags=subprocess.CREATE_NO_WINDOW)
                    print("[注入成功] -> 已成功喚醒 VoiceAttack 事件鏈！")
                except Exception as va_err:
                    print(f"[系統警報] 執行注入失敗: {va_err}")
                    
            else:
                print(f"[智慧分流] -> 未檢測到戰術通訊對象，判定為艙內對話，正在甩給客廳...")
                try:
                    payload = {"model": "dcs-copilot", "prompt": "[UHF_Private] " + pilot_text, "stream": False}
                    response = requests.post(OLLAMA_URL, json=payload, timeout=4)
                    if response.status_code == 200:
                        copilot_reply = response.json().get("response", "").strip()
                        safe_reply = copilot_reply.replace("'", "''").replace("\n", " ")
                        print(f"==================================================")
                        print(f"[客廳 4060M 獨立算力推論秒回] -> {copilot_reply}")
                        print(f"==================================================")
                        ps_script = f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak('{safe_reply}')"
                        subprocess.Popen(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
                        print("[音訊傳輸] -> 副駕駛語音已成功射進 Barracuda X 耳機！")
                except Exception:
                    print("[通訊失敗] 跨房間超時。")
                    
        time.sleep(0.02)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"\n[重連機制] 正在重新雷達掃描裝置...")
        time.slice(1.0)
        joy = find_joystick_by_name(TARGET_DEVICE_NAME)
        continue
