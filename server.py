"""
Penyuluh Agama Islam AI - Backend Server
Jalankan: python server.py
"""

import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

# ── Konfigurasi ──────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"
MYQURAN_BASE      = "https://api.myquran.com/v2"

SYSTEM_PROMPT = """Kamu adalah Asisten Penyuluh Agama Islam yang berilmu, bijaksana, dan ramah. Nama kamu "Penyuluh AI".

PANDUAN UTAMA:
- Selalu berpedoman pada Al-Qur'an dan Sunnah yang shahih
- Cantumkan dalil Arab disertai terjemahan Indonesia
- Gunakan bahasa Indonesia yang sopan dan mudah dipahami masyarakat umum
- Untuk masalah fiqih, sebutkan pendapat mazhab mu'tabar (Hanafi, Maliki, Syafi'i, Hanbali) jika ada perbedaan
- Akhiri jawaban dengan nasihat praktis yang bisa langsung diterapkan
- Jika menyangkut fatwa kompleks, anjurkan konsultasi ke ulama setempat

FORMAT JAWABAN:
- Ayat Al-Qur'an: "Allah ﷻ berfirman dalam QS [Surah]:[Ayat]:" lalu teks Arab, lalu terjemahan
- Hadits: "Rasulullah ﷺ bersabda (HR [Perawi]):" lalu teks Arab, lalu terjemahan
- Gunakan ﷻ setelah Allah dan ﷺ setelah Nabi Muhammad
"""

# ── Route utama: sajikan frontend ────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# ── Proxy ke Anthropic API ───────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY belum diset. Lihat README.md"}), 500

    data = request.get_json()
    messages  = data.get("messages", [])
    topic     = data.get("topic", "")

    # Tambahkan konteks topik ke pesan terakhir jika ada
    if topic and messages:
        last = messages[-1]
        messages[-1] = {
            "role": last["role"],
            "content": f"[Topik: {topic}] {last['content']}"
        }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    try:
        resp = requests.post(ANTHROPIC_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        text = result["content"][0]["text"]
        return jsonify({"reply": text})
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout. Coba lagi."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"API error: {e.response.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Proxy ke myQuran API (hindari CORS) ──────────────────
@app.route("/api/quran/<path:subpath>")
def proxy_quran(subpath):
    url = f"{MYQURAN_BASE}/{subpath}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return jsonify(r.json()), r.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "myQuran API timeout. Coba lagi."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Tidak dapat terhubung ke myQuran API. Cek koneksi internet."}), 503
    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"myQuran API error: {e.response.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("\n⚠️  PERINGATAN: ANTHROPIC_API_KEY belum diset!")
        print("   Jalankan: export ANTHROPIC_API_KEY=sk-ant-xxxx\n")
    else:
        print(f"\n✅ API Key ditemukan: {ANTHROPIC_API_KEY[:20]}...")
    print("🕌 Server Penyuluh AI berjalan di http://localhost:5000\n")
    app.run(debug=False, port=5000)
