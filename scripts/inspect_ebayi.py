import urllib.request, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
url = 'https://ebayi.org/canli-yayin'
try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        print("Page length:", len(html))
        m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
        print("m3u8s:", m3u8s)
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        print("iframes:", iframes)
        # Search for any player or stream keywords
        matches = re.findall(r'https?://[^\s"\'<>]*(?:taytv|tjk|stream|live|m3u8|embed|hls)[^\s"\'<>]*', html, re.I)
        print("stream matches:", list(set(matches[:15])))
        
        # Look around video or player
        for kw in ['video', 'player', 'iframe', 'taytv', 'tjktv', 'canli']:
            idx = html.lower().find(kw)
            if idx != -1:
                print(f"\n--- Found '{kw}' around {idx} ---")
                print(html[max(0, idx-100):min(len(html), idx+200)])
except Exception as e:
    print("Error:", e)
