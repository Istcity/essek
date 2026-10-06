import urllib.request
import re

url = 'https://www.youtube.com/@TJKTVCANLIYAYIN/live'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        print("Found videoIds:", list(dict.fromkeys(matches))[:5])
        
        # Check canonical or og:url
        og_match = re.search(r'<meta property="og:video:url" content="https://www.youtube.com/embed/([a-zA-Z0-9_-]{11})"', html)
        if og_match:
            print("Canonical embed videoId:", og_match.group(1))
except Exception as e:
    print("Error:", e)
