import urllib.request
import json
import re

req = urllib.request.Request('https://vhs-medya-cdn.ebayi.org/muhtemeller/r/contents/970bcbab.json', headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode('utf-8'))
p = data['data']['templates']['pages']['probables']
js_code = p.get('js', '')
print("Probables JS length:", len(js_code))

with open('data/probables_page.js', 'w', encoding='utf-8') as f:
    f.write(js_code)

# Search for URLs and ajax endpoints
urls = re.findall(r'["\']([^"\']*(?:api|ashx|json|get|data|muhtemel|odds|vhs|race|program|ganyan|ikili)[^"\']*)["\']', js_code, re.I)
print("Endpoints in probables js:")
for u in set(urls):
    print("  ->", u)
