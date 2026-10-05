import urllib.request, re, json

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.tjk.org/TR/YarisSever/Info/Page/GunlukYarisSonuclari'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', 'ignore')

# Find ajax urls or query params
apis = re.findall(r'(/TR/YarisSever/[^\s"\'<>]+)', html)
print('APIs found:', list(set(apis[:25])))

# Find scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if 'ajax' in s.lower() or 'sonuc' in s.lower() or 'get' in s.lower():
        print("\n--- Script with ajax/sonuc ---")
        lines = [line.strip() for line in s.split('\n') if any(w in line.lower() for w in ['url', 'action', 'data:', 'city', 'sehir', 'kosuno', 'bursa', 'post', 'get'])]
        print('\n'.join(lines[:15]))
