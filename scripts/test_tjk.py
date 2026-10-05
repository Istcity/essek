import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
}

req = urllib.request.Request('https://www.youtube.com/@TJKTVCANLIYAYIN/live', headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', 'ignore')
    final_url = resp.geturl()
    print("Final URL:", final_url)
    
    # 1. Check if redirected to watch?v=VIDEO_ID
    watch_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', final_url)
    if watch_match:
        print("Redirected to video ID:", watch_match.group(1))
    
    # 2. Check canonical
    can = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if can:
        print("Canonical:", can.group(1))
        
    # 3. Check liveStreamabilityRenderer
    m = re.search(r'"liveStreamabilityRenderer":\{"videoId":"([a-zA-Z0-9_-]{11})"', html)
    if m:
        print("liveStreamabilityRenderer videoId:", m.group(1))
        
    # 4. Check videoId
    vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
    print("Top video IDs found:", list(dict.fromkeys(vids))[:5])
