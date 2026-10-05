"""
Advanced Horse Racing Prediction & Handicapping Engine Pro v3.0.
Implements:
- Beyer Speed Figures & Distance Fatigue Decay Modeling
- Pedigree (Sire & Dam) Bloodline Tendencies (Arap & İngiliz)
- Wet / Dry / Heavy Track Condition Dynamics (Islak / Kuru Pist Katsayıları)
- Jockey - Horse Synergy Index
- Career Run Count & Experience Maturity Curve
- Gallop Consistency with IQR/Z-score Outlier Filtering
- Weight Handicap Adjustments
- Comprehensive Betting Studio Models:
  Ganyan, İkili, Sıralı İkili, Plase, Plase İkili, 3'lü Bahis (Trio),
  Tabela Bahis (4'lü Bahis), Sıralı 5'li Bahis ve Çifte Bahis
"""

import math
import re
from backend.gallop_engine import analyze_gallops, parse_time_str, format_seconds

# Surface speed differentials in seconds per 100m compared to standard Turf (Çim)
SURFACE_OFFSET_PER_100M = {
    "çim": 0.0,
    "cim": 0.0,
    "turf": 0.0,
    "sentetik": 0.085,
    "synthetic": 0.085,
    "kum": 0.195,
    "dirt": 0.195,
}

# Elite Jockey ratings in Turkey (win & place strike rates)
JOCKEY_RATINGS = {
    "g.kocakaya": 96, "ö.yıldırım": 95, "h.karataş": 95, "m.kaya": 93,
    "n.avci": 91, "m.çiçek": 90, "m.m.bilgin": 89, "a.sözen": 89,
    "e.aktuğ": 87, "mer.çelik": 88, "vedat.abiş": 95, "s.boyraz": 87,
    "h.çizik": 88, "f.çetin": 84, "o.yıldız": 85, "t.alıcı": 83,
    "a.meh.altın": 82, "mah.turan": 81, "u.temur": 83, "m.keçeci": 80,
    "e.kadirler": 78, "r.ketme": 76, "i.katı": 77, "a.kurşun": 92,
    "s.kaya": 94, "b.kılınç": 80, "m.s.çelik": 85, "f.yardımcı": 84
}

# Turkish Pedigree Database (Prominent Sires and their traits)
PEDIGREE_TRAITS = {
    # Arap Sires
    "kaizbert": {"stamina": 95, "surface_pref": "hepsi", "wet_affinity": 96, "sprint": 94, "desc": "Efsanevi aygır; çim, kum ve ıslak pistte üstün sürat ve dayanıklılık aktarır."},
    "turbo": {"stamina": 92, "surface_pref": "kum", "wet_affinity": 90, "sprint": 96, "desc": "Kum pistte yüksek sürat ve erken liderlik eğilimi."},
    "özgünhan": {"stamina": 96, "surface_pref": "çim", "wet_affinity": 88, "sprint": 85, "desc": "Orta ve uzun mesafelerde üstün ciğer kapasitesi ve son viraj sprinti."},
    "uçanbey": {"stamina": 88, "surface_pref": "çim", "wet_affinity": 89, "sprint": 92, "desc": "Çim pist sprinteri; virajı iyi döner ve diri kalır."},
    "karaüzüm": {"stamina": 93, "surface_pref": "kum", "wet_affinity": 98, "sprint": 86, "desc": "Ağır ve ıslak/çamurlu zeminlerde rakiplerine belirgin üstünlük sağlar."},
    "ayabakan": {"stamina": 90, "surface_pref": "kum", "wet_affinity": 91, "sprint": 89, "desc": "Dengeli kum atı, mücadeleci karakter."},
    "haberbatur": {"stamina": 94, "surface_pref": "çim", "wet_affinity": 90, "sprint": 87, "desc": "Klasik çim pedigrisi; mesafeyi çok sever."},
    "tamerinoğlu": {"stamina": 91, "surface_pref": "hepsi", "wet_affinity": 88, "sprint": 88, "desc": "Hem çimde hem kumda dengeli koşan dayanıklı soy."},
    "saadın gücü": {"stamina": 87, "surface_pref": "kum", "wet_affinity": 85, "sprint": 90, "desc": "Erken süratli ve kısa mesafede etkili."},
    "sarraf": {"stamina": 89, "surface_pref": "kum", "wet_affinity": 88, "sprint": 91, "desc": "Güçlü kum performansı ve mücadele gücü."},
    "gelibolu": {"stamina": 92, "surface_pref": "çim", "wet_affinity": 93, "sprint": 86, "desc": "Ağır çim ve uzun mesafede çok başarılı."},
    
    # İngiliz Sires
    "torok": {"stamina": 94, "surface_pref": "çim", "wet_affinity": 95, "sprint": 93, "desc": "Çim ve sentetikte grup koşuların başrolü; yumuşak/ıslak çimde çok etkilidir."},
    "native khan": {"stamina": 96, "surface_pref": "çim", "wet_affinity": 94, "sprint": 88, "desc": "Orta/uzun mesafe çim ve sentetik uzmanı; üstün dayanıklılık."},
    "luxor": {"stamina": 86, "surface_pref": "çim", "wet_affinity": 85, "sprint": 96, "desc": "Sürat ve mil koşularının (1200-1600m) elit aygırı."},
    "mendip": {"stamina": 90, "surface_pref": "kum", "wet_affinity": 93, "sprint": 92, "desc": "Kum pistte yüksek tempo ve viraj hakimiyeti."},
    "victory gallop": {"stamina": 97, "surface_pref": "kum", "wet_affinity": 90, "sprint": 82, "desc": "Açık yarış kazanan uzun mesafe kum canavarları üretir."},
    "lion heart": {"stamina": 88, "surface_pref": "kum", "wet_affinity": 92, "sprint": 95, "desc": "Yüksek başlangıç hızı, ıslak ve sulu kumda öncülük gücü."},
    "daredevil": {"stamina": 91, "surface_pref": "kum", "wet_affinity": 98, "sprint": 93, "desc": "Islak, sulu ve çamurlu pistlerde sıra dışı performans sıçraması yapar."},
    "bodemeister": {"stamina": 92, "surface_pref": "kum", "wet_affinity": 92, "sprint": 91, "desc": "Güçlü göğüs yapısı, sert kum zeminlerde yıpranmaz."},
    "kaneko": {"stamina": 95, "surface_pref": "hepsi", "wet_affinity": 91, "sprint": 89, "desc": "Türkiye yarışçılığının temel direği; mesafeye ve her piste uyumlu."},
    "smart robin": {"stamina": 93, "surface_pref": "çim", "wet_affinity": 89, "sprint": 87, "desc": "Derin çim ve 1800m+ mesafelerde etkili dayanıklılık."}
}

def clean_name(name):
    """Normalize jockey or horse name for dictionary lookup."""
    if not name:
        return ""
    n = str(name).replace('İ', 'i').replace('I', 'i').replace('ı', 'i').lower()
    n = n.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return re.sub(r'[^a-z0-9]', '', n)

CLEANED_JOCKEY_RATINGS = {clean_name(k): v for k, v in JOCKEY_RATINGS.items()}

def parse_record_time_seconds(record_str, distance):
    """Parse track record time like '1.29.33' or '1:29.33'."""
    sec = parse_time_str(record_str)
    if sec and sec > 30:
        return sec
    return (distance / 100.0) * 6.35

def get_surface_key(surface_text):
    """Detect surface type: çim, kum, sentetik."""
    s = (surface_text or "").lower()
    if "sentetik" in s or "synthetic" in s:
        return "sentetik"
    elif "kum" in s or "dirt" in s:
        return "kum"
    return "çim"

def analyze_pedigree(sire_name, dam_name, target_surface, target_distance):
    """
    Evaluates genetic pedigree aptitude for surface and distance stamina.
    """
    clean_s = clean_name(sire_name)
    matched = None
    for k, v in PEDIGREE_TRAITS.items():
        if k in clean_s or clean_s in k:
            matched = v
            break
            
    if not matched:
        # Default baseline pedigree profile
        is_turf_bias = "çim" in target_surface.lower()
        return {
            "score": 75.0,
            "stamina_score": 75.0,
            "wet_affinity": 75.0,
            "surface_match": "Dengeli Soy Kütüğü",
            "desc": f"Baba {sire_name or 'Bilinmiyor'} ve Anne {dam_name or 'Bilinmiyor'} soy hattı mesafe ve pist için standart dengeli genetik potansiyel barındırıyor."
        }
        
    # Evaluate distance suitability
    is_long = target_distance >= 1800
    stamina = matched["stamina"] if is_long else (matched["stamina"] * 0.4 + matched["sprint"] * 0.6)
    
    # Surface bonus
    pref = matched["surface_pref"]
    surf_match = True
    if pref == "hepsi" or target_surface.lower() in pref:
        surf_bonus = 6.0
    else:
        surf_bonus = -4.0
        surf_match = False
        
    pedigree_score = max(50.0, min(98.0, round(stamina * 0.7 + matched["wet_affinity"] * 0.2 + surf_bonus, 1)))
    
    return {
        "score": pedigree_score,
        "stamina_score": round(stamina, 1),
        "wet_affinity": matched["wet_affinity"],
        "surface_match": "Yüksek Uyum" if surf_match else "Orta Uyum",
        "desc": f"Baba {sire_name}: {matched['desc']}"
    }

def analyze_track_condition_impact(runner, target_surface, track_condition="Normal"):
    """
    Analyzes wet / dry / heavy track condition impact.
    Çim: Kuru, Yumuşak, Ağır / Çamur
    Kum: Normal, Islak / Sulu (Sulu kum kaçak atlara +%30 avantaj sağlar)
    """
    cond = (track_condition or "Normal").lower()
    is_wet = "ıslak" in cond or "sulu" in cond or "ağır" in cond or "çamur" in cond or "yumuşak" in cond
    
    pedigree_wet = runner.get("pedigree_analysis", {}).get("wet_affinity", 75.0)
    
    # Track penalty or boost
    if not is_wet:
        return {
            "condition": "Normal / Kuru Zemin",
            "impact_sec": 0.0,
            "speed_multiplier": 1.0,
            "notes": "Pist şartları normal ve kuru; safkanlar ideal tempolarını sahaya yansıtabilir."
        }
        
    if "kum" in target_surface.lower():
        # Wet dirt packs tight -> faster track (+kickback penalty for trailers)
        return {
            "condition": "Islak / Sulu Kum",
            "impact_sec": -0.85, # times become faster
            "speed_multiplier": 1.04,
            "wet_score": pedigree_wet,
            "notes": "Islak/sulu kum zeminde pist hızlanır. Önde kaçan safkanlar çamur sıçramasından (kickback) etkilenmediği için büyük avantaj yakalar."
        }
    else:
        # Wet turf -> heavy, times slow down, stamina counts
        sec_penalty = 1.6 if "ağır" in cond else 0.9
        return {
            "condition": "Ağır / Yumuşak Çim",
            "impact_sec": sec_penalty,
            "speed_multiplier": 0.97,
            "wet_score": pedigree_wet,
            "notes": f"Çim pist yumuşak/ağır; dereceler +{sec_penalty}sn civarında yavaşlayacaktır. Güçlü pedigriye ({pedigree_wet} puan) sahip safkanlar öne çıkar."
        }

def analyze_jockey_horse_synergy(jockey_name, horse_name, weight, last_6, is_maiden=False):
    """
    Computes synergy score between jockey and runner.
    Takes into account master jockey rating, weight tolerance, and past run rhythm.
    """
    clean_j = clean_name(jockey_name)
    base_jockey = 80.0
    for key, val in CLEANED_JOCKEY_RATINGS.items():
        if key in clean_j or clean_j in key:
            base_jockey = float(val)
            break
            
    is_apprentice = "ap" in (jockey_name or "").lower() or (weight <= 53.0 and base_jockey <= 82)
    
    # Master jockey bonus on clutch/maiden races
    if base_jockey >= 88:
        synergy_desc = f"Usta jokey {jockey_name} binişi ile yarış içi taktik ve son viraj hamle üstünlüğü."
        synergy_score = base_jockey + (4.0 if is_maiden else 2.0)
    elif is_apprentice:
        synergy_desc = f"Genç apranti {jockey_name} sıklet indirimi (indirimli kilo) avantajı sunuyor."
        synergy_score = base_jockey - 2.0
    else:
        synergy_desc = f"Jokey {jockey_name} ile safkan arasında dengeli bir uyum bulunuyor."
        synergy_score = base_jockey
        
    return {
        "jockey_score": round(base_jockey, 1),
        "synergy_score": round(synergy_score, 1),
        "is_master": base_jockey >= 88,
        "is_apprentice": is_apprentice,
        "details": synergy_desc
    }

def analyze_career_maturity(age_str, last_6, kgs):
    """
    Evaluates career progression and freshness based on age, runs and rest days.
    """
    age_digits = re.findall(r'\d+', str(age_str or '3'))
    age = int(age_digits[0]) if age_digits else 3
    
    # Run count from last_6
    past_runs = len(re.findall(r'\d', str(last_6 or '')))
    
    if past_runs <= 2:
        stage = "Genç & Yüksek Gelişim Potansiyeli"
        maturity_score = 88.0
        stage_desc = "Kariyerinin başında; her yarışında ciddi derece sıçraması yapabilecek gelişim evresinde."
    elif 3 <= past_runs <= 15:
        stage = "Kariyer Zirvesi & Olgunluk"
        maturity_score = 92.0
        stage_desc = "Formunun ve kondisyonunun zirvesinde; en istikrarlı koşu çağını yaşıyor."
    elif 16 <= past_runs <= 35:
        stage = "Deneyimli Grup Atı"
        maturity_score = 85.0
        stage_desc = "Yüksek yarış tecrübesi; koşu temposunu ve taktikleri çok iyi biliyor."
    else:
        stage = "Veteran / Tecrübeli"
        maturity_score = 78.0
        stage_desc = "Çok sayıda start almış tecrübeli safkan; yıpranma payına karşın pist bilgisini konuşturabilir."
        
    return {
        "age": age,
        "past_runs_count": past_runs,
        "stage": stage,
        "maturity_score": maturity_score,
        "desc": stage_desc
    }

def analyze_track_affinity(last_6, target_surface):
    """
    Parses last 6 races to compute affinity for target surface.
    Normalizes Turkish characters and handles '0' as 10th+ (unplaced).
    """
    if not last_6:
        return 58.0, 0, 0, "Daha önce resmi koşu kaydı yok (Orijin ve idman değerlendirildi)"

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
        # In TJK, '0' signifies 10th or worse (unplaced / tabelaya giremedi)
        finish_pos = 10 if raw_pos == 0 else raw_pos
        all_runs.append((surf_char, finish_pos))
        if surf_char == target_code:
            surface_runs.append(finish_pos)

    if not surface_runs:
        other_finishes = [p for _, p in all_runs]
        avg_other = sum(other_finishes) / len(other_finishes) if other_finishes else 6.0
        score = max(40.0, 68.0 - avg_other * 3.0)
        return score, 0, 0, f"Hedef pistte ({target_surface.capitalize()}) henüz start almadı; farklı pist tecrübesi bulunuyor."

    podium_count = sum(1 for p in surface_runs if 1 <= p <= 4)
    win_count = sum(1 for p in surface_runs if p == 1)
    second_count = sum(1 for p in surface_runs if p == 2)
    avg_finish = sum(surface_runs) / len(surface_runs)
    
    podium_rate = podium_count / len(surface_runs)
    top2_rate = sum(1 for p in surface_runs if p <= 2) / len(surface_runs)
    
    # Recent finish on target surface
    recent_finish = surface_runs[-1]
    recent_bonus = 8.0 if recent_finish <= 2 else (4.0 if recent_finish <= 4 else 0.0)
    
    # Consecutive top-2 finishes bonus (e.g. Ç2 Ç2 Ç2)
    streak_bonus = 0.0
    if len(surface_runs) >= 2 and all(p <= 2 for p in surface_runs[-3:]):
        streak_bonus = 8.0
    elif len(surface_runs) >= 2 and all(p <= 4 for p in surface_runs[-3:]):
        streak_bonus = 4.0

    base_score = 88.0 - (avg_finish - 1.0) * 5.0
    score = base_score + (podium_rate * 6.0) + (top2_rate * 5.0) + recent_bonus + streak_bonus + (win_count * 5.0)
    score = max(30.0, min(99.0, round(score, 1)))

    details = (
        f"{target_surface.capitalize()} pistte {len(surface_runs)} yarışta "
        f"{podium_count} kez tabela ({win_count} birincilik, {second_count} ikincilik, ortalama {avg_finish:.1f}.lik). "
        f"{'Üstün pist istikrarı!' if score >= 85 else ('Yüksek pist uyumu.' if score >= 75 else 'Dengeli pist performansı.')}"
    )
    return score, len(surface_runs), podium_count, details

def compute_surface_form(last_6, target_surface):
    """
    Computes current form prioritizing recent performance on the target surface.
    """
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

def calculate_adjusted_time(runner, target_distance, target_surface, record_time_sec, is_maiden=False):
    """
    Adjusts past best time to current conditions.
    Takes into account maiden class weight dynamics and track records.
    """
    best_time_str = runner.get("best_time", "")
    best_time_sec = parse_time_str(best_time_str)
    
    weight = runner.get("weight", 58.0)
    weight_diff = weight - 57.0

    if is_maiden:
        # In Maiden races, 60kg is an earned badge of superior placed form (class indicator)
        weight_penalty = 0.0
        class_bonus = 2.5 if weight >= 59.0 else 0.0
    else:
        weight_penalty = weight_diff * (0.20 * (target_distance / 1400.0))
        class_bonus = 0.0

    if best_time_sec and best_time_sec > 40:
        adjusted_time = best_time_sec + weight_penalty
        is_exact_match = True
        source_desc = f"Bu mesafedeki ({target_distance}m) resmi en iyi derecesi ({best_time_str})"
    else:
        # Benchmark estimation based on handicap & record
        handicap = runner.get("handicap", 35)
        if is_maiden:
            perf_tier = max(0.0, min(1.0, (handicap - 18) / 20.0))
        else:
            perf_tier = max(0.0, min(1.0, (handicap - 20) / 75.0))
            
        surface_key = get_surface_key(target_surface)
        surface_offset = SURFACE_OFFSET_PER_100M.get(surface_key, 0.0) * (target_distance / 100.0)
        
        ideal_time = record_time_sec + surface_offset
        handicap_delay = (1.0 - perf_tier) * (target_distance / 1000.0) * (2.0 if is_maiden else 3.8)
        adjusted_time = ideal_time + handicap_delay + weight_penalty
        is_exact_match = False
        source_desc = f"Hedef mesafe ve handikap ({handicap}) puanından hesaplandı"

    pace_100 = adjusted_time / (target_distance / 100.0)
    time_behind_record = max(0.0, adjusted_time - record_time_sec)
    points_lost = (time_behind_record / (target_distance / 1000.0)) * 5.0
    speed_figure = max(35.0, min(99.0, round(100.0 - points_lost + class_bonus, 1)))

    return {
        "adjusted_time_sec": round(adjusted_time, 2),
        "adjusted_time_str": format_seconds(adjusted_time),
        "pace_100m": round(pace_100, 2),
        "speed_figure": speed_figure,
        "is_exact_match": is_exact_match,
        "source_desc": source_desc,
        "weight_penalty_sec": round(weight_penalty, 2)
    }

def generate_all_bet_types(runners, race_number):
    """
    Generates tailored AI betting combinations for all TJK game types:
    - Ganyan & Plase (Tekli)
    - İkili & Sıralı İkili
    - Plase İkili
    - 3'lü Bahis (Trio - Sıralı & Virgüllü)
    - Tabela Bahis (4'lü Bahis - Sıralı & Virgüllü)
    - Sıralı 5'li Bahis
    - Çifte Bahis
    """
    if not runners:
        return {}
        
    top1 = runners[0]
    top2 = runners[1] if len(runners) > 1 else runners[0]
    top3 = runners[2] if len(runners) > 2 else top2
    top4 = runners[3] if len(runners) > 3 else top3
    top5 = runners[4] if len(runners) > 4 else top4
    
    value_bet = next((r for r in runners if r.get("is_value_bet")), None)
    
    # 1. GANYAN & PLASE
    ganyan_pick = {
        "horse_number": top1["number"],
        "horse_name": top1["name"],
        "win_probability": top1["win_probability"],
        "recommendation": "Banko Tek" if top1["win_probability"] >= 28 else "Öncelikli Tek",
        "value_alternative": {
            "horse_number": value_bet["number"],
            "horse_name": value_bet["name"],
            "agf": value_bet.get("agf", 0)
        } if value_bet else None
    }
    
    # 2. İKİLİ (İ) & SIRALI İKİLİ (S.İ)
    ikili_picks = [
        {"combo": f"{top1['number']} - {top2['number']}", "names": f"{top1['name']} & {top2['name']}", "confidence": "Yüksek (Asıl İkili)"},
        {"combo": f"{top1['number']} - {top3['number']}", "names": f"{top1['name']} & {top3['name']}", "confidence": "Kuvvetli Alternatif"}
    ]
    if value_bet and value_bet["number"] not in [top1["number"], top2["number"]]:
        ikili_picks.append({"combo": f"{top1['number']} - {value_bet['number']}", "names": f"{top1['name']} & {value_bet['name']}", "confidence": "Bomba İkili"})
        
    sirali_ikili = {
        "primary": f"{top1['number']} / {top2['number']}",
        "cover": f"{top2['number']} / {top1['number']}",
        "tactic": f"{top1['number']} numaralı safkanın liderliğinde, arkasına {top2['number']} ve {top3['number']} yazılması önerilir."
    }
    
    # 3. PLASE İKİLİ (İlk 3'e girebilecek ikililer)
    plase_ikili = [
        f"{top1['number']} - {top2['number']}",
        f"{top1['number']} - {top3['number']}",
        f"{top2['number']} - {top3['number']}"
    ]
    
    # 4. 3'LÜ BAHİS (TRIO)
    uclu_bahis = {
        "sirali": f"{top1['number']} / {top2['number']} / {top3['number']}",
        "virgullu_template": f"{top1['number']} // {top2['number']}, {top3['number']} // {top2['number']}, {top3['number']}, {top4['number']}",
        "trio_box": [top1["number"], top2["number"], top3["number"], top4["number"]],
        "combination_count": 6
    }
    
    # 5. TABELA BAHİS (4'lü Bahis - Sıralı / Sırasız)
    tabela_bahis = {
        "sirali": f"{top1['number']} / {top2['number']} / {top3['number']} / {top4['number']}",
        "virgullu_template": f"{top1['number']} // {top2['number']}, {top3['number']} // {top2['number']}, {top3['number']}, {top4['number']} // {top2['number']}, {top3['number']}, {top4['number']}, {top5['number']}",
        "box_5_horses": [top1["number"], top2["number"], top3["number"], top4["number"], top5["number"]],
        "analysis": f"1. ayakta {top1['number']} tek korumalı; 2, 3 ve 4. ayaklara rakipleri dağıtılarak virgüllü tabela kuponu kurulması önerilir."
    }
    
    # 6. SIRALI 5'Lİ BAHİS (En büyük ikramiye)
    top6 = runners[5] if len(runners) > 5 else top5
    sirali_besli = {
        "sirali_ideal": f"{top1['number']} / {top2['number']} / {top3['number']} / {top4['number']} / {top5['number']}",
        "virgullu_core": [top1["number"], top2["number"], top3["number"], top4["number"], top5["number"], top6["number"]],
        "template_str": f"{top1['number']} // {top2['number']},{top3['number']} // {top2['number']},{top3['number']},{top4['number']} // {top3['number']},{top4['number']},{top5['number']} // {top4['number']},{top5['number']},{top6['number']}",
        "jackpot_potential": "Günün en yüksek ganyanlı sürpriz kombinasyonu"
    }
    
    # 7. ÇİFTE BAHİS
    cifte = {
        "leg1": top1["number"],
        "leg1_name": top1["name"],
        "partner": top2["number"],
        "recommendation": f"{race_number}. Koşuda {top1['number']} (veya {top2['number']}) safkan ile sonraki koşunun favorisi bağlanmalıdır."
    }

    return {
        "ganyan": ganyan_pick,
        "ikili": ikili_picks,
        "sirali_ikili": sirali_ikili,
        "plase_ikili": plase_ikili,
        "uclu_bahis": uclu_bahis,
        "tabela_bahis": tabela_bahis,
        "sirali_besli": sirali_besli,
        "cifte": cifte
    }

def predict_race(race):
    """
    Evaluates all runners in a race using enhanced ensemble handicapping:
    1. Track & Surface Affinity (25% weight)
    2. Surface-Specific Recent Form & Streak (22% weight)
    3. Master Jockey & Runner Synergy (18% weight)
    4. Beyer Speed Figure & Class-adjusted Time (15% weight)
    5. Gallop Consistency & Outlier Filtering (12% weight)
    6. Pedigree Bloodline Traits (8% weight)
    """
    runners = race.get("runners", [])
    if not runners:
        return race

    distance = race.get("distance", 1400)
    surface = race.get("surface", "Çim")
    race_type = race.get("race_type", "")
    race_name = race.get("name", "")
    is_maiden = "maiden" in (race_type + " " + race_name).lower()
    
    record_time_str = race.get("record_time", "")
    record_time_sec = parse_record_time_seconds(record_time_str, distance)
    track_condition = race.get("track_condition", "Normal")

    analyzed_runners = []

    for r in runners:
        # 1. Adjusted Finishing Time & Speed Figure (Maiden aware)
        time_analysis = calculate_adjusted_time(r, distance, surface, record_time_sec, is_maiden=is_maiden)

        # 2. Track & Surface Affinity
        surf_score, surf_runs, podium_runs, surf_details = analyze_track_affinity(r.get("last_6", ""), surface)

        # 3. Surface-specific form momentum
        surface_form = compute_surface_form(r.get("last_6", ""), surface)

        # 4. Gallop consistency & Outlier Filtering
        gallop_analysis = analyze_gallops(r.get("name", ""), r.get("gallops"), r.get("handicap", 35))

        # 5. Pedigree (Sire & Dam) aptitude
        pedigree_analysis = analyze_pedigree(r.get("sire", ""), r.get("dam", ""), surface, distance)

        # 6. Wet / Dry / Heavy track condition impact
        r_temp = {**r, "pedigree_analysis": pedigree_analysis}
        condition_analysis = analyze_track_condition_impact(r_temp, surface, track_condition)

        # 7. Jockey - Horse Synergy (Master jockey edge in Maiden)
        synergy_analysis = analyze_jockey_horse_synergy(r.get("jockey", ""), r.get("name", ""), r.get("weight", 58.0), r.get("last_6", ""), is_maiden=is_maiden)

        # 8. Career maturity and recency
        maturity_analysis = analyze_career_maturity(r.get("age", ""), r.get("last_6", ""), r.get("kgs", 20))

        # Multi-factor composite rating calculation
        composite_rating = (
            (surf_score * 0.25) +
            (surface_form * 0.22) +
            (synergy_analysis["synergy_score"] * 0.18) +
            (time_analysis["speed_figure"] * 0.15) +
            (gallop_analysis["gallop_score"] * 0.12) +
            (pedigree_analysis["score"] * 0.08)
        )

        analyzed_runners.append({
            **r,
            "time_analysis": time_analysis,
            "surface_affinity": {
                "score": surf_score,
                "runs_count": surf_runs,
                "podium_count": podium_runs,
                "details": surf_details
            },
            "gallop_analysis": gallop_analysis,
            "pedigree_analysis": pedigree_analysis,
            "condition_analysis": condition_analysis,
            "synergy_analysis": synergy_analysis,
            "maturity_analysis": maturity_analysis,
            "jockey_score": synergy_analysis["jockey_score"],
            "form_score": round(surface_form, 1),
            "composite_rating": round(composite_rating, 2)
        })

    # Sort runners strictly by composite rating
    analyzed_runners.sort(key=lambda x: x["composite_rating"], reverse=True)

    # Softmax probabilities
    ratings = [r["composite_rating"] for r in analyzed_runners]
    max_rating = max(ratings)
    temperature = 3.5
    exp_ratings = [math.exp((r - max_rating) / temperature) for r in ratings]
    sum_exp = sum(exp_ratings)

    for i, runner in enumerate(analyzed_runners):
        win_prob = round((exp_ratings[i] / sum_exp) * 100.0, 1)
        runner["rank"] = i + 1
        runner["win_probability"] = win_prob

        agf_val = runner.get("agf", 0.0)
        runner["is_agf_favorite"] = (agf_val >= 25.0 or (agf_val > 0 and agf_val == max(r.get("agf", 0) for r in analyzed_runners)))
        
        is_value_bet = False
        value_tag = ""
        if runner["rank"] <= 2 and agf_val < 15.0 and agf_val > 0:
            is_value_bet = True
            value_tag = "Cazip Oran / Bomba Potansiyeli"
        elif runner["rank"] == 1:
            value_tag = "Kuvvetli Banko Adayı" if win_prob >= 28.0 else "Öncelikli Favori"
        elif runner["rank"] in [2, 3]:
            value_tag = "Güçlü Plase / İkili Ortağı"
        elif runner["rank"] == 4:
            value_tag = "Tabela Takipçisi"
        else:
            value_tag = "Sürpriz Adayı"

        runner["value_tag"] = value_tag
        runner["is_value_bet"] = is_value_bet
        runner["rationale"] = generate_rationale(runner, distance, surface, i + 1, len(analyzed_runners))

    # Pace & Tactical map
    pace_overview = project_race_pace(analyzed_runners, distance, surface)

    # Comprehensive Betting Studio Predictions
    bet_recommendations = generate_all_bet_types(analyzed_runners, race.get("race_number", 1))

    return {
        **race,
        "record_time_sec": record_time_sec,
        "runners": analyzed_runners,
        "pace_overview": pace_overview,
        "winner_prediction": analyzed_runners[0] if analyzed_runners else None,
        "bet_recommendations": bet_recommendations
    }

def generate_rationale(runner, distance, surface, rank, total_runners):
    """
    Generates rich, transparent Turkish handicapping explanation.
    """
    ta = runner["time_analysis"]
    ga = runner["gallop_analysis"]
    sa = runner["surface_affinity"]
    pa = runner.get("pedigree_analysis", {})
    ca = runner.get("condition_analysis", {})
    syn = runner.get("synergy_analysis", {})
    mat = runner.get("maturity_analysis", {})
    w = runner["weight"]
    
    reasons = []

    if rank == 1:
        reasons.append(
            f"Grup genelinde {distance}m {surface} şartlarında en yüksek hız endeksine ({ta['speed_figure']} puan) "
            f"ve {ta['adjusted_time_str']} düzeltilmiş derece potansiyeline sahip olmasıyla 1. sıraya yerleşti."
        )
    elif rank == 2:
        reasons.append(
            f"Lidere çok yakın derece projeksiyonu ({ta['adjusted_time_str']}) ve "
            f"istikrarlı son koşu formuyla yarışın en ciddi birincilik ve ikili adayı."
        )
    elif rank == 3:
        reasons.append(
            f"Mesafe temposuna uyumlu düzeltilmiş derecesi ({ta['adjusted_time_str']}) ve "
            f"tabela istikrarı ile ilk 3 ve üçlü bahis için yüksek şansa sahip."
        )
    elif rank <= 5:
        reasons.append(
            f"Koşunun temposuna ayak uydurabilecek hızda; özellikle yarış içi pres ve son viraj sprintinde tabela ve sıralı beşli için sürpriz yapabilir."
        )
    else:
        reasons.append(
            f"Düzeltilmiş derecesi rakiplerinin gerisinde kaldı ({ta['adjusted_time_str']}); "
            f"geniş kuponlar için sürpriz hanesinde düşünülebilir."
        )

    # Pedigree trait
    if pa and pa.get("desc"):
        reasons.append(f"Orijin Analizi: {pa['desc']} ({pa['score']} puan).")

    # Track condition
    if ca and ca.get("notes"):
        reasons.append(f"Zemin Etkisi: {ca['notes']}")

    # Jockey synergy
    if syn and syn.get("details"):
        reasons.append(f"Jokey Uyumu: {syn['details']}")

    # Gallop consistency
    if ga.get("outlier_count", 0) > 0:
        reasons.append(
            f"Galop Analizi: Ölçü dışı / aşırı dalgalı {ga['outlier_count']} idman ayıklandı. "
            f"İstikrarlı galop temposu 400m {ga['mean_400_pace']} sn olarak tespit edildi ({ga['gallop_score']} puan)."
        )
    else:
        reasons.append(
            f"Galop Analizi: İdmanlarında dalgalanma görülmedi, son 400m derecesi {ga['mean_400_pace']} sn ile "
            f"tutarlı sprint formu sergiledi ({ga['gallop_score']} puan)."
        )

    # Weight note
    if w <= 54.5:
        reasons.append(f"{w} kg ile belirgin sıklet avantajı taşıyor.")
    elif w >= 60.0:
        reasons.append(f"{w} kg ağır sıkleti dereceye yaklaşık +{ta['weight_penalty_sec']} sn etki yapabilir.")

    return " ".join(reasons)

def project_race_pace(runners, distance, surface):
    """
    Project tactical race pace (Liderlik mücadelesi, tempo tahmini).
    """
    styles = {"Kaçak (Öncü)": [], "Presçi (Takipçi)": [], "Bekleme (Sprinter)": []}
    
    for r in runners:
        mean_sprint = r["gallop_analysis"]["mean_400_pace"]
        gate = r.get("gate", 5)

        if mean_sprint < 24.8 and gate <= 5:
            styles["Kaçak (Öncü)"].append(r["name"].split()[0])
        elif mean_sprint < 25.8:
            styles["Presçi (Takipçi)"].append(r["name"].split()[0])
        else:
            styles["Bekleme (Sprinter)"].append(r["name"].split()[0])

    front_count = len(styles["Kaçak (Öncü)"])
    if front_count >= 3:
        tempo = "Çok Hızlı / Kırıcı Tempo"
        tempo_desc = "Önde birden fazla kaçak at liderlik kavgasına gireceğinden son virajda sprinterlerin şansı katlanacaktır."
    elif front_count >= 1:
        tempo = "Dengeli / Standart Tempo"
        tempo_desc = "Yarış makul bir tempoda başlayacak; virajı iyi dönen ön grup avantajını koruyabilir."
    else:
        tempo = "Ağır / Taktik Yarışı"
        tempo_desc = "Kaçak at bulunmadığından düşük tempolu yarış bekleniyor. Diri kalan atlar son sprintle sonuca gidecektir."

    return {
        "tempo": tempo,
        "tempo_description": tempo_desc,
        "front_runners": styles["Kaçak (Öncü)"],
        "pressers": styles["Presçi (Takipçi)"],
        "closers": styles["Bekleme (Sprinter)"]
    }
