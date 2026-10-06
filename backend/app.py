"""
TJK AI Horse Racing Prediction Web Application Server.
Multi-threaded Python HTTP Server serving high-speed REST APIs and modern SPA frontend.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime

# Configure UTF-8 for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Adjust module path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.tjk_scraper import get_available_cities, fetch_and_predict_city_program
from backend.gallop_engine import analyze_gallops

PORT = 8080

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class TJKAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # CORS Headers for all responses
        if path.startswith("/api/"):
            self.handle_api(path, query)
        elif path.endswith(".zip") and os.path.exists(os.path.join(BASE_DIR, os.path.basename(path))):
            zip_path = os.path.join(BASE_DIR, os.path.basename(path))
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(os.path.getsize(zip_path)))
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(zip_path)}"')
            self.end_headers()
            with open(zip_path, "rb") as f:
                self.copyfile(f, self.wfile)
        else:
            # Serve frontend files
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

                # Automatically enrich with live TJK e-bayi odds & 2'li ganyanlar
                try:
                    from backend.live_odds_service import get_live_odds_for_race
                    for race in (data.get("races") or []):
                        r_num = race.get("race_number", 1)
                        runners = race.get("runners") or []
                        odds = get_live_odds_for_race(city, r_num, runners)
                        if odds and odds.get("success"):
                            race["is_live_odds"] = odds.get("is_live", False)
                            race["live_odds_source"] = odds.get("source", "TJK")
                            race["ikili_ganyanlar"] = odds.get("ikili_ganyanlar", [])
                            race["sirali_ikili_ganyanlar"] = odds.get("sirali_ikili", [])

                            g_map = {g["number"]: g["ganyan"] for g in odds.get("ganyanlar", []) if "number" in g and "ganyan" in g}
                            for runner in runners:
                                r_no = runner.get("number")
                                if r_no in g_map:
                                    runner["live_ganyan"] = g_map[r_no]
                                    runner["ganyan"] = g_map[r_no]
                except Exception as e:
                    pass

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
                    "current_time": datetime.now().isoformat(),
                    "app": "TJK AI At Yarışı Tahmin & Analiz Platformu"
                })

            elif path == "/api/tjktv":
                vid = "a5eBdWz50Mc"
                try:
                    import urllib.request, re
                    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    r = urllib.request.Request('https://www.youtube.com/@TJKTVCANLIYAYIN/live', headers=h)
                    with urllib.request.urlopen(r, timeout=4) as resp:
                        html_txt = resp.read().decode('utf-8', 'ignore')
                        m = re.search(r'<meta property="og:video:url" content="https://www.youtube.com/embed/([a-zA-Z0-9_-]{11})"', html_txt)
                        if not m:
                            m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html_txt)
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

            elif path == "/api/live-odds":
                city = query.get("city", ["Bursa"])[0]
                race_num = int(query.get("race", [1])[0])
                runners = None
                try:
                    prog = fetch_and_predict_city_program(city)
                    if prog and "races" in prog and len(prog["races"]) >= race_num:
                        runners = prog["races"][race_num - 1].get("runners", [])
                except Exception:
                    pass

                from backend.live_odds_service import get_live_odds_for_race
                odds = get_live_odds_for_race(city, race_num, runners)
                self.send_json_response(odds)

            else:
                self.send_error(404, "API endpoint not found")
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

def run_server(port=PORT):
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, TJKAppHandler)
    print(f"============================================================")
    print(f"🚀 TJK AI At Yarışı Tahmin Platformu Başlatıldı!")
    print(f"🌐 Web Arayüzü: http://localhost:{port}")
    print(f"📱 Mobil & iOS: PWA ve Standalone Destekli")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")
        httpd.server_close()

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
