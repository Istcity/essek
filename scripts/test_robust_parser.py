"""
Test robust bulletin & program parser against all today's races (Bursa, Sanliurfa, etc.)
"""
import urllib.request
import urllib.parse
import re
import json

GEAR_CODES = {"KG", "K", "DB", "SK", "SKG", "GKR", "ÖG", "BB", "YP", "TG", "KÖG", "OG", "KOG"}

def parse_weight_overweight(val):
    if not val or val == '-':
        return 58.0
    val_str = str(val).replace(',', '.')
    # Check for pattern like '56 +0.70' or '56.5 +1.10'
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

def parse_horse_and_equipment(raw_name):
    """
    Parses horse name, equipment tokens, and scratched status.
    Examples:
      'ÇİLDUTAY KG DB SK' -> ('ÇİLDUTAY', 'KG DB SK', False)
      'KAYANİLİM GKR (Koşmaz)' -> ('KAYANİLİM', 'GKR', True)
      'MAMBA FOREVER KG K ÖG' -> ('MAMBA FOREVER', 'KG K ÖG', False)
      'STAIN FREE' -> ('STAIN FREE', '', False)
    """
    name_clean = raw_name.strip()
    is_scratched = bool(re.search(r'\(?\s*ko[sş]maz\s*\)?', name_clean, re.IGNORECASE))
    name_clean = re.sub(r'\(?\s*ko[sş]maz\s*\)?', '', name_clean, flags=re.IGNORECASE).strip()

    tokens = name_clean.split()
    gear_tokens = []
    horse_tokens = []

    # Process tokens from right to left
    found_horse = False
    for tok in reversed(tokens):
        u_tok = tok.upper()
        if not found_horse and (u_tok in GEAR_CODES or u_tok in ["AP", "DS"]):
            if u_tok in GEAR_CODES:
                gear_tokens.insert(0, u_tok)
        else:
            found_horse = True
            horse_tokens.insert(0, tok)

    clean_horse_name = " ".join(horse_tokens).strip() if horse_tokens else name_clean
    equipment_str = " ".join(gear_tokens)

    return clean_horse_name, equipment_str, is_scratched

def parse_agf_and_rank(agf_raw):
    """
    Parses '%53.83(1) %45.9(1)' -> agf_pct = 53.83, rank = 1
    """
    if not agf_raw:
        return 0.0, None
    m = re.search(r'%?\s*(\d+(?:[.,]\d+)?)(?:\s*\(\s*(\d+)\s*\))?', str(agf_raw))
    if m:
        agf_val = float(m.group(1).replace(',', '.'))
        rank_val = int(m.group(2)) if m.group(2) else None
        return agf_val, rank_val
    return 0.0, None

def parse_gate_and_ds(gate_raw, default_val=1):
    """
    Parses '14 - DS' -> gate = 14, outside_stall = True
    """
    if not gate_raw:
        return default_val, False
    val_str = str(gate_raw).strip()
    outside_stall = "DS" in val_str.upper()
    m = re.search(r'\d+', val_str)
    gate = int(m.group(0)) if m else default_val
    return gate, outside_stall

def test_on_city(city_name, date_str="05.10.2026"):
    parts = date_str.split('.')
    year, month, day = parts[2], parts[1], parts[0]
    fd = f"{year}-{month}-{day}"
    q = urllib.parse.quote(city_name)
    url = f"https://medya-cdn.tjk.org/raporftp/TJKPDF/{year}/{fd}/CSV/GunlukYarisProgrami/{date_str}-{q}-GunlukYarisProgrami-TR.csv"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode("utf-8-sig", errors="replace")

    races = []
    current_race = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        cols = [c.strip() for c in line.split(';')]

        if len(cols) >= 2 and ('Kosu :' in cols[0] or 'Koşu :' in cols[0]):
            m = re.search(r'(\d+)\.\s*Ko[sş]u\s*:\s*([\d.]+)', cols[0])
            race_num = int(m.group(1)) if m else len(races) + 1
            race_time = m.group(2) if m else ""

            race_type = cols[1] if len(cols) > 1 else ""

            # Robust Distance extraction: scan ALL columns for (\d{3,4})m
            distance = 1400
            for col in cols:
                dm = re.search(r'\b(\d{3,4})\s*m\b', col, re.IGNORECASE)
                if dm:
                    distance = int(dm.group(1))
                    break

            # Robust Surface extraction: scan ALL columns for Çim, Kum, Sentetik
            surface = None
            for col in cols:
                c_low = col.lower()
                if "sentetik" in c_low or "synthetic" in c_low:
                    surface = "Sentetik"
                    break
                elif "çim" in c_low or "cim" in c_low or "turf" in c_low:
                    surface = "Çim"
                    break
                elif "kum" in c_low or "dirt" in c_low:
                    surface = "Kum"
                    break

            if not surface:
                # Track fallback
                if any(k in city_name.lower() for k in ["urfa", "şanlıurfa", "elazığ", "diyarbakır"]):
                    surface = "Kum"
                else:
                    surface = "Çim"

            # Age condition
            age_condition = ""
            for col in cols:
                if any(k in col.lower() for k in ["yaşlı", "araplar", "ingilizler", "yaş"]):
                    age_condition = col
                    break

            # Record time
            record_time = ""
            for col in cols:
                if "Rekor Derece" in col:
                    rm = re.search(r'Rekor Derece\s*:\s*([\d.:]+)', col)
                    if rm:
                        record_time = rm.group(1)
                    break

            current_race = {
                "race_number": race_num,
                "time": race_time,
                "name": f"{race_num}. Koşu",
                "race_type": race_type,
                "age_group": age_condition,
                "distance": distance,
                "surface": surface,
                "record_time": record_time,
                "city": city_name,
                "runners": []
            }
            races.append(current_race)

        elif current_race is not None and len(cols) >= 12:
            if cols[0] in ['At No', 'No'] or 'İkramiye' in cols[0] or "GANYAN" in cols[0]:
                continue
            if not cols[0].isdigit():
                continue

            horse_no = int(cols[0])
            raw_name = cols[1]
            clean_name, equipment, is_scratched = parse_horse_and_equipment(raw_name)

            age = cols[2] if len(cols) > 2 else ""
            sire = cols[3] if len(cols) > 3 else ""
            dam = cols[4] if len(cols) > 4 else ""
            weight = parse_weight_overweight(cols[5]) if len(cols) > 5 else 58.0
            jockey = cols[6] if len(cols) > 6 else ""
            owner = cols[7] if len(cols) > 7 else ""
            trainer = cols[8] if len(cols) > 8 else ""
            gate, outside_stall = parse_gate_and_ds(cols[9] if len(cols) > 9 else str(horse_no), default_val=horse_no)
            agf_pct, agf_rank = parse_agf_and_rank(cols[10] if len(cols) > 10 else "")
            handicap_val = int(cols[11]) if len(cols) > 11 and cols[11].isdigit() else 35
            last_6 = cols[12] if len(cols) > 12 else ""
            kgs_val = int(cols[13]) if len(cols) > 13 and cols[13].isdigit() else 20
            s20_val = int(cols[14]) if len(cols) > 14 and cols[14].isdigit() else 15
            best_time = cols[15] if len(cols) > 15 else ""

            current_race["runners"].append({
                "number": horse_no,
                "name": clean_name,
                "raw_name": raw_name,
                "equipment": equipment,
                "is_scratched": is_scratched,
                "age": age,
                "sire": sire,
                "dam": dam,
                "weight": weight,
                "jockey": jockey,
                "owner": owner,
                "trainer": trainer,
                "gate": gate,
                "outside_stall": outside_stall,
                "agf": agf_pct,
                "agf_rank": agf_rank,
                "handicap": handicap_val,
                "last_6": last_6,
                "kgs": kgs_val,
                "s20": s20_val,
                "best_time": best_time
            })

    print(f"\n==================== {city_name} ====================")
    for r in races:
        scratched = [rn["name"] for rn in r["runners"] if rn["is_scratched"]]
        print(f"Koşu #{r['race_number']} | Saat: {r['time']} | Mesafe: {r['distance']}m | Pist: {r['surface']} | Tip: {r['race_type']} | At Sayısı: {len(r['runners'])}")
        if scratched:
            print(f"  --> Koşmaz Atlar: {scratched}")
        # Sample top 2 runners equipment and parsed info
        for rn in r["runners"][:2]:
            print(f"      #{rn['number']} {rn['name']} | Eq: '{rn['equipment']}' | Wt: {rn['weight']}kg | AGF: %{rn['agf']} (#{rn['agf_rank']})")

if __name__ == "__main__":
    test_on_city("Bursa")
    test_on_city("Sanliurfa")
