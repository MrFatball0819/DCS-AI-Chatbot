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

# ==================== 【真．絕對路徑鎖定晶片】 ====================
BASE_DIR = r"C:\Users\h_yue\DCS-AI-BOT"
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
MAPPING_PATH = os.path.join(BASE_DIR, "mapping.txt")
# =================================================================

# ─── 1. 【動態攔截晶片：決定是否鎖死 HuggingFace 網路】 ───
config_init = configparser.ConfigParser()
force_update = False
stt_model_name = "small.en"

if os.path.exists(CONFIG_PATH):
    try:
        config_init.read(CONFIG_PATH, encoding="utf-8")
        force_update = config_init.getboolean("HARDWARE", "stt_force_update", fallback=False)
        stt_model_name = config_init.get("HARDWARE", "stt_model_size", fallback="small.en")
    except Exception:
        pass

if not force_update:
    # 預設狀態：強制啟動鋼鐵離線防護，完全切斷與 Hugging Face 伺服器的啟動檢查
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

# 屏蔽遠端核心庫無意義的提示與警告雜訊
import logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# 延遲導入語音神經網路，確保環境隔離晶片優先成型
from faster_whisper import WhisperModel
# =========================================================================

# 2. 正式讀取設定檔 (config.ini)
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_PATH):
    print(f"[致命錯誤] 找不到核心設定檔 config.ini！")
    sys.exit()

config.read(CONFIG_PATH, encoding="utf-8")

try:
    TARGET_DEVICE_NAME = config.get("HARDWARE", "target_device_name").strip().lower()
    TARGET_BTN_ID = config.getint("HARDWARE", "target_btn_id")
    
    # 網路分流模式與雙軌大腦參數
    LLM_MODE = config.get("NETWORK", "llm_mode", fallback="local").strip().lower()
    OLLAMA_URL = config.get("NETWORK", "ollama_url")
    LOCAL_MODEL = config.get("NETWORK", "local_model", fallback="dcs-copilot")
    
    # 雲端分流備用參數 (OpenAI/DeepSeek 標準通用格式)
    CLOUD_API_URL = config.get("NETWORK", "cloud_api_url", fallback="https://deepseek.com")
    CLOUD_API_KEY = config.get("NETWORK", "cloud_api_key", fallback="")
    CLOUD_MODEL = config.get("NETWORK", "cloud_model", fallback="deepseek-chat")
    
    VA_PATH = config.get("PATHS", "va_path")
    
    raw_prefixes = config.get("ROUTING", "radio_prefixes")
    RADIO_TARGET_PREFIXES = {prefix.strip().lower() for prefix in raw_prefixes.split(",") if prefix.strip()}
except Exception as config_err:
    print(f"[設定檔錯誤] config.ini 格式解析崩潰: {config_err}")
    sys.exit()

# 加載外部發音修正表
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

# ─── 3. 【自適應大腦載入晶片】 ───
if force_update:
    print(f"[-] [STT 聯網維護模式]: 正在連線 Hugging Face 檢查/下載 [{stt_model_name}]...")
    stt_model = WhisperModel(stt_model_name, device="cpu", compute_type="int8", local_files_only=False)
    print("[+] 模型維護完畢！請記得在 config.ini 中將 stt_force_update 改回 False 以恢復物理單機運行。")
else:
    print(f"[-] [STT 鋼鐵單機模式]: 正在從本地快取 0 秒載入 [{stt_model_name}] 大腦 (已斷網離線)...")
    stt_model = WhisperModel(stt_model_name, device="cpu", compute_type="int8", local_files_only=True)

print(f"\n【DCS AI Chatbot: 真．戰術字首喀嚓完全體正式點火】")
print(f"【當前大腦模式】: LLM_MODE = {LLM_MODE.upper()}")
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

            # 即時重讀一次 config.ini 內部的關鍵參數，達成熱更新
            try:
                config.read(CONFIG_PATH, encoding="utf-8")
                raw_prefixes = config.get("ROUTING", "radio_prefixes")
                active_prefixes = {prefix.strip().lower() for prefix in raw_prefixes.split(",") if prefix.strip()}
                LLM_MODE = config.get("NETWORK", "llm_mode", fallback="local").strip().lower()
            except Exception:
                active_prefixes = RADIO_TARGET_PREFIXES
                
            is_radio_command = False
            matched_prefix = None
            
            for prefix in active_prefixes:
                if prefix in cleaned_command:
                    is_radio_command = True
                    matched_prefix = prefix
                    break

            # ─── 智慧分流：軌道一（全新戰術字首「喀嚓」晶片） ───
            if is_radio_command:
                final_va_command = cleaned_command.replace(matched_prefix, "").strip()
                
                print(f"[智慧分流] -> 攔截成功！話語中包含 \"{matched_prefix}\"，已執行物理喀嚓！")
                print(f"[最終引數] -> 準備發送純淨指令: \"{final_va_command}\" 至 VoiceAttack...")
                
                try:
                    subprocess.Popen([VA_PATH, "-command", final_va_command], creationflags=subprocess.CREATE_NO_WINDOW)
                    print("[注入成功] -> 已成功喚醒 VoiceAttack 事件鏈！")
                except Exception as va_err:
                    print(f"[系統警報] 執行注入失敗: {va_err}")
                    
            # ─── 智慧分流：軌道二（自適應本地/雲端雙軌私聊大腦） ───
            else:
                print(f"[智慧分流] -> 未檢測到戰術通訊對象，判定為艙內對話。")
                
                # 鋼鐵防廢話大鎖 Prompt 與 Token 限制
                system_instruction = "You are a pragmatic military fighter co-pilot in DCS World. Respond to the pilot in under 10 words. No chatter. Pure tactical response."
                max_tokens = 12
                copilot_reply = ""

                # ==== 軌道二 A：本地算力分流 (客廳 HP Victus / PVE 1070) ====
                if LLM_MODE == 'local':
                    print(f"[-] 數據包路由導向本地算力節點: {OLLAMA_URL} ({LOCAL_MODEL})")
                    payload = {
                        "model": LOCAL_MODEL,
                        "prompt": f"[UHF_Private] Pilot: {pilot_text}",
                        "stream": False
                    }
                    try:
                        response = requests.post(OLLAMA_URL, json=payload, timeout=4)
                        if response.status_code == 200:
                            copilot_reply = response.json().get("response", "").strip()
                    except Exception:
                        print("[通訊失敗] 跨房間本地連線超時。")

                # ==== 軌道二 B：雲端通用 Token API 分流 (DeepSeek / OpenRouter / OpenAI) ====
                elif LLM_MODE == 'cloud':
                    print(f"[-] 數據包路由導向雲端 Token 節點: {CLOUD_API_URL} ({CLOUD_MODEL})")
                    if not CLOUD_API_KEY or "sk-" not in CLOUD_API_KEY:
                        print("[!] 系統警報：雲端模式未配置正確的 cloud_api_key！")
                        continue
                        
                    headers = {
                        "Authorization": f"Bearer {CLOUD_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": CLOUD_MODEL,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": pilot_text}
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.2
                    }
                    try:
                        response = requests.post(CLOUD_API_URL, json=payload, headers=headers, timeout=4)
                        if response.status_code == 200:
                            copilot_reply = response.json()['choices']['message']['content'].strip()
                    except Exception as e:
                        print(f"[通訊失敗] 雲端 API 握手失敗或超時: {e}")

                # ==== 統一語音異步發射晶片 (Windows 原生 PowerShell TTS) ====
                if copilot_reply:
                    print(f"==================================================")
                    print(f"[{LLM_MODE.upper()} 大腦推論秒回] -> {copilot_reply}")
                    print(f"==================================================")
                    
                    # 進行字串清洗安全轉義，防止引號導致 PowerShell 腳本崩潰
                    safe_reply = copilot_reply.replace("'", "''").replace("\n", " ")
                    ps_script = f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak('{safe_reply}')"
                    
                    subprocess.Popen(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
                    print("[音訊傳輸] -> 副駕駛語音已成功射進 Barracuda X 耳機！")
                    
        time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n[-] 收到戰術中斷指令，DCS AI Chatbot 安全離線。")
        break
    except Exception as e:
        print(f"\n[重連機制] 正在重新雷達掃描裝置... 錯誤日誌: {e}")
        time.sleep(1.0)
        joy = find_joystick_by_name(TARGET_DEVICE_NAME)
        continue
