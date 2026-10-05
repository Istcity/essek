"""
Analyze historical TJK race results and calibrate multi-factor handicapping model.
Processes real official TJK race CSVs from CDN.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict

BASE_URL = "https://medya-cdn.tjk.org/raporftp/TJKPDF"

def fetch_historical_csvs(max_days=30):
    """Downloads past race day CSVs and returns parsed races."""
    races = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    cities = ['Bursa', 'Ankara', 'Adana', 'Kocaeli', 'Istanbul', 'Izmir']
    
    print(f"Scanning up to {max_days} days of TJK race results...")
    for days_ago in range(0, max_days):
        d = datetime.now() - timedelta(days=days_ago)
        date_str = d.strftime('%d.%m.%Y')
        year = d.strftime('%Y')
        formatted_date = d.strftime('%Y-%m-%d')
        
        for city in cities:
            quoted_city = urllib.parse.quote(city)
            url = f"{BASE_URL}/{year}/{formatted_date}/CSV/GunlukYarisSonuclari/{date_str}-{quoted_city}-GunlukYarisSonuclari-TR.csv"
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    text = resp.read().decode('utf-8-sig', 'ignore')
                    day_races = parse_csv_races(text, city, date_str)
                    if day_races:
                        races.extend(day_races)
            except Exception:
                pass
                
    print(f"Successfully loaded {len(races)} total historical races!")
    return races

def parse_csv_races(csv_text, city, date_str):
    lines = [l.strip() for l in csv_text.splitlines() if l.strip()]
    races = []
    current_race = None
    
    for line in lines:
        cols = [c.strip() for c in line.split(';')]
        if len(cols) >= 2 and ('Kosu :' in cols[0] or 'Koşu :' in cols[0]):
            m = re.search(r'(\d+)\.\s*Ko[sş]u', cols[0])
            if m:
                race_num = int(m.group(1))
                race_meta = cols[1] if len(cols) > 1 else ""
                
                # Extract distance and surface
                dist_m = re.search(r'(\d{3,4})m', line)
                distance = int(dist_m.group(1)) if dist_m else 1400
                
                surface = "kum"
                if "çim" in line.lower() or "cim" in line.lower():
                    surface = "çim"
                elif "sentetik" in line.lower():
                    surface = "sentetik"
                    
                is_maiden = "maiden" in line.lower()
                is_handicap = "handikap" in line.lower() or "şartlı" in line.lower() or "sartli" in line.lower()
                
                current_race = {
                    "city": city,
                    "date": date_str,
                    "race_number": race_num,
                    "distance": distance,
                    "surface": surface,
                    "is_maiden": is_maiden,
                    "is_handicap": is_handicap,
                    "runners": [],
                    "dividends": {}
                }
                races.append(current_race)
        elif current_race is not None:
            # Check runner line
            if len(cols) >= 14 and cols[0].isdigit():
                finish_order = int(cols[0])
                horse_name_raw = cols[1]
                age_sex = cols[2] if len(cols) > 2 else ""
                sire = cols[3] if len(cols) > 3 else ""
                dam = cols[4] if len(cols) > 4 else ""
                
                # Weight
                weight_str = cols[5] if len(cols) > 5 else "58"
                weight_val = 58.0
                try:
                    w_match = re.search(r'(\d+(\.\d+)?)', weight_str)
                    if w_match:
                        weight_val = float(w_match.group(1))
                except Exception:
                    pass
                    
                jockey = cols[6] if len(cols) > 6 else ""
                owner = cols[7] if len(cols) > 7 else ""
                trainer = cols[8] if len(cols) > 8 else ""
                
                # Gate / Stall
                gate = 5
                try:
                    gate_m = re.search(r'\d+', cols[9] if len(cols) > 9 else "5")
                    if gate_m:
                        gate = int(gate_m.group(0))
                except Exception:
                    pass
                    
                # AGF
                agf_pct = 0.0
                agf_rank = 99
                agf_raw = cols[10] if len(cols) > 10 else ""
                agf_pct_m = re.search(r'%?(\d+(\.\d+)?)', agf_raw)
                if agf_pct_m:
                    try:
                        agf_pct = float(agf_pct_m.group(1))
                    except Exception:
                        pass
                agf_rank_m = re.search(r'\((\d+)\)', agf_raw)
                if agf_rank_m:
                    try:
                        agf_rank = int(agf_rank_m.group(1))
                    except Exception:
                        pass
                        
                # Handikap points
                hp = 35
                try:
                    if len(cols) > 11 and cols[11].isdigit():
                        hp = int(cols[11])
                except Exception:
                    pass
                    
                time_str = cols[12] if len(cols) > 12 else ""
                
                # Ganyan
                ganyan = 0.0
                try:
                    g_str = (cols[13] if len(cols) > 13 else "").replace(',', '.')
                    g_m = re.search(r'\d+(\.\d+)?', g_str)
                    if g_m:
                        ganyan = float(g_m.group(0))
                except Exception:
                    pass
                    
                # Equipment extraction (KG, DB, SK, K, SKG, etc.)
                gear = []
                for token in ["SKG", "SK", "KG", "DB", "K", "BB", "GKR"]:
                    if f" {token}" in f" {horse_name_raw} ":
                        gear.append(token)
                        
                current_race["runners"].append({
                    "finish_order": finish_order,
                    "horse_name": horse_name_raw,
                    "gear": gear,
                    "age_sex": age_sex,
                    "sire": sire,
                    "dam": dam,
                    "weight": weight_val,
                    "jockey": jockey,
                    "is_apprentice": "AP" in jockey.upper(),
                    "trainer": trainer,
                    "owner": owner,
                    "gate": gate,
                    "agf_pct": agf_pct,
                    "agf_rank": agf_rank,
                    "handicap": hp,
                    "time_str": time_str,
                    "ganyan": ganyan
                })
    return races

def run_empirical_analysis(races):
    """Performs deep empirical statistical breakdown of Turkish horse races."""
    total_races = len(races)
    if total_races == 0:
        print("No races to analyze.")
        return {}

    # 1. AGF Rank #1 Win Rate
    agf1_wins = 0
    agf1_top2 = 0
    agf1_top4 = 0
    total_valid_agf = 0
    
    # 2. Gate (Stall) Bias by Distance
    sprint_gate_wins = defaultdict(int)
    sprint_gate_starts = defaultdict(int)
    route_gate_wins = defaultdict(int)
    route_gate_starts = defaultdict(int)
    
    # 3. Jockey Win Rates
    jockey_wins = defaultdict(int)
    jockey_starts = defaultdict(int)
    
    # 4. Trainer Win Rates
    trainer_wins = defaultdict(int)
    trainer_starts = defaultdict(int)
    
    # 5. Equipment (Gear) Impact
    gear_wins = defaultdict(int)
    gear_starts = defaultdict(int)
    
    # 6. Weight Spread Impact
    light_wins = 0 # <= 54kg
    light_starts = 0
    mid_wins = 0   # 55-58kg
    mid_starts = 0
    heavy_wins = 0 # >= 59kg
    heavy_starts = 0

    for r in races:
        runners = [x for x in r["runners"] if x.get("finish_order", 99) <= 25 and x.get("time_str") != "Koşmaz"]
        if len(runners) < 4:
            continue
            
        dist = r["distance"]
        is_sprint = dist <= 1400
        
        for runner in runners:
            order = runner["finish_order"]
            is_winner = (order == 1)
            is_top2 = (order <= 2)
            is_top4 = (order <= 4)
            
            # AGF analysis
            if runner["agf_rank"] == 1:
                total_valid_agf += 1
                if is_winner: agf1_wins += 1
                if is_top2: agf1_top2 += 1
                if is_top4: agf1_top4 += 1
                
            # Gate analysis
            g = runner["gate"]
            if 1 <= g <= 18:
                if is_sprint:
                    sprint_gate_starts[g] += 1
                    if is_winner: sprint_gate_wins[g] += 1
                else:
                    route_gate_starts[g] += 1
                    if is_winner: route_gate_wins[g] += 1
                    
            # Jockey analysis
            j = runner["jockey"].split()[0].lower() if runner["jockey"] else ""
            if j:
                jockey_starts[j] += 1
                if is_winner: jockey_wins[j] += 1
                
            # Trainer analysis
            tr = runner["trainer"].lower()
            if tr:
                trainer_starts[tr] += 1
                if is_winner: trainer_wins[tr] += 1
                
            # Gear analysis
            for g_item in runner["gear"]:
                gear_starts[g_item] += 1
                if is_winner: gear_wins[g_item] += 1
                
            # Weight analysis
            w = runner["weight"]
            if w <= 54.0:
                light_starts += 1
                if is_winner: light_wins += 1
            elif w <= 58.0:
                mid_starts += 1
                if is_winner: mid_wins += 1
            else:
                heavy_starts += 1
                if is_winner: heavy_wins += 1

    report = {
        "total_races": total_races,
        "agf1_win_pct": round((agf1_wins / max(1, total_valid_agf)) * 100, 1),
        "agf1_top2_pct": round((agf1_top2 / max(1, total_valid_agf)) * 100, 1),
        "agf1_top4_pct": round((agf1_top4 / max(1, total_valid_agf)) * 100, 1),
        "weight_strike_rates": {
            "light_lte_54kg": round((light_wins / max(1, light_starts)) * 100, 1),
            "mid_55_58kg": round((mid_wins / max(1, mid_starts)) * 100, 1),
            "heavy_gte_59kg": round((heavy_wins / max(1, heavy_starts)) * 100, 1),
        },
        "gear_strike_rates": {
            k: {"win_pct": round((gear_wins[k] / max(1, gear_starts[k])) * 100, 1), "starts": gear_starts[k]}
            for k in gear_starts if gear_starts[k] >= 10
        },
        "top_jockeys": [
            {"jockey": k, "win_pct": round((jockey_wins[k] / jockey_starts[k]) * 100, 1), "starts": jockey_starts[k]}
            for k in sorted(jockey_starts.keys(), key=lambda x: jockey_wins[x], reverse=True)[:10]
        ]
    }
    return report

if __name__ == "__main__":
    races = fetch_historical_csvs(max_days=30)
    rep = run_empirical_analysis(races)
    with open("historical_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print("Report saved successfully to historical_analysis_report.json")
    print(json.dumps(rep, indent=2, ensure_ascii=True))
