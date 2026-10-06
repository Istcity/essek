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
import subprocess
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

from backend.tjk_scraper import get_available_cities, fetch_and_predict_city_program, fetch_tjk_race_results
from backend.gallop_engine import analyze_gallops
from backend.live_odds_service import get_live_odds_for_race

def create_desktop_shortcut():
    """Create Windows Desktop shortcut (.lnk) automatically on user's desktop."""
    if sys.platform != "win32":
        return None
    try:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        if not os.path.exists(desktop_dir):
            return None

        shortcut_path = os.path.join(desktop_dir, "TJK AI At Yarışı Tahmin Platformu.lnk")

        if getattr(sys, 'frozen', False):
            target_exe = sys.executable
        else:
            cand = os.path.join(BASE_DIR, "dist", "TJK_RACING_AI_PRO_v2.exe")
            target_exe = cand if os.path.exists(cand) else sys.executable

        work_dir = os.path.dirname(target_exe)

        ps_commands = [
            '$WshShell = New-Object -ComObject WScript.Shell',
            f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')",
            f"$Shortcut.TargetPath = '{target_exe}'",
            f"$Shortcut.WorkingDirectory = '{work_dir}'",
            "$Shortcut.Description = 'TJK AI At Yarışı Tahmin ve Analiz Platformu PRO v2.0'",
            f"$Shortcut.IconLocation = '{target_exe},0'",
            '$Shortcut.Save()'
        ]
        full_ps = "; ".join(ps_commands)
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full_ps], capture_output=True, timeout=5)
        if os.path.exists(shortcut_path):
            return shortcut_path
    except Exception:
        pass
    return None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class TJKAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api(path, query)

        # Handle direct EXE download
        elif path.endswith(".exe") or path == "/download/exe":
            exe_candidates = [
                os.path.join(BASE_DIR, "dist", "TJK_RACING_AI_PRO_v2.exe"),
                os.path.join(FRONTEND_DIR, "dist", "TJK_RACING_AI_PRO_v2.exe"),
                os.path.join(BASE_DIR, "TJK_RACING_AI_PRO_v2.exe"),
                os.path.join(FRONTEND_DIR, "TJK_RACING_AI_PRO_v2.exe"),
            ]
            for exe_path in exe_candidates:
                if os.path.exists(exe_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(os.path.getsize(exe_path)))
                    self.send_header("Content-Disposition", 'attachment; filename="TJK_RACING_AI_PRO_v2.exe"')
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(exe_path, "rb") as f:
                        self.copyfile(f, self.wfile)
                    return
            self.send_error(404, "EXE File Not Found")

        # Handle direct ZIP download
        elif path.endswith(".zip") or path == "/download/zip":
            zip_candidates = [
                os.path.join(BASE_DIR, "TJK_RACING_AI_PRO_v2.zip"),
                os.path.join(FRONTEND_DIR, "TJK_RACING_AI_PRO_v2.zip"),
            ]
            for zip_path in zip_candidates:
                if os.path.exists(zip_path):
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Length", str(os.path.getsize(zip_path)))
                    self.send_header("Content-Disposition", 'attachment; filename="TJK_RACING_AI_PRO_v2.zip"')
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    with open(zip_path, "rb") as f:
                        self.copyfile(f, self.wfile)
                    return
            self.send_error(404, "ZIP File Not Found")

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

                # Automatically enrich with live TJK e-bayi odds & 2'li ganyanlar
                try:
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

            elif path == "/api/results":
                city = query.get("city", ["Bursa"])[0]
                date_str = query.get("date", [None])[0]
                results = fetch_tjk_race_results(city, date_str)
                self.send_json_response({"success": True, "city": city, "results": results})

            elif path == "/api/gallops":
                horse = query.get("horse", ["Şampiyon"])[0]
                rating = int(query.get("rating", [40])[0])
                analysis = analyze_gallops(horse, None, rating)
                self.send_json_response({"success": True, "horse": horse, "analysis": analysis})

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

                odds = get_live_odds_for_race(city, race_num, runners)
                self.send_json_response(odds)

            elif path == "/api/create-shortcut":
                s_path = create_desktop_shortcut()
                if s_path:
                    self.send_json_response({
                        "success": True, 
                        "message": "Masaüstünüze 'TJK AI At Yarışı Tahmin Platformu' kısayolu başarıyla eklendi!",
                        "path": s_path
                    })
                else:
                    self.send_json_response({
                        "success": False, 
                        "message": "Kısayol oluşturulamadı."
                    }, status=500)

            elif path == "/api/status":
                self.send_json_response({
                    "status": "online",
                    "version": "2.0.0-PRO",
                    "app": "essek - TJK At Yarışı Tahmin Platformu"
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
            else:
                self.send_error(404, "Endpoint Not Found")
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
        pass

def find_available_port(start_port=8080, max_attempts=20):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def open_browser_delayed(url, delay=1.0):
    time.sleep(delay)
    if sys.platform == "win32":
        # 1. Try launching Edge in dedicated App Mode (native desktop window!)
        edge_candidates = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            "msedge"
        ]
        for ep in edge_candidates:
            try:
                if os.path.exists(ep) or ep == "msedge":
                    subprocess.Popen([ep, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
            except Exception:
                pass

        # 2. Try Chrome in dedicated App Mode
        chrome_candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            "chrome"
        ]
        for cp in chrome_candidates:
            try:
                if os.path.exists(cp) or cp == "chrome":
                    subprocess.Popen([cp, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
            except Exception:
                pass

    # 3. Fallback to default browser
    try:
        webbrowser.open(url, new=2, autoraise=True)
    except Exception:
        try:
            if sys.platform == "win32":
                os.system(f'start "" "{url}"')
        except Exception:
            pass

def main():
    # 1. Automatically create Desktop Shortcut for the user
    s_path = create_desktop_shortcut()

    port = find_available_port(8080)
    server_address = ("127.0.0.1", port)
    app_url = f"http://localhost:{port}"

    print("=" * 68)
    print("  🏇 TJK AT YARIŞI YAPAY ZEKA TAHMİN & ANALİZ PLATFORMU v2.0-PRO")
    print("=" * 68)
    if s_path:
        print(f"[*] ✅ Masaüstü Kısayolu Eklendi: {s_path}")
    print(f"[*] Uygulama adresi: {app_url}")
    print("[*] Masaüstü penceresi ve tarayıcı otomatik açılıyor...")
    print("[*] Uygulamayı kapatmak istediğinizde bu pencereyi kapatmanız yeterlidir.")
    print("=" * 68)

    # Launch application window automatically
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
