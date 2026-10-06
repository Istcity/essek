"""
Benchmark and validate Engine v5.0 (18-Factor Deep Empirical Engine)
on 1,207 real official TJK races.
"""

import sys
import os
import json
import math
import re
from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

# Load empirical tables
with open('data/empirical_tables_1000.json', 'r', encoding='utf-8') as f:
    tables = json.load(f)

EMPIRICAL_TRAINERS = tables.get('trainers', {})
EMPIRICAL_JOCKEYS = tables.get('jockeys', {})
EMPIRICAL_SIRES = tables.get('sires', {})

def clean_key(name):
    if not name:
        return ""
    n = str(name).replace('İ', 'i').replace('I', 'i').replace('ı', 'i').lower()
    n = n.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return re.sub(r'[^a-z0-9]', '', n)

CLEAN_TRAINERS = {clean_key(k): v for k, v in EMPIRICAL_TRAINERS.items()}
CLEAN_JOCKEYS = {clean_key(k): v for k, v in EMPIRICAL_JOCKEYS.items()}
CLEAN_SIRES = {clean_key(k): v for k, v in EMPIRICAL_SIRES.items()}

# Surface speed offset
SURFACE_OFFSET_PER_100M = {
    "çim": 0.0, "cim": 0.0, "turf": 0.0,
    "sentetik": 0.085, "synthetic": 0.085,
    "kum": 0.195, "dirt": 0.195
}

GEAR_MODIFIERS = {
    "GKR": -4.5,
    "YP":  -5.5,
    "BB":  -2.0,
    "SKG": -0.8,
    "ÖG":  +2.5,
    "OG":  +2.5,
    "K":   +1.5,
    "DB":  +1.2,
    "SK":  +1.0,
    "KG":  +0.5
}

GATE_BIAS_SPRINT = {1: +3.0, 2: +2.5, 3: +2.0, 4: +1.5, 5: +0.5, 6: 0.0,
                    7: -1.0, 8: -1.5, 9: -2.5, 10: -3.0, 11: -3.5, 12: -4.0,
                    13: -4.5, 14: -5.0, 15: -5.5, 16: -6.0}
GATE_BIAS_ROUTE  = {1: +1.2, 2: +1.2, 3: +1.5, 4: +1.8, 5: +1.5, 6: +1.2,
                    7: +0.5, 8: 0.0, 9: -0.5, 10: -1.0, 11: -1.5, 12: -2.0,
                    13: -2.5, 14: -3.0, 15: -3.5, 16: -4.0}

def parse_time_str(time_str):
    if not time_str:
        return None
    s = str(time_str).strip().replace(',', '.')
    m = re.match(r'(?:(\d+)[:.])?(\d+)[:.](\d+)', s)
    if m:
        min_p = int(m.group(1)) if m.group(1) else 0
        sec_p = int(m.group(2))
        ms_p = int(m.group(3))
        ms_val = ms_p / (100.0 if len(m.group(3)) == 2 else 10.0)
        return min_p * 60 + sec_p + ms_val
    return None

def format_seconds(seconds):
    if not seconds or seconds <= 0:
        return "-"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:05.2f}"

def get_surface_key(surface_text):
    s = (surface_text or "").lower()
    if "sentetik" in s or "synthetic" in s:
        return "sentetik"
    elif "kum" in s or "dirt" in s:
        return "kum"
    return "çim"

def analyze_track_affinity(last_6, target_surface):
    if not last_6 or len(str(last_6)) < 2:
        return 65.0, 0, 0, "Hedef pistte resmi start kaydı yok"

    surf_key = get_surface_key(target_surface)
    target_code = "Ç" if surf_key == "çim" else ("S" if surf_key == "sentetik" else "K")
    
    tokens = re.findall(r'([ÇSKçskC])(\d+)', str(last_6))
    if not tokens:
        return 65.0, 0, 0, "Koşu detayı ayrıştırılamadı"

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
        score = max(45.0, 72.0 - avg_other * 3.0)
        return score, 0, 0, f"Hedef pistte ({target_surface}) henüz start almadı"

    podium_count = sum(1 for p in surface_runs if 1 <= p <= 4)
    win_count = sum(1 for p in surface_runs if p == 1)
    second_count = sum(1 for p in surface_runs if p == 2)
    avg_finish = sum(surface_runs) / len(surface_runs)
    
    podium_rate = podium_count / len(surface_runs)
    top2_rate = sum(1 for p in surface_runs if p <= 2) / len(surface_runs)
    
    recent_finish = surface_runs[-1]
    recent_bonus = 8.0 if recent_finish <= 2 else (4.0 if recent_finish <= 4 else 0.0)
    
    streak_bonus = 0.0
    if len(surface_runs) >= 2 and all(p <= 2 for p in surface_runs[-2:]):
        streak_bonus = 6.0

    base_score = 88.0 - (avg_finish - 1.0) * 4.5
    score = base_score + (podium_rate * 6.0) + (top2_rate * 5.0) + recent_bonus + streak_bonus + (win_count * 4.0)
    score = max(35.0, min(99.0, round(score, 1)))

    details = (
        f"{target_surface} pistte {len(surface_runs)} yarışta "
        f"{podium_count} tabela ({win_count} birincilik, {second_count} ikincilik)"
    )
    return score, len(surface_runs), podium_count, details

def compute_surface_form(last_6, target_surface):
    if not last_6:
        return 68.0
    surf_key = get_surface_key(target_surface)
    target_code = "Ç" if surf_key == "çim" else ("S" if surf_key == "sentetik" else "K")
    tokens = re.findall(r'([ÇSKçskC])(\d+)', str(last_6))
    if not tokens:
        return 68.0
    
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
        recent = surface_finishes[-3:]
        avg_rec = sum(recent) / len(recent)
        form = 92.0 - (avg_rec - 1.0) * 4.5
        if surface_finishes[-1] == 1:
            form += 8.0
        elif surface_finishes[-1] == 2:
            form += 5.0
        elif surface_finishes[-1] <= 4:
            form += 2.5
        return max(40.0, min(99.0, round(form, 1)))
    else:
        avg_all = sum(all_finishes) / len(all_finishes) if all_finishes else 6.0
        return max(40.0, 72.0 - avg_all * 2.8)

def compute_speed_figure(r, distance, surface, record_time_sec, is_maiden=False):
    best_time_str = r.get("best_time", "")
    best_time_sec = parse_time_str(best_time_str)
    weight = float(r.get("weight", 58.0))
    weight_diff = weight - 57.0

    if is_maiden:
        weight_penalty = 0.0
        class_bonus = 2.5 if weight >= 59.0 else 0.0
    else:
        weight_penalty = weight_diff * (0.18 * (distance / 1400.0))
        class_bonus = 0.0

    if best_time_sec and best_time_sec > 40:
        adjusted_time = best_time_sec + weight_penalty
        source_desc = f"Mesafedeki ({distance}m) resmi derecesi ({best_time_str})"
    else:
        handicap = float(r.get("handicap", 35))
        if is_maiden:
            perf_tier = max(0.0, min(1.0, (handicap - 18) / 20.0))
        else:
            perf_tier = max(0.0, min(1.0, (handicap - 20) / 75.0))
            
        surface_key = get_surface_key(surface)
        surface_offset = SURFACE_OFFSET_PER_100M.get(surface_key, 0.0) * (distance / 100.0)
        ideal_time = record_time_sec + surface_offset
        handicap_delay = (1.0 - perf_tier) * (distance / 1000.0) * (2.0 if is_maiden else 3.8)
        adjusted_time = ideal_time + handicap_delay + weight_penalty
        source_desc = f"Hedef mesafe ve handikap ({int(handicap)}) puanından projeksiyon"

    time_behind = max(0.0, adjusted_time - record_time_sec)
    points_lost = (time_behind / (distance / 1000.0)) * 5.0
    speed_figure = max(40.0, min(99.0, round(100.0 - points_lost + class_bonus, 1)))

    return {
        "adjusted_time_sec": round(adjusted_time, 2),
        "adjusted_time_str": format_seconds(adjusted_time),
        "speed_figure": speed_figure,
        "source_desc": source_desc,
        "weight_penalty_sec": round(weight_penalty, 2)
    }

def get_trainer_empirical(trainer_name):
    if not trainer_name:
        return 74.0, "Standart ahır formu"
    ck = clean_key(trainer_name)
    for k, v in CLEAN_TRAINERS.items():
        if len(k) >= 3 and (k in ck or ck in k):
            win_pct = v['win_rate']
            score = 70.0 + win_pct * 1.05 + (v['top4_rate'] - 35) * 0.25
            desc = f"Antrenör {trainer_name}: %{win_pct:.1f} kazanma, %{v['top4_rate']:.1f} tabela"
            return round(min(98.0, max(60.0, score)), 1), desc
    return 74.0, f"Antrenör {trainer_name}: Standart ahır performansı"

def get_jockey_empirical(jockey_name, is_maiden=False):
    if not jockey_name:
        return 76.0, "Standart jokey"
    ck = clean_key(jockey_name)
    for k, v in CLEAN_JOCKEYS.items():
        if len(k) >= 3 and (k in ck or ck in k):
            win_pct = v['win_rate']
            base = 70.0 + win_pct * 1.1 + (v['top4_rate'] - 35) * 0.25
            if is_maiden and win_pct >= 18.0:
                base += 3.0
            desc = f"Jokey {jockey_name}: %{win_pct:.1f} kazanma, %{v['top4_rate']:.1f} tabela"
            return round(min(99.0, max(58.0, base)), 1), desc
    if "ap" in jockey_name.lower():
        return 72.0, f"Apranti {jockey_name}: Kilo indirimi avantajı"
    return 76.0, f"Jokey {jockey_name}: Deneyimli binici"

def get_sire_empirical(sire_name):
    if not sire_name:
        return 75.0, "Dengeli soy kütüğü"
    ck = clean_key(sire_name)
    for k, v in CLEAN_SIRES.items():
        if len(k) >= 3 and (k in ck or ck in k):
            win_pct = v['win_rate']
            score = 70.0 + win_pct * 0.95 + (v['top4_rate'] - 35) * 0.2
            desc = f"Aygır {sire_name}: %{win_pct:.1f} kazanma, %{v['top4_rate']:.1f} tabela"
            return round(min(98.0, max(62.0, score)), 1), desc
    return 75.0, f"Aygır {sire_name}: Standart pedigri"

def compute_kgs_cycle(kgs):
    try:
        k = int(kgs)
    except:
        k = 20
    if 14 <= k <= 35:
        return 2.5, "İdeal dinlenme ve form aralığı (14-35 gün)", True
    elif 8 <= k <= 13:
        return 1.0, "Yakın koşu periyodu (formunu koruyor)", True
    elif 36 <= k <= 60:
        return 0.0, "Orta dinlenme periyodu", False
    elif k > 90:
        return -3.5, f"{k} gündür koşmuyor; yarış pası ve kondisyon eksiği riski", False
    elif k > 60:
        return -2.0, f"{k} gün ara; nefes açma ihtiyacı duyabilir", False
    elif k < 7:
        return -1.5, f"{k} gün önce koştu; aşırı yıpranma ve yorgunluk riski", False
    return 0.0, "Normal dinlenme", False

def compute_gear_impact(eq_str):
    if not eq_str:
        return 0.0, [], []
    eq_upper = eq_str.upper()
    total_mod = 0.0
    pos_notes = []
    neg_notes = []
    
    for g, mod in GEAR_MODIFIERS.items():
        if g in eq_upper:
            total_mod += mod
            if mod > 0:
                pos_notes.append(f"{g} (+{mod})")
            elif mod < 0:
                neg_notes.append(f"{g} ({mod})")
    return total_mod, pos_notes, neg_notes

def predict_race_v5(race):
    runners = race.get("runners", [])
    if not runners:
        return []

    distance = race.get("distance", 1400)
    surface = race.get("surface", "Kum")
    is_maiden = race.get("is_maiden", False)
    record_time_sec = (distance / 100.0) * 6.35

    all_agfs = [float(r.get("agf", 0.0)) for r in runners]
    max_agf = max(all_agfs) if all_agfs else 1.0
    all_weights = [float(r.get("weight", 58.0)) for r in runners]
    max_w = max(all_weights) if all_weights else 58.0
    all_hps = [float(r.get("handicap", 35)) for r in runners]
    max_hp = max(all_hps) if all_hps else 50.0
    min_hp = min(all_hps) if all_hps else 20.0

    scored_runners = []

    for r in runners:
        agf = float(r.get("agf", 0.0))
        ratio = agf / max(max_agf, 1.0) if max_agf > 0 else 0.5
        agf_score = 55.0 + (ratio ** 0.58) * 43.0

        # Surface affinity & form
        last_6 = r.get("last_6", "")
        surf_score, surf_runs, podium_runs, surf_details = analyze_track_affinity(last_6, surface)
        surface_form = compute_surface_form(last_6, surface)

        # Speed figure
        speed_info = compute_speed_figure(r, distance, surface, record_time_sec, is_maiden)

        # Jockey & Trainer empirical
        j_score, j_desc = get_jockey_empirical(r.get("jockey", ""), is_maiden)
        t_score, t_desc = get_trainer_empirical(r.get("trainer", ""))

        # Sire
        s_score, s_desc = get_sire_empirical(r.get("sire", ""))

        # Weight dynamic (Turkish racing: heavy = class)
        w = float(r.get("weight", 58.0))
        w_ratio = (w - 50.0) / max(max_w - 50.0, 1.0)
        class_weight_score = 70.0 + w_ratio * 12.0 if not is_maiden else 75.0

        # Handicap rating
        hp = float(r.get("handicap", 35))
        hp_score = 65.0 + ((hp - min_hp) / max(max_hp - min_hp, 1)) * 30.0

        # Power to Weight (HP / Weight)
        pwr = (hp / max(w, 48.0)) * 58.0
        pwr_score = 65.0 + min(30.0, max(0.0, (pwr - 25.0) * 1.0))

        # Gate bias
        gate = int(r.get("gate", 5) or 5)
        gate_bias = GATE_BIAS_SPRINT.get(gate, 0.0) if distance <= 1400 else GATE_BIAS_ROUTE.get(gate, 0.0)

        # Gear impact
        gear_mod, gear_pos, gear_neg = compute_gear_impact(r.get("equipment", ""))

        # KGS Cycle
        kgs_mod, kgs_desc, kgs_is_opt = compute_kgs_cycle(r.get("kgs", 20))

        # Pace match bonus (sprint inside gate vs route staying)
        pace_bonus = 0.0
        if distance <= 1400 and gate <= 4:
            pace_bonus = 2.0
        elif distance >= 2000 and hp >= 45:
            pace_bonus = 1.8

        # ============================================================
        # 18-FACTOR COMPOSITE ENSEMBLE
        # ============================================================
        composite = (
            (agf_score          * 0.22) +
            (surf_score         * 0.16) +
            (surface_form       * 0.14) +
            (j_score            * 0.13) +
            (speed_info["speed_figure"] * 0.11) +
            (t_score            * 0.08) +
            (hp_score           * 0.06) +
            (s_score            * 0.04) +
            (class_weight_score * 0.03) +
            (pwr_score          * 0.03)
        )
        composite += gate_bias * 0.08
        composite += gear_mod * 0.12
        composite += kgs_mod * 0.10
        composite += pace_bonus * 0.08

        # Structured Winning Drivers & Risk Flags
        dominant_factors = []
        risk_factors = []

        if agf_score >= 88:
            dominant_factors.append({
                "factor": "AGF / Piyasa Güveni",
                "icon": "🔥",
                "impact": f"+{round(agf_score * 0.22, 1)}",
                "desc": f"AGF #{r.get('agf_rank', 1)} (%{agf:.1f}) ile kamuoyunun en güvendiği safkan."
            })
        if j_score >= 88:
            dominant_factors.append({
                "factor": "Elit Jokey Tercihi",
                "icon": "👑",
                "impact": f"+{round(j_score * 0.13, 1)}",
                "desc": j_desc
            })
        if speed_info["speed_figure"] >= 85:
            dominant_factors.append({
                "factor": "Düzeltilmiş Hız Lideri",
                "icon": "⏱️",
                "impact": f"+{round(speed_info['speed_figure'] * 0.11, 1)}",
                "desc": f"{speed_info['adjusted_time_str']} derece projeksiyonu ile grubun en yüksek hız endeksine sahip."
            })
        if surf_score >= 85:
            dominant_factors.append({
                "factor": "Üstün Pist Afinitesi",
                "icon": "⚡",
                "impact": f"+{round(surf_score * 0.16, 1)}",
                "desc": surf_details
            })
        if surface_form >= 85:
            dominant_factors.append({
                "factor": "Yüksek Form Momentumu",
                "icon": "📈",
                "impact": f"+{round(surface_form * 0.14, 1)}",
                "desc": "Son koşularında istikrarlı birincilik/ikincilik serisi yakaladı."
            })
        if t_score >= 85:
            dominant_factors.append({
                "factor": "Başarılı Ahır / Antrenör",
                "icon": "🏢",
                "impact": f"+{round(t_score * 0.08, 1)}",
                "desc": t_desc
            })
        if gate_bias >= 2.0:
            dominant_factors.append({
                "factor": "Avantajlı İç Kulvar",
                "icon": "🚪",
                "impact": f"+{round(gate_bias * 0.08, 1)}",
                "desc": f"{gate}. iç kulvardan viraja bariyer dibinde avantajlı girme şansı."
            })
        if gear_pos:
            dominant_factors.append({
                "factor": "Olumlu Teçhizat",
                "icon": "🛡️",
                "impact": f"+{round(gear_mod * 0.12, 1)}",
                "desc": f"Etkili ekipman kombinasyonu: {', '.join(gear_pos)}"
            })
        if kgs_is_opt:
            dominant_factors.append({
                "factor": "İdeal Dinlenme Döngüsü",
                "icon": "🔋",
                "impact": "+0.25",
                "desc": kgs_desc
            })

        # Risk Factors
        if gear_neg:
            risk_factors.append({
                "factor": "Riskli Teçhizat Uyarısı",
                "icon": "⚠️",
                "impact": f"{round(gear_mod * 0.12, 1)}",
                "desc": f"Ampirik veride düşük galibiyete sahip ekipman: {', '.join(gear_neg)}"
            })
        if kgs_mod < 0:
            risk_factors.append({
                "factor": "Dinlenme/Kondisyon Riski",
                "icon": "⏳",
                "impact": f"{round(kgs_mod * 0.10, 1)}",
                "desc": kgs_desc
            })
        if w <= 52.0 and not is_maiden:
            risk_factors.append({
                "factor": "Düşük Sınıf Uyarısı",
                "icon": "⚖️",
                "impact": "-0.5",
                "desc": f"{w} kg hafif sıklet Türkiye yarışlarında alt grup göstergesi olabilir."
            })
        if gate >= 12 and distance <= 1400:
            risk_factors.append({
                "factor": "Dış Kulvar Dezavantajı",
                "icon": "🚪",
                "impact": "-0.3",
                "desc": f"{gate}. kulvar sprint mesafesinde virajda mesafe kaybettirebilir."
            })

        summary_parts = [d["desc"] for d in dominant_factors[:3]]
        factor_summary = " ".join(summary_parts) if summary_parts else "Dengeli kriter profili ile grupta mücadele edecek."

        scored_runners.append({
            **r,
            "composite": round(composite, 2),
            "speed_info": speed_info,
            "surf_score": surf_score,
            "surface_form": surface_form,
            "j_score": j_score,
            "t_score": t_score,
            "hp_score": hp_score,
            "winning_factors": {
                "dominant_factors": dominant_factors,
                "risk_factors": risk_factors,
                "factor_summary": factor_summary
            }
        })

    scored_runners.sort(key=lambda x: x["composite"], reverse=True)
    return scored_runners

def run_v5_benchmark():
    with open('data/historical_database_1000.json', 'r', encoding='utf-8') as f:
        races = json.load(f)

    total_races = len(races)
    print(f"Running Engine v5.0 Benchmark across {total_races} real historical TJK races...")

    top1_wins = 0
    top2_contains = 0
    top3_contains = 0
    top4_contains = 0
    exact_quinella = 0
    exacta_straight = 0
    total_ganyan = 0.0
    total_bets = 0

    for idx, r in enumerate(races):
        runners = r.get("runners", [])
        actual_winner = next((rn for rn in runners if rn.get("finish_order") == 1), None)
        actual_second = next((rn for rn in runners if rn.get("finish_order") == 2), None)
        if not actual_winner:
            continue

        preds = predict_race_v5(r)
        if not preds:
            continue

        total_bets += 1
        winner_name = actual_winner.get("name", "").strip().lower()
        winner_ganyan = actual_winner.get("ganyan", 0.0)

        # Top 1
        if preds[0].get("name", "").strip().lower() == winner_name:
            top1_wins += 1
            total_ganyan += winner_ganyan if winner_ganyan > 0 else 1.0

        # Top 2
        top2_names = [p.get("name", "").strip().lower() for p in preds[:2]]
        if winner_name in top2_names:
            top2_contains += 1

        # Top 3
        top3_names = [p.get("name", "").strip().lower() for p in preds[:3]]
        if winner_name in top3_names:
            top3_contains += 1

        # Top 4
        top4_names = [p.get("name", "").strip().lower() for p in preds[:4]]
        if winner_name in top4_names:
            top4_contains += 1

        # Quinella / Exacta
        if actual_second:
            second_name = actual_second.get("name", "").strip().lower()
            if set(top2_names) == {winner_name, second_name}:
                exact_quinella += 1
            if len(preds) >= 2 and preds[0].get("name", "").strip().lower() == winner_name and preds[1].get("name", "").strip().lower() == second_name:
                exacta_straight += 1

    win_rate = top1_wins / total_bets * 100
    top2_rate = top2_contains / total_bets * 100
    top3_rate = top3_contains / total_bets * 100
    top4_rate = top4_contains / total_bets * 100
    quinella_rate = exact_quinella / total_bets * 100
    exacta_rate = exacta_straight / total_bets * 100
    roi = total_ganyan / total_bets * 100

    print("\n=======================================================")
    print(f"🏁 ENGINE v5.0 (18 FAKTÖRLÜ DERİN MODEL) SONUÇLARI ({total_bets} Koşu)")
    print("=======================================================")
    print(f"🏆 1. Tek (Banko) İsabeti:          %{win_rate:.2f} ({top1_wins}/{total_bets})")
    print(f"🥈 Kazanan Modelin İlk 2'sinde:    %{top2_rate:.2f} ({top2_contains}/{total_bets})")
    print(f"🥉 Kazanan Modelin İlk 3'ünde:    %{top3_rate:.2f} ({top3_contains}/{total_bets})")
    print(f"🎯 Kazanan Modelin İlk 4'ünde:    %{top4_rate:.2f} ({top4_contains}/{total_bets})")
    print(f"🎲 İkili Bahis İsabeti:            %{quinella_rate:.2f}")
    print(f"🎯 Sıralı İkili İsabeti:           %{exacta_rate:.2f}")
    print(f"💰 1. At Sabit Ganyan ROI:         %{roi:.2f}")
    print("=======================================================\n")

    report = {
        "engine_version": "v5.0_deep_empirical_18_factors",
        "total_races": total_bets,
        "metrics": {
            "top1_win_strike_rate": round(win_rate, 2),
            "top2_contains_winner": round(top2_rate, 2),
            "top3_contains_winner": round(top3_rate, 2),
            "top4_contains_winner": round(top4_rate, 2),
            "exact_quinella_rate": round(quinella_rate, 2),
            "exacta_straight_rate": round(exacta_rate, 2),
            "top1_flat_roi_pct": round(roi, 2)
        }
    }
    with open('data/backtest_report_v5.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report

if __name__ == "__main__":
    run_v5_benchmark()
