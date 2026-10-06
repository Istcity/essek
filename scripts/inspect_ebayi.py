import urllib.request
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

req = urllib.request.Request('https://ebayi.tjk.org/ganyan/muhtemeller', headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

print(f"Total HTML Length: {len(html)}")

# Find forms, action URLs, scripts
scripts = re.findall(r'<script[^>]*src=[\'"]([^\'"]+)[\'"]', html)
print("Scripts:", scripts[:5])

# Find internal API/ajax endpoints
ajax_urls = re.findall(r'[\'"]([^\'"]*(?:muhtemel|ganyan|oran|ikili|bahis|Get)[^\'"]*)[\'"]', html, re.I)
print("Interesting endpoints / keywords in page:", set(ajax_urls[:20]))

# Search for any tables or selectors in HTML
tables = re.findall(r'<table[^>]*id=[\'"]([^\'"]+)[\'"]', html)
print("Table IDs:", tables)

selects = re.findall(r'<select[^>]*id=[\'"]([^\'"]+)[\'"]', html)
print("Select IDs:", selects)

# Save a snippet of HTML to examine
with open('data/ebayi_muhtemeller_sample.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Saved data/ebayi_muhtemeller_sample.html")
