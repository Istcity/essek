import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://vhs-medya-cdn.ebayi.org/muhtemeller/r/js/all.min.js?v32'
req = urllib.request.Request(url, headers=headers)
try:
    js = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
    print(f"JS length: {len(js)}")
    
    # Search for ajax, getJSON, fetch, or endpoints
    calls = re.findall(r'(\$\.(?:ajax|get|getJSON|post)\([^)]+\))', js)
    print(f"Ajax calls found: {len(calls)}")
    for c in calls[:10]:
        print("  Ajax:", c[:120])
        
    urls = set(re.findall(r'["\'](/[^"\']+)["\']', js))
    paths = [u for u in urls if any(k in u.lower() for k in ['muhtemel', 'ganyan', 'data', 'api', 'json', 'race', 'kosu', 'ikili'])]
    print("Relevant paths:", paths[:15])

    # Search for keyword "ikili"
    ikili_matches = re.findall(r'.{0,60}ikili.{0,60}', js, re.I)
    print(f"Ikili matches: {len(ikili_matches)}")
    for im in ikili_matches[:5]:
        print("  Ikili snippet:", im.strip())
        
except Exception as e:
    print("Error:", e)
