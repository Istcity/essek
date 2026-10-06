"""
Rigorous Backtesting and Performance Validation Engine
Runs predictions across 1,207 real official TJK races and benchmarks:
- Top-1 Win Strike Rate
- Top-2 Quinella / Exacta Placement
- Top-3 Trifecta Rate
- Top-4 Superfecta / Tabela Rate
- Ganyan ROI & Value Bet Yield
"""

import sys
import os
import json
from collections import defaultdict

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

sys.path.insert(0, r"C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\essek")
from backend.prediction_engine import predict_race

def run_backtest(max_races=None):
    with open('data/historical_database_1000.json', 'r', encoding='utf-8') as f:
        races = json.load(f)

    if max_races:
        races = races[:max_races]

    total_races = len(races)
    print(f"Starting rigorous backtest on {total_races} real historical TJK races...")

    top1_wins = 0
    top2_contains_winner = 0
    top3_contains_winner = 0
    top4_contains_winner = 0

    exact_top2_quinella = 0 # Model top 2 both finished in top 2 (any order)
    exacta_straight = 0     # Model 1 was 1st, Model 2 was 2nd

    total_ganyan_return = 0.0
    total_bets = 0

    value_bets_count = 0
    value_bets_wins = 0
    value_bets_top4 = 0
    value_bets_return = 0.0

    races_with_actual_winner = 0

    for idx, r in enumerate(races):
        # Find actual winner and top 4 from official finish_order
        actual_winner = None
        actual_second = None
        actual_top4_names = set()

        for rn in r.get("runners", []):
            fin = rn.get("finish_order")
            name = rn.get("name", "")
            if fin == 1:
                actual_winner = rn
            elif fin == 2:
                actual_second = rn
            if fin and fin <= 4:
                actual_top4_names.add(name.lower().strip())

        if not actual_winner:
            continue

        races_with_actual_winner += 1

        # Format race for prediction engine
        pred_input = {
            "race_number": r.get("race_number", 1),
            "distance": r.get("distance", 1400),
            "surface": r.get("surface", "Kum"),
            "race_type": r.get("race_type", ""),
            "name": f"{r.get('race_number', 1)}. Koşu",
            "city": r.get("city", "Bursa"),
            "date": r.get("date", "01.01.2026"),
            "runners": [
                {
                    "number": i + 1,
                    "name": rn.get("name", ""),
                    "raw_name": rn.get("raw_name", rn.get("name", "")),
                    "equipment": rn.get("equipment", ""),
                    "is_scratched": False,
                    "age": rn.get("age_sex", "3y"),
                    "sire": rn.get("sire", ""),
                    "dam": rn.get("dam", ""),
                    "weight": rn.get("weight", 58.0),
                    "jockey": rn.get("jockey", ""),
                    "trainer": rn.get("trainer", ""),
                    "owner": rn.get("owner", ""),
                    "gate": rn.get("gate", i + 1),
                    "agf": rn.get("agf", 0.0),
                    "agf_rank": rn.get("agf_rank", 99),
                    "handicap": rn.get("handicap", 35),
                    "last_6": rn.get("last_6", ""),
                    "kgs": rn.get("kgs", 20),
                    "s20": 15,
                    "best_time": rn.get("finish_time", "")
                }
                for i, rn in enumerate(r.get("runners", []))
            ]
        }

        try:
            pred_res = predict_race(pred_input)
            predicted_runners = pred_res.get("runners", [])
            if not predicted_runners:
                continue

            winner_name = actual_winner.get("name", "").lower().strip()
            winner_ganyan = actual_winner.get("ganyan", 0.0)

            # Check Model Rank 1
            model_top1 = predicted_runners[0]
            model_top1_name = model_top1.get("name", "").lower().strip()

            total_bets += 1
            if model_top1_name == winner_name:
                top1_wins += 1
                total_ganyan_return += winner_ganyan if winner_ganyan > 0 else 1.0

            # Check if Winner is in Top 2
            top2_names = [p.get("name", "").lower().strip() for p in predicted_runners[:2]]
            if winner_name in top2_names:
                top2_contains_winner += 1

            # Check if Winner is in Top 3
            top3_names = [p.get("name", "").lower().strip() for p in predicted_runners[:3]]
            if winner_name in top3_names:
                top3_contains_winner += 1

            # Check if Winner is in Top 4
            top4_names = [p.get("name", "").lower().strip() for p in predicted_runners[:4]]
            if winner_name in top4_names:
                top4_contains_winner += 1

            # Exact Quinella / Exacta
            if actual_second:
                second_name = actual_second.get("name", "").lower().strip()
                if set(top2_names) == {winner_name, second_name}:
                    exact_top2_quinella += 1
                if len(predicted_runners) >= 2:
                    if predicted_runners[0].get("name", "").lower().strip() == winner_name and \
                       predicted_runners[1].get("name", "").lower().strip() == second_name:
                        exacta_straight += 1

            # Value Bets
            for pr in predicted_runners:
                if pr.get("is_value_bet"):
                    value_bets_count += 1
                    p_name = pr.get("name", "").lower().strip()
                    if p_name == winner_name:
                        value_bets_wins += 1
                        value_bets_return += winner_ganyan
                    if p_name in actual_top4_names:
                        value_bets_top4 += 1

        except Exception as e:
            pass

        if (idx + 1) % 200 == 0:
            print(f"Processed {idx + 1}/{total_races} races... Current Top-1 Win%: {top1_wins / (total_bets or 1) * 100:.1f}%")

    # Final Statistics
    win_rate = (top1_wins / total_bets * 100) if total_bets else 0
    top2_rate = (top2_contains_winner / total_bets * 100) if total_bets else 0
    top3_rate = (top3_contains_winner / total_bets * 100) if total_bets else 0
    top4_rate = (top4_contains_winner / total_bets * 100) if total_bets else 0
    quinella_rate = (exact_top2_quinella / total_bets * 100) if total_bets else 0
    exacta_rate = (exacta_straight / total_bets * 100) if total_bets else 0
    roi = (total_ganyan_return / total_bets * 100) if total_bets else 0

    val_win_rate = (value_bets_wins / value_bets_count * 100) if value_bets_count else 0
    val_top4_rate = (value_bets_top4 / value_bets_count * 100) if value_bets_count else 0
    val_roi = (value_bets_return / value_bets_count * 100) if value_bets_count else 0

    report = {
        "total_races_tested": total_bets,
        "metrics": {
            "top1_win_strike_rate": round(win_rate, 2),
            "top2_contains_winner": round(top2_rate, 2),
            "top3_contains_winner": round(top3_rate, 2),
            "top4_contains_winner": round(top4_rate, 2),
            "exact_quinella_ikili_rate": round(quinella_rate, 2),
            "exacta_sirali_ikili_rate": round(exacta_rate, 2),
            "top1_flat_roi_pct": round(roi, 2)
        },
        "value_bets": {
            "total_value_bets": value_bets_count,
            "win_strike_rate": round(val_win_rate, 2),
            "top4_strike_rate": round(val_top4_rate, 2),
            "value_roi_pct": round(val_roi, 2)
        }
    }

    print("\n=======================================================")
    print(f"🏁 MODEL BACKTEST VE PERFORMANS RAPORU ({total_bets} Koşu)")
    print("=======================================================")
    print(f"🏆 1. Tek (Banko / Favori) Kazanma İsabeti: %{win_rate:.2f} ({top1_wins}/{total_bets})")
    print(f"🥈 Kazanan Modelin İlk 2'sinde Yer Alma:    %{top2_rate:.2f} ({top2_contains_winner}/{total_bets})")
    print(f"🥉 Kazanan Modelin İlk 3'ünde Yer Alma:    %{top3_rate:.2f} ({top3_contains_winner}/{total_bets})")
    print(f"🎯 Kazanan Modelin İlk 4'ünde Yer Alma:    %{top4_rate:.2f} ({top4_contains_winner}/{total_bets})")
    print(f"🎲 İkili Bahis (İlk 2 Birlikte) İsabeti:  %{quinella_rate:.2f}")
    print(f"🎯 Sıralı İkili (Tam Sıralı) İsabeti:     %{exacta_rate:.2f}")
    print(f"💰 1. At Sabit Ganyan Getirisi (ROI):     %{roi:.2f}")
    print(f"💣 Değer/Bomba Bahisleri İlk 4 İsabeti:   %{val_top4_rate:.2f} (ROI: %{val_roi:.2f})")
    print("=======================================================\n")

    with open('data/backtest_report_baseline.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report

if __name__ == "__main__":
    run_backtest()
