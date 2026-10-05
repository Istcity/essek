import urllib.request
import re

url = 'https://medya-cdn.tjk.org/raporftp/TJKPDF/2026/2026-10-05/CSV/GunlukYarisProgrami/05.10.2026-Bursa-GunlukYarisProgrami-TR.csv'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
raw = urllib.request.urlopen(req).read().decode('utf-8-sig', errors='replace')
lines = raw.splitlines()

print("SAMPLE RUNNERS IN BURSA:")
for l in lines:
    cols = [c.strip() for c in l.split(';')]
    if len(cols) > 10 and cols[0].isdigit():
        print(f"No: {cols[0]} | RawName: {cols[1]} | Wt: {cols[5]} | Jck: {cols[6]} | Gate: {cols[9]} | AGF: {cols[10]} | Last6: {cols[12]}")
