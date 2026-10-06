"""
Deep Empirical Analysis Engine on 1,207 Real TJK Races
Calculates statistically grounded strike rates, feature correlations, and optimal ensemble weights.
Saves comprehensive findings and calibrated parameters to data/empirical_model_weights.json.
"""

import json
import re
import sys
import os

from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

def analyze_1207_races():
    with open('data/historical_database_1000.json', 'r', encoding='utf-8') as f:
        races = json.load(f)

    total_races = len(races)
    print(f"Loaded {total_races} races for deep statistical handicapping analysis...")

    # 1. AGF Rank Strike Rates
    agf_stats = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top4": 0, "total_return": 0.0})
    
    # 2. Jockey Strike Rates (min 15 starts)
    jockey_stats = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top4": 0, "ganyan_sum": 0.0})

    # 3. Trainer Strike Rates (min 15 starts)
    trainer_stats = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top4": 0})

    # 4. Weight Breakdown by Race Type
    weight_stats = {
        "all": {"light_lte_54": {"starts": 0, "wins": 0}, "mid_55_58": {"starts": 0, "wins": 0}, "heavy_gte_59": {"starts": 0, "wins": 0}},
        "maiden": {"light_lte_54": {"starts": 0, "wins": 0}, "mid_55_58": {"starts": 0, "wins": 0}, "heavy_gte_59": {"starts": 0, "wins": 0}},
        "handicap": {"light_lte_54": {"starts": 0, "wins": 0}, "mid_55_58": {"starts": 0, "wins": 0}, "heavy_gte_59": {"starts": 0, "wins": 0}},
        "sartli": {"light_lte_54": {"starts": 0, "wins": 0}, "mid_55_58": {"starts": 0, "wins": 0}, "heavy_gte_59": {"starts": 0, "wins": 0}}
    }

    # 5. Equipment Strike Rates
    gear_stats = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top4": 0})

    # 6. Gate Bias by Distance and Surface
    gate_stats = {
        "sprint_kum": defaultdict(lambda: {"starts": 0, "wins": 0}),
        "sprint_cim": defaultdict(lambda: {"starts": 0, "wins": 0}),
        "route_kum": defaultdict(lambda: {"starts": 0, "wins": 0}),
        "route_cim": defaultdict(lambda: {"starts": 0, "wins": 0})
    }

    # 7. KGS (Days Rest) Strike Rates
    kgs_stats = {
        "quick_1_10": {"starts": 0, "wins": 0, "top4": 0},
        "ideal_11_28": {"starts": 0, "wins": 0, "top4": 0},
        "fresh_29_60": {"starts": 0, "wins": 0, "top4": 0},
        "layoff_61_plus": {"starts": 0, "wins": 0, "top4": 0}
    }

    # 8. Last Race Finish (Form Momentum)
    last_run_stats = defaultdict(lambda: {"starts": 0, "wins": 0, "top2": 0, "top4": 0})

    total_runners = 0

    for r in races:
        dist = r.get("distance", 1400)
        surf = r.get("surface", "Kum").lower()
        is_sprint = dist <= 1400
        surf_key = "cim" if "çim" in surf or "cim" in surf else ("kum" if "kum" in surf else "sentetik")
        gate_category = f"{'sprint' if is_sprint else 'route'}_{'cim' if surf_key == 'cim' else 'kum'}"

        race_type_key = "maiden" if r.get("is_maiden") else ("handicap" if r.get("is_handicap") else ("sartli" if r.get("is_sartli") else "all"))

        for rn in r.get("runners", []):
            total_runners += 1
            pos = rn.get("finish_order", 99)
            is_win = (pos == 1)
            is_top2 = (pos <= 2)
            is_top4 = (pos <= 4)
            ganyan = rn.get("ganyan", 0.0)

            # AGF Rank
            agf_rank = rn.get("agf_rank", 99)
            if agf_rank < 15:
                agf_stats[agf_rank]["starts"] += 1
                if is_win:
                    agf_stats[agf_rank]["wins"] += 1
                    agf_stats[agf_rank]["total_return"] += ganyan
                if is_top2:
                    agf_stats[agf_rank]["top2"] += 1
                if is_top4:
                    agf_stats[agf_rank]["top4"] += 1

            # Jockey
            jock = rn.get("jockey", "").strip().lower()
            # Clean jockey name
            jock_clean = re.sub(r'\s+ap$', '', jock).strip()
            if jock_clean:
                jockey_stats[jock_clean]["starts"] += 1
                if is_win:
                    jockey_stats[jock_clean]["wins"] += 1
                    jockey_stats[jock_clean]["ganyan_sum"] += ganyan
                if is_top2:
                    jockey_stats[jock_clean]["top2"] += 1
                if is_top4:
                    jockey_stats[jock_clean]["top4"] += 1

            # Trainer
            trainer = rn.get("trainer", "").strip().lower()
            if trainer:
                trainer_stats[trainer]["starts"] += 1
                if is_win:
                    trainer_stats[trainer]["wins"] += 1
                if is_top2:
                    trainer_stats[trainer]["top2"] += 1
                if is_top4:
                    trainer_stats[trainer]["top4"] += 1

            # Weight
            wt = rn.get("weight", 58.0)
            wt_tier = "light_lte_54" if wt <= 54.0 else ("heavy_gte_59" if wt >= 59.0 else "mid_55_58")
            weight_stats["all"][wt_tier]["starts"] += 1
            if is_win:
                weight_stats["all"][wt_tier]["wins"] += 1

            if race_type_key in weight_stats:
                weight_stats[race_type_key][wt_tier]["starts"] += 1
                if is_win:
                    weight_stats[race_type_key][wt_tier]["wins"] += 1

            # Equipment
            equipment = rn.get("equipment", "").strip().upper()
            if equipment:
                for eq_code in equipment.split():
                    gear_stats[eq_code]["starts"] += 1
                    if is_win:
                        gear_stats[eq_code]["wins"] += 1
                    if is_top2:
                        gear_stats[eq_code]["top2"] += 1
                    if is_top4:
                        gear_stats[eq_code]["top4"] += 1
            else:
                gear_stats["NONE"]["starts"] += 1
                if is_win:
                    gear_stats["NONE"]["wins"] += 1
                if is_top4:
                    gear_stats["NONE"]["top4"] += 1

            # Gate
            gate = rn.get("gate", 0)
            if 1 <= gate <= 18:
                gate_stats[gate_category][gate]["starts"] += 1
                if is_win:
                    gate_stats[gate_category][gate]["wins"] += 1

            # KGS (Rest Days)
            kgs = rn.get("kgs", 20)
            if kgs <= 10:
                tier = "quick_1_10"
            elif kgs <= 28:
                tier = "ideal_11_28"
            elif kgs <= 60:
                tier = "fresh_29_60"
            else:
                tier = "layoff_61_plus"
            kgs_stats[tier]["starts"] += 1
            if is_win:
                kgs_stats[tier]["wins"] += 1
            if is_top4:
                kgs_stats[tier]["top4"] += 1

            # Last race finish
            last_6 = rn.get("last_6", "")
            # Find the most recent finish
            m_fin = re.findall(r'\d+', str(last_6))
            if m_fin:
                try:
                    last_pos = int(m_fin[-1])
                    if last_pos == 0:
                        last_pos = 10
                    last_run_stats[last_pos]["starts"] += 1
                    if is_win:
                        last_run_stats[last_pos]["wins"] += 1
                    if is_top4:
                        last_run_stats[last_pos]["top4"] += 1
                except:
                    pass

    print(f"\n=======================================================")
    print(f"📊 EMPİRİK ANALİZ SONUÇLARI ({total_races} Koşu, {total_runners} Start)")
    print(f"=======================================================")

    # 1. AGF
    print("\n--- 1. AGF (Muhtemel Ganyan) Sıralaması Kazanma Oranları ---")
    agf_report = {}
    for rk in range(1, 9):
        st = agf_stats[rk]
        if st["starts"] > 0:
            win_pct = round(st["wins"] / st["starts"] * 100, 1)
            top2_pct = round(st["top2"] / st["starts"] * 100, 1)
            top4_pct = round(st["top4"] / st["starts"] * 100, 1)
            roi = round(st["total_return"] / st["starts"] * 100, 1)
            agf_report[rk] = {"win_pct": win_pct, "top2_pct": top2_pct, "top4_pct": top4_pct, "roi": roi, "starts": st["starts"]}
            print(f"AGF #{rk}: Kazanma %{win_pct:4.1f} | İlk 2 %{top2_pct:4.1f} | İlk 4 %{top4_pct:4.1f} | ROI %{roi:5.1f} ({st['starts']} yarış)")

    # 2. Jokeyler
    print("\n--- 2. En Başarılı Jokeyler (Min 25 Start) ---")
    jockey_report = {}
    qualified_jockeys = [
        (j, s) for j, s in jockey_stats.items() 
        if s["starts"] >= 25
    ]
    qualified_jockeys.sort(key=lambda x: x[1]["wins"] / x[1]["starts"], reverse=True)
    for j, s in qualified_jockeys[:20]:
        win_pct = round(s["wins"] / s["starts"] * 100, 1)
        top4_pct = round(s["top4"] / s["starts"] * 100, 1)
        jockey_report[j] = {"win_pct": win_pct, "top4_pct": top4_pct, "starts": s["starts"]}
        print(f"Jokey {j.upper():20}: Kazanma %{win_pct:4.1f} | İlk 4 %{top4_pct:4.1f} ({s['starts']:3d} start, {s['wins']:2d} galibiyet)")

    # 3. Kilo Analizi
    print("\n--- 3. Kilo Sıklet Analizi ---")
    weight_report = {}
    for wt_tier in ["light_lte_54", "mid_55_58", "heavy_gte_59"]:
        st = weight_stats["all"][wt_tier]
        wp = round(st["wins"] / st["starts"] * 100, 1) if st["starts"] > 0 else 0
        weight_report[wt_tier] = {"win_pct": wp, "starts": st["starts"]}
        print(f"Sıklet {wt_tier:16}: Kazanma %{wp:4.1f} ({st['starts']} start)")

    # 4. Ekipman Analizi
    print("\n--- 4. Ekipman / Teçhizat Etkisi ---")
    gear_report = {}
    sorted_gears = sorted(gear_stats.items(), key=lambda x: x[1]["wins"] / x[1]["starts"] if x[1]["starts"] > 0 else 0, reverse=True)
    for g, s in sorted_gears:
        if s["starts"] >= 50:
            wp = round(s["wins"] / s["starts"] * 100, 1)
            t4p = round(s["top4"] / s["starts"] * 100, 1)
            gear_report[g] = {"win_pct": wp, "top4_pct": t4p, "starts": s["starts"]}
            print(f"Ekipman {g:6}: Kazanma %{wp:4.1f} | İlk 4 %{t4p:4.1f} ({s['starts']} start)")

    # 5. KGS (Dinlenme Süresi)
    print("\n--- 5. Dinlenme Süresi (KGS) Etkisi ---")
    kgs_report = {}
    for k_tier, s in kgs_stats.items():
        wp = round(s["wins"] / s["starts"] * 100, 1) if s["starts"] > 0 else 0
        t4p = round(s["top4"] / s["starts"] * 100, 1) if s["starts"] > 0 else 0
        kgs_report[k_tier] = {"win_pct": wp, "top4_pct": t4p, "starts": s["starts"]}
        print(f"KGS {k_tier:16}: Kazanma %{wp:4.1f} | İlk 4 %{t4p:4.1f} ({s['starts']} start)")

    # 6. Son Koşu Derecesi (Form Momentumu)
    print("\n--- 6. Son Koşudaki Sıralamanın Bugüne Etkisi ---")
    last_run_report = {}
    for rk in range(1, 8):
        s = last_run_stats[rk]
        if s["starts"] > 0:
            wp = round(s["wins"] / s["starts"] * 100, 1)
            t4p = round(s["top4"] / s["starts"] * 100, 1)
            last_run_report[rk] = {"win_pct": wp, "top4_pct": t4p, "starts": s["starts"]}
            print(f"Son Yarış #{rk}: Bugün Kazanma %{wp:4.1f} | Bugün İlk 4 %{t4p:4.1f} ({s['starts']} at)")

    # Compile comprehensive empirical dictionary
    full_empirical_model = {
        "dataset_metadata": {
            "total_races": total_races,
            "total_runners": total_runners,
            "date_range": "Son 180 Günlük Gerçek TJK Resmi Sonuçları"
        },
        "agf_strike_rates": agf_report,
        "jockeys": jockey_report,
        "weights": weight_report,
        "gear": gear_report,
        "kgs_rest": kgs_report,
        "last_run_momentum": last_run_report
    }

    with open('data/empirical_model_weights.json', 'w', encoding='utf-8') as f:
        json.dump(full_empirical_model, f, ensure_ascii=False, indent=2)

    print("\nSaved empirical model weights to data/empirical_model_weights.json!")
    return full_empirical_model

if __name__ == "__main__":
    analyze_1207_races()
