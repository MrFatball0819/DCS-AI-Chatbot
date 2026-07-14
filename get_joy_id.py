import pygame
import time
import sys
import os
import configparser

# ==================== 【真．絕對路徑鎖定】 ====================
BASE_DIR = r"C:\Users\h_yue\DCS-AI-BOT"
CONFIG_PATH = os.path.join(BASE_DIR, "config.ini")
# =============================================================

# 1. 初始化微軟 DirectInput 遊戲硬體引擎
pygame.init()
pygame.joystick.init()

count = pygame.joystick.get_count()
if count == 0:
    print("[致命錯誤] 書房桌機沒有偵測到任何飛行搖桿或油門手柄！請檢查 USB 插頭。")
    sys.exit()

print(f"\n=== 系統目前偵測到 {count} 個飛行硬體裝置 ===")
for i in range(count):
    try:
        temp_joy = pygame.joystick.Joystick(i)
        temp_joy.init()
        print(f"裝置索引 [{i}]: {temp_joy.get_name()}")
    except Exception:
        pass

# 2. 自動去翻 config.ini 看看你鎖定了什麼硬體關鍵字
config = configparser.ConfigParser()
target_device_name = ""

if os.path.exists(CONFIG_PATH):
    try:
        config.read(CONFIG_PATH, encoding="utf-8")
        target_device_name = config.get("HARDWARE", "target_device_name").strip().lower()
        print(f"\n[設定檔讀取] 當前 config.ini 鎖定的硬體名稱關鍵字為: \"{target_device_name}\"")
    except Exception:
        print("\n[系統提示] config.ini 讀取失敗或格式不對。")

# 3. 【真．名稱自適應雷達鎖定晶片】
# 拋棄數字，直接用 config 裡的名稱去所有硬體裡撈裝置
joy = None
if target_device_name:
    for i in range(count):
        try:
            temp_joy = pygame.joystick.Joystick(i)
            temp_joy.init()
            if target_device_name in temp_joy.get_name().lower():
                joy = temp_joy
                print(f"👉 [雷達鎖定成功] 已透過名稱精準抓到目標硬體: {joy.get_name()}")
                break
        except Exception:
            pass

# 防呆機制：如果 config 裡的名字寫錯了或找不到，自動抓系統內第一個硬體頂替，絕不閃退
if joy is None:
    print(f"\n[警告] 找不到包含 \"{target_device_name}\" 的裝置。自動安全降維，鎖定索引 [0] 的硬體進行測試。")
    joy = pygame.joystick.Joystick(0)
    joy.init()

print(f"\n=== 進入硬體訊號隔離器: {joy.get_name()} ===")
print("正在自動建立背景常駐開關黑名單，請保持手放開，不要碰手柄上的任何開關...")
time.sleep(2.0)

pygame.event.pump()
blacklist = set()
for i in range(joy.get_numbuttons()):
    if joy.get_button(i):
        blacklist.add(i)

print(f"[隔離成功] 已成功穿透並封鎖 {len(blacklist)} 個背景常駐電訊干擾源！")
print("\n【現在，請按住您想要測試/更換的油門發話鍵】不要放開...")

try:
    while True:
        pygame.event.pump()
        active_buttons = []
        for i in range(joy.get_numbuttons()):
            if joy.get_button(i) and i not in blacklist:
                active_buttons.append(i)
        
        if active_buttons:
            print(f"==================================================")
            print(f"🎯 實體訊號精準穿透！")
            print(f"當前鎖定的硬體名稱 = {joy.get_name()}")
            print(f"您大拇指按住的發話鍵唯一代號 (target_btn_id) = {active_buttons}")
            print(f"==================================================")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n硬體安全掃描結束。")
