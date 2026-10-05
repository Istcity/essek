import urllib.request, re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
req = urllib.request.Request('https://www.youtube.com/@TJKTVCANLIYAYIN', headers=headers)
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', 'ignore')

cid = re.search(r'"externalId":"(UC[a-zA-Z0-9_-]{22})"', html)
if cid:
    print('Found Channel ID:', cid.group(1))

# Also search for live streams or videos on channel
live_vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
print('Videos:', list(dict.fromkeys(live_vids))[:10])

# Check what iframe embed URLs work for YouTube live stream
# 1: https://www.youtube-nocookie.com/embed/live_stream?channel=CHANNEL_ID
# 2: https://www.youtube.com/embed/live_stream?channel=CHANNEL_ID
# 3: Direct video ID embed: https://www.youtube.com/embed/VIDEO_ID?autoplay=1
print('Live embed URL:', f'https://www.youtube.com/embed/live_stream?channel={cid.group(1)}' if cid else 'N/A')
