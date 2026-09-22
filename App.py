from flask import Flask, render_template, request, send_file
import asyncio
import os
import re
from datetime import datetime
import tempfile

app = Flask(__name__)

VOICES = {
    "여자 SunHi (감성 리뷰)": "ko-KR-SunHiNeural",
    "남자 InJoon (담백 리뷰)": "ko-KR-InJoonNeural",
}

def sanitize(name):
    name = re.sub(r'[\\/:*?"<>|]', '_', name).strip()
    name = re.sub(r'\s+', '_', name)
    return name[:40] if name else "무제"

async def do_tts(text, voice_id, out_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice_id)
    await communicate.save(out_path)

@app.route('/')
def index():
    return render_template('index.html', voices=list(VOICES.keys()))

@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text', '').strip()
    project = request.form.get('project', '무제').strip()
    voice_display = request.form.get('voice', list(VOICES.keys())[0])
    voice_id = VOICES.get(voice_display, "ko-KR-SunHiNeural")

    if not text:
        return "대본을 입력하세요", 400

    clean = sanitize(project)
    timestamp = datetime.now().strftime("%m%d_%H%M%S")
    filename = f"{clean}_{timestamp}.mp3"

    # 임시 파일 생성
    tmpdir = tempfile.gettempdir()
    out_path = os.path.join(tmpdir, filename)

    try:
        asyncio.run(do_tts(text, voice_id, out_path))
        return send_file(out_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"오류: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
