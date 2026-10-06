import json
import sys
from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

races = json.load(open('data/historical_database_1000.json', encoding='utf-8'))
trainers = defaultdict(lambda: {'starts': 0, 'wins': 0, 'top4': 0})
for r in races:
    for rn in r.get('runners', []):
        tr = rn.get('trainer', '').strip().lower()
        if tr:
            trainers[tr]['starts'] += 1
            if rn.get('finish_order') == 1:
                trainers[tr]['wins'] += 1
            if rn.get('finish_order', 99) <= 4:
                trainers[tr]['top4'] += 1

top_tr = [(t, s) for t, s in trainers.items() if s['starts'] >= 30]
top_tr.sort(key=lambda x: x[1]['wins'] / x[1]['starts'], reverse=True)
for t, s in top_tr[:20]:
    win_pct = round(s['wins'] / s['starts'] * 100, 1)
    top4_pct = round(s['top4'] / s['starts'] * 100, 1)
    print(f"{t[:25]:25}: Win %{win_pct:4.1f} | Top4 %{top4_pct:4.1f} ({s['starts']} starts)")
