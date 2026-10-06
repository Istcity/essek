import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request('https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisProgrami', headers=headers)
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')

matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
print(f"Total links: {len(matches)}")
found = set()
for href, text in matches:
    clean_t = re.sub(r'<[^>]+>', '', text).strip()
    if any(k in clean_t.lower() or k in href.lower() for k in ['ganyan', 'muhtemel', 'oran', 'ikili', 'bahis']):
        if (clean_t, href) not in found:
            print(f"{clean_t} -> {href}")
            found.add((clean_t, href))
