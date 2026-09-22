from flask import Flask, request, send_file
from flask_cors import CORS
import asyncio, os, re
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)  # ← 깃허브 페이지에서 호출 허용

VOICES = {"여자 SunHi (감성 리뷰)": "ko-KR-SunHiNeural", "남자 InJoon (담백 리뷰)": "ko-KR-InJoonNeural"}

def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
    return re.sub(r'\s+', '_', name)[:40] or "무제"

async def do_tts(text, voice_id, out_path):
    import edge_tts
    await edge_tts.Communicate(text, voice_id).save(out_path)

@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text','').strip()
    project = request.form.get('project','무제').strip()
    voice_display = request.form.get('voice','여자 SunHi (감성 리뷰)')
    voice_id = VOICES.get(voice_display, "ko-KR-SunHiNeural")
    if not text: return "대본 없음", 400
    clean = sanitize(project)
    filename = f"{clean}_{datetime.now().strftime('%m%d_%H%M')}.mp3"
    out_path = os.path.join(tempfile.gettempdir(), filename)
    asyncio.run(do_tts(text, voice_id, out_path))
    return send_file(out_path, as_attachment=True, download_name=filename)

@app.route('/')
def index():
    return "tazzangmp3 API - use /tts"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
