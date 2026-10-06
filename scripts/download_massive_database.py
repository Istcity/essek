"""
Massive Historical Race Downloader and Ingestion Engine
Fetches 1,000+ real official TJK race CSVs across multiple months and cities.
Saves parsed races to data/historical_database_1000.json for backtesting and factor discovery.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

BASE_URL = "https://medya-cdn.tjk.org/raporftp/TJKPDF"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

ALL_CITIES = [
    'Bursa', 'Istanbul', 'Ankara', 'Izmir', 'Adana', 'Kocaeli', 
    'Antalya', 'Sanliurfa', 'Diyarbakir', 'Elazig'
]

GEAR_CODES = {"KG", "K", "DB", "SK", "SKG", "GKR", "ÖG", "BB", "YP", "TG", "KÖG", "OG", "KOG"}

def parse_weight(val):
    if not val or val == '-':
        return 58.0
    val_str = str(val).replace(',', '.')
    m_plus = re.match(r'^\s*(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)', val_str)
    if m_plus:
        try:
            return float(m_plus.group(1)) + float(m_plus.group(2))
        except:
            pass
    m = re.search(r'[-+]?\d+(?:\.\d+)?', val_str)
    if m:
        try:
            return float(m.group(0))
        except:
            return 58.0
    return 58.0

def parse_gear_and_clean_name(raw_name):
    clean = re.sub(r'\(?\s*ko[sş]maz\s*\)?', '', raw_name, flags=re.IGNORECASE).strip()
    tokens = clean.split()
    gear = []
    h_tokens = []
    found_horse = False
    for tok in reversed(tokens):
        u = tok.upper()
        if not found_horse and (u in GEAR_CODES or u in ["AP", "DS"]):
            if u in GEAR_CODES:
                gear.insert(0, u)
        else:
            found_horse = True
            h_tokens.insert(0, tok)
    h_name = " ".join(h_tokens).strip() if h_tokens else clean
    return h_name, " ".join(gear)

def fetch_single_csv(target):
    url, city, date_str = target
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            raw = resp.read()
            text = raw.decode('utf-8-sig', errors='replace')
            return parse_csv_content(text, city, date_str)
    except:
        return []

def parse_csv_content(csv_text, city, date_str):
    lines = [l.strip() for l in csv_text.splitlines() if l.strip()]
    races = []
    current_race = None

    for line in lines:
        cols = [c.strip() for c in line.split(';')]
        if len(cols) >= 2 and ('Kosu :' in cols[0] or 'Koşu :' in cols[0]):
            m = re.search(r'(\d+)\.\s*Ko[sş]u', cols[0])
            if m:
                race_num = int(m.group(1))
                race_time_m = re.search(r'Ko[sş]u\s*:\s*([\d.]+)', cols[0])
                race_time = race_time_m.group(1) if race_time_m else ""

                race_type = cols[1] if len(cols) > 1 else ""

                # Distance
                dist = 1400
                for c in cols:
                    dm = re.search(r'\b(\d{3,4})\s*m\b', c, re.IGNORECASE)
                    if dm:
                        dist = int(dm.group(1))
                        break

                # Surface
                surf = "Kum"
                for c in cols:
                    cl = c.lower()
                    if "sentetik" in cl or "synthetic" in cl:
                        surf = "Sentetik"
                        break
                    elif "çim" in cl or "cim" in cl or "turf" in cl:
                        surf = "Çim"
                        break
                    elif "kum" in cl or "dirt" in cl:
                        surf = "Kum"
                        break
                if not surf:
                    surf = "Kum" if any(k in city.lower() for k in ["urfa", "elazığ", "diyarbakır"]) else "Çim"

                is_maiden = "maiden" in line.lower()
                is_handicap = "handikap" in line.lower()
                is_sartli = "şartlı" in line.lower() or "sartli" in line.lower()
                is_open = "açık" in line.lower() or "acik" in line.lower() or "grup" in line.lower() or "g1" in line.lower() or "g2" in line.lower() or "g3" in line.lower() or "a2" in line.lower() or "a3" in line.lower()

                current_race = {
                    "city": city,
                    "date": date_str,
                    "race_number": race_num,
                    "time": race_time,
                    "distance": dist,
                    "surface": surf,
                    "race_type": race_type,
                    "is_maiden": is_maiden,
                    "is_handicap": is_handicap,
                    "is_sartli": is_sartli,
                    "is_open": is_open,
                    "runners": []
                }
                races.append(current_race)

        elif current_race is not None and len(cols) >= 12 and cols[0].isdigit():
            finish_pos = int(cols[0])
            raw_name = cols[1]
            h_name, equipment = parse_gear_and_clean_name(raw_name)

            age_sex = cols[2] if len(cols) > 2 else ""
            sire = cols[3] if len(cols) > 3 else ""
            dam = cols[4] if len(cols) > 4 else ""
            weight = parse_weight(cols[5]) if len(cols) > 5 else 58.0
            jockey = cols[6] if len(cols) > 6 else ""
            owner = cols[7] if len(cols) > 7 else ""
            trainer = cols[8] if len(cols) > 8 else ""

            gate = finish_pos
            try:
                gm = re.search(r'\d+', cols[9] if len(cols) > 9 else "")
                if gm:
                    gate = int(gm.group(0))
            except:
                pass

            agf_pct = 0.0
            agf_rank = 99
            agf_raw = cols[10] if len(cols) > 10 else ""
            am = re.search(r'%?(\d+(?:[.,]\d+)?)', agf_raw)
            if am:
                try:
                    agf_pct = float(am.group(1).replace(',', '.'))
                except:
                    pass
            rm = re.search(r'\((\d+)\)', agf_raw)
            if rm:
                try:
                    agf_rank = int(rm.group(1))
                except:
                    pass

            handicap = 35
            if len(cols) > 11 and cols[11].isdigit():
                handicap = int(cols[11])

            finish_time = cols[12] if len(cols) > 12 else ""

            ganyan = 0.0
            if len(cols) > 13:
                gm = re.search(r'\d+(?:[.,]\d+)?', cols[13])
                if gm:
                    try:
                        ganyan = float(gm.group(0).replace(',', '.'))
                    except:
                        pass

            last_6 = cols[14] if len(cols) > 14 else ""
            kgs = 20
            if len(cols) > 15 and cols[15].isdigit():
                kgs = int(cols[15])

            current_race["runners"].append({
                "finish_order": finish_pos,
                "name": h_name,
                "raw_name": raw_name,
                "equipment": equipment,
                "age_sex": age_sex,
                "sire": sire,
                "dam": dam,
                "weight": weight,
                "jockey": jockey,
                "trainer": trainer,
                "owner": owner,
                "gate": gate,
                "agf": agf_pct,
                "agf_rank": agf_rank,
                "handicap": handicap,
                "finish_time": finish_time,
                "ganyan": ganyan,
                "last_6": last_6,
                "kgs": kgs
            })

    return [r for r in races if len(r["runners"]) >= 4]

def download_1000_races(days_back=120):
    targets = []
    print(f"Generating URL queue for past {days_back} days across {len(ALL_CITIES)} tracks...")

    for days_ago in range(0, days_back):
        d = datetime.now() - timedelta(days=days_ago)
        date_str = d.strftime('%d.%m.%Y')
        year = d.strftime('%Y')
        formatted_date = d.strftime('%Y-%m-%d')
        for city in ALL_CITIES:
            q = urllib.parse.quote(city)
            url = f"{BASE_URL}/{year}/{formatted_date}/CSV/GunlukYarisSonuclari/{date_str}-{q}-GunlukYarisSonuclari-TR.csv"
            targets.append((url, city, date_str))

    print(f"Total candidate URLs: {len(targets)}. Starting parallel download with 24 workers...")
    all_races = []
    completed = 0

    with ThreadPoolExecutor(max_workers=24) as executor:
        futures = {executor.submit(fetch_single_csv, t): t for t in targets}
        for fut in as_completed(futures):
            completed += 1
            res = fut.result()
            if res:
                all_races.extend(res)
                if len(all_races) >= 1200:
                    print(f"Target reached: {len(all_races)} races ingested! Cancelling remaining...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

            if completed % 100 == 0:
                print(f"Scanned {completed}/{len(targets)} URLs -> Found {len(all_races)} valid races so far...")

    print(f"\n==========================================")
    print(f"TOTAL REAL TJK RACES INGESTED: {len(all_races)}")
    print(f"==========================================")

    # Save to disk
    os.makedirs('data', exist_ok=True)
    out_path = 'data/historical_database_1000.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_races, f, ensure_ascii=False)
    print(f"Saved {len(all_races)} historical races to {out_path} ({os.path.getsize(out_path) / 1024 / 1024:.2f} MB)")

    return all_races

if __name__ == "__main__":
    download_1000_races(days_back=180)
