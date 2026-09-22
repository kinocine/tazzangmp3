from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import asyncio, os, re
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# 한국어 + 외국어 대표
VOICES = {
    # 한국어 - 안정 2개
    "여자 SunHi (감성 리뷰) - 추천": "ko-KR-SunHiNeural",
    "남자 InJoon (담백 리뷰)": "ko-KR-InJoonNeural",
    # 한국어 - 추가 진단용
    "여자 JiMin (밝은 청년)": "ko-KR-JiMinNeural",
    "여자 SeoHyeon (차분한 낭독)": "ko-KR-SeoHyeonNeural",
    "여자 SoonBok (중년 여성)": "ko-KR-SoonBokNeural",
    "여자 YuJin (젊은 여성)": "ko-KR-YuJinNeural",
    "남자 BongJin (구수한 아저씨)": "ko-KR-BongJinNeural",
    "남자 GookMin (뉴스 앵커)": "ko-KR-GookMinNeural",
    "남자 Hyunsu (친근한 청년)": "ko-KR-HyunsuNeural",
    "남자 Hyunsu 다국어": "ko-KR-HyunsuMultilingualNeural",
    # 외국어 - 대표 3개
    "영어 Jenny (미국 여성)": "en-US-JennyNeural",
    "일본어 Nanami (일본 여성)": "ja-JP-NanamiNeural",
    "중국어 Xiaoxiao (중국 여성)": "zh-CN-XiaoxiaoNeural",
}

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
    voice_display = request.form.get('voice','여자 SunHi (감성 리뷰) - 추천')
    voice_id = VOICES.get(voice_display, voice_display)
    if voice_display.startswith("ko-KR-") or voice_display.startswith("en-") or voice_display.startswith("ja-") or voice_display.startswith("zh-"):
        voice_id = voice_display
    if not text:
        return "대본 없음", 400
    clean = sanitize(project)
    filename = f"{clean}_{datetime.now().strftime('%m%d_%H%M')}.mp3"
    out_path = os.path.join(tempfile.gettempdir(), filename)
    try:
        asyncio.run(do_tts(text, voice_id, out_path))
    except Exception as e:
        return f"TTS 실패 [{voice_id}]: {str(e)}", 500
    return send_file(out_path, as_attachment=True, download_name=filename)

@app.route('/voices', methods=['GET'])
def voices():
    async def list_all():
        import edge_tts
        all_voices = await edge_tts.list_voices()
        # 언어별 필터
        def filter_by(prefix):
            return [v for v in all_voices if v.get('ShortName','').startswith(prefix)]
        ko = filter_by('ko-KR')
        en = filter_by('en-US')
        ja = filter_by('ja-JP')
        zh = filter_by('zh-CN')
        result = []
        for display, vid in VOICES.items():
            matched = next((v for v in all_voices if v['ShortName']==vid), None)
            result.append({
                "display": display,
                "id": vid,
                "status": "✅" if matched else "❌",
                "found": bool(matched),
                "gender": matched.get('Gender','') if matched else "",
                "locale": matched.get('Locale','') if matched else ""
            })
        return {
            "server_time": datetime.now().isoformat(),
            "counts": {"ko-KR": len(ko), "en-US": len(en), "ja-JP": len(ja), "zh-CN": len(zh), "total": len(all_voices)},
            "our_mapping_check": result,
            "all_ko": [{"ShortName": v["ShortName"], "Gender": v["Gender"]} for v in ko],
            "all_en_sample": [{"ShortName": v["ShortName"]} for v in en[:10]],
            "all_ja_sample": [{"ShortName": v["ShortName"]} for v in ja[:10]],
            "all_zh_sample": [{"ShortName": v["ShortName"]} for v in zh[:10]],
        }
    try:
        data = asyncio.run(list_all())
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "tazzangmp3 API - /tts /voices"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
