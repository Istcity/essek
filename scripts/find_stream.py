import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

test_urls = [
    'https://www.youtube.com/@TJKTVCANLIYAYIN/live',
    'https://www.youtube.com/channel/UCNLO4lpteIloZ4IKb9L2DoA/live',
    'https://canlitv.center/tjk-tv-canli-izle',
    'https://canlitv.mobi/tjk-tv',
    'https://canlitv.vin/tjk-tv-canli-izle'
]

for url in test_urls:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode('utf-8', 'ignore')
            final_url = resp.geturl()
            print(f"=== {url} ===")
            print(f"Final URL: {final_url}")
            
            # Look for videoId
            vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', content)
            if vids:
                print(f"Video IDs: {list(dict.fromkeys(vids))[:5]}")
            
            # Look for m3u8
            m3u8 = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', content)
            if m3u8:
                print(f"m3u8: {m3u8[:3]}")
                
            # Look for iframe
            iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', content)
            if iframes:
                print(f"iframes: {iframes[:3]}")
    except Exception as e:
        print(f"Error {url}: {e}")
