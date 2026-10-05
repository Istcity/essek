import urllib.request
import re

for url in ['https://www.tjk.org/TR/YarisSever/Static/Canli', 'https://ebayi.org/canli-yayin']:
    print(f"=== {url} ===")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
            print("Found m3u8:", m3u8s)
            iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            print("Found iframes:", iframes)
    except Exception as e:
        print("Error:", e)
