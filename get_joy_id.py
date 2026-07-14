import pygame
import time
import sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("[警報] 未偵測到硬體！")
    sys.exit()

# 鎖定您的搖桿編號: 2
joy = pygame.joystick.Joystick(2)
joy.init()

print(f"=== 已成功鎖定高端裝置: {joy.get_name()} ===")
print("正在自動掃描並建立背景常駐按鍵黑名單，請保持手放開，不要碰任何按鍵...")
time.sleep(1.5)

pygame.event.pump()
blacklist = set()
for i in range(joy.get_numbuttons()):
    if joy.get_button(i):
        blacklist.add(i)

print(f"[黑名單建立成功] 已成功過濾 {len(blacklist)} 個背景常駐硬體干擾源！")
print("\n【現在，請按住您的油門發話鍵不要放開】...")

try:
    while True:
        pygame.event.pump()
        active_buttons = []
        for i in range(joy.get_numbuttons()):
            if joy.get_button(i) and i not in blacklist:
                active_buttons.append(i)
        
        if active_buttons:
            print(f"==================================================")
            print(f"🎯 成功穿透干擾！")
            print(f"【您的實體油門發話鍵唯一的 Button ID 是: {active_buttons[0]}】")
            print(f"==================================================")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n掃描結束。")
