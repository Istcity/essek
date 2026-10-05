import urllib.request, re, json

# 1. Inspect TJK Tay TV / Static/Canli page
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
try:
    req = urllib.request.Request('https://www.tjk.org/TR/YarisSever/Static/Canli', headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        print("=== TJK Static/Canli ===")
        # Look for video, iframe, m3u8, embed, tay tv
        m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
        print("m3u8s:", m3u8s)
        iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html)
        print("iframes:", iframes)
        players = re.findall(r'(https?://[^\s"\'<>]*(?:taytv|tjk|stream|hls|live)[^\s"\'<>]*)', html, re.I)
        print("Stream matches:", list(set(players[:10])))
except Exception as e:
    print("Error on static/canli:", e)

# 2. Inspect Bursa 1st race
try:
    with open('frontend/data/program_Bursa.json', 'r', encoding='utf-8') as f:
        bursa = json.load(f)
    race1 = bursa['races'][0]
    print("\n=== BURSA 1. KOSU ===")
    print("Race name:", race1.get('name'), "Time:", race1.get('time'), "Distance:", race1.get('distance'), race1.get('surface'))
    for r in race1.get('runners', []):
        print(f"#{r['number']} {r['name']} | Jockey: {r.get('jockey')} | Sire: {r.get('sire')} / Dam: {r.get('dam')} | W: {r.get('weight')} | Hand: {r.get('handicap')} | Last6: {r.get('last_6')} | KGS: {r.get('kgs')} | Rank in pred: {r.get('rank')} | WinProb: {r.get('win_probability')}%")
except Exception as e:
    print("Error on Bursa json:", e)
