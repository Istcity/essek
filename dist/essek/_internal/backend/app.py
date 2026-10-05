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
