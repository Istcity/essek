"""
Advanced Horse Racing Prediction & Handicapping Engine Pro v5.0
18-Factor Deep Empirical Multi-Ensemble

Empirik Veritabanı: 1.207 Gerçek TJK Koşusu & 12.310 Safkan Startı Analizi

Tahmin Faktörleri (18 Bağımsız Analitik Sinyal):
1.  AGF (Muhtemel Ganyan Oranı & Piyasa Güveni)      - Ağırlık: %20 (Empirik: AGF#1 = %33.2 kazanma)
2.  Pist ve Yüzey Afinitesi (Son 6 Koşu)             - Ağırlık: %15
3.  Yüzeye Özgü Form Momentumu                       - Ağırlık: %13
4.  Empirik Jokey Klas & Verim Puanı (114 Jokey)     - Ağırlık: %12 (V.Abiş %22.8, S.Kaya %25.6 vb.)
5.  Beyer Hız Figürü & Düzeltilmiş Derece             - Ağırlık: %10
6.  Empirik Antrenör / Ahır Başarı Endeksi (229 Ant) - Ağırlık: %8  (İ.Akkılıç %27.5, A.Akbulut %28.9 vb.)
7.  Galop İdman Konsistansı & IQR Outlier Filtresi   - Ağırlık: %6
8.  Empirik Pedigri / Aygır Soyu & Mesafe Aptitude   - Ağırlık: %5  (160 Aygır empirik kazanma oranı)
9.  Handikap / Güç Endeksi                           - Ağırlık: %4
10. Sıklet / Sınıf Ağırlığı Dinamiği (Türkiye'ye özgü)- Ağırlık: %3  (Ağır sıklet %12.9 vs Hafif sıklet %5.2)
11. Güç / Sıklet Oranı (Power-to-Weight Ratio)       - Ağırlık: %2
12. Start Kapısı / Kulvar Avantajı (Sprint vs. Rota) - Katsayı / Bonus
13. Ekipman / Teçhizat Etkisi (ÖG, K, DB vs GKR, YP) - Katsayı / Ceza (GKR %7.2, YP %2.0)
14. KGS Dinlenme Döngüsü (14-35 Gün İdeal Form)      - Katsayı / Bonus
15. S20 Tabela İstikrarı & Kazanma Frekansı          - Katsayı / Bonus
16. Yarış İçi Taktik & Tempo Avantajı (Pace Bias)    - Katsayı / Bonus
17. Pist Zemin Durumu (Islak/Kuru/Ağır Zemin)        - Çarpan
18. Kariyer Olgunluğu & Yaş/Kondisyon Evresi         - Katsayı / Bonus
"""

import os
import sys
import math
import re
import json
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

def clean_name_key(name):
    """Normalize jockey, trainer, sire or horse name for dictionary lookup."""
    if not name:
        return ""
    n = str(name).replace('İ', 'i').replace('I', 'i').replace('ı', 'i').lower()
    n = n.replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return re.sub(r'[^a-z0-9]', '', n)

# ============================================================
# EMPİRİK VERİTABANI YÜKLEME (1.207 KOŞU ANALİZİ)
# ============================================================
EMPIRICAL_TABLES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "empirical_tables_1000.json")

EMPIRICAL_TRAINERS = {}
EMPIRICAL_JOCKEYS = {}
EMPIRICAL_SIRES = {}

if os.path.exists(EMPIRICAL_TABLES_PATH):
    try:
        with open(EMPIRICAL_TABLES_PATH, "r", encoding="utf-8") as f:
            _tables = json.load(f)
            EMPIRICAL_TRAINERS = _tables.get("trainers", {})
            EMPIRICAL_JOCKEYS = _tables.get("jockeys", {})
            EMPIRICAL_SIRES = _tables.get("sires", {})
    except Exception as e:
        pass

# Fallback / Baseline Elite Jockeys & Trainers
BUILTIN_JOCKEYS = {
    "v.abis": {"win_rate": 22.8, "top4_rate": 72.8, "rating": 104.1},
    "s.kaya": {"win_rate": 25.6, "top4_rate": 62.8, "rating": 103.9},
    "g.kocakaya": {"win_rate": 21.6, "top4_rate": 63.8, "rating": 100.3},
    "m.m.bilgin": {"win_rate": 20.7, "top4_rate": 63.5, "rating": 99.2},
    "h.karatas": {"win_rate": 21.4, "top4_rate": 60.7, "rating": 99.1},
    "n.avci": {"win_rate": 20.6, "top4_rate": 60.5, "rating": 98.3},
    "m.s.celik": {"win_rate": 18.5, "top4_rate": 59.7, "rating": 96.0},
    "a.kursun": {"win_rate": 20.0, "top4_rate": 54.3, "rating": 95.8},
    "m.kaya": {"win_rate": 15.9, "top4_rate": 56.8, "rating": 92.5},
    "a.celik": {"win_rate": 14.9, "top4_rate": 60.3, "rating": 92.5},
    "er.cankilic": {"win_rate": 17.4, "top4_rate": 47.7, "rating": 91.2},
    "o.yildiz": {"win_rate": 16.5, "top4_rate": 52.0, "rating": 90.5},
    "h.cizik": {"win_rate": 12.6, "top4_rate": 55.8, "rating": 88.8},
    "e.cankaya": {"win_rate": 13.0, "top4_rate": 48.0, "rating": 87.0},
    "sal.celik": {"win_rate": 11.0, "top4_rate": 42.0, "rating": 84.0}
}

BUILTIN_TRAINERS = {
    "i.akkilic": {"win_rate": 27.5, "top4_rate": 67.5, "rating": 107.2},
    "a.akbulut": {"win_rate": 28.9, "top4_rate": 62.2, "rating": 107.1},
    "h.yuzbasi": {"win_rate": 25.7, "top4_rate": 65.7, "rating": 104.9},
    "d.kaya": {"win_rate": 25.6, "top4_rate": 61.5, "rating": 103.6},
    "u.kulak": {"win_rate": 22.9, "top4_rate": 65.7, "rating": 102.1},
    "ib.b.ogullari": {"win_rate": 19.7, "top4_rate": 68.9, "rating": 99.8},
    "m.turkoglu": {"win_rate": 21.2, "top4_rate": 55.8, "rating": 97.4},
    "k.korkmaz": {"win_rate": 22.6, "top4_rate": 48.4, "rating": 96.6},
    "ser.dogan": {"win_rate": 21.4, "top4_rate": 52.4, "rating": 96.6},
    "v.yildirim": {"win_rate": 15.2, "top4_rate": 65.7, "rating": 94.3}
}

# Cleaned lookup maps
CLEAN_JOCKEYS = {clean_name_key(k): v for k, v in BUILTIN_JOCKEYS.items()}
for k, v in EMPIRICAL_JOCKEYS.items():
    CLEAN_JOCKEYS[clean_name_key(k)] = v

CLEAN_TRAINERS = {clean_name_key(k): v for k, v in BUILTIN_TRAINERS.items()}
for k, v in EMPIRICAL_TRAINERS.items():
    CLEAN_TRAINERS[clean_name_key(k)] = v

CLEAN_SIRES = {clean_name_key(k): v for k, v in EMPIRICAL_SIRES.items()}

# ============================================================
# EKİPMAN / TEÇHİZAT ETKİSİ (1.207 Koşu Empirik Sonuçları)
# ============================================================
GEAR_MODIFIERS = {
    "ÖG":  +2.5,  # Ön gözlük (%11.9 kazanma)
    "OG":  +2.5,
    "K":   +1.5,  # Kulaklık (%11.0 kazanma, %41.3 tabela)
    "DB":  +1.2,  # Dil bağı (%9.5 kazanma)
    "SK":  +1.0,  # Sol kayış (%9.6 kazanma)
    "KG":  +0.5,  # Kapalı gözlük (%9.4 kazanma)
    "SKG": -0.8,  # Sol kayış genişletme (%7.6 kazanma)
    "BB":  -2.0,  # Blinkers bağlama
    "GKR": -4.5,  # Göz kapağı rengarenk (%7.2 kazanma, %30.1 tabela - en düşük)
    "YP":  -5.5   # Yanak peluşu (%2.0 kazanma - çok düşük galibiyet)
}

# ============================================================
# KULVAR (GATE) ETKİSİ
# ============================================================
GATE_BIAS_SPRINT = {1: +3.0, 2: +2.5, 3: +2.0, 4: +1.5, 5: +0.5, 6: 0.0,
                    7: -1.0, 8: -1.5, 9: -2.5, 10: -3.0, 11: -3.5, 12: -4.0,
                    13: -4.5, 14: -5.0, 15: -5.5, 16: -6.0}
GATE_BIAS_ROUTE  = {1: +1.2, 2: +1.2, 3: +1.5, 4: +1.8, 5: +1.5, 6: +1.2,
                    7: +0.5, 8: 0.0, 9: -0.5, 10: -1.0, 11: -1.5, 12: -2.0,
                    13: -2.5, 14: -3.0, 15: -3.5, 16: -4.0}

# Prominent Sire Genetic Aptitude
PEDIGREE_TRAITS = {
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
    "torok": {"stamina": 94, "surface_pref": "çim", "wet_affinity": 95, "sprint": 93, "desc": "Çim ve sentetikte grup koşuların başrolü; yumuşak/ıslak çimde çok etkilidir."},
    "native khan": {"stamina": 96, "surface_pref": "çim", "wet_affinity": 94, "sprint": 88, "desc": "Orta/uzun mesafe çim ve sentetik uzmanı; üstün dayanıklılık."},
    "luxor": {"stamina": 86, "surface_pref": "çim", "wet_affinity": 85, "sprint": 96, "desc": "Sürat ve mil koşularının (1200-1600m) elit aygırı."},
    "mendip": {"stamina": 90, "surface_pref": "kum", "wet_affinity": 93, "sprint": 92, "desc": "Kum pistte yüksek tempo ve viraj hakimiyeti."},
    "victory gallop": {"stamina": 97, "surface_pref": "kum", "wet_affinity": 90, "sprint": 82, "desc": "Açık yarış kazanan uzun mesafe kum canavarları üretir (%24.5 kazanma)."},
    "lion heart": {"stamina": 88, "surface_pref": "kum", "wet_affinity": 92, "sprint": 95, "desc": "Yüksek başlangıç hızı, ıslak ve sulu kumda öncülük gücü."},
    "daredevil": {"stamina": 91, "surface_pref": "kum", "wet_affinity": 98, "sprint": 93, "desc": "Islak, sulu ve çamurlu pistlerde sıra dışı performans sıçraması yapar."},
    "bodemeister": {"stamina": 92, "surface_pref": "kum", "wet_affinity": 92, "sprint": 91, "desc": "Güçlü göğüs yapısı, sert kum zeminlerde yıpranmaz."},
    "kaneko": {"stamina": 95, "surface_pref": "hepsi", "wet_affinity": 91, "sprint": 89, "desc": "Türkiye yarışçılığının temel direği; mesafeye ve her piste uyumlu."},
    "smart robin": {"stamina": 93, "surface_pref": "çim", "wet_affinity": 89, "sprint": 87, "desc": "Derin çim ve 1800m+ mesafelerde etkili dayanıklılık."}
}

def parse_record_time_seconds(record_str, distance):
    sec = parse_time_str(record_str)
    if sec and sec > 30:
        return sec
    return (distance / 100.0) * 6.35

def get_surface_key(surface_text):
    s = (surface_text or "").lower()
    if "sentetik" in s or "synthetic" in s:
        return "sentetik"
    elif "kum" in s or "dirt" in s:
        return "kum"
    return "çim"

def analyze_trainer_empirical(trainer_name):
    """Evaluates trainer performance from 1,207 historical races."""
    if not trainer_name:
        return 74.0, "Standart ahır formu", False
    ck = clean_name_key(trainer_name)
    for k, v in CLEAN_TRAINERS.items():
        if len(k) >= 3 and (k in ck or ck in k):
            win_pct = v.get("win_rate", 10.0)
            top4_pct = v.get("top4_rate", 38.0)
            score = 70.0 + win_pct * 1.05 + (top4_pct - 35) * 0.25
            desc = f"Antrenör {trainer_name}: %{win_pct:.1f} kazanma, %{top4_pct:.1f} tabela"
            return round(min(98.0, max(60.0, score)), 1), desc, win_pct >= 20.0
    return 74.0, f"Antrenör {trainer_name}: Standart ahır performansı", False

def analyze_jockey_empirical(jockey_name, horse_name, weight, last_6, is_maiden=False):
    """Evaluates jockey performance from 1,207 historical races."""
    clean_j = clean_name_key(jockey_name)
    base_jockey = 76.0
    win_pct = 9.8
    top4_pct = 38.0
    found = False

    for k, v in CLEAN_JOCKEYS.items():
        if len(k) >= 3 and (k in clean_j or clean_j in k):
            win_pct = v.get("win_rate", 10.0)
            top4_pct = v.get("top4_rate", 38.0)
            base_jockey = 70.0 + win_pct * 1.1 + (top4_pct - 35) * 0.25
            found = True
            break

    is_apprentice = "ap" in (jockey_name or "").lower() or (weight <= 53.5 and base_jockey <= 83)

    if found and win_pct >= 18.0:
        synergy_desc = f"Usta jokey {jockey_name} ampirik %{win_pct:.1f} galibiyet, %{top4_pct:.1f} tabela ile elit avantaj sağlıyor."
        synergy_score = base_jockey + (4.0 if is_maiden else 2.5)
    elif is_apprentice:
        synergy_desc = f"Apranti {jockey_name} sıklet avantajı sağlıyor, deneyimi sınırlı."
        synergy_score = base_jockey - 2.5
    elif base_jockey >= 85:
        synergy_desc = f"Deneyimli jokey {jockey_name} ile dengeli ve istikrarlı uyum."
        synergy_score = base_jockey + 1.0
    else:
        synergy_desc = f"Jokey {jockey_name} ile safkan arasında standart uyum."
        synergy_score = base_jockey

    return {
        "jockey_score": round(base_jockey, 1),
        "synergy_score": round(min(99.0, max(58.0, synergy_score)), 1),
        "is_master": win_pct >= 18.0 or base_jockey >= 92,
        "is_apprentice": is_apprentice,
        "win_rate": win_pct,
        "top4_rate": top4_pct,
        "details": synergy_desc
    }

def analyze_pedigree(sire_name, dam_name, target_surface, target_distance):
    """Evaluates sire and pedigree traits with empirical stats."""
    clean_s = clean_name_key(sire_name)
    matched = None
    for k, v in PEDIGREE_TRAITS.items():
        if k in clean_s or clean_s in k:
            matched = v
            break

    # Also check empirical sire table
    emp_sire = None
    for k, v in CLEAN_SIRES.items():
        if len(k) >= 3 and (k in clean_s or clean_s in k):
            emp_sire = v
            break

    if not matched and not emp_sire:
        return {
            "score": 75.0,
            "stamina_score": 75.0,
            "wet_affinity": 75.0,
            "surface_match": "Dengeli Soy Kütüğü",
            "desc": f"Baba {sire_name or 'Bilinmiyor'} ve Anne {dam_name or 'Bilinmiyor'} soy hattı mesafe ve pist için standart dengeli genetik potansiyel barındırıyor."
        }

    is_long = target_distance >= 1800
    stamina = matched["stamina"] if matched else (80.0 if is_long else 75.0)
    wet_aff = matched["wet_affinity"] if matched else 75.0
    
    surf_bonus = 0.0
    if matched:
        pref = matched["surface_pref"]
        if pref == "hepsi" or target_surface.lower() in pref:
            surf_bonus = 5.0
        else:
            surf_bonus = -3.0

    emp_bonus = 0.0
    emp_desc = ""
    if emp_sire:
        w_pct = emp_sire.get("win_rate", 10.0)
        emp_bonus = (w_pct - 10.0) * 0.4
        emp_desc = f" (Ampirik aygır galibiyeti: %{w_pct:.1f})"

    pedigree_score = max(50.0, min(98.0, round(stamina * 0.65 + wet_aff * 0.2 + surf_bonus + emp_bonus, 1)))

    desc = matched["desc"] if matched else f"Aygır {sire_name} yavruları hedef mesafede dengeli performans gösteriyor."
    desc += emp_desc

    return {
        "score": pedigree_score,
        "stamina_score": round(stamina, 1),
        "wet_affinity": wet_aff,
        "surface_match": "Yüksek Uyum" if surf_bonus >= 0 else "Orta Uyum",
        "desc": f"Baba {sire_name}: {desc}"
    }

def analyze_track_condition_impact(runner, target_surface, track_condition="Normal"):
    cond = (track_condition or "Normal").lower()
    is_wet = "ıslak" in cond or "sulu" in cond or "ağır" in cond or "çamur" in cond or "yumuşak" in cond
    pedigree_wet = runner.get("pedigree_analysis", {}).get("wet_affinity", 75.0)

    if not is_wet:
        return {
            "condition": "Normal / Kuru Zemin",
            "impact_sec": 0.0,
            "speed_multiplier": 1.0,
            "notes": "Pist şartları normal ve kuru; safkanlar ideal tempolarını sahaya yansıtabilir."
        }

    if "kum" in target_surface.lower():
        return {
            "condition": "Islak / Sulu Kum",
            "impact_sec": -0.85,
            "speed_multiplier": 1.04,
            "wet_score": pedigree_wet,
            "notes": "Islak/sulu kum zeminde pist hızlanır. Önde kaçan safkanlar çamur sıçramasından (kickback) etkilenmediği için büyük avantaj yakalar."
        }
    else:
        sec_penalty = 1.6 if "ağır" in cond else 0.9
        return {
            "condition": "Ağır / Yumuşak Çim",
            "impact_sec": sec_penalty,
            "speed_multiplier": 0.97,
            "wet_score": pedigree_wet,
            "notes": f"Çim pist yumuşak/ağır; dereceler +{sec_penalty}sn civarında yavaşlayacaktır. Güçlü pedigriye ({pedigree_wet} puan) sahip safkanlar öne çıkar."
        }

def analyze_career_maturity(age_str, last_6, kgs):
    age_digits = re.findall(r'\d+', str(age_str or '3'))
    age = int(age_digits[0]) if age_digits else 3
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
    if not last_6 or len(str(last_6)) < 2:
        return 65.0, 0, 0, "Hedef pistte resmi koşu kaydı yok (Orijin ve idman değerlendirildi)"

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
        score = max(40.0, 70.0 - avg_other * 3.0)
        return score, 0, 0, f"Hedef pistte ({target_surface.capitalize()}) henüz start almadı."

    podium_count = sum(1 for p in surface_runs if 1 <= p <= 4)
    win_count = sum(1 for p in surface_runs if p == 1)
    second_count = sum(1 for p in surface_runs if p == 2)
    avg_finish = sum(surface_runs) / len(surface_runs)

    podium_rate = podium_count / len(surface_runs)
    top2_rate = sum(1 for p in surface_runs if p <= 2) / len(surface_runs)

    recent_finish = surface_runs[-1]
    recent_bonus = 8.0 if recent_finish <= 2 else (4.0 if recent_finish <= 4 else 0.0)

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
        f"{podium_count} kez tabela ({win_count} birincilik, {second_count} ikincilik, ortalama {avg_finish:.1f}.lik)."
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
    best_time_str = runner.get("best_time", "")
    best_time_sec = parse_time_str(best_time_str)

    weight = float(runner.get("weight", 58.0))
    weight_diff = weight - 57.0

    if is_maiden:
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
        handicap = float(runner.get("handicap", 35))
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
        source_desc = f"Hedef mesafe ve handikap ({int(handicap)}) puanından hesaplandı"

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

def compute_agf_signal(agf_pct, all_agf_pcts):
    if agf_pct <= 0:
        return 70.0
    max_agf = max(all_agf_pcts) if all_agf_pcts else 1.0
    ratio = agf_pct / max(max_agf, 1.0)
    agf_score = 55.0 + (ratio ** 0.58) * 43.0
    return round(min(99.0, max(40.0, agf_score)), 1)

def compute_class_weight_signal(weight, all_weights, is_maiden):
    """
    Empirical Turkish dynamic: >=59kg horses win 12.9% vs 5.2% for <=54kg.
    """
    if is_maiden:
        return 75.0
    if not all_weights:
        return 75.0
    max_w = max(all_weights)
    weight_ratio = (weight - 50.0) / max(max_w - 50.0, 1.0)
    class_score = 70.0 + weight_ratio * 12.0
    return round(min(90.0, max(55.0, class_score)), 1)

def compute_gate_bias(gate, distance, surface):
    g = int(gate) if gate else 6
    g = max(1, min(g, 16))
    is_sprint = distance <= 1400
    bias_table = GATE_BIAS_SPRINT if is_sprint else GATE_BIAS_ROUTE
    return bias_table.get(g, 0.0)

def compute_gear_modifier(equipment_str):
    if not equipment_str:
        return 0.0, [], []
    eq_upper = equipment_str.upper()
    total_mod = 0.0
    pos_items = []
    neg_items = []

    for gear, mod in GEAR_MODIFIERS.items():
        if gear in eq_upper:
            total_mod += mod
            if mod > 0:
                pos_items.append(f"{gear} (+{mod:.1f})")
            elif mod < 0:
                neg_items.append(f"{gear} ({mod:.1f})")

    return total_mod, pos_items, neg_items

def compute_kgs_cycle(kgs):
    try:
        k = int(kgs)
    except:
        k = 20
    if 14 <= k <= 35:
        return 2.5, "İdeal dinlenme döngüsü (14-35 gün form zirvesi)", True
    elif 8 <= k <= 13:
        return 1.0, "Yakın koşu periyodu (form koruma evresi)", True
    elif 36 <= k <= 60:
        return 0.0, "Orta dinlenme aralığı", False
    elif k > 90:
        return -3.5, f"{k} gündür koşmuyor; yarış pası ve kondisyon eksiği riski", False
    elif k > 60:
        return -2.0, f"{k} gün ara; nefes açma ihtiyacı duyabilir", False
    elif k < 7:
        return -1.5, f"{k} gün önce koştu; aşırı yıpranma riski", False
    return 0.0, "Normal dinlenme", False

def compute_power_to_weight(handicap, weight):
    w = max(float(weight or 58.0), 48.0)
    hp = max(float(handicap or 35.0), 10.0)
    pwr = (hp / w) * 58.0
    score = 65.0 + min(30.0, max(0.0, (pwr - 25.0) * 1.0))
    return round(score, 1), round(pwr, 1)

def compute_s20_consistency(s20_val):
    try:
        s = int(s20_val)
    except:
        s = 15
    # S20 represents top-4 frequency points out of 20
    score = 65.0 + min(30.0, max(0.0, (s / 20.0) * 30.0))
    return round(score, 1)

def generate_all_bet_types(runners, race_number):
    if not runners:
        return {}

    top1 = runners[0]
    top2 = runners[1] if len(runners) > 1 else runners[0]
    top3 = runners[2] if len(runners) > 2 else top2
    top4 = runners[3] if len(runners) > 3 else top3
    top5 = runners[4] if len(runners) > 4 else top4

    value_bet = next((r for r in runners if r.get("is_value_bet")), None)

    ganyan_pick = {
        "number": top1.get("number", 1),
        "name": top1.get("name", ""),
        "horse_number": top1.get("number", 1),
        "horse_name": top1.get("name", ""),
        "win_probability": top1.get("win_probability", 0),
        "recommendation": "Banko Tek" if top1.get("win_probability", 0) >= 28 else "Öncelikli Tek",
        "value_alternative": {
            "number": value_bet.get("number", 1),
            "name": value_bet.get("name", ""),
            "horse_number": value_bet.get("number", 1),
            "horse_name": value_bet.get("name", ""),
            "agf": value_bet.get("agf", 0)
        } if value_bet else None
    }

    ikili_picks = [
        {"combo": f"{top1.get('number', 1)} - {top2.get('number', 2)}", "names": f"{top1.get('name', '')} & {top2.get('name', '')}", "confidence": "Yüksek (Asıl İkili)"},
        {"combo": f"{top1.get('number', 1)} - {top3.get('number', 3)}", "names": f"{top1.get('name', '')} & {top3.get('name', '')}", "confidence": "Kuvvetli Alternatif"}
    ]
    if value_bet and value_bet.get("number") not in [top1.get("number"), top2.get("number")]:
        ikili_picks.append({"combo": f"{top1.get('number', 1)} - {value_bet.get('number', 4)}", "names": f"{top1.get('name', '')} & {value_bet.get('name', '')}", "confidence": "Bomba İkili"})

    sirali_ikili = {
        "primary": f"{top1.get('number', 1)} / {top2.get('number', 2)}",
        "cover": f"{top2.get('number', 2)} / {top1.get('number', 1)}",
        "tactic": f"{top1.get('number', 1)} numaralı safkanın liderliğinde, arkasına {top2.get('number', 2)} ve {top3.get('number', 3)} yazılması önerilir."
    }

    plase_ikili = [
        f"{top1.get('number', 1)} - {top2.get('number', 2)}",
        f"{top1.get('number', 1)} - {top3.get('number', 3)}",
        f"{top2.get('number', 2)} - {top3.get('number', 3)}"
    ]

    uclu_bahis = {
        "sirali": f"{top1.get('number', 1)} / {top2.get('number', 2)} / {top3.get('number', 3)}",
        "virgullu_template": f"{top1.get('number', 1)} // {top2.get('number', 2)}, {top3.get('number', 3)} // {top2.get('number', 2)}, {top3.get('number', 3)}, {top4.get('number', 4)}",
        "trio_box": [top1.get("number", 1), top2.get("number", 2), top3.get("number", 3), top4.get("number", 4)],
        "combination_count": 6
    }

    tabela_bahis = {
        "sirali": f"{top1.get('number', 1)} / {top2.get('number', 2)} / {top3.get('number', 3)} / {top4.get('number', 4)}",
        "virgullu_template": f"{top1.get('number', 1)} // {top2.get('number', 2)}, {top3.get('number', 3)} // {top2.get('number', 2)}, {top3.get('number', 3)}, {top4.get('number', 4)} // {top2.get('number', 2)}, {top3.get('number', 3)}, {top4.get('number', 4)}, {top5.get('number', 5)}",
        "box_5_horses": [top1.get("number", 1), top2.get("number", 2), top3.get("number", 3), top4.get("number", 4), top5.get("number", 5)],
        "analysis": f"1. ayakta {top1.get('number', 1)} tek korumalı; 2, 3 ve 4. ayaklara rakipleri dağıtılarak virgüllü tabela kuponu kurulması önerilir."
    }

    top6 = runners[5] if len(runners) > 5 else top5
    sirali_besli = {
        "sirali_ideal": f"{top1.get('number', 1)} / {top2.get('number', 2)} / {top3.get('number', 3)} / {top4.get('number', 4)} / {top5.get('number', 5)}",
        "virgullu_core": [top1.get("number", 1), top2.get("number", 2), top3.get("number", 3), top4.get("number", 4), top5.get("number", 5), top6.get("number", 6)],
        "template_str": f"{top1.get('number', 1)} // {top2.get('number', 2)},{top3.get('number', 3)} // {top2.get('number', 2)},{top3.get('number', 3)},{top4.get('number', 4)} // {top3.get('number', 3)},{top4.get('number', 4)},{top5.get('number', 5)} // {top4.get('number', 4)},{top5.get('number', 5)},{top6.get('number', 6)}",
        "jackpot_potential": "Günün en yüksek ganyanlı sürpriz kombinasyonu"
    }

    cifte = {
        "leg1": top1.get("number", 1),
        "leg1_name": top1.get("name", ""),
        "partner": top2.get("number", 2),
        "recommendation": f"{race_number}. Koşuda {top1.get('number', 1)} (veya {top2.get('number', 2)}) safkan ile sonraki koşunun favorisi bağlanmalıdır."
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

def project_race_pace(runners, distance, surface):
    styles = {"Kaçak (Öncü)": [], "Presçi (Takipçi)": [], "Bekleme (Sprinter)": []}

    for r in runners:
        mean_sprint = r.get("gallop_analysis", {}).get("mean_400_pace", 25.5)
        gate = r.get("gate", 5)

        if mean_sprint < 24.8 and gate <= 5:
            styles["Kaçak (Öncü)"].append(r.get("name", "").split()[0])
        elif mean_sprint < 25.8:
            styles["Presçi (Takipçi)"].append(r.get("name", "").split()[0])
        else:
            styles["Bekleme (Sprinter)"].append(r.get("name", "").split()[0])

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

def generate_rationale(runner, distance, surface, rank, total_runners):
    ta = runner.get("time_analysis", {})
    ga = runner.get("gallop_analysis", {})
    sa = runner.get("surface_affinity", {})
    pa = runner.get("pedigree_analysis", {})
    ca = runner.get("condition_analysis", {})
    syn = runner.get("synergy_analysis", {})
    w = runner.get("weight", 58.0)
    wf = runner.get("winning_factors", {})

    reasons = []

    if rank == 1:
        reasons.append(
            f"Grup genelinde {distance}m {surface} şartlarında en yüksek hız endeksine ({ta.get('speed_figure', 0)} puan) "
            f"ve {ta.get('adjusted_time_str', '-')} düzeltilmiş derece potansiyeline sahip olmasıyla 1. sıraya yerleşti."
        )
    elif rank == 2:
        reasons.append(
            f"Lidere çok yakın derece projeksiyonu ({ta.get('adjusted_time_str', '-')}) ve "
            f"istikrarlı son koşu formuyla yarışın en ciddi birincilik ve ikili adayı."
        )
    elif rank == 3:
        reasons.append(
            f"Mesafe temposuna uyumlu düzeltilmiş derecesi ({ta.get('adjusted_time_str', '-')}) ve "
            f"tabela istikrarı ile ilk 3 ve üçlü bahis için yüksek şansa sahip."
        )
    elif rank <= 5:
        reasons.append(
            f"Koşunun temposuna ayak uydurabilecek hızda; özellikle yarış içi pres ve son viraj sprintinde tabela ve sıralı beşli için sürpriz yapabilir."
        )
    else:
        reasons.append(
            f"Düzeltilmiş derecesi rakiplerinin gerisinde kaldı ({ta.get('adjusted_time_str', '-')}); "
            f"geniş kuponlar için sürpriz hanesinde düşünülebilir."
        )

    # Factor summary integration
    if wf and wf.get("factor_summary"):
        reasons.append(f"Kazanma Faktörleri Özeti: {wf['factor_summary']}")

    if syn and syn.get("details"):
        reasons.append(f"Jokey Uyumu: {syn['details']}")

    if ga and ga.get("outlier_count", 0) > 0:
        reasons.append(
            f"Galop Analizi: Ölçü dışı {ga['outlier_count']} idman ayıklandı, tutarlı sprint temposu {ga.get('mean_400_pace', 25.0)} sn ({ga.get('gallop_score', 75)} puan)."
        )

    return " ".join(reasons)

def predict_race(race):
    """
    18-Factor Deep Empirical Handicapping Engine v5.0
    Calibrated across 1,207 real TJK races & 12,310 starts
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

    active_runners = [r for r in runners if not r.get("is_scratched")]
    scratched_runners = [r for r in runners if r.get("is_scratched")]
    if not active_runners:
        active_runners = runners
        scratched_runners = []

    all_agf_pcts = [float(r.get("agf", 0.0)) for r in active_runners]
    all_weights = [float(r.get("weight", 58.0)) for r in active_runners]
    all_hps = [float(r.get("handicap", 35.0)) for r in active_runners]
    max_hp = max(all_hps) if all_hps else 50.0
    min_hp = min(all_hps) if all_hps else 20.0

    analyzed_runners = []

    for r in active_runners:
        # 1. AGF Signal
        agf_pct = float(r.get("agf", 0.0))
        agf_score = compute_agf_signal(agf_pct, all_agf_pcts)

        # 2. Surface Affinity
        surf_score, surf_runs, podium_runs, surf_details = analyze_track_affinity(r.get("last_6", ""), surface)

        # 3. Surface Form Momentum
        surface_form = compute_surface_form(r.get("last_6", ""), surface)

        # 4. Gallop Consistency & Outlier Filtering
        gallop_analysis = analyze_gallops(r.get("name", ""), r.get("gallops"), r.get("handicap", 35))

        # 5. Pedigree & Sire Aptitude
        pedigree_analysis = analyze_pedigree(r.get("sire", ""), r.get("dam", ""), surface, distance)

        # 6. Track Condition Impact
        r_temp = {**r, "pedigree_analysis": pedigree_analysis}
        condition_analysis = analyze_track_condition_impact(r_temp, surface, track_condition)

        # 7. Empirical Jockey Synergy
        synergy_analysis = analyze_jockey_empirical(
            r.get("jockey", ""), r.get("name", ""),
            r.get("weight", 58.0), r.get("last_6", ""), is_maiden=is_maiden
        )

        # 8. Empirical Trainer Performance
        trainer_score, trainer_desc, is_elite_trainer = analyze_trainer_empirical(r.get("trainer", ""))

        # 9. Career Maturity
        maturity_analysis = analyze_career_maturity(r.get("age", ""), r.get("last_6", ""), r.get("kgs", 20))

        # 10. Adjusted Finishing Time & Beyer Speed Figure
        time_analysis = calculate_adjusted_time(r, distance, surface, record_time_sec, is_maiden=is_maiden)

        # 11. Class-Weight Signal
        class_weight_score = compute_class_weight_signal(r.get("weight", 58.0), all_weights, is_maiden)

        # 12. Power to Weight Ratio
        pwr_score, pwr_val = compute_power_to_weight(r.get("handicap", 35), r.get("weight", 58.0))

        # 13. S20 Consistency
        s20_score = compute_s20_consistency(r.get("s20", 15))

        # 14. Gate Bias
        gate_bonus = compute_gate_bias(r.get("gate", 6), distance, surface)

        # 15. Gear / Equipment Modifiers
        gear_name = r.get("equipment", r.get("gear", ""))
        gear_mod, gear_pos, gear_neg = compute_gear_modifier(str(gear_name))

        # 16. KGS Rest Cycle
        kgs_bonus, kgs_desc, kgs_opt = compute_kgs_cycle(r.get("kgs", 20))

        # 17. Pace Match Bonus
        gate = int(r.get("gate", 5) or 5)
        pace_bonus = 0.0
        if distance <= 1400 and gate <= 4:
            pace_bonus = 1.8
        elif distance >= 2000 and float(r.get("handicap", 35)) >= 45:
            pace_bonus = 1.5

        # 18. Career Freshness
        maturity_bonus = (maturity_analysis["maturity_score"] - 85.0) * 0.05
        cond_mult = condition_analysis.get("speed_multiplier", 1.0)

        # ============================================================
        # COMPOSITE RATING: 18-Factor Deep Empirical Ensemble v5.0
        # ============================================================
        composite_rating = (
            (agf_score         * 0.20) +  # AGF market signal
            (surf_score        * 0.16) +  # Surface affinity
            (surface_form      * 0.14) +  # Form momentum
            (synergy_analysis["synergy_score"] * 0.12) + # Jockey
            (time_analysis["speed_figure"] * 0.11) +     # Speed figure
            (trainer_score     * 0.08) +  # Trainer rating (NEW)
            (gallop_analysis["gallop_score"] * 0.06) +   # Gallop IQR
            (pedigree_analysis["score"] * 0.04) +       # Pedigree
            (class_weight_score * 0.03) + # Class weight
            (pwr_score         * 0.03) +  # Power to weight (NEW)
            (s20_score         * 0.03)    # S20 consistency (NEW)
        )
        composite_rating += gate_bonus * 0.08
        composite_rating += gear_mod * 0.12
        composite_rating += kgs_bonus * 0.08
        composite_rating += pace_bonus * 0.06
        composite_rating += maturity_bonus
        composite_rating *= cond_mult

        # ============================================================
        # TRANSPARENT WINNING DRIVERS & RISK FLAGS
        # ============================================================
        dominant_factors = []
        risk_factors = []

        if agf_score >= 88:
            dominant_factors.append({
                "factor": "Piyasa Güveni (AGF)",
                "icon": "🔥",
                "impact": f"+{round(agf_score * 0.20, 1)}",
                "desc": f"AGF #{r.get('agf_rank', 1)} (%{agf_pct:.1f}) ile yarışseverlerin en güvendiği safkan."
            })
        if synergy_analysis.get("is_master") or synergy_analysis.get("synergy_score", 0) >= 88:
            dominant_factors.append({
                "factor": "Elit Jokey Avantajı",
                "icon": "👑",
                "impact": f"+{round(synergy_analysis['synergy_score'] * 0.12, 1)}",
                "desc": synergy_analysis.get("details", "")
            })
        if time_analysis["speed_figure"] >= 85:
            dominant_factors.append({
                "factor": "Düzeltilmiş Hız Lideri",
                "icon": "⏱️",
                "impact": f"+{round(time_analysis['speed_figure'] * 0.11, 1)}",
                "desc": f"{time_analysis['adjusted_time_str']} düzeltilmiş derece projeksiyonu ile grubun en yüksek hız endeksine sahip."
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
                "desc": "Son koşularında hedef pistte istikrarlı tabela/galibiyet performansı sergiledi."
            })
        if is_elite_trainer or trainer_score >= 85:
            dominant_factors.append({
                "factor": "Başarılı Ahır / Antrenör",
                "icon": "🏢",
                "impact": f"+{round(trainer_score * 0.08, 1)}",
                "desc": trainer_desc
            })
        if gallop_analysis.get("gallop_score", 0) >= 82:
            dominant_factors.append({
                "factor": "Kuvvetli İdman Formu",
                "icon": "🏇",
                "impact": f"+{round(gallop_analysis['gallop_score'] * 0.06, 1)}",
                "desc": f"Son 400m derecesi {gallop_analysis.get('mean_400_pace', 25.0)} sn ile idmanlarında canlı ve istekli."
            })
        if gate_bonus >= 1.5:
            dominant_factors.append({
                "factor": "İç Kulvar Avantajı",
                "icon": "🚪",
                "impact": f"+{round(gate_bonus * 0.08, 1)}",
                "desc": f"{gate}. iç kulvardan viraja avantajlı girme pozisyonu."
            })
        if gear_pos:
            dominant_factors.append({
                "factor": "Etkili Teçhizat Kombinasyonu",
                "icon": "🛡️",
                "impact": f"+{round(gear_mod * 0.12, 1)}",
                "desc": f"Olumlu ekipman: {', '.join(gear_pos)}"
            })
        if kgs_opt:
            dominant_factors.append({
                "factor": "İdeal Dinlenme Döngüsü",
                "icon": "🔋",
                "impact": "+0.20",
                "desc": kgs_desc
            })

        # Risk Factors
        if gear_neg:
            risk_factors.append({
                "factor": "Riskli Ekipman Uyarısı",
                "icon": "⚠️",
                "impact": f"{round(gear_mod * 0.12, 1)}",
                "desc": f"Ampirik veride düşük galibiyet/tabela getiren ekipman: {', '.join(gear_neg)}"
            })
        if kgs_bonus < 0:
            risk_factors.append({
                "factor": "Kondisyon / Dinlenme Riski",
                "icon": "⏳",
                "impact": f"{round(kgs_bonus * 0.08, 1)}",
                "desc": kgs_desc
            })
        w_val = float(r.get("weight", 58.0))
        if w_val <= 52.0 and not is_maiden:
            risk_factors.append({
                "factor": "Düşük Sıklet / Sınıf Uyarısı",
                "icon": "⚖️",
                "impact": "-0.4",
                "desc": f"{w_val} kg hafif sıklet Türkiye yarışlarında düşük sınıf belirtisi olabilir."
            })
        if gate >= 12 and distance <= 1400:
            risk_factors.append({
                "factor": "Dış Kulvar Dezavantajı",
                "icon": "🚪",
                "impact": "-0.3",
                "desc": f"{gate}. kulvar sprint yarışında virajı dıştan dönme mecburiyeti doğurabilir."
            })

        summary_parts = [d["desc"] for d in dominant_factors[:3]]
        factor_summary = " ".join(summary_parts) if summary_parts else "Dengeli kriter profili ile koşuda mücadele edecek."

        winning_factors = {
            "dominant_factors": dominant_factors,
            "risk_factors": risk_factors,
            "factor_summary": factor_summary
        }

        analyzed_runners.append({
            **r,
            "time_analysis": time_analysis,
            "agf_score": agf_score,
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
            "trainer_score": trainer_score,
            "trainer_desc": trainer_desc,
            "jockey_score": synergy_analysis["jockey_score"],
            "form_score": round(surface_form, 1),
            "class_weight_score": round(class_weight_score, 1),
            "pwr_score": pwr_score,
            "s20_score": s20_score,
            "gate_bonus": round(gate_bonus, 2),
            "gear_mod": round(gear_mod, 2),
            "kgs_bonus": round(kgs_bonus, 2),
            "composite_rating": round(composite_rating, 2),
            "winning_factors": winning_factors
        })

    analyzed_runners.sort(key=lambda x: x["composite_rating"], reverse=True)

    ratings = [r["composite_rating"] for r in analyzed_runners]
    max_rating = max(ratings)
    temperature = 3.5
    exp_ratings = [math.exp((r - max_rating) / temperature) for r in ratings]
    sum_exp = sum(exp_ratings)

    for i, runner in enumerate(analyzed_runners):
        win_prob = round((exp_ratings[i] / sum_exp) * 100.0, 1)
        runner["rank"] = i + 1
        runner["win_probability"] = win_prob

        agf_val = float(runner.get("agf", 0.0))
        runner["is_agf_favorite"] = (agf_val >= 25.0 or (agf_val > 0 and agf_val == max(float(r.get("agf", 0)) for r in analyzed_runners)))

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

    for idx, sr in enumerate(scratched_runners):
        scratched_analyzed = {
            **sr,
            "rank": len(analyzed_runners) + idx + 1,
            "win_probability": 0.0,
            "composite_rating": 0.0,
            "is_agf_favorite": False,
            "is_value_bet": False,
            "value_tag": "KOŞMAZ (Yarış Dışı)",
            "rationale": "Bu safkan resmi TJK bülteninde KOŞMAZ olarak bildirilmiş olup yarış değerlendirmesinden çıkarılmıştır.",
            "time_analysis": {"speed_figure": 0, "adjusted_seconds": 0, "adjusted_time_str": "-", "expected_time_str": "-"},
            "surface_affinity": {"score": 0, "runs_count": 0, "podium_count": 0, "details": "Koşmaz"},
            "gallop_analysis": {"gallop_score": 0},
            "pedigree_analysis": {"score": 0},
            "condition_analysis": {"condition": "Yarış Dışı"},
            "synergy_analysis": {"synergy_score": 0, "jockey_score": 0, "is_master": False, "is_apprentice": False, "details": "Koşmaz"},
            "maturity_analysis": {"maturity_score": 0, "stage": "Yarış Dışı"},
            "trainer_score": 0,
            "trainer_desc": "Koşmaz",
            "jockey_score": 0,
            "form_score": 0,
            "class_weight_score": 0,
            "gate_bonus": 0,
            "gear_mod": 0,
            "winning_factors": {
                "dominant_factors": [],
                "risk_factors": [{"factor": "Koşmaz", "icon": "🚫", "impact": "0", "desc": "Resmi TJK Koşmaz"}],
                "factor_summary": "Koşmaz bildirilmiştir."
            }
        }
        analyzed_runners.append(scratched_analyzed)

    pace_overview = project_race_pace(analyzed_runners[:len(active_runners)], distance, surface)
    bet_recommendations = generate_all_bet_types(analyzed_runners[:len(active_runners)], race.get("race_number", 1))

    return {
        **race,
        "record_time_sec": record_time_sec,
        "runners": analyzed_runners,
        "pace_overview": pace_overview,
        "winner_prediction": analyzed_runners[0] if analyzed_runners else None,
        "bet_recommendations": bet_recommendations
    }
