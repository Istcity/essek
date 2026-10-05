"""
essek - TJK At Yarışı Tahmin ve Analiz Platformu
Ana Çalıştırılabilir Dosya (Standalone Executable Entry Point)
"""

import os
import sys
import json
import socket
import webbrowser
import threading
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Determine base dir & frontend dir (supporting PyInstaller MEIPASS bundle)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
    FRONTEND_DIR = os.path.join(sys._MEIPASS, "frontend")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.tjk_scraper import get_available_cities, fetch_and_predict_city_program
from backend.gallop_engine import analyze_gallops

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class TJKAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api(path, query)
        else:
            if path == "/" or path == "":
                self.path = "/index.html"
            return super().do_GET()

    def handle_api(self, path, query):
        try:
            if path == "/api/cities":
                date_str = query.get("date", [None])[0]
                cities = get_available_cities(date_str)
                self.send_json_response({"success": True, "cities": cities, "count": len(cities)})

            elif path == "/api/program":
                city = query.get("city", ["Bursa"])[0]
                date_str = query.get("date", [None])[0]
                data = fetch_and_predict_city_program(city, date_str)
                self.send_json_response({"success": True, "data": data})

            elif path == "/api/gallops":
                horse = query.get("horse", ["Şampiyon"])[0]
                rating = int(query.get("rating", [40])[0])
                analysis = analyze_gallops(horse, None, rating)
                self.send_json_response({"success": True, "horse": horse, "analysis": analysis})

            elif path == "/api/status":
                self.send_json_response({
                    "status": "online",
                    "version": "2.0.0-PRO",
                    "app": "essek - TJK At Yarışı Tahmin Platformu"
                })

            elif path == "/api/tjktv":
                vid = "hnZK5wXzQDk"
                try:
                    import urllib.request, re
                    h = {'User-Agent': 'Mozilla/5.0'}
                    r = urllib.request.Request('https://www.youtube.com/@TJKTVCANLIYAYIN/live', headers=h)
                    with urllib.request.urlopen(r, timeout=4) as resp:
                        m = re.search(r'"liveStreamabilityRenderer":\{"videoId":"([a-zA-Z0-9_-]{11})"', resp.read().decode('utf-8', 'ignore'))
                        if m:
                            vid = m.group(1)
                except Exception:
                    pass

                self.send_json_response({
                    "success": True,
                    "video_id": vid,
                    "embed_url": f"https://www.youtube.com/embed/{vid}?autoplay=1",
                    "live_url": "https://www.youtube.com/@TJKTVCANLIYAYIN/live",
                    "tjk_web_url": "https://www.tjk.org/TR/YarisSever/CanliYayin/TjkTv"
                })
            else:
                self.send_error(404, "Endpoint bulunamadı")
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)}, status=500)

    def send_json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging in terminal
        pass

def find_available_port(start_port=8080, max_attempts=20):
    """Finds an open port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def open_browser_delayed(url, delay=1.2):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    port = find_available_port(8080)
    server_address = ("127.0.0.1", port)
    app_url = f"http://localhost:{port}"

    print("=" * 65)
    print("  🏇 ESSEK - TJK AT YARIŞI YAPAY ZEKA TAHMİN PLATFORMU v2.0")
    print("=" * 65)
    print(f"[*] Sunucu başlatıldı: {app_url}")
    print(f"[*] Tarayıcı otomatik açılıyor...")
    print(f"[*] Uygulamayı kapatmak için bu pencereyi kapatabilirsiniz.")
    print("=" * 65)

    # Launch browser automatically in a separate daemon thread
    browser_thread = threading.Thread(target=open_browser_delayed, args=(app_url,), daemon=True)
    browser_thread.start()

    httpd = ThreadedHTTPServer(server_address, TJKAppHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nUygulama sonlandırılıyor...")
        httpd.server_close()

if __name__ == "__main__":
    main()
