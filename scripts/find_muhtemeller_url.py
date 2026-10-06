import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

test_urls = [
    'https://www.tjk.org/TR/YarisSever/Info/Page/MuhtemelGanyanlar',
    'https://www.tjk.org/TR/YarisSever/Info/Muhtemeller',
    'https://www.tjk.org/TR/YarisSever/Muhtemeller',
    'https://www.tjk.org/TR/YarisSever/Info/Page/Muhtemel',
    'https://medya-cdn.tjk.org/muhtemel/',
    'https://www.tjk.org/TR/YarisSever/Info/GetMuhtemelGanyanlar',
    'https://ebayi.tjk.org/ganyan/muhtemeller',
]

for url in test_urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"SUCCESS {resp.status}: {url} (Length: {len(resp.read())})")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {url}")
    except Exception as e:
        print(f"ERR: {url} -> {e}")
