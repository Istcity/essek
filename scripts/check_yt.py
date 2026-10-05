import urllib.request
import re

for ch in ['@TJKTVCANLIYAYIN', '@TAYTVCANLIYAYIN', '@tjk']:
    url = f'https://www.youtube.com/{ch}/live'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode('utf-8', errors='ignore')
            m = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', data)
            print(f'{ch}: videoIds = {m[:3]}')
    except Exception as e:
        print(f'{ch} error: {e}')
