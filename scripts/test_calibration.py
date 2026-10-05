import json, math, re

def clean_name(name):
    if not name:
        return ""
    n = str(name).replace('İ', 'i').replace('I', 'i').replace('ı', 'i').lower()
    n = n.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return re.sub(r'[^a-z0-9]', '', n)

JOCKEY_RATINGS = {
    "g.kocakaya": 96, "ö.yıldırım": 95, "h.karataş": 95, "m.kaya": 92,
    "n.avci": 91, "m.çiçek": 90, "m.m.bilgin": 89, "a.sözen": 89,
    "e.aktuğ": 87, "mer.çelik": 88, "vedat.abiş": 95, "s.boyraz": 87,
    "h.çizik": 88, "f.çetin": 84, "o.yıldız": 85, "t.alıcı": 83,
    "a.meh.altın": 82, "mah.turan": 81, "u.temur": 83, "m.keçeci": 80,
    "e.kadirler": 78, "r.ketme": 76, "i.katı": 77, "a.kurşun": 92,
    "s.kaya": 94, "b.kılınç": 80, "m.s.çelik": 85, "f.yardımcı": 84
}
CLEANED_JOCKEY_RATINGS = {clean_name(k): v for k, v in JOCKEY_RATINGS.items()}

def get_surface_key(surface_text):
    s = (surface_text or "").lower()
    if "sentetik" in s or "synthetic" in s:
        return "sentetik"
    elif "kum" in s or "dirt" in s:
        return "kum"
    return "çim"

def analyze_track_affinity(last_6, target_surface):
    if not last_6:
        return 58.0, 0, 0, "Daha önce resmi koşu kaydı yok"

    surf_key = get_surface_key(target_surface)
    target_code = "Ç" if surf_key == "çim" else ("S" if surf_key == "sentetik" else "K")
    
    tokens = re.findall(r'([ÇSKçskC])(\d+)', str(last_6))
    if not tokens:
        return 58.0, 0, 0, "Koşu detayı ayrıştırılamadı"

    surface_runs = []
    all_runs = []
    for surf, pos in tokens:
        surf_char = "Ç" if surf.upper() in ["Ç", "C"] else ("S" if surf.upper() == "S" else "K")
        raw_pos = int(pos)
        finish_pos = 10 if raw_pos == 0 else raw_pos
        all_runs.append((surf_char, finish_pos))
        if surf_char == target_code:
            surface_runs.append(finish_pos)

    if not surface_runs:
        other_finishes = [p for _, p in all_runs]
        avg_other = sum(other_finishes) / len(other_finishes) if other_finishes else 6.0
        score = max(40.0, 68.0 - avg_other * 3.0)
        return score, 0, 0, f"Hedef pistte ({target_surface.capitalize()}) henüz start almadı."

    podium_count = sum(1 for p in surface_runs if 1 <= p <= 4)
    win_count = sum(1 for p in surface_runs if p == 1)
    second_count = sum(1 for p in surface_runs if p == 2)
    avg_finish = sum(surface_runs) / len(surface_runs)
    
    podium_rate = podium_count / len(surface_runs)
    top2_rate = sum(1 for p in surface_runs if p <= 2) / len(surface_runs)
    
    # Recent finish on target surface
    recent_finish = surface_runs[-1]
    recent_bonus = 8.0 if recent_finish <= 2 else (4.0 if recent_finish <= 4 else 0.0)
    
    # Consecutive top-2 finishes bonus
    streak_bonus = 0.0
    if len(surface_runs) >= 2 and all(p <= 2 for p in surface_runs[-3:]):
        streak_bonus = 8.0
    elif len(surface_runs) >= 2 and all(p <= 4 for p in surface_runs[-3:]):
        streak_bonus = 4.0

    base_score = 88.0 - (avg_finish - 1.0) * 5.0
    score = base_score + (podium_rate * 6.0) + (top2_rate * 5.0) + recent_bonus + streak_bonus + (win_count * 5.0)
    score = max(30.0, min(99.0, round(score, 1)))

    details = (
        f"{target_surface.capitalize()} pistte {len(surface_runs)} yarışta {podium_count} kez tabela."
    )
    return score, len(surface_runs), podium_count, details

def compute_surface_form(last_6, target_surface):
    if not last_6:
        return 65.0
    surf_key = get_surface_key(target_surface)
    target_code = "Ç" if surf_key == "çim" else ("S" if surf_key == "sentetik" else "K")
    tokens = re.findall(r'([ÇSKçskC])(\d+)', str(last_6))
    if not tokens:
        return 65.0
    
    surface_finishes = []
    all_finishes = []
    for s, p in tokens:
        sc = "Ç" if s.upper() in ["Ç", "C"] else ("S" if s.upper() == "S" else "K")
        raw_p = int(p)
        pos = 10 if raw_p == 0 else raw_p
        all_finishes.append(pos)
        if sc == target_code:
            surface_finishes.append(pos)

    if surface_finishes:
        # Evaluate surface form (focusing on most recent surface starts)
        recent = surface_finishes[-3:]
        avg_rec = sum(recent) / len(recent)
        form = 92.0 - (avg_rec - 1.0) * 5.0
        if surface_finishes[-1] <= 2:
            form += 7.0
        elif surface_finishes[-1] <= 4:
            form += 3.5
        if len(surface_finishes) >= 2 and all(p <= 2 for p in recent):
            form += 5.0
        return max(40.0, min(99.0, round(form, 1)))
    else:
        avg_all = sum(all_finishes) / len(all_finishes) if all_finishes else 6.0
        return max(40.0, 70.0 - avg_all * 3.0)

with open('data/program_Bursa.json', 'r', encoding='utf-8') as f:
    bursa_data = json.load(f)

race = bursa_data['races'][0]
surface = race.get('surface', 'Çim')
distance = race.get('distance', 1400)
is_maiden = "maiden" in (race.get('race_type', '') + race.get('name', '')).lower()

tested_runners = []
for r in race['runners']:
    l6 = r.get('last_6', '')
    w = r.get('weight', 57.0)
    h = r.get('handicap', 30)
    jockey = r.get('jockey', '')
    
    # 1. Jockey synergy
    cj = clean_name(jockey)
    base_j = 80.0
    for k, val in CLEANED_JOCKEY_RATINGS.items():
        if k in cj or cj in k:
            base_j = float(val)
            break
    
    if is_maiden and base_j >= 86:
        base_j += 3.0
    
    # 2. Surface affinity
    surf_sc, s_runs, p_runs, details = analyze_track_affinity(l6, surface)
    
    # 3. Form score on target surface
    form_sc = compute_surface_form(l6, surface)
    
    # 4. Speed & Time analysis
    bt = r.get('best_time')
    weight_diff = w - 57.0
    if is_maiden:
        class_bonus = 2.5 if w >= 59.0 else 0.0
    else:
        class_bonus = 0.0
        
    if bt and len(bt) >= 5:
        time_sc = 84.0 + class_bonus
    else:
        if is_maiden:
            perf_tier = max(0.0, min(1.0, (h - 18) / 20.0))
            time_sc = 77.0 + (perf_tier * 9.0) + class_bonus
        else:
            perf_tier = max(0.0, min(1.0, (h - 20) / 75.0))
            time_sc = 70.0 + (perf_tier * 15.0)

    # 5. Gallops
    ga = r.get('gallop_analysis', {}).get('gallop_score', 72.0)
    
    # 6. Pedigree
    pa = r.get('pedigree_analysis', {}).get('score', 75.0)

    # Composite rating with calibrated weights
    composite = (
        (surf_sc * 0.25) +
        (form_sc * 0.22) +
        (base_j * 0.18) +
        (time_sc * 0.15) +
        (ga * 0.12) +
        (pa * 0.08)
    )
    
    tested_runners.append({
        "number": r['number'],
        "name": r['name'],
        "jockey": jockey,
        "weight": w,
        "handicap": h,
        "last_6": l6,
        "surf_score": surf_sc,
        "form_score": form_sc,
        "jockey_score": base_j,
        "time_score": round(time_sc, 1),
        "gallop_score": ga,
        "composite": round(composite, 2)
    })

tested_runners.sort(key=lambda x: x['composite'], reverse=True)

ratings = [x['composite'] for x in tested_runners]
max_r = max(ratings)
temp = 3.5
exp_r = [math.exp((x - max_r) / temp) for x in ratings]
sum_e = sum(exp_r)

print("="*95)
print(f"{'RANK':4s} | {'NUM':3s} | {'NAME':18s} | {'JOCKEY':12s} | {'KG':4s} | {'PROB':6s} | {'COMP':6s} | {'SURF':5s} | {'FORM':5s} | {'JOCK':5s} | {'LAST 6':15s}")
print("="*95)
for i, tr in enumerate(tested_runners):
    prob = (exp_r[i] / sum_e) * 100.0
    print(f"#{i+1:2d}  | #{tr['number']:2d} | {tr['name'][:18]:18s} | {tr['jockey'][:12]:12s} | {tr['weight']:4.1f} | {prob:5.1f}% | {tr['composite']:6.2f} | {tr['surf_score']:5.1f} | {tr['form_score']:5.1f} | {tr['jockey_score']:5.1f} | {tr['last_6']:15s}")
