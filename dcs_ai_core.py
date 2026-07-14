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
# 強制錨定書房桌機根目錄，徹底粉碎 PyInstaller 打包成 .exe 後相對路徑找不到設定檔的閃退硬傷
BASE_DIR = r"C:\Users\h_yue"
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
MAPPING_PATH = os.path.join(BASE_DIR, "mapping.txt")
# =================================================================

# 1. 動態讀取外部硬體與路徑設定檔 (config.ini)
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    print(f"[致命錯誤] 在 [{CONFIG_PATH}] 找不到核心設定檔 config.ini！請建立該檔案。")
    sys.exit()

config.read(CONFIG_PATH, encoding="utf-8")

try:
    TARGET_JOY_ID = config.getint("HARDWARE", "target_joy_id")
    TARGET_BTN_ID = config.getint("HARDWARE", "target_btn_id")
    OLLAMA_URL = config.get("NETWORK", "ollama_url")
    VA_PATH = config.get("PATHS", "va_path")
    
    # 讀取 VoiceAttack 字典字串並自動切割、清洗成 Python 集合
    raw_commands = config.get("COMMANDS", "va_commands")
    VOICE_ATTACK_COMMANDS = {cmd.strip() for cmd in raw_commands.split(",") if cmd.strip()}
except Exception as config_err:
    print(f"[設定檔錯誤] config.ini 格式解析崩潰，請檢查欄位: {config_err}")
    sys.exit()

# 2. 動態加載外部 Addon 詞彙庫 (mapping.txt)
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

# 初始化微軟標準遊戲硬體引擎
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() <= TARGET_JOY_ID:
    print(f"[致命錯誤] 系統未偵測到編號為 [{TARGET_JOY_ID}] 的油門手柄！請檢查 USB 插頭。")
    sys.exit()

joy = pygame.joystick.Joystick(TARGET_JOY_ID)
joy.init()
print(f"已成功對接高端油門手柄: {joy.get_name()}")

# 建立常駐硬體干擾黑名單（閹割掉 16 個背景常駐開關訊號）
pygame.event.pump()
blacklist = set()
for i in range(joy.get_numbuttons()):
    if joy.get_button(i) and i != TARGET_BTN_ID:
        blacklist.add(i)
print(f"[硬體隔離] 已成功將背景 {len(blacklist)} 個常駐開關列入黑名單，數據鏈極致純淨。")

print("正在加載書房桌機 Faster-Whisper 語音神經網路 (small.en)...")
# 鎖定 CPU 滿血 Int8 量化推論，0 驅動依賴，100% 不卡死、不掉幀
stt_model = WhisperModel("small.en", device="cpu", compute_type="int8")

print(f"\n【DCS 獨立 AI 真．不壞之身完全體數據鏈已正式通車】")
print(f"【實戰操作】: 請直接按住油門實體發話鍵 [Button {TARGET_BTN_ID}] 開始發話，放開結束錄音...")

p = pyaudio.PyAudio()
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

while True:
    try:
        pygame.event.pump()
        
        # 智慧監聽：油門 Button 8 觸發錄音
        if joy.get_button(TARGET_BTN_ID):
            print("\n[座艙無線電通話中]... 正在收集 Barracuda X 音訊流...")
            
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            
            # 軍規級去抖動防斷流晶片
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
            
            # 執行 Faster-Whisper 高精準度辨識
            segments, _ = stt_model.transcribe(wav_buffer, beam_size=5)
            pilot_text = "".join([segment.text for segment in segments]).strip()
            
            if not pilot_text:
                print("[提示] 未檢測到明確語音，請再試一次。")
                continue
                
            print(f"\n[油門發話辨識成功] -> \"{pilot_text}\"")
            
            # 標準無感清洗
            cleaned_command = pilot_text.replace(",", "").replace(".", "").replace("!", "").strip().lower()
            if "atc" in cleaned_command:
                cleaned_command = cleaned_command.replace("atc", "").strip()

            # 真．外掛詞庫動態替换
            phrase_map = load_phrase_mapping()
            for wrong, right in phrase_map.items():
                if wrong in cleaned_command:
                    cleaned_command = cleaned_command.replace(wrong, right)

            # 智慧分流軌道一：注入 VoiceAttack（升級：模糊包含算法）
            matched_va_command = None
            for va_cmd in VOICE_ATTACK_COMMANDS:
                if va_cmd.lower() in cleaned_command:
                    matched_va_command = va_cmd
                    break

            if matched_va_command:
                print(f"[智慧分流] -> 模糊匹配成功！在話語中攔截到無線電指令: \"{matched_va_command}\"")
                try:
                    subprocess.Popen([VA_PATH, "-command", matched_va_command], creationflags=subprocess.CREATE_NO_WINDOW)
                    print("[注入成功] -> 已成功喚醒 VoiceAttack 原生事件！")
                except Exception as va_err:
                    print(f"[系統警報] 執行注入失敗，請確認設定檔中的 va_path: {va_err}")
                    
            # 智慧分流軌道二：戰術對話 ➔ 跨房間高鐵甩字給客廳 4060M
            else:
                print(f"[智慧分流] -> 未命中無線電字典，判定為艙內對話，正在甩給客廳...")
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
                    else:
                        print(f"[網路警報] 客廳回應錯誤代碼: {response.status_code}")
                except Exception:
                    print("[通訊失敗] 跨房間超時，請檢查設定檔中的 ollama_url 是否存活。")
                    
        time.sleep(0.02)
        
    except KeyboardInterrupt:
        print("\n[系統提示] 原生油門數據鏈已安全斷開。")
        break
    except Exception as e:
        print(f"\n[恢復機制] 執行緒異常攔截: {e}")
        continue
