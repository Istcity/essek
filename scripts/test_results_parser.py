import urllib.request, urllib.parse, re, json
from datetime import datetime

def fetch_tjk_race_results(city_name, date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%d.%m.%Y")
        
    parts = date_str.split('.')
    if len(parts) == 3:
        year, month, day = parts[2], parts[1], parts[0]
        formatted_date = f"{year}-{month}-{day}"
    else:
        now = datetime.now()
        year, month, day = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
        formatted_date = f"{year}-{month}-{day}"
        date_str = f"{day}.{month}.{year}"
        
    quoted_city = urllib.parse.quote(city_name)
    csv_url = f"https://medya-cdn.tjk.org/raporftp/TJKPDF/{year}/{formatted_date}/CSV/GunlukYarisSonuclari/{date_str}-{quoted_city}-GunlukYarisSonuclari-TR.csv"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(csv_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode('utf-8', 'ignore')
    except Exception as e:
        print(f"Error fetching results CSV for {city_name}: {e}")
        return {}

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results_by_race = {}
    current_race_num = None
    
    for line in lines:
        cols = [c.strip() for c in line.split(';')]
        if len(cols) >= 2 and ('Kosu :' in cols[0] or 'Koşu :' in cols[0]):
            m = re.search(r'(\d+)\.\s*Ko[sş]u', cols[0])
            if m:
                current_race_num = int(m.group(1))
                results_by_race[current_race_num] = {
                    "race_number": current_race_num,
                    "standings": [],
                    "dividends": {}
                }
        elif current_race_num is not None:
            # Check if this line is a runner result
            # Format: Sıra; At İsmi; Yaş; Baba; Anne; Kilo; Jokey; Sahip; Antrenör; St; AGF; H; Derece; Ganyan; Fark
            if len(cols) >= 14 and cols[0].isdigit():
                finish_order = int(cols[0])
                horse_name = cols[1]
                weight = cols[5]
                jockey = cols[6]
                gate = cols[9]
                time_str = cols[12] if len(cols) > 12 else ""
                ganyan = cols[13] if len(cols) > 13 else ""
                margin = cols[14] if len(cols) > 14 else ""
                
                # Extract horse number from name or column if possible
                results_by_race[current_race_num]["standings"].append({
                    "order": finish_order,
                    "name": horse_name,
                    "jockey": jockey,
                    "weight": weight,
                    "time": time_str,
                    "ganyan": ganyan,
                    "margin": margin,
                    "gate": gate
                })
            elif len(cols) >= 1 and ("GANYAN" in cols[0] or "İKİLİ" in cols[0] or "PLASE" in cols[0] or "TABELA" in cols[0] or "ÇİFTE" in cols[0]):
                # Parse payout line, e.g.: GANYAN(2) :2,70 TL, İKİLİ(2/8) :11,70 TL, SIRALI İKİLİ(2/8) :20,60 TL
                payout_text = "; ".join(cols)
                payout_items = re.findall(r'([^,:]+)\s*:\s*([\d,]+)\s*TL', payout_text)
                for bet_name, prize in payout_items:
                    results_by_race[current_race_num]["dividends"][bet_name.strip()] = prize.strip() + " TL"

    return results_by_race

if __name__ == "__main__":
    res = fetch_tjk_race_results("Bursa", "05.10.2026")
    print(f"Parsed {len(res)} completed races for Bursa:")
    for rnum, rdata in res.items():
        print(f"\n--- {rnum}. Koşu Sonuçları ({len(rdata['standings'])} at) ---")
        for s in rdata['standings'][:5]:
            print(f"  {s['order']}. {s['name']} | Jok: {s['jockey']} | Derece: {s['time']} | Ganyan: {s['ganyan']} TL | Fark: {s['margin']}")
        print("  İkramiyeler:", rdata['dividends'])
