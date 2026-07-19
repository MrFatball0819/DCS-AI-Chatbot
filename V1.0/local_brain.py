# ==========================================
# 🧠 DCS 戰術 AI 副駕駛 - 邊緣端【純語音識別】大閘 (local_brain.py)
# ==========================================
from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import io
import os

app = Flask(__name__)

# 🔒 鎖死正牌的 8核 VM 記憶體滿血優化參數
MODEL_SIZE = "small.en"

print(f"\n[Brain] 正在 8核 VM 記憶體中加載優化版 Whisper '{MODEL_SIZE}' 核心...")
# 鎖死無損 float32 精度，調用 4 執行緒，0 磁碟損耗
model = WhisperModel(MODEL_SIZE, device="cpu", cpu_threads=4, compute_type="float32")
print("[Brain] 邊緣端純聽覺大閘加載完畢！0延遲內存管道就位。")

@app.route('/whisper', methods=['POST'])
def handle_voice_stream():
    try:
        # 1. 生吞 Node.js 跨進程空投過來的純記憶體 WAV 位元組流
        wav_bytes = request.data
        if not wav_bytes:
            return jsonify({"status": "error", "message": "空音訊"}), 400

        # 🔥 0磁碟損耗：直接在記憶體中還原成檔案流 (In-Memory Stream)
        audio_file = io.BytesIO(wav_bytes)

        # 2. 純 C 語言編譯優化的 CTranslate2 一線推理，0.2秒極速出字
        segments, info = model.transcribe(audio_file, beam_size=5)
        recognized_text = "".join([segment.text for segment in segments]).strip()
        
        print(f"\n[🚀 D-1581 網關純記憶體識別大成功]: '{recognized_text}'")

        # 3. 🚀 守本分、講尊嚴：回傳全球最標準、最直白的 text 欄位給總控，絕不越權調用 LLM！
        return jsonify({
            "status": "success", 
            "text": recognized_text
        })

    except Exception as e:
        print(f"[Brain Error] 語音識別底層崩潰: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # 常駐在正牌的 5002 埠
    app.run(host='127.0.0.1', port=5002, debug=False)
