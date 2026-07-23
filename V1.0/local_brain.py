from flask import Flask, request, jsonify
from faster_whisper import WhisperModel
import io
import os

app = Flask(__name__)

MODEL_SIZE = "small.en"

print(f"\n[Brain] Loading optimized Whisper '{MODEL_SIZE}' core in memory...")
model = WhisperModel(MODEL_SIZE, device="cpu", cpu_threads=4, compute_type="float32")
print("[Brain] Audio receiver gateway ready. In-memory pipeline active.")

@app.route('/whisper', methods=['POST'])
def handle_voice_stream():
    try:
        wav_bytes = request.data
        if not wav_bytes:
            return jsonify({"status": "error", "message": "Empty audio stream"}), 400

        audio_file = io.BytesIO(wav_bytes)

        # 🔒 強制鎖定英文語系，拒絕任何自作聰明的自動偵測幻聽
        segments, info = model.transcribe(audio_file, beam_size=5, language="en")
        recognized_text = "".join([segment.text for segment in segments]).strip()

        print(f"\n[🚀 Brain Out]: '{recognized_text}'")

        return jsonify({
            "status": "success", 
            "text": recognized_text
        })

    except Exception as e:
        print(f"[Brain Error] Inference breakdown: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=False)
